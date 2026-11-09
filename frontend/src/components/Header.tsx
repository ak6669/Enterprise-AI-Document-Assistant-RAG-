import React from 'react';
import { Database, Cpu, ShieldCheck, FileText } from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  documentCount: number;
}

export const Header: React.FC<HeaderProps> = ({ health, documentCount }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-white tracking-tight">Enterprise RAG Assistant</h1>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">
                v1.0 Production
              </span>
            </div>
            <p className="text-xs text-slate-400">Context-Grounded Document Intelligence & Verifiable Citations</p>
          </div>
        </div>

        {/* Live System Diagnostics */}
        <div className="flex items-center space-x-4 text-xs">
          {/* Document count */}
          <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
            <FileText className="w-3.5 h-3.5 text-brand-400" />
            <span className="font-medium text-slate-200">{documentCount}</span>
            <span className="text-slate-400">Docs Indexed</span>
          </div>

          {/* Vector Store */}
          <div className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">ChromaDB:</span>
            <span className="font-semibold text-emerald-400">
              {health ? `${health.vector_store.indexed_chunks} chunks` : 'Connecting...'}
            </span>
          </div>

          {/* LLM Model */}
          <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">LLM:</span>
            <span className="font-semibold text-indigo-300">
              {health?.llm.model || 'gpt-4o-mini'}
            </span>
          </div>

          {/* Overall Status Pill */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800/90 border border-slate-700 text-slate-300">
            <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            <span className="font-medium text-slate-200">
              {health?.status === 'healthy' ? 'Online' : 'Initializing'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
