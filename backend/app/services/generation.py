"""Response generation service: RAG prompt construction and LLM calls."""

from collections.abc import AsyncGenerator
from typing import Any

from mistralai import Mistral

from app.core.config import Settings, get_settings
from app.models.schemas import ChatMessage, ChatResponse, SourceChunk


class GenerationService:
    """Service for generating responses using Mistral LLM."""

    def __init__(
        self,
        mistral_client: Mistral,
        settings: Settings | None = None,
    ):
        self.mistral = mistral_client
        self.settings = settings or get_settings()

    def build_rag_prompt(
        self,
        question: str,
        sources: list[SourceChunk],
        history: list[ChatMessage] | None = None,
    ) -> list[dict[str, str]]:
        """Build the prompt with RAG context."""
        # System prompt
        system_content = """You are a helpful assistant that answers questions based on the provided document excerpts.

Guidelines:
- Answer questions using ONLY the information from the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but thorough
- When relevant, mention which document(s) the information comes from
- If asked about something not in the documents, politely explain you can only answer based on the uploaded documents"""

        # Build context from sources
        if sources:
            context_parts = []
            for i, source in enumerate(sources, 1):
                context_parts.append(
                    f"[Excerpt {i} from '{source.document_name}']:\n{source.content}"
                )
            context = "\n\n---\n\n".join(context_parts)
            system_content += f"\n\n## Document Context:\n\n{context}"
        else:
            system_content += "\n\nNote: No documents have been uploaded yet. Please ask the user to upload documents first."

        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]

        # Add conversation history
        if history:
            for msg in history[-6:]:  # Keep last 6 messages for context
                messages.append({"role": msg.role.value, "content": msg.content})

        # Add current question
        messages.append({"role": "user", "content": question})

        return messages

    def generate(
        self,
        question: str,
        sources: list[SourceChunk],
        history: list[ChatMessage] | None = None,
    ) -> ChatResponse:
        """Generate a complete response (non-streaming)."""
        messages = self.build_rag_prompt(question, sources, history)

        response = self.mistral.chat.complete(
            model=self.settings.mistral_chat_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        answer = response.choices[0].message.content

        return ChatResponse(answer=answer, sources=sources)

    async def generate_stream(
        self,
        question: str,
        sources: list[SourceChunk],
        history: list[ChatMessage] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generate a streaming response with SSE format."""
        messages = self.build_rag_prompt(question, sources, history)

        # First, send sources metadata
        yield {
            "type": "sources",
            "data": [source.model_dump() for source in sources],
        }

        # Stream the response
        stream = self.mistral.chat.stream(
            model=self.settings.mistral_chat_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        for chunk in stream:
            if chunk.data.choices and chunk.data.choices[0].delta.content:
                content = chunk.data.choices[0].delta.content
                yield {
                    "type": "content",
                    "data": content,
                }

        # Signal completion
        yield {
            "type": "done",
            "data": None,
        }
