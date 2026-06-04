"""
backend/rag/retriever.py
-------------------------
Cross-domain retriever: searches ALL active ChromaDB collections,
pools results, sorts by L2 distance, returns top-k best chunks globally.
"""

import logging
from typing import List

from langchain_core.documents import Document

from backend.rag.vector_store import (
    similarity_search,
    similarity_search_with_score,
    list_active_domains,
)

logger = logging.getLogger(__name__)


def retrieve_documents(query: str, domain: str | None = None, k: int = 5) -> List[Document]:
    """
    Retrieve matching document chunks from ChromaDB.

    If domain is None or 'default', performs cross-domain search across
    all active collections and returns the globally best matches by score.
    If domain is specified, searches only that collection.
    """
    if not domain or domain == "default":
        active_domains = list_active_domains()
        active_domains = [d for d in active_domains if d and d != "default"]

        if not active_domains:
            logger.info("No active domains found. Trying 'default'.")
            try:
                return similarity_search(query, "default", k=k)
            except Exception as e:
                logger.error(f"Failed to retrieve from 'default': {e}")
                return []

        logger.info(f"Cross-domain search across {len(active_domains)} domains: {active_domains}")

        all_results = []
        for d in active_domains:
            try:
                results = similarity_search_with_score(query, d, k=k)
                all_results.extend(results)
                logger.info(f"  Domain '{d}': {len(results)} result(s)")
            except Exception as e:
                logger.warning(f"  Skipping domain '{d}' due to error: {e}")

        if not all_results:
            logger.warning("Cross-domain search returned no results.")
            return []

        # Sort ascending by L2 distance — lower = closer match
        all_results.sort(key=lambda x: x[1])
        top_k = all_results[:k]
        logger.info(f"Top-{k} scores: {[round(s, 4) for _, s in top_k]}")
        return [doc for doc, _ in top_k]

    else:
        logger.info(f"Single-domain search in '{domain}' (k={k}) for: '{query}'")
        try:
            return similarity_search(query, domain, k=k)
        except Exception as e:
            logger.error(f"Failed to retrieve from domain '{domain}': {e}")
            return []
