"""Document management API endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.dependencies import (
    ChromaCollectionDep,
    MistralClientDep,
    SettingsDep,
)
from app.models.schemas import DocumentInfo, DocumentListResponse, DocumentUploadResponse
from app.services.ingestion import IngestionService

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Check extension
    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    mistral_client: MistralClientDep,
    collection: ChromaCollectionDep,
    settings: SettingsDep,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """Upload and process a document for RAG."""
    validate_file(file)

    # Read file content to check size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    # Reset file position
    await file.seek(0)

    # Process document
    service = IngestionService(mistral_client, collection, settings)

    try:
        doc_info = await service.ingest_document(
            file=file.file,
            filename=file.filename,
            file_size=file_size,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )

    return DocumentUploadResponse(
        document=doc_info,
        message=f"Document '{file.filename}' processed successfully ({doc_info.chunk_count} chunks)",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    mistral_client: MistralClientDep,
    collection: ChromaCollectionDep,
    settings: SettingsDep,
) -> DocumentListResponse:
    """List all uploaded documents."""
    service = IngestionService(mistral_client, collection, settings)
    documents = service.list_documents()

    return DocumentListResponse(
        documents=documents,
        total=len(documents),
    )


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(
    doc_id: str,
    mistral_client: MistralClientDep,
    collection: ChromaCollectionDep,
    settings: SettingsDep,
) -> DocumentInfo:
    """Get information about a specific document."""
    service = IngestionService(mistral_client, collection, settings)
    documents = service.list_documents()

    for doc in documents:
        if doc.id == doc_id:
            return doc

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document '{doc_id}' not found",
    )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    mistral_client: MistralClientDep,
    collection: ChromaCollectionDep,
    settings: SettingsDep,
) -> dict[str, str]:
    """Delete a document and its chunks."""
    service = IngestionService(mistral_client, collection, settings)

    if service.delete_document(doc_id):
        return {"message": f"Document '{doc_id}' deleted successfully"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document '{doc_id}' not found",
    )
