import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { DocumentItem } from '../types';

interface DocumentUploadProps {
  onUploadSuccess: (newDoc: DocumentItem) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadSuccessName, setUploadSuccessName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    setErrorMessage(null);
    setUploadSuccessName(null);

    const validExtensions = ['pdf', 'docx', 'txt'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !validExtensions.includes(ext)) {
      setErrorMessage(`Unsupported format .${ext}. Only PDF, DOCX, and TXT files are supported.`);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMessage('File size exceeds 50MB limit.');
      return;
    }

    setIsUploading(true);
    try {
      const result = await api.uploadDocument(file);
      setUploadSuccessName(file.name);
      onUploadSuccess(result);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Document processing failed. Please try again.';
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <span>Ingest Knowledge Base</span>
        </h2>
        <span className="text-xs text-slate-400">PDF, DOCX, TXT up to 50MB</span>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-brand-500 bg-brand-500/10'
            : 'border-slate-700/80 hover:border-slate-600 bg-slate-900/40 hover:bg-slate-800/40'
        } ${isUploading ? 'opacity-70 pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileSelect}
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center justify-center py-2 space-y-2">
            <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
            <p className="text-sm font-medium text-slate-200">
              Extracting pages, chunking & generating embeddings...
            </p>
            <p className="text-xs text-slate-400">This ensures precise page citations in answers.</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-2 space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
              <UploadCloud className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">
                <span className="text-brand-400 underline">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-slate-500 mt-0.5">Automated page-aware extraction & indexing</p>
            </div>
          </div>
        )}
      </div>

      {/* Success notification */}
      {uploadSuccessName && (
        <div className="mt-3 flex items-center space-x-2 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span className="truncate">Successfully indexed <strong>{uploadSuccessName}</strong></span>
        </div>
      )}

      {/* Error notification */}
      {errorMessage && (
        <div className="mt-3 flex items-center space-x-2 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs animate-in fade-in">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};
