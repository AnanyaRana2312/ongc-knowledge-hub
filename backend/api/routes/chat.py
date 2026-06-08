"""
backend/api/routes/chat.py
--------------------------
Chat / Q&A endpoint — stub for Week 2 RAG integration.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

import uuid
import json
from backend.rag.chain import generate_answer
from backend.db.database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's question to ask the knowledge base.")
    domain: Optional[str] = Field(None, description="Optional domain constraint. If omitted, dynamically routed.")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation memory.")


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
    logger.info(f"Received chat request: question='{request.question}', domain='{request.domain}', session_id='{request.session_id}'")
    
    try:
        # 1. Fetch chat history if session_id is provided
        chat_history = []
        if request.session_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC", (request.session_id,))
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                chat_history.append({"role": row["role"], "content": row["content"]})
                
        # 2. Generate Answer
        result = generate_answer(query=request.question, domain=request.domain, chat_history=chat_history)
        
        # 3. Extract Citations
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
            
        # 4. Save to Database
        if request.session_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Auto-update title if it's the first message (meaning session is empty)
            if not chat_history:
                title = request.question[:50] + ("..." if len(request.question) > 50 else "")
                cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, request.session_id))
            
            # Save user message
            user_msg_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO messages (id, session_id, role, content, citations) VALUES (?, ?, ?, ?, ?)", 
                          (user_msg_id, request.session_id, "user", request.question, "[]"))
                          
            # Save assistant message
            ast_msg_id = str(uuid.uuid4())
            citations_json = json.dumps([c.model_dump() for c in citations])
            cursor.execute("INSERT INTO messages (id, session_id, role, content, citations) VALUES (?, ?, ?, ?, ?)", 
                          (ast_msg_id, request.session_id, "assistant", result["answer"], citations_json))
                          
            conn.commit()
            conn.close()
            
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
