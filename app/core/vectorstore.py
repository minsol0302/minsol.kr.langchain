"""벡터스토어 설정 및 관리 (Neon Postgres + pgvector).

로컬 Docker 컨테이너의 Postgres/pgvector 대신,
외부에서 제공되는 Postgres (예: Neon) 인스턴스를 사용합니다.

연결 정보는 `app.config.Settings.database_url` 을 통해 주입되며,
이는 `.env` 의 `DATABASE_URL` 값(없으면 기존 POSTGRES_* 조합)을 사용합니다.
"""

from typing import List

import psycopg2
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector

from app.config import settings


class SimpleEmbeddings(Embeddings):
    """간단한 더미 임베딩 클래스 (OpenAI API 키가 없을 때 사용)."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 임베딩으로 변환."""
        return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        """쿼리를 임베딩으로 변환."""
        return [0.1, 0.2, 0.3, 0.4, 0.5]


def get_embeddings() -> Embeddings:
    """임베딩 모델 반환."""
    if settings.openai_api_key:
        return OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
    return SimpleEmbeddings()


def get_connection_string() -> str:
    """PGVector에 사용할 데이터베이스 연결 문자열 반환."""
    return settings.database_url


def get_vectorstore() -> "PGVector":
    """PGVector 벡터스토어 인스턴스 반환 (Neon 등 외부 Postgres 사용)."""
    embeddings = get_embeddings()
    connection_string = get_connection_string()

    vectorstore = PGVector(
        connection_string=connection_string,
        embedding_function=embeddings,
        collection_name="langchain_collection",
    )
    return vectorstore


def add_sample_documents(vectorstore: "PGVector") -> None:
    """샘플 문서들을 벡터스토어에 추가."""
    sample_docs = [
        Document(
            page_content="LangChain은 대규모 언어 모델을 활용한 애플리케이션 개발을 위한 프레임워크입니다.",
            metadata={"source": "langchain_intro", "type": "definition"},
        ),
        Document(
            page_content="pgvector는 PostgreSQL에서 벡터 유사도 검색을 가능하게 하는 확장입니다.",
            metadata={"source": "pgvector_intro", "type": "definition"},
        ),
        Document(
            page_content="Docker는 애플리케이션을 컨테이너로 패키징하여 배포를 쉽게 만드는 플랫폼입니다.",
            metadata={"source": "docker_intro", "type": "definition"},
        ),
        Document(
            page_content="Python은 데이터 과학과 AI 개발에 널리 사용되는 프로그래밍 언어입니다.",
            metadata={"source": "python_intro", "type": "definition"},
        ),
        Document(
            page_content="FastAPI는 현대적이고 빠른 웹 프레임워크로, 자동 API 문서화와 타입 검증을 제공합니다.",
            metadata={"source": "fastapi_intro", "type": "definition"},
        ),
    ]
    vectorstore.add_documents(sample_docs)


def initialize_vectorstore() -> "PGVector":
    """벡터스토어 초기화 및 샘플 데이터 추가.

    원격 Postgres를 사용하므로, 단 한 번 초기화되면 이후에는
    같은 컬렉션을 계속 재사용합니다.

    벡터 차원 불일치 오류가 발생하면 기존 컬렉션을 삭제하고 재생성합니다.
    """
    import psycopg2

    vectorstore = get_vectorstore()

    try:
        existing_docs = vectorstore.similarity_search("test", k=1)
        if not existing_docs:
            add_sample_documents(vectorstore)
    except (psycopg2.errors.DataException, Exception) as e:
        # 벡터 차원 불일치 오류 감지
        error_str = str(e)
        if "different vector dimensions" in error_str:
            print("⚠️ 벡터 차원 불일치 감지! 기존 컬렉션을 삭제하고 재생성합니다...")
            try:
                conn = psycopg2.connect(settings.database_url)
                cur = conn.cursor()

                # 컬렉션 UUID 찾기
                cur.execute(
                    """
                    SELECT uuid FROM langchain_pg_collection
                    WHERE name = %s
                    """,
                    ("langchain_collection",),
                )
                result = cur.fetchone()

                if result:
                    collection_uuid = result[0]
                    # 컬렉션의 모든 임베딩 삭제
                    cur.execute(
                        """
                        DELETE FROM langchain_pg_embedding
                        WHERE collection_id = %s
                        """,
                        (collection_uuid,),
                    )
                    # 컬렉션 삭제
                    cur.execute(
                        """
                        DELETE FROM langchain_pg_collection
                        WHERE uuid = %s
                        """,
                        (collection_uuid,),
                    )
                    conn.commit()
                    print("✅ 기존 컬렉션 삭제 완료")

                cur.close()
                conn.close()

                # 새로운 벡터스토어 생성 및 샘플 문서 추가
                vectorstore = get_vectorstore()
                add_sample_documents(vectorstore)
                print("✅ 새로운 벡터로 재생성 완료")
            except Exception as cleanup_error:
                print(f"❌ 컬렉션 재생성 중 오류: {cleanup_error}")
                # 재시도: 샘플 문서 추가
                add_sample_documents(vectorstore)
        else:
            # 다른 오류의 경우 그냥 샘플 문서 추가 시도
            add_sample_documents(vectorstore)
        # 테이블/컬렉션이 없거나 기타 오류가 있을 경우 샘플 문서를 추가
        add_sample_documents(vectorstore)

    return vectorstore


# 라우터에서 사용할 타입 별칭
VectorStoreType = PGVector
