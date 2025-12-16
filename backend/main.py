"""FastAPI backend server for LangChain chatbot."""

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.documents import Document
from langchain_community.vectorstores import PGVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from sqlalchemy import create_engine, text
import time

app = FastAPI(title="LangChain Chatbot API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
vector_store: Optional[PGVector] = None
chain: Optional[ConversationalRetrievalChain] = None


class ChatMessage(BaseModel):
    """Chat message model."""

    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    conversation_id: str
    sources: Optional[List[dict]] = None


def wait_for_postgres(max_retries: int = 30, delay: int = 2) -> None:
    """Wait for PostgreSQL to be ready."""
    connection_string = os.getenv(
        "POSTGRES_CONNECTION_STRING",
        "postgresql://postgres:postgres@postgres:5432/postgres",
    )

    for i in range(max_retries):
        try:
            engine = create_engine(connection_string, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return
        except Exception:
            if i < max_retries - 1:
                time.sleep(delay)
            else:
                raise


def initialize_vector_store() -> None:
    """Initialize the vector store and chain."""
    global vector_store, chain

    if vector_store is not None:
        return

    # Wait for PostgreSQL
    wait_for_postgres()

    connection_string = os.getenv(
        "POSTGRES_CONNECTION_STRING",
        "postgresql://postgres:postgres@postgres:5432/postgres",
    )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_api_key,
    )

    # Create vector store (use new collection to avoid dimension mismatch)
    collection_name = "langchain_chatbot_v2"
    vector_store = PGVector(
        connection_string=connection_string,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    # Add initial documents if collection is empty
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            # Check if collection exists and has any embeddings
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM langchain_pg_embedding
                    WHERE collection_id = (
                        SELECT uuid FROM langchain_pg_collection
                        WHERE name = :collection_name
                    )
                """), {"collection_name": collection_name})
                count = result.scalar() or 0
            except Exception:
                # Collection doesn't exist yet
                count = 0

            if count == 0:
                print("📝 Adding initial documents to vector store...")
                initial_documents = [
                    Document(
                        page_content="LangChain is a framework for developing applications powered by language models.",
                        metadata={"source": "intro", "topic": "framework"},
                    ),
                    Document(
                        page_content="pgvector is a PostgreSQL extension for vector similarity search.",
                        metadata={"source": "intro", "topic": "database"},
                    ),
                    Document(
                        page_content="Vector stores enable semantic search over large collections of documents.",
                        metadata={"source": "intro", "topic": "search"},
                    ),
                ]
                vector_store.add_documents(initial_documents)
                print(f"✓ Added {len(initial_documents)} initial documents")
            else:
                print(f"✓ Collection already has {count} documents")
    except Exception as e:
        print(f"⚠ Could not check/add initial documents: {e}")
        # Continue anyway - documents might already exist

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=openai_api_key,
    )

    # Create memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    # Create chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        return_source_documents=True,
        verbose=True,
    )

    print("✓ Vector store and chain initialized successfully")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    try:
        initialize_vector_store()
        print("✓ Vector store and chain initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize vector store: {e}")
        print("⚠ The API will still work but may not have RAG capabilities")


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"message": "LangChain Chatbot API", "status": "running"}


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vector_store_initialized": vector_store is not None,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage) -> ChatResponse:
    """Chat endpoint."""
    if chain is None:
        try:
            initialize_vector_store()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service not ready: {str(e)}",
            ) from e

    try:
        # Get conversation ID or use default
        conversation_id = chat_message.conversation_id or "default"

        # Run the chain
        result = chain.invoke(
            {
                "question": chat_message.message,
                "chat_history": [],
            }
        )

        # Extract sources
        sources = []
        if "source_documents" in result:
            for doc in result["source_documents"]:
                sources.append(
                    {
                        "content": doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content,
                        "metadata": doc.metadata,
                    }
                )

        return ChatResponse(
            response=result.get("answer", "Sorry, I couldn't generate a response."),
            conversation_id=conversation_id,
            sources=sources if sources else None,
        )
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in chat endpoint: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

