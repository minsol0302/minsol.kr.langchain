"""FastAPI 메인 애플리케이션."""

import sys
from pathlib import Path

# Python 경로 설정: app 모듈을 찾을 수 있도록 경로 추가
current_file = Path(__file__).absolute()
# main.py가 /home/ubuntu/rag-app/app/main.py 또는 /home/ubuntu/rag-app/main.py에 있을 수 있음
if current_file.name == 'main.py':
    # main.py가 있는 디렉토리의 부모 디렉토리(프로젝트 루트)를 sys.path에 추가
    project_root = current_file.parent.parent if current_file.parent.name == 'app' else current_file.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import asyncio
from contextlib import asynccontextmanager

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.models import HealthResponse
from app.api.routes import search
from app.router import chat_router


def wait_for_postgres() -> None:
    """PostgreSQL 데이터베이스가 준비될 때까지 대기.

    Docker 컨테이너 대신 외부(Postgres/Neon 등) 인스턴스를 사용하므로,
    `Settings.database_url`을 사용해 접속을 시도합니다.
    """
    import time

    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            # DATABASE_URL 포함: postgresql://... 형태의 전체 URI 사용
            conn = psycopg2.connect(settings.database_url)
            conn.close()
            print("✅ PostgreSQL 데이터베이스 연결 성공!")
            return
        except psycopg2.OperationalError as exc:
            retry_count += 1
            print(
                f"⏳ PostgreSQL 연결 대기 중... ({retry_count}/{max_retries}) - {exc}"
            )
            time.sleep(2)

    raise Exception("PostgreSQL 데이터베이스에 연결할 수 없습니다.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 함수."""
    # 시작 시
    print("🚀 FastAPI RAG 애플리케이션 시작 중...")
    wait_for_postgres()
    print("🔧 벡터스토어 초기화 중...")
    # 순환 의존성을 피하기 위해 지연 임포트
    from app.core.vectorstore import initialize_vectorstore

    initialize_vectorstore()

    # 🔧 ChatService 초기화 및 모델 로드
    from app.service.chat_service import ChatService
    from pathlib import Path

    print("🤖 ChatService 초기화 중...")
    # 모델 경로 명시적으로 지정 (app/model/midm)
    model_path = Path(__file__).parent / "model" / "midm"

    # 모델 경로가 없으면 경고만 출력하고 계속 진행
    if not model_path.exists():
        print(f"⚠️ 모델 경로를 찾을 수 없습니다: {model_path}")
        print("⚠️ ChatService를 초기화하지 않고 계속 진행합니다.")
        app.state.chat_service = None
    else:
        try:
            chat_service = ChatService(model_path=str(model_path))
            chat_service.load_model(use_4bit=True)
            app.state.chat_service = chat_service
            print("✅ ChatService 초기화 완료!")
        except Exception as e:
            print(f"⚠️ ChatService 초기화 실패: {e}")
            print("⚠️ ChatService 없이 계속 진행합니다.")
            app.state.chat_service = None

    # 🔧 LLM 생성 및 전역 설정 (하위 호환성을 위해 유지)
    from app.core.llm import create_llm_from_config

    llm = create_llm_from_config(settings)
    if llm:
        print("✅ 사용자 정의 LLM이 설정되었습니다.")
        # 전역 변수로 저장하여 라우터에서 사용
        app.state.llm = llm
    else:
        print("⚠️ LLM 설정이 불완전합니다. 기본 동작으로 실행합니다.")
        app.state.llm = None
    print("✅ 애플리케이션 준비 완료!")
    yield
    # 종료 시
    print("👋 애플리케이션 종료 중...")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="LangChain과 pgvector를 사용한 RAG API 서버",
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(search.router)
app.include_router(chat_router.router)


@app.get("/", tags=["root"])
async def root() -> dict:
    """루트 엔드포인트."""
    return {
        "message": "LangChain RAG API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """헬스체크 엔드포인트."""
    try:
        # 데이터베이스 연결 확인 (DATABASE_URL 기반)
        conn = psycopg2.connect(settings.database_url)
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database=db_status,
        openai_configured=settings.openai_api_key is not None,
    )

# python -m app.main (프로젝트 루트에서)
# 또는 python main.py (app 디렉토리에서)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

