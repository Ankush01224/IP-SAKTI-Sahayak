export interface QueryClassificationResult {
  domain: 'IP_DOMAIN' | 'REGULATORY_DOMAIN' | 'GENERAL';
  sub_domain: string;
  confidence: number;
  matched_keywords: string[];
  reasoning?: string;
}

export interface CitationItem {
  document_id: number;
  chunk_id?: number;
  document_title: string;
  section_number: string;
  section_title: string;
  jurisdiction: string;
  snippet: string;
  page_number?: number;
  similarity_score: number;
  is_verified?: boolean;
  verification_status?: string;
  verification_details?: string;
}

export interface ChatResponse {
  answer: string;
  citations: CitationItem[];
  confidence_score: number;
  confidence_status: 'HIGH_CONFIDENCE' | 'PARTIAL_EVIDENCE' | 'INSUFFICIENT_EVIDENCE' | 'GENERAL_QUERY';
  language: string;
  latency_ms: number;
  timestamp: string;
  query_classification?: QueryClassificationResult;
  retrieval_strategy?: string;
}

export interface DocumentItem {
  id: number;
  title: string;
  filename: string;
  jurisdiction: string;
  category: string;
  file_size: number;
  version: string;
  uploaded_at?: string;
  updated_at?: string;
  chunk_count: number;
  is_active: boolean;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
  total_count: number;
}

export interface HealthResponse {
  status: string;
  project_name: string;
  version: string;
  database_connected: boolean;
  total_documents: number;
  total_chunks: number;
  embedding_provider: string;
  llm_provider: string;
}

const API_BASE = '/api/v1';

export const api = {
  async sendChat(query: string, language: string = 'en', sessionId?: string): Promise<ChatResponse> {
    let res: Response;
    try {
      res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          language,
          session_id: sessionId,
          max_citations: 4
        }),
      });
    } catch {
      throw new Error('Cannot reach the server. Make sure the backend is running on port 8000.');
    }

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      const detail = err?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        throw new Error(detail);
      }
      if (res.status >= 500) {
        throw new Error('The server is unavailable or encountered an error. Check that the backend is running on port 8000.');
      }
      throw new Error(`Request failed (${res.status}).`);
    }

    return res.json();
  },

  async getDocuments(): Promise<DocumentListResponse> {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) {
      throw new Error('Failed to fetch documents');
    }
    return res.json();
  },

  async uploadDocument(file: File, title: string, jurisdiction: string, category: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (jurisdiction) formData.append('jurisdiction', jurisdiction);
    if (category) formData.append('category', category);

    const res = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }

    return res.json();
  },

  async deleteDocument(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      throw new Error('Failed to delete document');
    }
    return res.json();
  },

  async seedCorpus(): Promise<any> {
    const res = await fetch(`${API_BASE}/documents/seed`, {
      method: 'POST',
    });
    if (!res.ok) {
      throw new Error('Failed to seed corpus');
    }
    return res.json();
  },

  async getHealth(): Promise<HealthResponse> {
    const res = await fetch('/health');
    if (!res.ok) {
      throw new Error('Health check failed');
    }
    return res.json();
  }
};
