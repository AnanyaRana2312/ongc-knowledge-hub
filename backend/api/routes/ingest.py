"""
backend/api/routes/ingest.py
-----------------------------
Document ingestion endpoint — accepts file uploads, processes them,
and indexes the content into the ChromaDB vector store.
"""

import logging
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status, BackgroundTasks

from backend.ingestion.pipeline import run_ingestion_pipeline
from backend.ingestion.ocr import TesseractMissingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# Directory inside the workspace for temporary upload files
TEMP_UPLOAD_DIR = Path("data/temp")


import enum

class DomainEnum(str, enum.Enum):
    safety = "safety"
    drilling = "drilling"
    hr_management = "HR management"
    supply_chain_management = "supply chain management"
    fire = "fire"
    procurement = "procurement"
    production = "production"
    geology = "geology"
    finance_and_accounts = "finance and accounts"
    materials_managements = "materials managements"
    health_and_safety = "health and safety"
    instrumentation = "instrumentation"

def background_ingest_and_cleanup(file_path: Path, domain: str, filename: str):
    """Run ingestion in the background and clean up the file afterwards."""
    try:
        logger.info(f"Starting background ingestion for '{filename}'")
        run_ingestion_pipeline(str(file_path), domain)
        logger.info(f"Background ingestion completed for '{filename}'")
    except Exception as exc:
        logger.error(f"Background ingestion failed for '{filename}': {exc}")
    finally:
        if file_path.exists():
            try:
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary upload file: {file_path}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to delete temp file '{file_path}': {cleanup_err}")

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), domain: DomainEnum = DomainEnum.safety):
    """
    Upload a document (PDF, DOCX, or plain text) for processing and indexing
    into the ChromaDB vector store under a specific domain. The processing
    happens in the background so the upload returns immediately.

    Args:
        file: The file to ingest.
        domain: Target knowledge base category/namespace.

    Returns:
        Immediate processing status.
    """
    # 1. Create temporary directory if it doesn't exist
    TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Define safe temporary file path
    filename = Path(file.filename).name
    temp_file_path = TEMP_UPLOAD_DIR / filename

    logger.info(f"Received file upload '{filename}' for domain '{domain.value}'")

    try:
        # 3. Write uploaded file to disk
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 4. Enqueue the ingestion orchestrator as a background task
        background_tasks.add_task(background_ingest_and_cleanup, temp_file_path, domain.value, filename)
        
        return {
            "filename": filename,
            "domain": domain.value,
            "status": "processing",
            "message": "Document is being processed in the background."
        }

    except Exception as exc:
        logger.exception(f"Unexpected error processing upload '{filename}': {exc}")
        if temp_file_path.exists():
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue document: {exc}"
        )
