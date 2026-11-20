import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Sparkles, ShieldCheck, AlertCircle, Copy, Check, Clock, Bookmark } from 'lucide-react';
import { CitationCard } from './CitationCard';
import { CitationItem, QueryClassificationResult } from '../api/client';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: CitationItem[];
  confidenceScore?: number;
  confidenceStatus?: 'HIGH_CONFIDENCE' | 'PARTIAL_EVIDENCE' | 'INSUFFICIENT_EVIDENCE' | 'GENERAL_QUERY';
  queryClassification?: QueryClassificationResult;
  latencyMs?: number;
  timestamp: string;
}

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getConfidenceBadge = (status?: string, score?: number) => {
    if (!status) return null;
    if (status === 'GENERAL_QUERY') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-blue-50 text-blue-800 border border-blue-300 px-2 py-0.5 rounded-full">
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          Domain Clarification
        </span>
      );
    }
    if (status === 'HIGH_CONFIDENCE') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300 px-2 py-0.5 rounded-full">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          Statutory Grounding: {Math.round((score || 0.85) * 100)}%
        </span>
      );
    }
    if (status === 'PARTIAL_EVIDENCE') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-full">
          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
          Partial Evidence: {Math.round((score || 0.65) * 100)}%
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-rose-50 text-rose-800 border border-rose-300 px-2 py-0.5 rounded-full">
        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
        Insufficient Evidence Fallback
      </span>
    );
  };

  const getClassificationBadge = (classification?: QueryClassificationResult) => {
    if (!classification) return null;
    const isIP = classification.domain === 'IP_DOMAIN';
    const isReg = classification.domain === 'REGULATORY_DOMAIN';

    const colorClass = isIP
      ? 'bg-purple-50 text-purple-800 border-purple-300'
      : isReg
      ? 'bg-indigo-50 text-indigo-800 border-indigo-300'
      : 'bg-slate-100 text-slate-700 border-slate-300';

    const label = classification.sub_domain
      ? `${classification.domain === 'IP_DOMAIN' ? 'IP' : classification.domain === 'REGULATORY_DOMAIN' ? 'Reg' : 'Gen'}: ${classification.sub_domain}`
      : classification.domain;

    return (
      <span
        className={`inline-flex items-center gap-1 text-[11px] font-semibold border px-2 py-0.5 rounded-full ${colorClass}`}
        title={`Query Domain: ${classification.domain} | Sub-domain: ${classification.sub_domain || 'None'} (Confidence: ${Math.round(classification.confidence * 100)}%)`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
        {label}
      </span>
    );
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="flex items-start gap-2.5 max-w-[85%] sm:max-w-[75%]">
          <div className="bg-ayush-800 text-white rounded-2xl rounded-tr-none px-4 py-2.5 shadow-sm text-sm leading-relaxed">
            <p className="whitespace-pre-wrap">{message.text}</p>
            <span className="text-[10px] text-ayush-200 mt-1 block text-right">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-0.5">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="flex items-start gap-3 max-w-[95%] sm:max-w-[85%]">
        <div className="w-8 h-8 rounded-full bg-ayush-700 text-white flex items-center justify-center shrink-0 shadow mt-0.5">
          <Sparkles className="w-4 h-4" />
        </div>

        <div className="flex-1 bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-sm text-sm text-slate-800">
          {/* Header Metadata Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-3 border-b border-slate-100">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-bold text-xs text-slate-900 tracking-wide">
                IP-SAKTI Sahayak
              </span>
              {getClassificationBadge(message.queryClassification)}
              {getConfidenceBadge(message.confidenceStatus, message.confidenceScore)}
            </div>

            <div className="flex items-center gap-2 text-slate-400 text-xs">
              {message.latencyMs && (
                <span className="flex items-center gap-1 text-[11px] text-slate-500">
                  <Clock className="w-3 h-3" /> {message.latencyMs}ms
                </span>
              )}
              <button
                onClick={handleCopy}
                className="hover:text-slate-700 p-1 rounded hover:bg-slate-50 transition-colors"
                title="Copy response"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Markdown Body */}
          <div className="prose prose-slate prose-sm max-w-none prose-headings:text-slate-900 prose-headings:font-bold prose-p:leading-relaxed prose-strong:text-slate-900 prose-code:bg-slate-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-ayush-900 prose-code:font-mono">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.text}
            </ReactMarkdown>
          </div>

          {/* Source Citations Section */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-slate-100">
              <div className="flex items-center gap-1.5 mb-2.5">
                <Bookmark className="w-3.5 h-3.5 text-ayush-700" />
                <h5 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Verified Statutory Citations ({message.citations.length})
                </h5>
              </div>

              <div className="grid grid-cols-1 gap-2">
                {message.citations.map((citation, idx) => (
                  <CitationCard key={idx} citation={citation} index={idx + 1} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
