"""RAG API 라우트."""

from fastapi import APIRouter, HTTPException, Depends, Request

from app.api.models import RAGRequest, RAGResponse, DocumentResponse
from app.core.vectorstore import get_vectorstore, VectorStoreType
from app.core.rag_chain import create_rag_chain

router = APIRouter(prefix="/rag", tags=["rag"])


def get_vectorstore_dependency() -> VectorStoreType:
    """벡터스토어 의존성 주입."""
    return get_vectorstore()


@router.post("/query", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    fastapi_request: Request,
    vectorstore: VectorStoreType = Depends(get_vectorstore_dependency),
) -> RAGResponse:
    """
    RAG (Retrieval-Augmented Generation) 질의를 수행합니다.

    - **question**: 질문 내용
    - **k**: 검색에 사용할 문서 개수 (1-10)
    """
    try:
        # 주입된 LLM 가져오기
        llm = getattr(fastapi_request.app.state, 'llm', None)

        # RAG 체인 생성 (LLM 주입)
        rag_chain = create_rag_chain(vectorstore, llm=llm)

        # 검색된 문서 가져오기 (참조용)
        retriever = vectorstore.as_retriever(search_kwargs={"k": request.k})
        source_docs = retriever.invoke(request.question)

        # RAG 체인 실행
        answer = rag_chain.invoke(request.question)

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG 질의 중 오류 발생: {str(e)}")


@router.get("/health")
async def rag_health() -> dict:
    """RAG 서비스 헬스체크."""
    return {"status": "healthy", "service": "rag"}

