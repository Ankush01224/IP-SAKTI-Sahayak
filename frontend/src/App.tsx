import React, { useState } from 'react';
import { Home } from './pages/Home';
import { Admin } from './pages/Admin';
import { MessageSquare, Database } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'admin'>('chat');

  return (
    <div className="h-screen flex flex-col bg-slate-100 text-slate-900 font-sans overflow-hidden">
      {/* Global Ayush Brand Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo */}
            <div className="w-8 h-8 rounded-lg bg-ayush-800 text-white flex items-center justify-center font-serif font-black text-base shadow-sm">
              🌿
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-sm sm:text-base tracking-tight text-slate-900">
                  IP-SAKTI Sahayak
                </span>
                <span className="bg-ayush-100 text-ayush-800 text-[10px] font-bold px-1.5 py-0.5 rounded border border-ayush-200">
                  SIH26045
                </span>
              </div>
              <p className="text-[10px] text-slate-500 hidden sm:block">
                Ministry of Ayush · Multilingual Source-Cited IP & Regulatory Assistant
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'chat'
                  ? 'bg-white text-ayush-800 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Legal Chat</span>
            </button>
            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'admin'
                  ? 'bg-white text-ayush-800 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Corpus Admin</span>
            </button>
          </nav>
        </div>
      </header>

      {/* 3. Main Workspace Surface */}
      <main className="flex-1 flex flex-col min-h-0 overflow-y-auto">
        {activeTab === 'chat' ? <Home /> : <Admin />}
      </main>
    </div>
  );
};

export default App;
