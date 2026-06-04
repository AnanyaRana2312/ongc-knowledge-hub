import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status
from langchain_core.documents import Document

from backend.api.main import app

client = TestClient(app)


@patch("backend.api.routes.chat.generate_answer")
def test_chat_endpoint_success(mock_generate):
    mock_generate.return_value = {
        "answer": "This is a mocked answer.",
        "source_documents": [
            Document(
                page_content="Context text", 
                metadata={"source": "manual.pdf", "page": 5, "domain": "drilling", "chunk_index": 2}
            )
        ]
    }
    
    response = client.post(
        "/chat/",
        json={"question": "Test question?", "domain": "drilling"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["answer"] == "This is a mocked answer."
    assert len(data["citations"]) == 1
    assert data["citations"][0]["source"] == "manual.pdf"
    assert data["citations"][0]["domain"] == "drilling"
    assert data["citations"][0]["page"] == 5
    assert data["citations"][0]["chunk_index"] == 2
    
    mock_generate.assert_called_once_with(query="Test question?", domain="drilling")


@patch("backend.api.routes.chat.generate_answer")
def test_chat_endpoint_no_domain(mock_generate):
    mock_generate.return_value = {
        "answer": "Answer without domain.",
        "source_documents": []
    }
    
    response = client.post(
        "/chat/",
        json={"question": "Test question?"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    mock_generate.assert_called_once_with(query="Test question?", domain=None)


def test_chat_endpoint_missing_question():
    response = client.post(
        "/chat/",
        json={"domain": "safety"} # missing question
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("backend.api.routes.chat.generate_answer")
def test_chat_endpoint_exception(mock_generate):
    mock_generate.side_effect = RuntimeError("Internal generation error")
    
    response = client.post(
        "/chat/",
        json={"question": "Test question?"}
    )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to generate answer" in response.json()["detail"]
