import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.rag.vector_store import list_ingested_documents, delete_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentInfo(BaseModel):
    source: str = Field(..., description="Source filename of the document")
    domain: str = Field(..., description="Knowledge domain collection name")


@router.get("/", response_model=List[DocumentInfo])
async def get_documents():
    """
    List all documents that have been uploaded and ingested into the knowledge base,
    along with their associated domains.
    """
    logger.info("Fetching list of ingested documents")
    docs = list_ingested_documents()
    return [DocumentInfo(**doc) for doc in docs]


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(filename: str):
    """
    Delete a document and all of its associated data from the vector database.
    """
    logger.info(f"Deleting document: {filename}")
    try:
        delete_document(filename)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
