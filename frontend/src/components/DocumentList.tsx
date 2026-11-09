import React from 'react';
import { FileText, Trash2, CheckCircle2, Clock, AlertTriangle, Layers, BookOpen } from 'lucide-react';
import { DocumentItem } from '../types';

interface DocumentListProps {
  documents: DocumentItem[];
  selectedDocId?: string | null;
  onSelectDoc?: (docId: string | null) => void;
  onDeleteDoc: (docId: string) => void;
  isLoading: boolean;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onDeleteDoc,
}) => {
  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFormatBadge = (ext: string) => {
    switch (ext.toLowerCase()) {
      case 'pdf':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">PDF</span>;
      case 'docx':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">DOCX</span>;
      default:
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">TXT</span>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'INDEXED':
        return <span title="Indexed & Ready"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /></span>;
      case 'PROCESSING':
        return <span title="Processing"><Clock className="w-3.5 h-3.5 text-amber-400 animate-spin" /></span>;
      default:
        return <span title="Processing Error"><AlertTriangle className="w-3.5 h-3.5 text-rose-400" /></span>;
    }
  };

  return (
    <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-5 shadow-sm flex flex-col flex-1">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <span>Active Knowledge Sources</span>
          <span className="text-xs font-normal text-slate-400">({documents.length})</span>
        </h3>
        {onSelectDoc && (
          <button
            onClick={() => onSelectDoc(null)}
            className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
              !selectedDocId
                ? 'bg-brand-500/20 text-brand-300 font-semibold border border-brand-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Sources
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-2.5 max-h-[380px] pr-1">
        {documents.length === 0 ? (
          <div className="text-center py-10 px-4 rounded-xl border border-dashed border-slate-800 text-slate-500 text-xs">
            <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600 opacity-60" />
            <p>No documents uploaded yet.</p>
            <p className="text-[11px] text-slate-600 mt-1">Upload PDF, DOCX or TXT files above to query.</p>
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocId === doc.id;
            return (
              <div
                key={doc.id}
                onClick={() => onSelectDoc && onSelectDoc(isSelected ? null : doc.id)}
                className={`group flex items-start justify-between p-3 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-brand-950/40 border-brand-500/60 shadow-sm shadow-brand-500/10'
                    : 'bg-slate-900/40 hover:bg-slate-800/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start space-x-3 overflow-hidden">
                  <div className="mt-0.5">{getFormatBadge(doc.file_type)}</div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate group-hover:text-white" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <div className="flex items-center space-x-3 mt-1.5 text-[11px] text-slate-400">
                      <span className="flex items-center space-x-1" title="Page Count">
                        <BookOpen className="w-3 h-3 text-slate-500" />
                        <span>{doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}</span>
                      </span>
                      <span className="flex items-center space-x-1" title="Vector Chunks">
                        <Layers className="w-3 h-3 text-slate-500" />
                        <span>{doc.chunk_count} chunks</span>
                      </span>
                      <span>{formatBytes(doc.file_size)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
                  {getStatusIcon(doc.status)}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Remove "${doc.filename}" from knowledge base?`)) {
                        onDeleteDoc(doc.id);
                      }
                    }}
                    className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete document"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
