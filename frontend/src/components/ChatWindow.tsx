import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Trash2, ArrowUpRight, Loader2, Bot, AlertCircle } from 'lucide-react';
import { MessageBubble, ChatMessage } from './MessageBubble';
import { LanguageSelector } from './LanguageSelector';
import { PRESET_PROMPTS } from '../hooks/useChat';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  language: string;
  onSetLanguage: (lang: string) => void;
  onSendMessage: (query: string) => void;
  onClearChat: () => void;
  error: string | null;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  language,
  onSetLanguage,
  onSendMessage,
  onClearChat,
  error
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handlePromptClick = (query: string) => {
    onSendMessage(query);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/50">
      {/* Top Secondary Action Bar */}
      <div className="bg-white border-b border-slate-200 px-4 py-2.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-xs font-semibold text-slate-700">
            Ayush Legal Corpus Grounded
          </span>
          <span className="text-slate-300">|</span>
          <span className="text-xs text-slate-500 hidden sm:inline">
            National & International Regimes
          </span>
        </div>

        <div className="flex items-center gap-2">
          <LanguageSelector
            currentLanguage={language}
            onSelectLanguage={onSetLanguage}
            disabled={isLoading}
          />
          {messages.length > 0 && (
            <button
              onClick={onClearChat}
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
              title="Clear conversation"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 max-w-5xl w-full mx-auto">
        {messages.length === 0 ? (
          <div className="py-6 flex flex-col items-center text-center">
            {/* Hero Emblem Banner */}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-ayush-800 to-ayush-600 text-white flex items-center justify-center shadow-lg shadow-ayush-900/10 mb-4">
              <Sparkles className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              IP-SAKTI Sahayak
            </h2>
            <p className="text-sm text-slate-600 max-w-lg mt-2 leading-relaxed">
              Automated, source-grounded intelligence for <strong>Ayurveda Intellectual Property</strong>, 
              Patents Act §3(p), National Biodiversity Authority (NBA) approvals, and ASU drug licensing.
            </p>

            {/* Zero Hallucination Guarantee Badge */}
            <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-full text-xs font-medium text-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Strict Grounding: Answers cited directly from statutory gazettes.
            </div>

            {/* Curated Question Starters */}
            <div className="mt-8 w-full text-left">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 text-center">
                Frequently Consulted Regulatory Queries
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-3xl mx-auto">
                {PRESET_PROMPTS.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => handlePromptClick(p.query)}
                    className="flex flex-col text-left p-3.5 bg-white border border-slate-200 hover:border-ayush-600 hover:shadow-md rounded-xl transition-all group"
                  >
                    <div className="flex items-center justify-between w-full mb-1">
                      <span className="text-[10px] font-bold text-ayush-800 uppercase tracking-wide bg-ayush-50 px-2 py-0.5 rounded border border-ayush-100">
                        {p.tag}
                      </span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-ayush-700 transition-colors" />
                    </div>
                    <span className="text-xs font-semibold text-slate-800 group-hover:text-ayush-900 mt-1">
                      {p.title}
                    </span>
                    <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">
                      {p.query}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div>
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
          </div>
        )}

        {isLoading && (
          <div className="flex items-center gap-3 text-sm text-slate-600 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm w-fit max-w-md animate-pulse mb-6">
            <Loader2 className="w-5 h-5 text-ayush-700 animate-spin" />
            <div>
              <p className="font-semibold text-xs text-slate-900">
                Retrieving Official Regulatory Clauses...
              </p>
              <p className="text-[11px] text-slate-600">
                Matching against Patents Act §3(p), Biological Diversity Act, and TKDL index.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs mb-4">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <p>{error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Query Input Box */}
      <div className="bg-white border-t border-slate-200 p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative flex items-end bg-slate-50 border border-slate-300 focus-within:border-ayush-600 focus-within:ring-2 focus-within:ring-ayush-600/20 rounded-2xl transition-all shadow-inner p-1.5">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                language === 'hi'
                  ? 'आयुर्वेद बौद्धिक संपदा या विनियामक नियमों पर प्रश्न पूछें...'
                  : 'Ask an Ayurveda IP, Section 3(p), NBA approval, or regulatory compliance question...'
              }
              disabled={isLoading}
              className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none resize-none max-h-32 min-h-[42px]"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-2.5 bg-ayush-800 hover:bg-ayush-900 disabled:bg-slate-300 text-white rounded-xl transition-all shrink-0 ml-2 shadow-sm"
              title="Send query"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-600 mt-2 px-1">
            <span>
              Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for newline
            </span>
            <span className="italic">
              Powered by Ministry of Ayush Grounded RAG
            </span>
          </div>
        </form>
      </div>
    </div>
  );
};
