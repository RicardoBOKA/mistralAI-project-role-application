"""Tests for service layer."""

import io
from unittest.mock import MagicMock, patch

import pytest

from app.services.ingestion import IngestionService
from app.services.retrieval import RetrievalService
from app.services.generation import GenerationService
from app.models.schemas import ChatMessage, MessageRole, SourceChunk


class TestIngestionService:
    """Tests for document ingestion service."""

    @pytest.fixture
    def service(self) -> IngestionService:
        """Create an ingestion service with mocked dependencies."""
        mock_mistral = MagicMock()
        mock_collection = MagicMock()
        return IngestionService(mock_mistral, mock_collection)

    def test_extract_txt(self, service: IngestionService):
        """Test text extraction from TXT file."""
        content = b"Hello, this is a test document."
        file = io.BytesIO(content)
        
        result = service.extract_text(file, "test.txt")
        
        assert result == "Hello, this is a test document."

    def test_chunk_text_single_chunk(self, service: IngestionService):
        """Test chunking with text smaller than chunk size."""
        text = "This is a short text that fits in one chunk."
        
        chunks = service.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_multiple_chunks(self, service: IngestionService):
        """Test chunking with longer text."""
        # Create text that should produce multiple chunks
        paragraphs = ["Paragraph " + str(i) + ". " + "x" * 500 for i in range(5)]
        text = "\n\n".join(paragraphs)
        
        chunks = service.chunk_text(text)
        
        assert len(chunks) > 1

    def test_chunk_text_empty(self, service: IngestionService):
        """Test chunking with empty text."""
        chunks = service.chunk_text("")
        assert chunks == []

    def test_chunk_text_whitespace_only(self, service: IngestionService):
        """Test chunking with whitespace-only text."""
        chunks = service.chunk_text("   \n\n   \t   ")
        assert chunks == []

    def test_generate_document_id(self, service: IngestionService):
        """Test document ID generation."""
        doc_id = service.generate_document_id("my_document.pdf", "content")
        
        assert len(doc_id) > 0
        assert "_" in doc_id


class TestRetrievalService:
    """Tests for document retrieval service."""

    @pytest.fixture
    def service(self) -> RetrievalService:
        """Create a retrieval service with mocked dependencies."""
        mock_mistral = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        return RetrievalService(mock_mistral, mock_collection)

    def test_search_empty_collection(self, service: RetrievalService):
        """Test search on empty collection."""
        results = service.search("test query")
        assert results == []


class TestGenerationService:
    """Tests for response generation service."""

    @pytest.fixture
    def service(self) -> GenerationService:
        """Create a generation service with mocked dependencies."""
        mock_mistral = MagicMock()
        return GenerationService(mock_mistral)

    def test_build_rag_prompt_with_sources(self, service: GenerationService):
        """Test prompt building with sources."""
        sources = [
            SourceChunk(
                document_id="doc1",
                document_name="test.pdf",
                chunk_index=0,
                content="Test content",
                score=0.95,
            )
        ]
        
        messages = service.build_rag_prompt("What is this?", sources)
        
        assert len(messages) >= 2  # System + user
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert "Test content" in messages[0]["content"]

    def test_build_rag_prompt_without_sources(self, service: GenerationService):
        """Test prompt building without sources."""
        messages = service.build_rag_prompt("What is this?", [])
        
        assert len(messages) >= 2
        assert "No documents" in messages[0]["content"]

    def test_build_rag_prompt_with_history(self, service: GenerationService):
        """Test prompt building with conversation history."""
        history = [
            ChatMessage(role=MessageRole.USER, content="Previous question"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Previous answer"),
        ]
        
        messages = service.build_rag_prompt("New question", [], history)
        
        # Should have system + history + current question
        assert len(messages) == 4
        assert messages[1]["content"] == "Previous question"
        assert messages[2]["content"] == "Previous answer"
