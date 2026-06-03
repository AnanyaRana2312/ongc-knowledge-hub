"""
backend/ingestion/chunker.py
-----------------------------
Splits LangChain Documents into smaller overlapping chunks
suitable for embedding and vector storage.

Why chunking matters:
- LLMs have context limits — we can't feed entire documents
- Smaller chunks = more precise similarity matches in ChromaDB
- Overlap ensures context is not lost at chunk boundaries

Default settings (tuned for ONGC technical documents):
    chunk_size    = 1000 characters (~150-200 words)
    chunk_overlap = 200 characters  (20% overlap)
"""

import logging
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default chunking parameters
# ---------------------------------------------------------------------------
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Separators tried in order — prefers splitting on paragraphs, then
# sentences, then words, then characters as a last resort.
DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]


def chunk_documents(
    documents: List[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Document]:
    """
    Split a list of Documents into smaller chunks.

    Each output chunk inherits the metadata of its source document,
    plus a 'chunk_index' field indicating its position.

    Args:
        documents:     List of LangChain Document objects (from loader.py).
        chunk_size:    Maximum characters per chunk.
        chunk_overlap: Characters of overlap between consecutive chunks.

    Returns:
        List of chunked Document objects ready for embedding.

    Example:
        from backend.ingestion.loader import load_document
        from backend.ingestion.chunker import chunk_documents

        docs = load_document("data/sample_sop.pdf")
        chunks = chunk_documents(docs)
        print(f"{len(chunks)} chunks created")
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=DEFAULT_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # Attach chunk index to each chunk's metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["chunk_size"] = len(chunk.page_content)

    total_chars = sum(len(d.page_content) for d in documents)
    logger.info(
        f"Chunked {len(documents)} document(s) → {len(chunks)} chunks "
        f"(chunk_size={chunk_size}, overlap={chunk_overlap}, "
        f"source_chars={total_chars})"
    )

    return chunks
