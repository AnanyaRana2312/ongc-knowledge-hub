"""
backend/api/routes/chat.py
--------------------------
Chat / Q&A endpoint — stub for Week 2 RAG integration.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.rag.chain import generate_answer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's question to ask the knowledge base.")
    domain: Optional[str] = Field(None, description="Optional domain constraint. If omitted, dynamically routed.")


class Citation(BaseModel):
    source: str = Field(..., description="Original filename of the source document.")
    page: Optional[int] = Field(None, description="Page number where the information was found.")
    domain: str = Field(..., description="The domain/collection of the document.")
    chunk_index: Optional[int] = Field(None, description="Index of the chunk in the document.")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="The LLM generated answer.")
    citations: List[Citation] = Field(default_factory=list, description="List of source documents used for the answer.")


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a natural language question and receive an LLM-generated answer
    grounded in the knowledge base using Retrieval-Augmented Generation (RAG).
    """
    logger.info(f"Received chat request: question='{request.question}', domain='{request.domain}'")
    
    try:
        result = generate_answer(query=request.question, domain=request.domain)
        
        # Extract metadata into Citations
        citations = []
        for doc in result.get("source_documents", []):
            citations.append(
                Citation(
                    source=doc.metadata.get("source", "unknown"),
                    page=doc.metadata.get("page"),
                    domain=doc.metadata.get("domain", "default"),
                    chunk_index=doc.metadata.get("chunk_index"),
                )
            )
            
        return ChatResponse(
            answer=result["answer"],
            citations=citations
        )
    except Exception as exc:
        logger.exception(f"Error processing chat request: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {exc}"
        )
