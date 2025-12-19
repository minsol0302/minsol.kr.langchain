"""
챗봇 API 라우터.

RAG (Retrieval-Augmented Generation) 기반 챗봇 엔드포인트를 제공합니다.
OpenAI API를 사용하여 응답을 생성합니다.
POST /rag/query - RAG 질의 수행
GET /rag/health - RAG 서비스 헬스체크
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request

from app.api.models import RAGRequest, RAGResponse, DocumentResponse
from app.core.vectorstore import get_vectorstore, VectorStoreType
from app.service.openai_service import OpenAIService

router = APIRouter(prefix="/rag", tags=["rag"])


def get_vectorstore_dependency() -> VectorStoreType:
    """벡터스토어 의존성 주입."""
    return get_vectorstore()


def get_openai_service(fastapi_request: Request) -> OpenAIService:
    """OpenAI 서비스 의존성 주입."""
    openai_service = getattr(fastapi_request.app.state, 'openai_service', None)
    if not openai_service:
        raise HTTPException(
            status_code=500,
            detail="OpenAI 서비스가 초기화되지 않았습니다. OPENAI_API_KEY를 확인하세요."
        )
    return openai_service


@router.post("/query", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    vectorstore: VectorStoreType = Depends(get_vectorstore_dependency),
    openai_service: OpenAIService = Depends(get_openai_service),
) -> RAGResponse:
    """
    RAG (Retrieval-Augmented Generation) 질의를 수행합니다.

    OpenAI API를 사용하여 응답을 생성합니다.

    - **question**: 질문 내용
    - **k**: 검색에 사용할 문서 개수 (1-10, 기본값: 3)

    비용 최적화:
    - gpt-3.5-turbo 사용
    - max_tokens 제한 (기본 500)
    - 간결한 프롬프트 사용
    """
    try:
        # 검색된 문서 가져오기
        retriever = vectorstore.as_retriever(search_kwargs={"k": request.k})
        source_docs = retriever.invoke(request.question)

        # 검색된 문서를 컨텍스트로 구성
        context = "\n\n".join([
            f"[문서 {i+1}]\n{doc.page_content}"
            for i, doc in enumerate(source_docs)
        ])

        # OpenAI API를 사용하여 응답 생성
        # max_tokens를 제한하여 비용 절감
        answer = openai_service.chat_with_rag(
            question=request.question,
            context=context,
            max_tokens=500,  # 비용 절감을 위한 토큰 제한
            temperature=0.7,
        )

        # 응답 모델 생성
        sources = [
            DocumentResponse(
                content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in source_docs
        ]

        return RAGResponse(
            question=request.question,
            answer=answer,
            sources=sources,
        )
    except ValueError as e:
        # API 키 관련 오류
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG 질의 중 오류 발생: {str(e)}")


@router.get("/health")
async def rag_health() -> dict:
    """RAG 서비스 헬스체크."""
    return {"status": "healthy", "service": "rag"}
