"""Dependency injection for FastAPI."""

from functools import lru_cache
from typing import Annotated

import chromadb
from fastapi import Depends
from mistralai import Mistral

from app.core.config import Settings, get_settings


@lru_cache
def get_mistral_client() -> Mistral:
    """Get cached Mistral client instance."""
    settings = get_settings()
    return Mistral(api_key=settings.mistral_api_key)


@lru_cache
def get_chroma_client() -> chromadb.PersistentClient:
    """Get cached ChromaDB client instance."""
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_directory)


def get_chroma_collection(
    client: Annotated[chromadb.PersistentClient, Depends(get_chroma_client)],
) -> chromadb.Collection:
    """Get or create the documents collection."""
    settings = get_settings()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


# Type aliases for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
MistralClientDep = Annotated[Mistral, Depends(get_mistral_client)]
ChromaCollectionDep = Annotated[chromadb.Collection, Depends(get_chroma_collection)]
