import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from langchain_core.documents import Document

from backend.api.main import app

client = TestClient(app)


@patch("backend.api.routes.search.retrieve_documents")
def test_search_endpoint_success(mock_retrieve):
    # Mock document list returned by retriever
    mock_retrieve.return_value = [
        Document(
            page_content="Drilling safety guideline details.",
            metadata={"source": "safety_rules.pdf", "page": 4, "chunk_index": 12, "domain": "safety"}
        )
    ]

    response = client.get(
        "/search/",
        params={"q": "drilling safety", "domain": "safety", "k": 3}
    )

    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    assert results[0]["content"] == "Drilling safety guideline details."
    assert results[0]["source"] == "safety_rules.pdf"
    assert results[0]["page"] == 4
    assert results[0]["chunk_index"] == 12
    assert results[0]["domain"] == "safety"

    mock_retrieve.assert_called_once_with(query="drilling safety", domain="safety", k=3)


@patch("backend.api.routes.search.retrieve_documents")
def test_search_endpoint_missing_parameters(mock_retrieve):
    # 'q' is a required parameter
    response = client.get(
        "/search/",
        params={"domain": "safety"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("backend.api.routes.search.retrieve_documents")
def test_search_endpoint_error(mock_retrieve):
    mock_retrieve.side_effect = RuntimeError("Chroma connection lost")

    response = client.get(
        "/search/",
        params={"q": "any query"}
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Semantic search failed" in response.json()["detail"]

@patch("backend.api.routes.search.retrieve_documents")
def test_search_endpoint_no_domain(mock_retrieve):
    mock_retrieve.return_value = [
        Document(
            page_content="Drilling safety guideline details.",
            metadata={"source": "safety_rules.pdf", "page": 4, "chunk_index": 12, "domain": "drilling"}
        )
    ]

    response = client.get(
        "/search/",
        params={"q": "drilling safety", "k": 3}
    )

    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    assert results[0]["domain"] == "drilling"

    mock_retrieve.assert_called_once_with(query="drilling safety", domain=None, k=3)
