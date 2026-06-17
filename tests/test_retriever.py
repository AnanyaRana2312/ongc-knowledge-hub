import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from backend.rag.retriever import retrieve_documents


@patch("backend.rag.retriever.similarity_search")
def test_retrieve_documents_success(mock_search):
    mock_search.return_value = [Document(page_content="retrieved chunk")]

    results = retrieve_documents("query", "domain_test", k=2)

    mock_search.assert_called_once_with("query", "domain_test", k=2)
    assert len(results) == 1
    assert results[0].page_content == "retrieved chunk"


@patch("backend.rag.retriever.similarity_search", side_effect=Exception("Database error"))
def test_retrieve_documents_failure(mock_search):
    results = retrieve_documents("query", "domain_test", k=2)

    mock_search.assert_called_once()
    # Should catch exception and return an empty list gracefully
    assert results == []

@patch("backend.rag.retriever.similarity_search")
@patch("backend.rag.retriever.classify_query_domain")
@patch("backend.rag.retriever.list_active_domains")
def test_retrieve_documents_dynamic_routing(mock_list, mock_classify, mock_search):
    mock_list.return_value = ["drilling", "safety"]
    mock_classify.return_value = "drilling"
    mock_search.return_value = [Document(page_content="drilling chunk")]

    results = retrieve_documents("query about drilling", domain=None, k=2)

    mock_list.assert_called_once()
    mock_classify.assert_called_once_with("query about drilling", ["drilling", "safety"])
    mock_search.assert_called_once_with("query about drilling", "drilling", k=2)
    assert len(results) == 1

@patch("backend.rag.retriever.similarity_search")
@patch("backend.rag.retriever.list_active_domains")
def test_retrieve_documents_dynamic_routing_no_domains(mock_list, mock_search):
    mock_list.return_value = []
    mock_search.return_value = []

    results = retrieve_documents("query about nothing", domain=None, k=2)

    mock_list.assert_called_once()
    mock_search.assert_called_once_with("query about nothing", "default", k=2)


@patch("backend.rag.retriever.similarity_search_with_score")
@patch("backend.rag.retriever.list_active_domains")
def test_retrieve_documents_cross_domain_all(mock_list, mock_search_score):
    mock_list.return_value = ["drilling", "safety"]
    mock_search_score.side_effect = [
        [(Document(page_content="drilling doc", metadata={"domain": "drilling"}), 0.3)],
        [(Document(page_content="safety doc", metadata={"domain": "safety"}), 0.1)]
    ]

    results = retrieve_documents("safety query", domain="all", k=1)

    mock_list.assert_called_once()
    assert mock_search_score.call_count == 2
    assert len(results) == 1
    # Check that it sorted by score ascending, so safety doc (score 0.1) is returned first
    assert results[0].page_content == "safety doc"
