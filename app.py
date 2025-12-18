"""
Demo Application: LangChain with pgvector

This is a standalone demo script that demonstrates basic LangChain
functionality with PostgreSQL/pgvector for vector storage.

Purpose:
    - Test pgvector integration
    - Demonstrate LangChain basics
    - Verify database connectivity

Note: This is separate from the main backend API (app/main.py)
      and uses a different collection to avoid conflicts.

Usage:
    python app.py
"""

import os
import time
from typing import List

from langchain_core.documents import Document
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import create_engine, text


def wait_for_postgres(max_retries: int = 10, delay: int = 2) -> None:
    """Wait for Neon PostgreSQL to be ready."""
    connection_string = os.getenv(
        "POSTGRES_CONNECTION_STRING",
        "postgresql://neondb_owner:npg_2CUgeTP5KBuO@ep-restless-cell-a1n05rxq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
    )

    for i in range(max_retries):
        try:
            engine = create_engine(connection_string, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            print("✓ PostgreSQL is ready!")
            return
        except Exception as e:
            if i < max_retries - 1:
                print(f"Waiting for PostgreSQL... (attempt {i+1}/{max_retries})")
                time.sleep(delay)
            else:
                raise Exception(f"Failed to connect to PostgreSQL: {e}") from e


def main() -> None:
    """Main function demonstrating LangChain with pgvector."""
    print("🚀 Starting LangChain Hello World with pgvector...")

    # Wait for PostgreSQL to be ready
    wait_for_postgres()

    # Connection string for Neon PostgreSQL with pgvector
    connection_string = os.getenv(
        "POSTGRES_CONNECTION_STRING",
        "postgresql://neondb_owner:npg_2CUgeTP5KBuO@ep-restless-cell-a1n05rxq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
    )

    # Collection name for the vector store (use different collection for app.py)
    collection_name = "langchain_app_demo"

    # Initialize OpenAI embeddings
    # API key is read from OPENAI_API_KEY environment variable
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it in docker-compose.yaml or as an environment variable."
        )

    print("🔑 Using OpenAI embeddings...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",  # You can use "text-embedding-3-large" for better quality
        openai_api_key=openai_api_key,
    )

    print(f"📦 Creating vector store with collection: {collection_name}")

    # Create PGVector instance
    vector_store = PGVector(
        connection_string=connection_string,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    # Create sample documents
    documents = [
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

    print("📝 Adding documents to vector store...")
    vector_store.add_documents(documents)
    print(f"✓ Added {len(documents)} documents")

    # Perform similarity search
    query = "What is LangChain?"
    print(f"\n🔍 Searching for: '{query}'")
    results: List[Document] = vector_store.similarity_search(query, k=2)

    print(f"\n📊 Found {len(results)} results:")
    for i, doc in enumerate(results, 1):
        print(f"\n{i}. {doc.page_content}")
        print(f"   Metadata: {doc.metadata}")

    # Perform similarity search with scores
    print(f"\n🔍 Searching with scores for: '{query}'")
    results_with_scores = vector_store.similarity_search_with_score(query, k=2)

    print(f"\n📊 Found {len(results_with_scores)} results with scores:")
    for i, (doc, score) in enumerate(results_with_scores, 1):
        print(f"\n{i}. [Score: {score:.4f}] {doc.page_content}")
        print(f"   Metadata: {doc.metadata}")

    print("\n✅ LangChain Hello World with pgvector completed successfully!")
    print("\n🔄 Container will keep running. Press Ctrl+C to exit.")

    # Keep container running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


if __name__ == "__main__":
    main()

