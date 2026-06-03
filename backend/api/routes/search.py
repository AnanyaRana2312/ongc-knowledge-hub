"""
backend/api/routes/search.py
-----------------------------
Semantic search endpoint — searches the ChromaDB vector store
and returns the most relevant document chunks.
"""

import logging
from typing import List

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field

from backend.rag.retriever import retrieve_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


class SearchResult(BaseModel):
    content: str = Field(..., description="Text content of the document chunk")
    source: str = Field(..., description="Source filename of the chunk")
    page: int | None = Field(None, description="Page index (1-based) where chunk appears")
    chunk_index: int | None = Field(None, description="Global chunk index")
    domain: str = Field(..., description="Knowledge domain collection name")


@router.get("/", response_model=List[SearchResult])
async def search(
    q: str = Query(..., description="Semantic search query"),
    domain: str | None = Query(None, description="Knowledge base domain / collection name. If omitted, will be auto-classified."),
    k: int = Query(5, ge=1, le=20, description="Number of results to retrieve"),
):
    """
    Perform a semantic similarity search across the knowledge base
    and return the most relevant document chunks. If domain is not provided,
    it dynamically routes to the most relevant collection.
    """
    logger.info(f"Received search request: q='{q}', domain='{domain}', k={k}")

    try:
        # Run retrieval
        docs = retrieve_documents(query=q, domain=domain, k=k)

        # Format docs into response schema
        results = []
        for doc in docs:
            results.append(
                SearchResult(
                    content=doc.page_content,
                    source=doc.metadata.get("source", "unknown"),
                    page=doc.metadata.get("page"),
                    chunk_index=doc.metadata.get("chunk_index"),
                    domain=doc.metadata.get("domain", domain),
                )
            )

        return results

    except Exception as exc:
        logger.exception(f"Error during search execution: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {exc}",
        )
