"""
backend/rag/retriever.py
-------------------------
Retriever module wrapping the vector store similarity search.
Exposes retrieval interfaces for semantic search and RAG pipelines.
"""

import logging
from typing import List

from langchain_core.documents import Document

from backend.rag.vector_store import similarity_search, list_active_domains
from backend.rag.router import classify_query_domain

logger = logging.getLogger(__name__)


def retrieve_documents(query: str, domain: str | None = None, k: int = 5) -> List[Document]:
    """
    Retrieve matching documents / text chunks from ChromaDB.

    Args:
        query: User search query string.
        domain: Domain collection to search within. If None or 'default', it will be dynamically routed.
        k: Number of documents to retrieve.

    Returns:
        List of matching LangChain Document objects.
    """
    if not domain or domain == "default":
        active_domains = list_active_domains()
        # Filter out default or empty domains
        active_domains = [d for d in active_domains if d and "default" not in d]
        
        if active_domains:
            domain = classify_query_domain(query, active_domains)
            logger.info(f"Dynamically routed query '{query}' to domain: '{domain}'")
        else:
            domain = "default"
            logger.info("No active specific domains found for routing. Using 'default'.")

    logger.info(f"Retrieving top {k} document(s) for query: '{query}' in domain: '{domain}'")
    try:
        return similarity_search(query, domain, k=k)
    except Exception as e:
        logger.error(f"Failed to retrieve documents for query '{query}': {e}")
        # Return empty list if collection doesn't exist yet or query fails
        return []
