"""
OpenAI API 기반 챗봇 서비스

비용 최소화를 위한 최적화:
- gpt-3.5-turbo 사용
- max_tokens 제한
- system prompt 최소화
- streaming 선택사항
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import os

from openai import OpenAI
from app.config import settings


@dataclass
class ChatMessage:
    """대화 메시지 데이터 클래스."""
    role: str  # "system", "user", "assistant"
    content: str


class OpenAIService:
    """OpenAI API를 사용한 챗봇 서비스."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        OpenAI 서비스 초기화.

        Args:
            api_key: OpenAI API 키 (None이면 settings에서 가져옴)
            model: 사용할 모델 (기본값: gpt-3.5-turbo)
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경변수를 설정하세요.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.default_max_tokens = 500  # 비용 절감을 위한 기본 토큰 제한
        self.default_temperature = 0.7

    def chat(
        self,
        user_message: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> str:
        """
        OpenAI Chat Completions API를 사용하여 응답 생성.

        Args:
            user_message: 사용자 메시지
            context: RAG 컨텍스트 (선택사항)
            system_prompt: 시스템 프롬프트 (최소화 권장)
            max_tokens: 최대 토큰 수 (기본값: 500)
            temperature: 온도 (기본값: 0.7)
            conversation_history: 대화 히스토리 (선택사항)

        Returns:
            생성된 응답 텍스트
        """
        messages = []

        # 시스템 프롬프트 (최소화)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        elif context:
            # 컨텍스트가 있으면 간단한 시스템 프롬프트 추가
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant. Answer based on the provided context."
            })

        # 대화 히스토리 추가
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})

        # 컨텍스트와 사용자 메시지 구성
        if context:
            user_content = f"""다음 컨텍스트를 바탕으로 질문에 답해주세요:

컨텍스트:
{context}

질문: {user_message}

답변:"""
        else:
            user_content = user_message

        messages.append({"role": "user", "content": user_content})

        # API 호출
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature or self.default_temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API 호출 실패: {str(e)}")

    def chat_with_rag(
        self,
        question: str,
        context: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        RAG 기반 질의응답 (간편 메서드).

        Args:
            question: 질문
            context: 검색된 컨텍스트
            max_tokens: 최대 토큰 수
            temperature: 온도

        Returns:
            생성된 응답
        """
        return self.chat(
            user_message=question,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
        """
        예상 비용 계산 (gpt-3.5-turbo 기준).

        Args:
            prompt_tokens: 프롬프트 토큰 수
            completion_tokens: 완성 토큰 수

        Returns:
            비용 정보 딕셔너리
        """
        # gpt-3.5-turbo 가격 (2024년 기준, 실제 가격은 OpenAI 문서 확인)
        # Input: $0.50 / 1M tokens
        # Output: $1.50 / 1M tokens
        input_cost_per_1k = 0.0005  # $0.50 / 1000
        output_cost_per_1k = 0.0015  # $1.50 / 1000

        input_cost = (prompt_tokens / 1000) * input_cost_per_1k
        output_cost = (completion_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
        }
