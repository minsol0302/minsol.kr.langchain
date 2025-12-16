# 프로젝트 연결 상태 확인

## ✅ 연결 상태 요약

### 1. **Next.js ↔ LangChain Backend (FastAPI)**
- **상태**: ✅ 연결됨
- **연결 방식**: HTTP REST API
- **엔드포인트**: `http://localhost:8000/chat`
- **코드 위치**:
  - Frontend: `webapp/app/page.tsx` (line 48)
  - Backend: `backend/main.py` (line 197)

### 2. **LangChain Backend ↔ PostgreSQL (pgvector)**
- **상태**: ✅ 연결됨
- **연결 방식**: SQLAlchemy + psycopg2
- **Connection String**: `postgresql://postgres:postgres@postgres:5432/postgres`
- **Vector Store**: PGVector 사용
- **컬렉션**: `langchain_chatbot_v2`
- **코드 위치**: `backend/main.py` (line 97-101)
- **확인**: 로그에 "✓ Collection already has 3 documents" 표시됨

### 3. **LangChain Backend ↔ OpenAI API**
- **상태**: ✅ 연결됨
- **사용 모델**:
  - Embeddings: `text-embedding-3-small` (1536 차원)
  - LLM: `gpt-3.5-turbo`
- **코드 위치**:
  - Embeddings: `backend/main.py` (line 90-93)
  - LLM: `backend/main.py` (line 146-150)

### 4. **Docker 컨테이너 네트워크**
- **상태**: ✅ 모든 컨테이너 실행 중
- **서비스**:
  - `langchain-postgres`: PostgreSQL with pgvector (포트 5432)
  - `langchain-backend`: FastAPI 서버 (포트 8000)
  - `langchain-frontend`: Next.js 앱 (포트 3000)
  - `langchain-app`: 데모 스크립트

## 연결 흐름도

```
사용자 (브라우저)
    ↓
Next.js Frontend (localhost:3000)
    ↓ HTTP POST /chat
FastAPI Backend (localhost:8000)
    ↓
    ├─→ OpenAI API (Embeddings + Chat)
    │   └─→ text-embedding-3-small (벡터 생성)
    │   └─→ gpt-3.5-turbo (응답 생성)
    │
    └─→ PostgreSQL (pgvector)
        └─→ langchain_chatbot_v2 컬렉션
            └─→ 벡터 검색 (RAG)
```

## 확인 방법

### 백엔드 상태 확인
```bash
docker-compose logs langchain-backend | grep "initialized"
```

### 프론트엔드 확인
브라우저에서 http://localhost:3000 접속

### API 테스트
브라우저 개발자 도구 → Network 탭에서 `/chat` 요청 확인

## 현재 설정

- **OpenAI Embeddings**: text-embedding-3-small (1536 차원)
- **OpenAI LLM**: gpt-3.5-turbo
- **Vector Store**: PGVector (PostgreSQL + pgvector)
- **Collection**: langchain_chatbot_v2
- **초기 문서**: 3개 (LangChain, pgvector, Vector stores 관련)

