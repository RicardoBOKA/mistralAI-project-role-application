"""Document retrieval service: similarity search in vector store."""

import chromadb
from mistralai import Mistral

from app.core.config import Settings, get_settings
from app.models.schemas import SourceChunk


class RetrievalService:
    """Service for retrieving relevant document chunks."""

    def __init__(
        self,
        mistral_client: Mistral,
        collection: chromadb.Collection,
        settings: Settings | None = None,
    ):
        self.mistral = mistral_client
        self.collection = collection
        self.settings = settings or get_settings()

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a query."""
        response = self.mistral.embeddings.create(
            model=self.settings.mistral_embed_model,
            inputs=[query],
        )
        return response.data[0].embedding

    def search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[SourceChunk]:
        """Search for relevant chunks using similarity search."""
        if top_k is None:
            top_k = self.settings.retrieval_top_k

        # Check if collection has any documents
        if self.collection.count() == 0:
            return []

        # Embed the query
        query_embedding = self.embed_query(query)

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to SourceChunk objects
        chunks = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                document = results["documents"][0][i]
                distance = results["distances"][0][i]

                # Convert cosine distance to similarity score (0-1)
                # ChromaDB returns squared L2 distance for cosine, so we convert
                similarity = max(0, 1 - distance)

                chunks.append(
                    SourceChunk(
                        document_id=metadata["document_id"],
                        document_name=metadata["document_name"],
                        chunk_index=metadata["chunk_index"],
                        content=document,
                        score=round(similarity, 4),
                    )
                )

        # Sort by score descending
        chunks.sort(key=lambda x: x.score, reverse=True)
        return chunks

    def search_with_filter(
        self,
        query: str,
        document_ids: list[str],
        top_k: int | None = None,
    ) -> list[SourceChunk]:
        """Search within specific documents only."""
        if top_k is None:
            top_k = self.settings.retrieval_top_k

        if not document_ids:
            return self.search(query, top_k)

        # Check if collection has any documents
        if self.collection.count() == 0:
            return []

        # Embed the query
        query_embedding = self.embed_query(query)

        # Build filter for specific documents
        where_filter = {"document_id": {"$in": document_ids}}

        # Search in ChromaDB with filter
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to SourceChunk objects
        chunks = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                document = results["documents"][0][i]
                distance = results["distances"][0][i]

                similarity = max(0, 1 - distance)

                chunks.append(
                    SourceChunk(
                        document_id=metadata["document_id"],
                        document_name=metadata["document_name"],
                        chunk_index=metadata["chunk_index"],
                        content=document,
                        score=round(similarity, 4),
                    )
                )

        chunks.sort(key=lambda x: x.score, reverse=True)
        return chunks
