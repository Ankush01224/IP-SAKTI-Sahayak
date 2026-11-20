import React, { useState } from 'react';
import { BookOpen, ExternalLink, ChevronDown, ChevronUp, Scale, CheckCircle2 } from 'lucide-react';
import { CitationItem } from '../api/client';

interface CitationCardProps {
  citation: CitationItem;
  index: number;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getJurisdictionBadge = (jur: string) => {
    if (jur.toLowerCase().includes('india')) {
      return <span className="bg-orange-50 text-orange-800 border border-orange-200 text-[10px] font-semibold px-1.5 py-0.5 rounded">🇮🇳 India</span>;
    }
    if (jur.toLowerCase().includes('us') || jur.toLowerCase().includes('fda')) {
      return <span className="bg-blue-50 text-blue-800 border border-blue-200 text-[10px] font-semibold px-1.5 py-0.5 rounded">🇺🇸 US FDA</span>;
    }
    return <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-semibold px-1.5 py-0.5 rounded">🌐 International</span>;
  };

  return (
    <div className="border border-slate-200 hover:border-ayush-500/50 bg-white rounded-lg p-3 transition-all shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2">
          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-ayush-100 text-ayush-800 text-xs font-bold shrink-0 mt-0.5">
            {index}
          </span>
          <div>
            <h4 className="text-xs font-bold text-slate-900 leading-tight">
              {citation.document_title}
            </h4>
            <div className="flex flex-wrap items-center gap-1.5 mt-1">
              {getJurisdictionBadge(citation.jurisdiction)}
              <span className="bg-slate-100 text-slate-700 text-[10px] font-medium px-1.5 py-0.5 rounded">
                {citation.section_number}
              </span>
              {citation.page_number && (
                <span className="text-[10px] text-slate-500">
                  p. {citation.page_number}
                </span>
              )}
              {citation.is_verified && (
                <span className="bg-emerald-50 text-emerald-800 border border-emerald-300 text-[10px] font-semibold px-1.5 py-0.5 rounded flex items-center gap-1">
                  <CheckCircle2 className="w-2.5 h-2.5 text-emerald-600" />
                  Verified
                </span>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-slate-100 transition-colors shrink-0"
          title={isExpanded ? "Collapse excerpt" : "Expand excerpt"}
        >
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {citation.section_title && citation.section_title !== citation.section_number && (
        <p className="text-[11px] text-slate-600 font-medium mt-1.5 pl-7 line-clamp-1">
          {citation.section_title}
        </p>
      )}

      {/* Expandable Verbatim Excerpt */}
      {isExpanded ? (
        <div className="mt-2.5 pt-2.5 border-t border-slate-100 pl-7 text-xs text-slate-700">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-ayush-600" /> Grounded Text Excerpt
            </span>
            <span className="text-[10px] text-slate-600">
              Relevance: {Math.round(citation.similarity_score * 100)}%
            </span>
          </div>
          <blockquote className="bg-slate-50 border-l-2 border-ayush-600 p-2 text-slate-800 rounded-r text-[11px] leading-relaxed italic">
            "{citation.snippet}"
          </blockquote>
          {citation.verification_details && (
            <p className="text-[10px] text-emerald-800 mt-1.5 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
              {citation.verification_details}
            </p>
          )}
        </div>
      ) : (
        <div className="mt-1 pl-7">
          <p className="text-[11px] text-slate-500 line-clamp-1 italic">
            "{citation.snippet}"
          </p>
        </div>
      )}
    </div>
  );
};
