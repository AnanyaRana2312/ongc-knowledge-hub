import logging
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.rag.vector_store import list_ingested_documents

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
