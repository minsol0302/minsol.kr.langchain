# LangChain Chatbot - Next.js PWA

LangChain과 pgvector를 사용한 AI 챗봇 애플리케이션입니다. Next.js로 구축된 PWA(Progressive Web App)입니다.

## 구조

- **Backend**: FastAPI 서버 (LangChain + pgvector)
- **Frontend**: Next.js PWA (React + TypeScript)
- **Database**: PostgreSQL with pgvector extension

## 시작하기

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### 2. Docker Compose로 실행

```bash
docker-compose up --build
```

이 명령은 다음 서비스를 시작합니다:
- PostgreSQL (포트 5432)
- LangChain Backend API (포트 8000)
- Next.js Frontend (포트 3000)

### 3. 접속

브라우저에서 http://localhost:3000 으로 접속하세요.

## 개발 모드

### Backend만 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend만 실행

```bash
cd webapp
npm install
npm run dev
```

## PWA 기능

이 애플리케이션은 PWA로 구성되어 있어:
- 모바일 기기에 설치 가능
- 오프라인에서도 기본 기능 사용 가능 (Service Worker)
- 앱처럼 실행 가능

### 모바일에서 설치하기

1. 브라우저에서 사이트 접속
2. 브라우저 메뉴에서 "홈 화면에 추가" 선택
3. 앱이 설치됩니다

## API 엔드포인트

### POST /chat

챗봇과 대화하기

**Request:**
```json
{
  "message": "What is LangChain?",
  "conversation_id": "optional-conversation-id"
}
```

**Response:**
```json
{
  "response": "LangChain is a framework...",
  "conversation_id": "conv-123",
  "sources": [
    {
      "content": "LangChain is a framework...",
      "metadata": {...}
    }
  ]
}
```

### GET /health

서비스 상태 확인

## 문제 해결

### 백엔드가 시작되지 않는 경우

1. `.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는지 확인
2. PostgreSQL이 정상적으로 실행 중인지 확인: `docker-compose ps`
3. 백엔드 로그 확인: `docker-compose logs langchain-backend`

### 프론트엔드가 백엔드에 연결되지 않는 경우

1. `docker-compose.yaml`의 `NEXT_PUBLIC_API_URL` 확인
2. 브라우저 개발자 도구의 Network 탭에서 API 호출 확인
3. CORS 설정 확인 (백엔드의 `main.py`)

## 기술 스택

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **AI/ML**: LangChain, OpenAI API
- **Database**: PostgreSQL, pgvector
- **Containerization**: Docker, Docker Compose

