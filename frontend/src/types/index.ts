export interface SourceChunk {
  document_id: string;
  document_name: string;
  chunk_index: number;
  content: string;
  score: number;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  chunk_count: number;
  uploaded_at: string;
  file_size: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  isStreaming?: boolean;
}

export interface ChatRequest {
  message: string;
  history: Array<{ role: "user" | "assistant"; content: string }>;
}

export interface DocumentUploadResponse {
  document: DocumentInfo;
  message: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total: number;
}

export type StreamEventType = "sources" | "content" | "done" | "error";

export interface StreamEvent {
  type: StreamEventType;
  data: unknown;
}
