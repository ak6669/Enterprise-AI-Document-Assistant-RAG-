import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { DocumentUpload } from './components/DocumentUpload';
import { DocumentList } from './components/DocumentList';
import { ChatInterface } from './components/ChatInterface';
import { SourceInspectorModal } from './components/SourceInspectorModal';
import { DocumentItem, SystemHealth, Citation } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);

  const loadData = useCallback(async () => {
    try {
      const [healthData, docsData] = await Promise.allSettled([
        api.getHealth(),
        api.getDocuments(),
      ]);

      if (healthData.status === 'fulfilled') {
        setHealth(healthData.value);
      }
      if (docsData.status === 'fulfilled') {
        setDocuments(docsData.value);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000); // Polling health & docs every 15s
    return () => clearInterval(interval);
  }, [loadData]);

  const handleUploadSuccess = (newDoc: DocumentItem) => {
    setDocuments((prev) => [newDoc, ...prev.filter((d) => d.id !== newDoc.id)]);
    loadData();
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (selectedDocId === docId) {
        setSelectedDocId(null);
      }
      loadData();
    } catch (err) {
      console.error('Error deleting document:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header Diagnostics Bar */}
      <Header health={health} documentCount={documents.length} />

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-4.5rem)]">
        {/* Left Column: Document Ingestion & List (4 cols) */}
        <div className="lg:col-span-4 flex flex-col space-y-4 h-full overflow-hidden">
          <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          <DocumentList
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDoc={setSelectedDocId}
            onDeleteDoc={handleDeleteDocument}
            isLoading={isLoadingDocs}
          />
        </div>

        {/* Right Column: Grounded Chat & Citations (8 cols) */}
        <div className="lg:col-span-8 h-full overflow-hidden">
          <ChatInterface
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDoc={setSelectedDocId}
            onInspectCitation={setActiveCitation}
          />
        </div>
      </main>

      {/* Citation Source Inspector Modal */}
      <SourceInspectorModal
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />
    </div>
  );
};

export default App;
