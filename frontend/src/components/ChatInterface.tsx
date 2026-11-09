import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Clock, RefreshCw, BookOpen, Filter } from 'lucide-react';
import { ChatMessage, Citation, DocumentItem } from '../types';
import { CitationCard } from './CitationCard';
import { api } from '../services/api';

interface ChatInterfaceProps {
  documents: DocumentItem[];
  selectedDocId: string | null;
  onSelectDoc: (docId: string | null) => void;
  onInspectCitation: (citation: Citation) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onInspectCitation,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I am your Enterprise AI Document Assistant. Upload enterprise documents (PDF, DOCX, or TXT) on the left, and ask questions. Every answer will be strictly grounded in your documents with verified source names and page numbers.',
      created_at: new Date().toISOString(),
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [topK, setTopK] = useState<number>(4);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputQuery.trim();
    if (!query || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const response = await api.sendMessage({
        message: query,
        conversationId: conversationId,
        topK: topK,
        documentIds: selectedDocId ? [selectedDocId] : undefined,
      });

      setConversationId(response.conversation_id);

      const assistantMessage: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        latency_seconds: response.latency_seconds,
        created_at: response.created_at,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || 'Failed to generate response. Please ensure backend is running.';
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Error: ${errorMsg}`,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = () => {
    setConversationId(undefined);
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: 'New conversation started. Ask any question regarding your uploaded enterprise documents.',
        created_at: new Date().toISOString(),
      },
    ]);
  };

  const selectedDocObj = documents.find((d) => d.id === selectedDocId);

  return (
    <div className="bg-slate-900/60 rounded-2xl border border-slate-800 flex flex-col h-full shadow-sm overflow-hidden">
      {/* Top Chat Bar: Scope filter & New conversation button */}
      <div className="px-5 py-3.5 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-slate-300">
            <Filter className="w-3.5 h-3.5 text-brand-400" />
            <span className="text-slate-400">Context Scope:</span>
            {selectedDocObj ? (
              <span className="px-2 py-0.5 rounded-md bg-brand-500/20 text-brand-300 font-semibold border border-brand-500/30 flex items-center space-x-1">
                <span>{selectedDocObj.filename}</span>
                <button
                  onClick={() => onSelectDoc(null)}
                  className="ml-1 hover:text-white"
                  title="Remove filter"
                >
                  ×
                </button>
              </span>
            ) : (
              <span className="font-semibold text-slate-200">All Indexed Documents ({documents.length})</span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Top K selector */}
          <div className="flex items-center space-x-1 text-xs text-slate-400">
            <span>Chunks:</span>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 text-slate-200 rounded px-1.5 py-0.5 text-xs focus:outline-none"
            >
              <option value={2}>Top 2</option>
              <option value={4}>Top 4</option>
              <option value={6}>Top 6</option>
            </select>
          </div>

          <button
            onClick={handleResetChat}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs transition-colors"
            title="Start new conversation thread"
          >
            <RefreshCw className="w-3 h-3" />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
                  isUser
                    ? 'bg-gradient-to-tr from-brand-600 to-brand-500 text-white'
                    : 'bg-slate-800 text-brand-400 border border-slate-700'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble & Citations */}
              <div className={`max-w-[85%] space-y-2.5 ${isUser ? 'items-end' : 'items-start'}`}>
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'bg-slate-800/80 text-slate-100 border border-slate-700/80 shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Latency badge for assistant */}
                  {!isUser && msg.latency_seconds !== undefined && msg.latency_seconds > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-700/50 flex items-center space-x-1 text-[10px] text-slate-400">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>Retrieved and synthesized in {msg.latency_seconds}s</span>
                    </div>
                  )}
                </div>

                {/* Citations Grid */}
                {!isUser && msg.citations && msg.citations.length > 0 && (
                  <div className="space-y-2 pt-1">
                    <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Verified Citations ({msg.citations.length})</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {msg.citations.map((citation, idx) => (
                        <CitationCard
                          key={`${citation.document_id}-${citation.page_number}-${idx}`}
                          citation={citation}
                          index={idx}
                          onInspect={onInspectCitation}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-xl bg-slate-800 text-brand-400 border border-slate-700 flex items-center justify-center flex-shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/80 text-sm flex items-center space-x-2 text-slate-300">
              <Sparkles className="w-4 h-4 text-brand-400 animate-spin" />
              <span>Retrieving relevant pages and synthesizing grounded answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-800 bg-slate-900/90">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder={
              documents.length === 0
                ? 'Upload documents on the left before querying...'
                : 'Ask a question grounded in your documents (e.g. "What are the quarterly targets on page 3?")...'
            }
            disabled={isLoading}
            className="w-full bg-slate-950 border border-slate-700/80 focus:border-brand-500 rounded-xl px-4 py-3 pr-12 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="absolute right-2 p-2 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:bg-slate-800 text-white disabled:text-slate-600 transition-colors shadow-sm"
            title="Send query"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
