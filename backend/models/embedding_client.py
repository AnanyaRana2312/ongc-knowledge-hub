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

    Uses the same llama3 model as the LLM for simplicity.
    Can be swapped to a dedicated embedding model (e.g. nomic-embed-text)
    by changing OLLAMA_MODEL in .env without modifying any calling code.
    """
    return OllamaEmbeddings(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )
