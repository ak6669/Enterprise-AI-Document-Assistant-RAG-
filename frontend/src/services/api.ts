import axios from 'axios';
import { DocumentItem, Conversation, SystemHealth, Citation } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // System Health
  async getHealth(): Promise<SystemHealth> {
    const response = await apiClient.get<SystemHealth>('/health');
    return response.data;
  },

  // Document Management
  async getDocuments(): Promise<DocumentItem[]> {
    const response = await apiClient.get<DocumentItem[]>('/documents');
    return response.data;
  },

  async uploadDocument(file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<DocumentItem>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async deleteDocument(documentId: string): Promise<void> {
    await apiClient.delete(`/documents/${documentId}`);
  },

  // Chat & RAG
  async sendMessage(params: {
    message: string;
    conversationId?: string;
    topK?: number;
    documentIds?: string[];
  }): Promise<{
    conversation_id: string;
    message_id: string;
    query: string;
    answer: string;
    citations: Citation[];
    latency_seconds: number;
    created_at: string;
  }> {
    const response = await apiClient.post('/chat', {
      message: params.message,
      conversation_id: params.conversationId,
      top_k: params.topK || 4,
      document_ids: params.documentIds,
    });
    return response.data;
  },

  async getConversations(): Promise<Conversation[]> {
    const response = await apiClient.get<Conversation[]>('/chat/conversations');
    return response.data;
  },

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await apiClient.get<Conversation>(`/chat/conversations/${conversationId}`);
    return response.data;
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/chat/conversations/${conversationId}`);
  },
};
