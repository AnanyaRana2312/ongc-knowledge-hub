"""
backend/api/routes/search.py
-----------------------------
Semantic search endpoint — stub for Week 2 ChromaDB integration.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
async def search(query: str):
    """
    Perform a semantic similarity search across the knowledge base
    and return the most relevant document chunks.

    TODO (Week 2):
        - Embed query using OllamaEmbeddings
        - Query ChromaDB for top-k similar chunks
        - Return ranked results with source metadata
    """
    return {"query": query, "results": [], "message": "Search endpoint — coming in Week 2"}
