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

from fastapi import APIRouter, File, HTTPException, UploadFile, status

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
    health_and_safety = "health and saftey"
    instrumentation = "instrumentation"

@router.post("/", status_code=status.HTTP_201_CREATED)
async def ingest_document(file: UploadFile = File(...), domain: DomainEnum = DomainEnum.safety):
    """
    Upload a document (PDF, DOCX, or plain text) for processing and indexing
    into the ChromaDB vector store under a specific domain.

    Args:
        file: The file to ingest.
        domain: Target knowledge base category/namespace.

    Returns:
        Ingestion summary (filename, domain, chunk count, loaders, and status).
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

        # 4. Run the ingestion orchestrator
        summary = run_ingestion_pipeline(str(temp_file_path), domain.value)
        return summary

    except ValueError as val_err:
        logger.warning(f"Validation error during ingestion of '{filename}': {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except TesseractMissingError as tess_err:
        logger.error(f"OCR dependency missing: {tess_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(tess_err)
        )
    except Exception as exc:
        logger.exception(f"Unexpected error processing upload '{filename}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {exc}"
        )
    finally:
        # 5. Safely clean up the temporary file
        if temp_file_path.exists():
            try:
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temporary upload file: {temp_file_path}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to delete temp file '{temp_file_path}': {cleanup_err}")
