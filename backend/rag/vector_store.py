"""
backend/rag/vector_store.py
----------------------------
ChromaDB client wrapper using LangChain's Chroma vector store integration.
Manages domain-specific collections, text embedding storage, and similarity search.
"""

import logging
import re
from typing import List

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from backend.api.config import settings
from backend.models.embedding_client import get_embeddings

logger = logging.getLogger(__name__)


def sanitize_collection_name(name: str) -> str:
    """
    Sanitize the domain name to satisfy ChromaDB collection name rules:
    - 3-63 characters long.
    - Starts and ends with an alphanumeric character.
    - Contains only alphanumeric, underscores, or hyphens.
    - No consecutive periods (periods are completely stripped here).

    Args:
        name: Raw domain name string.

    Returns:
        Sanitized collection name string.
    """
    # Lowercase and strip whitespace
    clean = name.lower().strip()

    # Replace all non-alphanumeric, non-underscore, and non-hyphen chars with underscore
    clean = re.sub(r"[^a-z0-9_-]", "_", clean)

    # Remove leading non-alphanumeric characters
    clean = re.sub(r"^[^a-z0-9]+", "", clean)

    # Remove trailing non-alphanumeric characters
    clean = re.sub(r"[^a-z0-9]+$", "", clean)

    # If the name is too short, prefix it
    if len(clean) < 3:
        clean = f"domain_{clean}" if clean else "domain_default"

    # Truncate if too long
    if len(clean) > 63:
        clean = clean[:63]
        # Clean trailing non-alphanumeric if truncation introduced one
        clean = re.sub(r"[^a-z0-9]+$", "", clean)

    logger.debug(f"Sanitized domain '{name}' to collection name '{clean}'")
    return clean


def get_vector_store(domain: str) -> Chroma:
    """
    Get or create a ChromaDB vector store instance for a given domain.

    Args:
        domain: Domain name representing the specific knowledge category.

    Returns:
        A configured Chroma vector store object.
    """
    embeddings = get_embeddings()
    collection = sanitize_collection_name(domain)

    logger.info(
        f"Initializing Chroma store for domain '{domain}' (collection: '{collection}') "
        f"at path: {settings.chroma_persist_dir}"
    )

    return Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )


def add_documents_to_store(documents: List[Document], domain: str) -> None:
    """
    Embed and store a list of documents into the domain-specific collection.

    Args:
        documents: List of LangChain Document objects.
        domain: Target domain/collection for the documents.
    """
    if not documents:
        logger.warning(f"No documents provided to add to store for domain '{domain}'")
        return

    vector_store = get_vector_store(domain)
    vector_store.add_documents(documents)

    logger.info(f"Successfully added {len(documents)} document chunk(s) to domain '{domain}'")


def similarity_search(query: str, domain: str, k: int = 5) -> List[Document]:
    """
    Run similarity search for a query against a domain-specific collection.

    Args:
        query: Search query string.
        domain: Domain namespace to search inside.
        k: Number of nearest matches to return.

    Returns:
        List of matching LangChain Documents.
    """
    vector_store = get_vector_store(domain)
    logger.info(f"Running similarity search in domain '{domain}' (k={k}) for query: '{query}'")
    return vector_store.similarity_search(query, k=k)


def similarity_search_with_score(query: str, domain: str, k: int = 5) -> list:
    """
    Run similarity search returning (Document, distance_score) tuples.
    Lower L2 distance score = closer / more relevant match.

    Args:
        query: Search query string.
        domain: Domain namespace to search inside.
        k: Number of nearest matches to return.

    Returns:
        List of (Document, float) tuples sorted by distance ascending.
    """
    vector_store = get_vector_store(domain)
    logger.debug(f"Similarity search with score in domain '{domain}' (k={k}) for: '{query}'")
    return vector_store.similarity_search_with_score(query, k=k)


def list_active_domains() -> List[str]:
    """
    List all active collection names in ChromaDB.

    Returns:
        List of active domain strings.
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        return [c.name for c in client.list_collections()]
    except Exception as e:
        logger.error(f"Failed to list active collections from ChromaDB: {e}")
        return []


def list_ingested_documents() -> List[dict]:
    """
    List all ingested documents and their associated domains.
    
    Returns:
        A list of dictionaries containing 'source' and 'domain' keys.
    """
    documents = []
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collections = client.list_collections()
        
        for c in collections:
            domain_name = c.name
            # Retrieve all metadata for this collection
            result = c.get(include=["metadatas"])
            metadatas = result.get("metadatas", [])
            
            # Use a set to get unique document sources within this domain
            seen_sources = set()
            for meta in metadatas:
                if not meta:
                    continue
                source = meta.get("source")
                if source and source not in seen_sources:
                    seen_sources.add(source)
                    documents.append({
                        "source": source,
                        "domain": meta.get("domain", domain_name)
                    })
                    
    except Exception as e:
        logger.error(f"Failed to list ingested documents from ChromaDB: {e}")
        
    return documents
