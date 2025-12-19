# OpenAI API 전환 가이드

## 개요

로컬 LLM에서 OpenAI API 기반으로 전환했습니다. 비용 최적화를 위해 gpt-3.5-turbo를 사용하며, 토큰 제한 및 프롬프트 최적화를 적용했습니다.

## 주요 변경사항

### 1. 새로운 서비스: `OpenAIService`
- 위치: `app/service/openai_service.py`
- 기능:
  - OpenAI Chat Completions API 사용
  - RAG 기반 질의응답 지원
  - 비용 최적화 (max_tokens 제한, 간결한 프롬프트)

### 2. 라우터 업데이트
- `app/router/chat_router.py`: OpenAI 서비스 사용으로 변경
- 기존 엔드포인트 유지: `POST /rag/query`

### 3. 의존성 변경
- 로컬 LLM 관련 패키지 제거 (transformers, peft, datasets 등)
- OpenAI 패키지 사용 (이미 langchain-openai에 포함)

## 환경 변수 설정

`.env` 파일에 다음을 추가하세요:

```bash
# 필수
OPENAI_API_KEY=sk-...

# 선택사항 (기본값: gpt-3.5-turbo)
OPENAI_MODEL=gpt-3.5-turbo
```

## API 사용 예제

### Swagger UI에서 테스트
1. `http://your-server:8000/docs` 접속
2. `POST /rag/query` 엔드포인트 선택
3. 요청 본문:
```json
{
  "question": "질문 내용",
  "k": 3
}
```

### cURL 예제
```bash
curl -X POST "http://your-server:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "질문 내용",
    "k": 3
  }'
```

### Python 예제
```python
import requests

response = requests.post(
    "http://your-server:8000/rag/query",
    json={
        "question": "질문 내용",
        "k": 3
    }
)
print(response.json())
```

## 비용 최적화

### 1. 모델 선택
- `gpt-3.5-turbo`: 가장 저렴한 옵션
- `gpt-4`: 더 정확하지만 비용이 높음 (필요시 사용)

### 2. 토큰 제한
- 기본 `max_tokens`: 500
- 필요시 조정 가능 (서비스 초기화 시)

### 3. 프롬프트 최적화
- System prompt 최소화
- 컨텍스트 길이 제한
- 불필요한 설명 제거

### 4. 예상 비용 (gpt-3.5-turbo)
- Input: $0.50 / 1M tokens
- Output: $1.50 / 1M tokens
- 예: 1000 토큰 입력 + 500 토큰 출력 ≈ $0.00125

## 배포

### EC2 배포
1. `.env` 파일에 `OPENAI_API_KEY` 추가
2. GitHub Actions로 자동 배포 또는 수동 배포
3. 서비스 재시작:
```bash
sudo systemctl restart fastapi-rag
```

### Vercel 프론트엔드 연동
- API 엔드포인트: `http://your-ec2-ip:8000/rag/query`
- CORS 설정: 이미 활성화됨
- JSON 응답 형식:
```json
{
  "question": "질문",
  "answer": "답변",
  "sources": [
    {
      "content": "문서 내용",
      "metadata": {}
    }
  ]
}
```

## 문제 해결

### OpenAI API 키 오류
```
ValueError: OpenAI API 키가 설정되지 않았습니다
```
- `.env` 파일에 `OPENAI_API_KEY` 확인
- 환경변수 로드 확인

### 모듈 오류
```
ModuleNotFoundError: No module named 'openai'
```
- `pip install openai>=1.0.0` 실행
- 또는 `pip install -r requirements.txt` 재실행

### 비용 모니터링
- OpenAI 대시보드에서 사용량 확인
- `OpenAIService.estimate_cost()` 메서드로 예상 비용 계산

## 추가 기능 (선택사항)

### Streaming 지원
현재는 비활성화되어 있지만, 필요시 `openai_service.py`에 추가 가능:
```python
stream = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    stream=True,
)
```

### 대화 히스토리 관리
`conversation_history` 파라미터로 세션별 히스토리 관리 가능

## 롤백 방법

로컬 LLM으로 되돌리려면:
1. `app/main.py`에서 OpenAI 서비스 초기화 제거
2. `app/router/chat_router.py`에서 ChatService 사용으로 변경
3. `requirements.txt`에 transformers, peft 등 추가
