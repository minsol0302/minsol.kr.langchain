"""
챗봇 API 라우터.

RAG (Retrieval-Augmented Generation) 기반 챗봇 엔드포인트를 제공합니다.
POST /rag/query - RAG 질의 수행
GET /rag/health - RAG 서비스 헬스체크
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request

from app.api.models import RAGRequest, RAGResponse, DocumentResponse
from app.core.vectorstore import get_vectorstore, VectorStoreType
from app.service.chat_service import ChatService
from app.core.rag_chain import create_rag_chain

router = APIRouter(prefix="/rag", tags=["rag"])


def get_vectorstore_dependency() -> VectorStoreType:
    """벡터스토어 의존성 주입."""
    return get_vectorstore()


def get_chat_service(fastapi_request: Request) -> Optional[ChatService]:
    """ChatService 의존성 주입."""
    chat_service = getattr(fastapi_request.app.state, 'chat_service', None)
    return chat_service


@router.post("/query", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    fastapi_request: Request,
    vectorstore: VectorStoreType = Depends(get_vectorstore_dependency),
    chat_service: Optional[ChatService] = Depends(get_chat_service),
) -> RAGResponse:
    """
    RAG (Retrieval-Augmented Generation) 질의를 수행합니다.

    ChatService에 로드된 모델을 사용하여 대화형 응답을 생성합니다.
    ChatService가 없으면 기존 RAG 체인을 사용합니다.

    - **question**: 질문 내용
    - **k**: 검색에 사용할 문서 개수 (1-10)
    """
    try:
        # 검색된 문서 가져오기 (참조용)
        retriever = vectorstore.as_retriever(search_kwargs={"k": request.k})
        source_docs = retriever.invoke(request.question)

        # ChatService가 있으면 사용, 없으면 기존 RAG 체인 사용
        if chat_service is not None:
            # 검색된 문서를 컨텍스트로 구성
            context = "\n\n".join([
                f"[문서 {i+1}]\n{doc.page_content}"
                for i, doc in enumerate(source_docs)
            ])

            # RAG 프롬프트 구성
            rag_prompt = f"""다음 컨텍스트를 바탕으로 질문에 답해주세요:

컨텍스트:
{context}

질문: {request.question}

답변:"""

            # ChatService를 사용하여 응답 생성
            # 대화 히스토리는 사용하지 않고 매번 독립적인 질의로 처리
            chat_service.clear_history()
            answer = chat_service.chat(
                rag_prompt,
                max_new_tokens=512,
                temperature=0.7,
                reset_history=True,
            )
        else:
            # 기존 RAG 체인 사용 (하위 호환성)
            llm = getattr(fastapi_request.app.state, 'llm', None)
            rag_chain = create_rag_chain(vectorstore, llm=llm)
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
