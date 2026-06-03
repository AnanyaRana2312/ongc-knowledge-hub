"""
backend/api/config.py
---------------------
Centralised settings loaded from environment variables / .env file.
All other modules should import settings from here — never read os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration loaded from .env"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_timeout: int = 120

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Logging
    log_level: str = "INFO"

    # OCR Settings
    tesseract_cmd: str = ""


# Singleton instance — import this everywhere
settings = Settings()
