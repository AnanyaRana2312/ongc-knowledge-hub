"""
backend/api/routes/ingest.py
-----------------------------
Document ingestion endpoint — stub for Week 2 ingestion pipeline.
"""

from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/")
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, or image) for processing and indexing
    into the ChromaDB vector store.

    TODO (Week 2):
        - Detect file type and route to appropriate loader
        - Parse and chunk document content
        - Generate embeddings and store in ChromaDB
        - Return ingestion summary (chunk count, document ID)
    """
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "Ingestion endpoint — coming in Week 2",
    }
