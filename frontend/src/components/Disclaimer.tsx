import React from 'react';
import { AlertTriangle, ShieldCheck, Scale } from 'lucide-react';

export const Disclaimer: React.FC = () => {
  return (
    <aside aria-label="Regulatory Disclaimer" className="bg-amber-50 border-b border-amber-200 text-amber-900 px-4 py-2 text-xs md:text-sm sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1 bg-amber-200 text-amber-900 rounded-full shrink-0">
            <Scale className="w-3.5 h-3.5" />
          </div>
          <div className="leading-snug">
            <span className="font-semibold uppercase tracking-wider text-[10px] bg-amber-200 text-amber-900 px-1.5 py-0.5 rounded mr-1.5">
              Statutory Research Aid
            </span>
            <span className="font-medium text-amber-950">
              IP-SAKTI Sahayak (SIH26045 · Ministry of Ayush)
            </span>
            <span className="hidden sm:inline text-amber-800 ml-1">
              — All outputs are strictly grounded in official statutory gazettes and TKDL guidelines. This system does <strong>not</strong> constitute certified legal advice.
            </span>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-1.5 shrink-0 text-xs font-semibold text-emerald-800 bg-emerald-100/80 px-2 py-0.5 rounded-full border border-emerald-300">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Zero-Hallucination Guard Active</span>
        </div>
      </div>
    </aside>
  );
};
