"""
backend/models/ollama_client.py
--------------------------------
Thin wrapper around langchain-ollama's ChatOllama.

Usage:
    from backend.models.ollama_client import get_llm, health_check

    llm = get_llm()
    is_alive = health_check()
"""

import httpx
from functools import lru_cache

from langchain_ollama import ChatOllama

from backend.api.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    """
    Return a cached ChatOllama instance configured from environment settings.
    Using lru_cache ensures the model client is only initialised once per process.
    """
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_timeout,
    )


def health_check() -> bool:
    """
    Ping the Ollama REST API to confirm it is reachable and the model is loaded.

    Returns:
        True if Ollama is responsive, False otherwise.
    """
    try:
        url = f"{settings.ollama_base_url}/api/tags"
        response = httpx.get(url, timeout=5)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            return any(settings.ollama_model in m for m in models)
        return False
    except Exception:
        return False
