# 로컬 개발 환경 설정 가이드

이 프로젝트는 Docker 없이 로컬 환경에서 직접 실행할 수 있습니다.

## 📋 사전 요구사항

- Python 3.11 이상
- Node.js 20 이상 및 npm
- Neon PostgreSQL 계정 (또는 다른 PostgreSQL + pgvector)

## 🚀 빠른 시작

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# OpenAI API Key (필수)
OPENAI_API_KEY=your-openai-api-key-here

# Neon PostgreSQL 연결 문자열 (필수)
DATABASE_URL=postgresql://neondb_owner:npg_2CUgeTP5KBuO@ep-restless-cell-a1n05rxq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# 선택적 설정
DEBUG=false
LLM_PROVIDER=openai
```

### 2. 백엔드 (FastAPI) 설정 및 실행

**⚠️ 중요: 프로젝트 루트(`RAG`)에서 실행해야 합니다!**

```bash
# 프로젝트 루트에서 Python 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 백엔드 의존성 설치
pip install -r app/requirements.txt

# 프로젝트 루트에서 FastAPI 서버 실행
# 방법 1: uvicorn 사용 (권장)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 방법 2: Python 모듈로 실행
python -m app.main

# 방법 3: app 디렉토리에서 직접 실행 (app 디렉토리로 이동 후)
cd app
python main.py
```

백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

**API 문서**: http://localhost:8000/docs

### 3. 프론트엔드 (Next.js) 설정 및 실행

새 터미널 창에서:

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install
# 또는
npm ci

# 개발 서버 실행
npm run dev
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

### 4. 데모 스크립트 실행 (선택사항)

새 터미널 창에서:

```bash
# 프로젝트 루트로 이동
cd ..

# Python 가상환경 활성화 (백엔드와 동일)
# Windows:
app\venv\Scripts\activate
# macOS/Linux:
source app/venv/bin/activate

# 데모 스크립트 실행
python app.py
```

## 📁 프로젝트 구조

```
RAG/
├── app/                    # 백엔드 (FastAPI)
│   ├── main.py            # FastAPI 메인 애플리케이션
│   ├── requirements.txt   # Python 의존성
│   ├── api/               # API 라우터
│   ├── core/              # 핵심 로직 (RAG, LLM, VectorStore)
│   └── config.py          # 설정 관리
│
├── frontend/              # 프론트엔드 (Next.js)
│   ├── package.json       # Node.js 의존성
│   ├── app/               # Next.js 앱 라우터
│   └── components/        # React 컴포넌트
│
├── app.py                 # 데모 스크립트
├── requirements.txt       # 데모 스크립트 의존성
└── .env                   # 환경 변수 (생성 필요)
```

## 🔧 주요 명령어

### 백엔드

**⚠️ 모든 명령어는 프로젝트 루트(`RAG`)에서 실행하세요!**

```bash
# 개발 모드 (자동 리로드) - 권장
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 특정 포트로 실행
uvicorn app.main:app --port 8080

# Python 모듈로 실행 (프로젝트 루트에서)
python -m app.main
```

### 프론트엔드

```bash
# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행
npm start

# 린트 검사
npm run lint
```

## 🌐 API 엔드포인트

백엔드가 실행되면 다음 엔드포인트를 사용할 수 있습니다:

- `GET /` - 루트 엔드포인트
- `GET /health` - 헬스체크
- `GET /docs` - Swagger UI 문서
- `GET /redoc` - ReDoc 문서
- `POST /api/search` - 벡터 검색
- `POST /api/rag` - RAG 쿼리

## 🔍 문제 해결

### 백엔드가 시작되지 않을 때

1. **작업 디렉토리 확인**: 프로젝트 루트(`RAG`)에서 실행해야 합니다
   - ❌ 잘못된 방법: `cd app` 후 `python -m app.main`
   - ✅ 올바른 방법: 프로젝트 루트에서 `uvicorn app.main:app --reload`

2. Python 버전 확인: `python --version` (3.11 이상 필요)

3. 의존성 설치 확인: `pip list`로 필요한 패키지가 설치되었는지 확인

4. 환경 변수 확인: `.env` 파일이 프로젝트 루트에 있고 올바른지 확인

5. 포트 충돌 확인: 8000 포트가 사용 중인지 확인
   ```bash
   # Windows
   netstat -ano | findstr :8000
   # macOS/Linux
   lsof -i :8000
   ```

6. ModuleNotFoundError 발생 시:
   - 프로젝트 루트에서 실행 중인지 확인
   - `PYTHONPATH` 환경 변수 설정: `set PYTHONPATH=.` (Windows) 또는 `export PYTHONPATH=.` (macOS/Linux)

### 프론트엔드가 시작되지 않을 때

1. Node.js 버전 확인: `node --version` (20 이상 권장)
2. 의존성 재설치: `rm -rf node_modules && npm install`
3. 포트 충돌 확인: 3000 포트가 사용 중인지 확인

### 데이터베이스 연결 오류

1. Neon PostgreSQL에서 pgvector 확장 활성화:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. 연결 문자열 확인: `.env`의 `DATABASE_URL`이 올바른지 확인

3. 네트워크 연결 확인: Neon 데이터베이스가 접근 가능한지 확인

## 📝 참고사항

- 백엔드와 프론트엔드는 독립적으로 실행할 수 있습니다
- 프론트엔드는 백엔드 API를 `http://localhost:8000`에서 찾습니다
- 환경 변수는 `.env` 파일에서 자동으로 로드됩니다
- 개발 중에는 `DEBUG=true`로 설정하여 자동 리로드를 활성화할 수 있습니다
