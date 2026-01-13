import type {
  DocumentInfo,
  DocumentListResponse,
  DocumentUploadResponse,
  SourceChunk,
  StreamEvent,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(error.detail || "Request failed", response.status);
  }
  return response.json();
}

export const api = {
  documents: {
    async upload(file: File): Promise<DocumentUploadResponse> {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: "POST",
        body: formData,
      });

      return handleResponse<DocumentUploadResponse>(response);
    },

    async list(): Promise<DocumentListResponse> {
      const response = await fetch(`${API_BASE_URL}/api/documents`);
      return handleResponse<DocumentListResponse>(response);
    },

    async get(docId: string): Promise<DocumentInfo> {
      const response = await fetch(`${API_BASE_URL}/api/documents/${docId}`);
      return handleResponse<DocumentInfo>(response);
    },

    async delete(docId: string): Promise<void> {
      const response = await fetch(`${API_BASE_URL}/api/documents/${docId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new ApiError(error.detail || "Delete failed", response.status);
      }
    },
  },

  chat: {
    async send(
      message: string,
      history: Array<{ role: "user" | "assistant"; content: string }>
    ): Promise<{ answer: string; sources: SourceChunk[] }> {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });

      return handleResponse(response);
    },

    async *stream(
      message: string,
      history: Array<{ role: "user" | "assistant"; content: string }>
    ): AsyncGenerator<StreamEvent, void, unknown> {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new ApiError(error.detail || "Stream failed", response.status);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                yield data as StreamEvent;
              } catch {
                // Skip invalid JSON
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },
  },
};

export { ApiError };
