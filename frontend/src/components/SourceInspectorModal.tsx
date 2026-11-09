import React from 'react';
import { X, BookOpen, FileText, CheckCircle, Shield } from 'lucide-react';
import { Citation } from '../types';

interface SourceInspectorModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const SourceInspectorModal: React.FC<SourceInspectorModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 px-6 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-brand-500/10 text-brand-400 flex items-center justify-center border border-brand-500/20">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Source Citation Inspector</h3>
              <p className="text-xs text-slate-400">Verifiable Grounding Evidence</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          {/* Metadata badges */}
          <div className="flex flex-wrap gap-2 text-xs">
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200">
              <FileText className="w-3.5 h-3.5 text-brand-400" />
              <span className="text-slate-400">Document:</span>
              <span className="font-semibold">{citation.filename}</span>
            </div>
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
              <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
              <span className="font-semibold">Page {citation.page_number}</span>
            </div>
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              <span>Similarity: {Math.round(citation.score * 100)}%</span>
            </div>
          </div>

          {/* Raw Text Chunk Box */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Retrieved Context Text
            </label>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap select-text">
              {citation.excerpt}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 text-[11px] text-slate-400">
            <p className="font-semibold text-slate-300 mb-1">RAG Grounding Guarantee</p>
            <p>
              This text passage was indexed from <strong>{citation.filename}</strong> on <strong>Page {citation.page_number}</strong>.
              The language model is constrained to construct responses strictly from indexed passages matching this evidence.
            </p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 px-6 border-t border-slate-800 bg-slate-900/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
