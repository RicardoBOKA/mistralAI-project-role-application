"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Mistral AI Configuration
    mistral_api_key: str
    mistral_embed_model: str = "mistral-embed"
    mistral_chat_model: str = "mistral-small-latest"

    # ChromaDB Configuration
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "documents"

    # Document Storage
    upload_directory: str = "./data/uploads"

    # Chunking Configuration
    chunk_size: int = 500  # Target tokens per chunk
    chunk_overlap: int = 50  # Overlap between chunks

    # Retrieval Configuration
    retrieval_top_k: int = 5

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    cors_origins: list[str] = ["http://localhost:3000"]

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.upload_directory).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
