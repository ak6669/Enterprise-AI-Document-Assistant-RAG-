import React from 'react';
import { BookOpen, ExternalLink, Award } from 'lucide-react';
import { Citation } from '../types';

interface CitationCardProps {
  citation: Citation;
  index: number;
  onInspect?: (citation: Citation) => void;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index, onInspect }) => {
  const matchPercent = Math.round(citation.score * 100);

  return (
    <div
      onClick={() => onInspect && onInspect(citation)}
      className="group relative flex flex-col justify-between p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/60 hover:border-brand-500/50 transition-all cursor-pointer shadow-sm"
    >
      <div>
        {/* Header with Document Name and Page Number Badge */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center space-x-1.5 overflow-hidden">
            <span className="w-5 h-5 rounded-full bg-brand-500/20 text-brand-400 text-[10px] font-bold flex items-center justify-center flex-shrink-0">
              {index + 1}
            </span>
            <span
              className="text-xs font-semibold text-slate-200 truncate group-hover:text-brand-300 transition-colors"
              title={citation.filename}
            >
              {citation.filename}
            </span>
          </div>

          {/* Page Badge */}
          <div className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-semibold flex-shrink-0">
            <BookOpen className="w-3 h-3 text-indigo-400" />
            <span>Page {citation.page_number}</span>
          </div>
        </div>

        {/* Excerpt */}
        <p className="text-[11px] text-slate-400 line-clamp-3 leading-relaxed font-mono bg-slate-950/50 p-2 rounded-lg border border-slate-800/80">
          "{citation.excerpt}"
        </p>
      </div>

      {/* Footer info: match score & inspect action */}
      <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-500">
        <div className="flex items-center space-x-1">
          <Award className="w-3 h-3 text-emerald-400" />
          <span>Semantic Score: <strong className="text-emerald-400 font-semibold">{matchPercent}%</strong></span>
        </div>
        <span className="flex items-center space-x-0.5 text-brand-400 group-hover:underline">
          <span>View context</span>
          <ExternalLink className="w-2.5 h-2.5" />
        </span>
      </div>
    </div>
  );
};
