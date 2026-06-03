import pytest
from unittest.mock import MagicMock, patch
from backend.rag.router import classify_query_domain

@patch("backend.rag.router.get_llm")
def test_classify_query_domain_success(mock_get_llm):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = " drilling "
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    result = classify_query_domain("tension query", ["drilling", "safety"])

    assert result == "drilling"
    mock_llm.invoke.assert_called_once()


@patch("backend.rag.router.get_llm")
def test_classify_query_domain_no_match(mock_get_llm):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "unknown_domain"
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    result = classify_query_domain("tension query", ["drilling", "safety"])

    assert result == "default"


def test_classify_query_domain_no_domains():
    result = classify_query_domain("query", [])
    assert result == "default"


def test_classify_query_domain_one_domain():
    result = classify_query_domain("query", ["only_domain"])
    assert result == "only_domain"

@patch("backend.rag.router.get_llm")
def test_classify_query_domain_exception(mock_get_llm):
    mock_get_llm.side_effect = Exception("LLM Error")

    result = classify_query_domain("query", ["drilling", "safety"])

    assert result == "default"
