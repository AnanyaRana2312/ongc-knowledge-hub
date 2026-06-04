"""
backend/api/main.py
--------------------
FastAPI application entry point.

Run locally:
    uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

Auto-generated docs available at:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.config import settings
from backend.api.routes import chat, ingest, search, documents
from backend.models.ollama_client import health_check

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ONGC Knowledge Hub API",
    description=(
        "Secure AI-powered enterprise knowledge management system. "
        "Provides semantic search, RAG-based Q&A, and document ingestion."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Create React App
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(ingest.router)
app.include_router(documents.router)

# ---------------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"])
async def root():
    """API root — basic info."""
    return {
        "name": "ONGC Knowledge Hub API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    """
    Health check endpoint.
    Reports API status and whether Ollama is reachable.
    """
    ollama_ok = health_check()
    return {
        "status": "ok",
        "ollama": "reachable" if ollama_ok else "unreachable",
        "model": settings.ollama_model,
    }
