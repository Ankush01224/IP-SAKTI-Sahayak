import React, { useState, useEffect } from 'react';
import { Database, FileText, Trash2, RefreshCw, Layers, ShieldCheck, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api, DocumentItem, HealthResponse } from '../api/client';
import { DocumentUpload } from '../components/DocumentUpload';

export const Admin: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [docsRes, healthRes] = await Promise.all([
        api.getDocuments(),
        api.getHealth()
      ]);
      setDocuments(docsRes.documents);
      setHealth(healthRes);
    } catch (err: any) {
      console.error('Failed to fetch admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDelete = async (id: number, title: string) => {
    if (!window.confirm(`Are you sure you want to remove "${title}" from the active regulatory corpus?`)) {
      return;
    }

    try {
      await api.deleteDocument(id);
      setNotification({ type: 'success', message: `Document "${title}" removed from corpus.` });
      fetchData();
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to delete document' });
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await api.seedCorpus();
      setNotification({ type: 'success', message: res.message || 'Seed regulatory corpus reloaded.' });
      fetchData();
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to seed corpus' });
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-900 flex items-center gap-2.5">
            <Database className="w-6 h-6 text-ayush-800" />
            Corpus Management & Regulatory Indexing
          </h1>
          <p className="text-xs md:text-sm text-slate-600 mt-1">
            Ministry of Ayush Regulatory Library — Manage statutory gazettes, Acts, and international herbal guidance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-semibold transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${seeding ? 'animate-spin' : ''}`} />
            <span>Reload Seed Corpus</span>
          </button>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div className={`mt-4 p-3 rounded-xl text-xs flex items-center justify-between gap-2 ${
          notification.type === 'success' ? 'bg-emerald-50 text-emerald-900 border border-emerald-200' : 'bg-rose-50 text-rose-900 border border-rose-200'
        }`}>
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertTriangle className="w-4 h-4 text-rose-600" />}
            <span>{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-xs font-bold px-1.5 py-0.5 hover:opacity-75">
            ×
          </button>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Corpus Documents
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-slate-900">
              {health?.total_documents ?? documents.length}
            </span>
            <span className="text-xs text-slate-500">gazettes</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Semantic Chunks
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-ayush-800">
              {health?.total_chunks ?? documents.reduce((acc, d) => acc + d.chunk_count, 0)}
            </span>
            <span className="text-xs text-slate-500">indexed</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Embedding Engine
          </span>
          <div className="flex items-center gap-1.5 mt-1">
            <Layers className="w-4 h-4 text-ayush-700 shrink-0" />
            <span className="text-xs font-semibold text-slate-800 truncate" title={health?.embedding_provider}>
              {health?.embedding_provider ? health.embedding_provider.split('(')[0].trim() : 'Active'}
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Database Status
          </span>
          <div className="flex items-center gap-1.5 mt-1">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="text-xs font-semibold text-emerald-800">
              {health?.database_connected ? 'Connected & Verified' : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="mt-8">
        <DocumentUpload onUploadSuccess={fetchData} />
      </div>

      {/* Document Library Table */}
      <div className="mt-8 bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-ayush-700" />
            Active Regulatory Library ({documents.length} Files)
          </h2>
          <span className="text-xs text-slate-500">
            Visible in citation searches
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">
            Loading corpus catalog...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No documents in corpus. Click "Reload Seed Corpus" above to load default statutes.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-3">Jurisdiction</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Chunks</th>
                  <th className="py-3 px-3">Last Updated</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900 max-w-xs truncate">
                      {doc.title}
                    </td>
                    <td className="py-3 px-3">
                      <span className="bg-slate-100 text-slate-800 text-[10px] font-medium px-2 py-0.5 rounded">
                        {doc.jurisdiction}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-500">
                      {doc.category}
                    </td>
                    <td className="py-3 px-3 font-semibold text-ayush-800">
                      {doc.chunk_count}
                    </td>
                    <td className="py-3 px-3 text-slate-400">
                      {doc.updated_at ? new Date(doc.updated_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.title)}
                        className="text-slate-400 hover:text-rose-600 p-1 rounded hover:bg-rose-50 transition-colors"
                        title="Delete from corpus"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
