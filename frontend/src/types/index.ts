export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'INDEXED' | 'FAILED';
export type DocumentType = 'pdf' | 'docx' | 'txt';

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: DocumentType;
  file_size: number;
  status: DocumentStatus;
  page_count: number;
  chunk_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  document_id: string;
  filename: string;
  page_number: number;
  chunk_id: string;
  excerpt: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  latency_seconds?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface SystemHealth {
  status: string;
  version: string;
  database: string;
  vector_store: {
    status: string;
    indexed_chunks: number;
  };
  llm: {
    configured: boolean;
    model: string;
  };
  embedding_model: string;
}
