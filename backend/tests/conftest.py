"""Pytest configuration and fixtures."""

import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["MISTRAL_API_KEY"] = "test-api-key"
os.environ["CHROMA_PERSIST_DIRECTORY"] = tempfile.mkdtemp()
os.environ["UPLOAD_DIRECTORY"] = tempfile.mkdtemp()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    from app.main import app
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Generate minimal valid PDF content for testing."""
    # Minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test document content for RAG testing.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF"""


@pytest.fixture
def sample_txt_content() -> bytes:
    """Generate sample text content for testing."""
    return b"""This is a test document for the RAG application.

It contains multiple paragraphs to test the chunking functionality.
The document discusses various topics that can be queried.

Section 1: Introduction
This section provides an overview of the document content.
It explains the purpose and scope of the test document.

Section 2: Main Content
This section contains the main body of the document.
It includes detailed information that can be retrieved through RAG.

Section 3: Conclusion
This section summarizes the key points of the document.
It provides final thoughts and recommendations."""
