"""
챗봇 서비스 - QLoRA 기반 대화 및 학습

PEFT의 QLoRA 방식을 사용하여:
- 대화형 LLM 인터페이스 제공
- 세션별 히스토리 관리
- QLoRA 기반 파인튜닝 학습
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel,
    TaskType,
)
from datasets import Dataset
import torch.nn as nn

from app.config import settings


@dataclass
class ChatMessage:
    """대화 메시지 데이터 클래스."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


@dataclass
class TrainingConfig:
    """QLoRA 학습 설정."""
    model_path: str
    output_dir: str = "checkpoints/qlora"
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: Optional[List[str]] = None
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    learning_rate: float = 2e-4
    max_seq_length: int = 512
    save_steps: int = 500
    logging_steps: int = 100
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True


class ChatService:
    """QLoRA 기반 챗봇 서비스."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        peft_model_path: Optional[str] = None,
    ):
        """
        초기화.

        Args:
            model_path: 기본 모델 경로 (None이면 app/model/midm 사용)
            peft_model_path: 학습된 PEFT 어댑터 경로 (None이면 기본 모델만 사용)
        """
        # 모델 경로 설정
        if model_path is None:
            # app/service/chat_service.py -> app/model/midm
            model_path = Path(__file__).parent.parent / "model" / "midm"
        else:
            model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"모델 경로를 찾을 수 없습니다: {model_path}\n"
                f"모델을 {model_path}에 설치하거나 model_path 인자를 지정해주세요."
            )

        self.model_path = str(model_path)
        self.peft_model_path = peft_model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.chat_history: List[ChatMessage] = []

        print(f"🤖 ChatService 초기화 중...")
        print(f"   모델 경로: {self.model_path}")
        print(f"   디바이스: {self.device}")

    def load_model(self, use_4bit: bool = True) -> None:
        """모델과 토크나이저를 로드합니다."""
        if self.model is not None:
            print("ℹ️ 모델이 이미 로드되어 있습니다.")
            return

        print("📝 토크나이저 로딩 중...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True,
        )

        # 패딩 토큰 설정
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        print("🧠 모델 로딩 중...")

        # 4-bit 양자화 설정
        if use_4bit and self.device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
            )

        # PEFT 어댑터가 있으면 로드
        if self.peft_model_path and Path(self.peft_model_path).exists():
            print(f"🔌 PEFT 어댑터 로딩 중: {self.peft_model_path}")
            self.model = PeftModel.from_pretrained(
                self.model,
                self.peft_model_path,
            )

        self.model.eval()
        print("✅ 모델 로딩 완료!")

    def chat(
        self,
        user_message: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        reset_history: bool = False,
    ) -> str:
        """
        사용자 메시지에 대한 응답을 생성합니다.

        Args:
            user_message: 사용자 메시지
            max_new_tokens: 최대 생성 토큰 수
            temperature: 생성 온도
            top_p: Top-p 샘플링
            reset_history: 대화 히스토리 초기화 여부

        Returns:
            생성된 응답
        """
        if self.model is None:
            self.load_model()

        if reset_history:
            self.chat_history = []

        # 사용자 메시지 추가
        self.chat_history.append(
            ChatMessage(role="user", content=user_message)
        )

        # 대화 히스토리를 프롬프트로 변환
        prompt = self._format_chat_history()

        # 토크나이징 (token_type_ids 제거)
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
            return_token_type_ids=False,  # token_type_ids 제거
        ).to(self.device)

        # token_type_ids가 있으면 제거
        if "token_type_ids" in inputs:
            inputs.pop("token_type_ids")

        # 생성 (token_type_ids 제외하고 전달)
        generate_kwargs = {
            "input_ids": inputs["input_ids"],
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": True,
            "pad_token_id": self.tokenizer.eos_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }

        # attention_mask가 있으면 포함
        if "attention_mask" in inputs:
            generate_kwargs["attention_mask"] = inputs["attention_mask"]

        with torch.no_grad():
            outputs = self.model.generate(**generate_kwargs)

        # 디코딩
        generated_text = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()

        # 어시스턴트 응답 추가
        self.chat_history.append(
            ChatMessage(role="assistant", content=generated_text)
        )

        return generated_text

    def _format_chat_history(self) -> str:
        """대화 히스토리를 프롬프트 형식으로 변환합니다."""
        prompt_parts = []
        for msg in self.chat_history:
            if msg.role == "user":
                prompt_parts.append(f"### 사용자:\n{msg.content}\n")
            elif msg.role == "assistant":
                prompt_parts.append(f"### 어시스턴트:\n{msg.content}\n")

        # 마지막 사용자 메시지에 대한 응답 요청
        prompt_parts.append("### 어시스턴트:\n")

        return "".join(prompt_parts)

    def train_qlora(
        self,
        training_data: List[Dict[str, str]],
        config: Optional[TrainingConfig] = None,
    ) -> str:
        """
        QLoRA 방식으로 모델을 파인튜닝합니다.

        Args:
            training_data: 학습 데이터 리스트 [{"instruction": "...", "input": "...", "output": "..."}]
            config: 학습 설정 (None이면 기본값 사용)

        Returns:
            학습된 모델 저장 경로
        """
        if config is None:
            config = TrainingConfig(model_path=self.model_path)

        print("🚀 QLoRA 학습 시작...")
        print(f"   학습 데이터: {len(training_data)}개")
        print(f"   출력 디렉토리: {config.output_dir}")

        # 모델 로드 (학습용)
        if self.model is None:
            self.load_model(use_4bit=config.use_4bit)

        # 데이터셋 준비
        dataset = self._prepare_dataset(training_data, config.max_seq_length)

        # LoRA 설정
        if config.target_modules is None:
            # Midm 모델의 기본 타겟 모듈
            config.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

        lora_config = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            target_modules=config.target_modules,
            lora_dropout=config.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

        # 모델을 학습 가능하도록 준비
        if config.use_4bit:
            self.model = prepare_model_for_kbit_training(self.model)

        # PEFT 모델 적용
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        # 학습 인자 설정
        training_args = TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            learning_rate=config.learning_rate,
            fp16=True,
            logging_steps=config.logging_steps,
            save_steps=config.save_steps,
            save_total_limit=3,
            optim="paged_adamw_8bit",
            warmup_steps=100,
            report_to="none",
        )

        # 데이터 콜레이터
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        # Trainer 생성
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
        )

        # 학습 실행
        print("📚 학습 중...")
        trainer.train()

        # 모델 저장
        output_path = Path(config.output_dir) / "final"
        output_path.mkdir(parents=True, exist_ok=True)
        trainer.save_model(str(output_path))

        print(f"✅ 학습 완료! 모델 저장 경로: {output_path}")

        return str(output_path)

    def _prepare_dataset(
        self,
        training_data: List[Dict[str, str]],
        max_length: int,
    ) -> Dataset:
        """학습 데이터를 토크나이징하여 Dataset으로 변환합니다."""
        def format_prompt(example):
            """프롬프트 포맷팅."""
            instruction = example.get("instruction", "")
            input_text = example.get("input", "")
            output = example.get("output", "")

            if input_text:
                prompt = f"### 지시사항:\n{instruction}\n\n### 입력:\n{input_text}\n\n### 응답:\n{output}"
            else:
                prompt = f"### 지시사항:\n{instruction}\n\n### 응답:\n{output}"

            return {"text": prompt}

        # 데이터셋 생성
        dataset = Dataset.from_list(training_data)
        dataset = dataset.map(format_prompt)

        # 토크나이징
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_length,
                padding="max_length",
            )

        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
        )

        return tokenized_dataset

    def save_chat_history(self, filepath: str) -> None:
        """대화 히스토리를 파일로 저장합니다."""
        history_dict = [
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
            for msg in self.chat_history
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history_dict, f, ensure_ascii=False, indent=2)
        print(f"💾 대화 히스토리 저장: {filepath}")

    def load_chat_history(self, filepath: str) -> None:
        """파일에서 대화 히스토리를 로드합니다."""
        with open(filepath, "r", encoding="utf-8") as f:
            history_dict = json.load(f)
        self.chat_history = [
            ChatMessage(**msg) for msg in history_dict
        ]
        print(f"📂 대화 히스토리 로드: {filepath}")

    def clear_history(self) -> None:
        """대화 히스토리를 초기화합니다."""
        self.chat_history = []
        print("🗑️ 대화 히스토리 초기화됨")
