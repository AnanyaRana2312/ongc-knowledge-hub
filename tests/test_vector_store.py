import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from backend.rag.vector_store import (
    sanitize_collection_name,
    get_vector_store,
    add_documents_to_store,
    similarity_search,
)


def test_sanitize_collection_name():
    # Test lowercase conversion and trimming
    assert sanitize_collection_name("  TestCollection  ") == "testcollection"

    # Test invalid characters replacement
    assert sanitize_collection_name("drilling.safety!info") == "drilling_safety_info"

    # Test leading non-alphanumeric removal
    assert sanitize_collection_name("---safety") == "safety"

    # Test trailing non-alphanumeric removal
    assert sanitize_collection_name("safety_") == "safety"

    # Test too short collection name padding
    assert sanitize_collection_name("a") == "domain_a"
    assert sanitize_collection_name("") == "domain_default"

    # Test too long name truncation
    long_name = "a" * 80
    sanitized = sanitize_collection_name(long_name)
    assert len(sanitized) <= 63
    assert sanitized == "a" * 63


@patch("backend.rag.vector_store.get_embeddings")
@patch("backend.rag.vector_store.Chroma")
def test_get_vector_store(mock_chroma, mock_get_embeddings):
    mock_embeddings = MagicMock()
    mock_get_embeddings.return_value = mock_embeddings

    get_vector_store("HR-domain")

    mock_chroma.assert_called_once()
    kwargs = mock_chroma.call_args[1]
    assert kwargs["collection_name"] == "hr-domain"
    assert kwargs["embedding_function"] == mock_embeddings


@patch("backend.rag.vector_store.get_vector_store")
def test_add_documents_to_store_empty(mock_get_store):
    add_documents_to_store([], "hr")
    mock_get_store.assert_not_called()


@patch("backend.rag.vector_store.get_vector_store")
def test_add_documents_to_store_success(mock_get_store):
    mock_store = MagicMock()
    mock_get_store.return_value = mock_store

    docs = [Document(page_content="test chunk")]
    add_documents_to_store(docs, "hr")

    mock_get_store.assert_called_once_with("hr")
    mock_store.add_documents.assert_called_once_with(docs)


@patch("backend.rag.vector_store.get_vector_store")
def test_similarity_search(mock_get_store):
    mock_store = MagicMock()
    mock_get_store.return_value = mock_store
    mock_store.similarity_search.return_value = [Document(page_content="match")]

    results = similarity_search("query", "hr", k=3)

    mock_get_store.assert_called_once_with("hr")
    mock_store.similarity_search.assert_called_once_with("query", k=3)
    assert len(results) == 1
    assert results[0].page_content == "match"
