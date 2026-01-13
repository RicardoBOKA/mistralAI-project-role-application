"""Chat API endpoints with streaming support."""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import (
    ChromaCollectionDep,
    MistralClientDep,
    SettingsDep,
)
from app.models.schemas import ChatRequest, ChatResponse
from app.services.generation import GenerationService
from app.services.retrieval import RetrievalService

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    mistral_client: MistralClientDep,
    collection: ChromaCollectionDep,
    settings: SettingsDep,
) -> ChatResponse:
    """Answer a question using RAG (non-streaming)."""
    # Retrieve relevant chunks
    retrieval_service = RetrievalService(mistral_client, collection, settings)
    sources = retrieval_service.search(request.message)

    # Generate response
    generation_service = GenerationService(mistral_client, settings)
    response = generation_service.generate(
        question=request.message,
        sources=sources,
        history=request.history,
    )

    return response


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    mistral_client: MistralClientDep,
    collection: ChromaCollectionDep,
    settings: SettingsDep,
) -> StreamingResponse:
    """Answer a question using RAG with streaming response."""
    # Retrieve relevant chunks
    retrieval_service = RetrievalService(mistral_client, collection, settings)

    try:
        sources = retrieval_service.search(request.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve context: {str(e)}",
        )

    # Create streaming generator
    generation_service = GenerationService(mistral_client, settings)

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            async for event in generation_service.generate_stream(
                question=request.message,
                sources=sources,
                history=request.history,
            ):
                # Format as SSE
                data = json.dumps(event)
                yield f"data: {data}\n\n"
        except Exception as e:
            error_event = json.dumps({"type": "error", "data": str(e)})
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
