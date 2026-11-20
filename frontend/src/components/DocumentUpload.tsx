import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api/client';

interface DocumentUploadProps {
  onUploadSuccess: () => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [jurisdiction, setJurisdiction] = useState('India');
  const [category, setCategory] = useState('Ayurveda Regulatory');
  const [isUploading, setIsUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '));
      }
      setSuccessMessage(null);
      setErrorMessage(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selectedFile = e.dataTransfer.files[0];
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '));
      }
      setSuccessMessage(null);
      setErrorMessage(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const res = await api.uploadDocument(file, title, jurisdiction, category);
      setSuccessMessage(res.message || 'Document uploaded and chunked successfully!');
      setFile(null);
      setTitle('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      onUploadSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to process document');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-ayush-100 text-ayush-800 rounded-lg">
          <UploadCloud className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Ingest Regulatory Gazette or Statute
          </h3>
          <p className="text-xs text-slate-500">
            Parses PDF, Markdown, or text documents into semantic regulatory chunks.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Drop Zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-300 hover:border-ayush-600 bg-slate-50 hover:bg-ayush-50/40 rounded-xl p-6 text-center cursor-pointer transition-colors"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.md,.txt,.markdown"
            className="hidden"
          />
          {file ? (
            <div className="flex items-center justify-center gap-2 text-sm font-semibold text-ayush-900">
              <FileText className="w-5 h-5 text-ayush-700" />
              <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          ) : (
            <div className="space-y-1">
              <UploadCloud className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="text-xs font-semibold text-slate-700">
                Click or drag & drop regulatory document here
              </p>
              <p className="text-[11px] text-slate-400">
                Supports PDF, Markdown (.md), and TXT
              </p>
            </div>
          )}
        </div>

        {/* Metadata Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Document Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Biological Diversity Act"
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-ayush-600"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Jurisdiction
            </label>
            <select
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-ayush-600 cursor-pointer"
            >
              <option value="India">🇮🇳 India (Ministry of Ayush)</option>
              <option value="United States">🇺🇸 United States (US FDA)</option>
              <option value="European Union">🇪🇺 European Union (EMA)</option>
              <option value="International (WHO / WIPO)">🌐 International (WHO / WIPO)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-ayush-600 cursor-pointer"
            >
              <option value="Patent Law & Section 3(p)">Patent Law & Section 3(p)</option>
              <option value="Biological Diversity & ABS">Biological Diversity & ABS</option>
              <option value="Drugs & Cosmetics Act">Drugs & Cosmetics Act (Chapter IV-A)</option>
              <option value="TKDL & Biopiracy Defense">TKDL & Biopiracy Defense</option>
              <option value="Export & WHO-GMP Quality">Export & WHO-GMP Quality</option>
              <option value="International Herbal Regulations">International Herbal Regulations</option>
            </select>
          </div>
        </div>

        {/* Feedback Messages */}
        {successMessage && (
          <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <p>{successMessage}</p>
          </div>
        )}

        {errorMessage && (
          <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <p>{errorMessage}</p>
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={!file || isUploading}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-ayush-800 hover:bg-ayush-900 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Parsing & Generating Semantic Embeddings...</span>
            </>
          ) : (
            <>
              <UploadCloud className="w-4 h-4" />
              <span>Ingest & Index Document</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
