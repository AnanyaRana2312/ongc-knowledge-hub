"""
backend/api/routes/chat.py
--------------------------
Chat / Q&A endpoint — stub for Week 2 RAG integration.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
async def chat():
    """
    Send a natural language question and receive an LLM-generated answer
    grounded in the knowledge base.

    TODO (Week 2):
        - Accept ChatRequest schema (question, session_id, domain)
        - Run RAG retrieval pipeline
        - Stream response tokens back to client
    """
    return {"message": "Chat endpoint — coming in Week 2"}
