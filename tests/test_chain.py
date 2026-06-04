import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from backend.rag.chain import generate_answer, format_context

def test_format_context():
    docs = [
        Document(page_content="Content 1", metadata={"source": "doc1.txt", "page": 1}),
        Document(page_content="Content 2", metadata={"source": "doc2.pdf"}),
    ]
    result = format_context(docs)
    assert "--- Document 1 (Source: doc1.txt, Page: 1) ---" in result
    assert "Content 1" in result
    assert "--- Document 2 (Source: doc2.pdf, Page: N/A) ---" in result
    assert "Content 2" in result

@patch("backend.rag.chain.retrieve_documents")
def test_generate_answer_no_context(mock_retrieve):
    mock_retrieve.return_value = []
    
    result = generate_answer("What is the speed of light?")
    
    mock_retrieve.assert_called_once_with(query="What is the speed of light?", domain=None, k=5)
    assert "I don't have enough information" in result["answer"]
    assert result["source_documents"] == []


@patch("backend.rag.chain.get_llm")
@patch("backend.rag.chain.retrieve_documents")
def test_generate_answer_success(mock_retrieve, mock_get_llm):
    mock_retrieve.return_value = [
        Document(page_content="The speed of light is 300,000 km/s.", metadata={"source": "physics.txt"})
    ]
    
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Based on the context, the speed of light is 300,000 km/s."
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm
    
    result = generate_answer("What is the speed of light?")
    
    mock_retrieve.assert_called_once()
    mock_llm.invoke.assert_called_once()
    assert result["answer"] == "Based on the context, the speed of light is 300,000 km/s."
    assert len(result["source_documents"]) == 1

@patch("backend.rag.chain.get_llm")
@patch("backend.rag.chain.retrieve_documents")
def test_generate_answer_exception(mock_retrieve, mock_get_llm):
    mock_retrieve.return_value = [
        Document(page_content="Some context", metadata={"source": "test.txt"})
    ]
    mock_get_llm.side_effect = Exception("Ollama is down")
    
    result = generate_answer("query")
    
    assert "I encountered an error" in result["answer"]
