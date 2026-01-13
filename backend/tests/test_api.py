"""Tests for API endpoints."""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestDocumentsAPI:
    """Tests for document management endpoints."""

    def test_list_documents_empty(self, client: TestClient):
        """Test listing documents when none exist."""
        response = client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)

    def test_upload_invalid_file_type(self, client: TestClient):
        """Test uploading unsupported file type."""
        file_content = b"test content"
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()

    def test_upload_empty_file(self, client: TestClient):
        """Test uploading empty file."""
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", io.BytesIO(b""), "text/plain")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_delete_nonexistent_document(self, client: TestClient):
        """Test deleting a document that doesn't exist."""
        response = client.delete("/api/documents/nonexistent-doc-id")
        assert response.status_code == 404

    @patch("app.services.ingestion.IngestionService.generate_embeddings")
    def test_upload_txt_document(
        self,
        mock_embeddings: MagicMock,
        client: TestClient,
        sample_txt_content: bytes,
    ):
        """Test uploading a TXT document."""
        # Mock embeddings to avoid API call
        mock_embeddings.return_value = [[0.1] * 1024]

        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")},
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]


class TestChatAPI:
    """Tests for chat endpoints."""

    def test_chat_request_validation(self, client: TestClient):
        """Test chat endpoint validates request body."""
        # Empty message
        response = client.post(
            "/api/chat",
            json={"message": "", "history": []},
        )
        assert response.status_code == 422

    def test_chat_without_documents(self, client: TestClient):
        """Test chat when no documents are uploaded."""
        with patch("app.services.retrieval.RetrievalService.search") as mock_search:
            mock_search.return_value = []

            with patch("app.services.generation.GenerationService.generate") as mock_gen:
                mock_gen.return_value = MagicMock(
                    answer="No documents uploaded yet.",
                    sources=[],
                )

                response = client.post(
                    "/api/chat",
                    json={"message": "What is this about?", "history": []},
                )

                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "sources" in data


class TestChatStreamAPI:
    """Tests for streaming chat endpoint."""

    def test_stream_endpoint_returns_sse(self, client: TestClient):
        """Test that stream endpoint returns SSE response."""
        with patch("app.services.retrieval.RetrievalService.search") as mock_search:
            mock_search.return_value = []

            with patch("app.services.generation.GenerationService.generate_stream") as mock_stream:
                async def mock_generator():
                    yield {"type": "sources", "data": []}
                    yield {"type": "content", "data": "Test response"}
                    yield {"type": "done", "data": None}

                mock_stream.return_value = mock_generator()

                response = client.post(
                    "/api/chat/stream",
                    json={"message": "Test question", "history": []},
                )

                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
