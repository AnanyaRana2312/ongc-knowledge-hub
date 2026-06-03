"""
backend/ingestion/pipeline.py
------------------------------
Orchestrates the entire document ingestion pipeline:
1. Detects document type (and whether PDFs are scanned/image-only).
2. Routes to appropriate loader (standard parsing vs. OCR extraction).
3. Splits document text into overlapping chunks using RecursiveCharacterTextSplitter.
4. Generates embeddings and index chunks into a domain-specific ChromaDB collection.
"""

import logging
from pathlib import Path

from backend.ingestion.chunker import chunk_documents
from backend.ingestion.loader import load_document
from backend.ingestion.ocr import is_scanned_pdf, ocr_pdf
from backend.rag.vector_store import add_documents_to_store

logger = logging.getLogger(__name__)


def run_ingestion_pipeline(file_path: str, domain: str) -> dict:
    """
    Run the complete ingestion pipeline for a document.

    Args:
        file_path: Absolute or relative path to the target document.
        domain: Target domain / knowledge namespace for organizing documents.

    Returns:
        A dict containing processing metadata:
        {
            "filename": str,
            "domain": str,
            "num_chunks": int,
            "status": str,
            "loaders": List[str]
        }

    Raises:
        FileNotFoundError: If the document path does not exist.
        ValueError: If the document suffix / format is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Starting ingestion pipeline for file: '{path.name}' under domain: '{domain}'")

    suffix = path.suffix.lower()
    docs = []

    # Check if we need OCR (specifically for scanned PDFs)
    if suffix == ".pdf" and is_scanned_pdf(str(path)):
        logger.info(f"PDF '{path.name}' detected as scanned/image-only. Routing to OCR loader...")
        docs = ocr_pdf(str(path))
    else:
        # Standard loaders for digital PDF, docx, txt
        logger.info(f"Loading '{path.name}' using standard parser...")
        docs = load_document(str(path))

    if not docs:
        logger.warning(f"No content extracted from file: '{path.name}'")
        return {
            "filename": path.name,
            "domain": domain,
            "num_chunks": 0,
            "status": "warning_empty",
            "loaders": [],
        }

    # Split documents into chunks
    chunks = chunk_documents(docs)

    # Propagate domain info to chunk metadata
    for chunk in chunks:
        chunk.metadata["domain"] = domain

    # Store in ChromaDB
    logger.info(f"Adding {len(chunks)} chunk(s) to ChromaDB for domain: '{domain}'...")
    add_documents_to_store(chunks, domain)

    # Gather list of loaders used
    loaders_used = list(
        set(d.metadata.get("loader", d.metadata.get("type", "unknown")) for d in docs)
    )

    summary = {
        "filename": path.name,
        "domain": domain,
        "num_chunks": len(chunks),
        "status": "success",
        "loaders": loaders_used,
    }

    logger.info(f"Ingestion pipeline completed successfully for '{path.name}': {summary}")
    return summary
