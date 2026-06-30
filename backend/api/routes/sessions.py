import logging
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.db.database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionInfo(BaseModel):
    id: str
    title: str
    created_at: str


class SessionUpdate(BaseModel):
    title: str


class Citation(BaseModel):
    source: str
    page: Optional[int] = None
    domain: str
    chunk_index: Optional[int] = None


class MessageInfo(BaseModel):
    id: str
    role: str
    content: str
    citations: List[Citation] = []
    created_at: str


@router.get("/", response_model=List[SessionInfo])
async def list_sessions():
    """List all chat sessions, ordered by most recent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [SessionInfo(**dict(row)) for row in rows]


@router.post("/", response_model=SessionInfo, status_code=status.HTTP_201_CREATED)
async def create_session(title: str = "New Chat"):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (id, title) VALUES (?, ?)", (session_id, title))
    conn.commit()
    
    # Fetch created to get timestamp
    cursor.execute("SELECT id, title, created_at FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    return SessionInfo(**dict(row))


@router.get("/{session_id}", response_model=List[MessageInfo])
async def get_session_messages(session_id: str):
    """Get all messages for a specific session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify session exists
    cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
        
    cursor.execute("SELECT id, role, content, citations, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        row_dict = dict(row)
        if row_dict["citations"]:
            try:
                row_dict["citations"] = json.loads(row_dict["citations"])
            except json.JSONDecodeError:
                row_dict["citations"] = []
        else:
            row_dict["citations"] = []
        messages.append(MessageInfo(**row_dict))
        
    return messages


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """Delete a session and all its messages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
        
    conn.commit()
    conn.close()


@router.patch("/{session_id}", response_model=SessionInfo)
async def update_session(session_id: str, update_data: SessionUpdate):
    """Rename/update a chat session title."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (update_data.title, session_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    conn.commit()
    
    # Fetch updated session
    cursor.execute("SELECT id, title, created_at FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    return SessionInfo(**dict(row))
