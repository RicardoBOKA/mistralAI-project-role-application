"""Document ingestion service: extraction, chunking, and embedding."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import chromadb
from mistralai import Mistral
from pypdf import PdfReader

from app.core.config import Settings, get_settings
from app.models.schemas import DocumentInfo


class IngestionService:
    """Service for ingesting documents into the vector store."""

    def __init__(
        self,
        mistral_client: Mistral,
        collection: chromadb.Collection,
        settings: Settings | None = None,
    ):
        self.mistral = mistral_client
        self.collection = collection
        self.settings = settings or get_settings()

    def extract_text(self, file: BinaryIO, filename: str) -> str:
        """Extract text from uploaded file based on file type."""
        file_ext = Path(filename).suffix.lower()

        if file_ext == ".pdf":
            return self._extract_pdf(file)
        elif file_ext == ".txt":
            return self._extract_txt(file)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def _extract_pdf(self, file: BinaryIO) -> str:
        """Extract text from PDF file."""
        reader = PdfReader(file)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)

    def _extract_txt(self, file: BinaryIO) -> str:
        """Extract text from TXT file."""
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return content

    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks with overlap."""
        # Clean text
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return []

        # Split by paragraphs first
        paragraphs = re.split(r"\n\n+", text)

        chunks = []
        current_chunk = ""

        # Approximate tokens as words / 0.75
        target_chars = self.settings.chunk_size * 4  # ~4 chars per token
        overlap_chars = self.settings.chunk_overlap * 4

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If paragraph alone is too big, split by sentences
            if len(paragraph) > target_chars:
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > target_chars:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            # Keep overlap from end of previous chunk
                            current_chunk = current_chunk[-overlap_chars:] if overlap_chars else ""
                    current_chunk += " " + sentence
            else:
                if len(current_chunk) + len(paragraph) > target_chars:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = current_chunk[-overlap_chars:] if overlap_chars else ""
                current_chunk += "\n\n" + paragraph

        # Add remaining content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts using Mistral."""
        if not texts:
            return []

        response = self.mistral.embeddings.create(
            model=self.settings.mistral_embed_model,
            inputs=texts,
        )

        return [item.embedding for item in response.data]

    def generate_document_id(self, filename: str, content: str) -> str:
        """Generate a unique document ID based on filename and content hash."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        safe_filename = re.sub(r"[^a-zA-Z0-9]", "_", Path(filename).stem)[:20]
        return f"{safe_filename}_{content_hash}"

    async def ingest_document(
        self,
        file: BinaryIO,
        filename: str,
        file_size: int,
    ) -> DocumentInfo:
        """Full pipeline: extract, chunk, embed, and store document."""
        # Extract text
        text = self.extract_text(file, filename)
        if not text.strip():
            raise ValueError("Document contains no extractable text")

        # Generate document ID
        doc_id = self.generate_document_id(filename, text)

        # Check if document already exists and delete old version
        existing = self.collection.get(where={"document_id": doc_id})
        if existing and existing["ids"]:
            self.collection.delete(ids=existing["ids"])

        # Chunk text
        chunks = self.chunk_text(text)
        if not chunks:
            raise ValueError("Document could not be chunked")

        # Generate embeddings
        embeddings = self.generate_embeddings(chunks)

        # Prepare data for ChromaDB
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": doc_id,
                "document_name": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        # Store in ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        # Save file to disk
        upload_path = Path(self.settings.upload_directory) / f"{doc_id}_{filename}"
        file.seek(0)
        upload_path.write_bytes(file.read())

        # Save document metadata
        metadata_path = Path(self.settings.upload_directory) / f"{doc_id}.json"
        file_ext = Path(filename).suffix.lower().lstrip(".")
        doc_info = DocumentInfo(
            id=doc_id,
            filename=filename,
            file_type=file_ext,
            chunk_count=len(chunks),
            uploaded_at=datetime.now(timezone.utc),
            file_size=file_size,
        )
        metadata_path.write_text(doc_info.model_dump_json(indent=2))

        return doc_info

    def list_documents(self) -> list[DocumentInfo]:
        """List all ingested documents."""
        upload_dir = Path(self.settings.upload_directory)
        documents = []

        for metadata_file in upload_dir.glob("*.json"):
            try:
                data = json.loads(metadata_file.read_text())
                documents.append(DocumentInfo(**data))
            except Exception:
                continue

        # Sort by upload date, newest first
        documents.sort(key=lambda d: d.uploaded_at, reverse=True)
        return documents

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its chunks from the store."""
        # Delete from ChromaDB
        existing = self.collection.get(where={"document_id": doc_id})
        if existing and existing["ids"]:
            self.collection.delete(ids=existing["ids"])

        # Delete files
        upload_dir = Path(self.settings.upload_directory)
        deleted = False

        # Delete metadata file
        metadata_file = upload_dir / f"{doc_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()
            deleted = True

        # Delete document file (find by prefix)
        for doc_file in upload_dir.glob(f"{doc_id}_*"):
            if not doc_file.suffix == ".json":
                doc_file.unlink()
                deleted = True

        return deleted
