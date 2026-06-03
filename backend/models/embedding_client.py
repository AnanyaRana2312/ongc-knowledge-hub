"""
backend/models/embedding_client.py
------------------------------------
Embedding interface using Ollama (llama3 model).

ChromaDB and LangChain retrievers use this to convert text into vectors.

Usage:
    from backend.models.embedding_client import get_embeddings

    embeddings = get_embeddings()
    vector = embeddings.embed_query("What is ONGC's drilling policy?")
"""

from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

from backend.api.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    """
    Return a cached OllamaEmbeddings instance.

    Uses the dedicated embedding model (default: nomic-embed-text) in Ollama.
    """
    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )
