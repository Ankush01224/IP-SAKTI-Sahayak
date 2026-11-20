from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language query about Ayurveda IP or regulatory rules")
    language: str = Field("en", description="ISO language code, e.g. en, hi, sa, ta, te, mr, bn, gu")
    session_id: Optional[str] = Field(None, description="Optional session tracking ID")
    max_citations: int = Field(4, ge=1, le=10, description="Max citation chunks to retrieve")

class QueryClassificationResult(BaseModel):
    domain: str = Field(..., description="IP_DOMAIN, REGULATORY_DOMAIN, or GENERAL")
    sub_domain: str = Field(..., description="Specific sub-domain (e.g. Patent, AYUSH, Export, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the classification")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords triggering classification")
    reasoning: Optional[str] = Field(None, description="Classification rationale")

class CitationItem(BaseModel):
    document_id: int
    chunk_id: Optional[int] = None
    document_title: str
    section_number: str
    section_title: str
    jurisdiction: str
    snippet: str
    page_number: Optional[int] = None
    similarity_score: float
    is_verified: bool = Field(True, description="Whether citation was verified against database corpus")
    verification_status: str = Field("VERIFIED", description="VERIFIED, UNVERIFIED_SOURCE, or METADATA_MISMATCH")
    verification_details: Optional[str] = Field("Statutory record and section verified in database corpus.", description="Details of ground-truth check")

class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationItem] = []
    confidence_score: float
    confidence_status: str  # "HIGH_CONFIDENCE", "PARTIAL_EVIDENCE", "INSUFFICIENT_EVIDENCE", "GENERAL_QUERY"
    language: str
    latency_ms: float
    timestamp: str
    query_classification: Optional[QueryClassificationResult] = None
    retrieval_strategy: Optional[str] = Field(None, description="Retrieval strategy: hybrid_vector_bm25_rrf, direct_vector, general_bypass")

class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    jurisdiction: str
    category: str
    file_size: int
    version: str
    uploaded_at: Optional[str]
    updated_at: Optional[str]
    chunk_count: int
    is_active: bool

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total_count: int

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse
    chunks_created: int

class HealthResponse(BaseModel):
    status: str
    project_name: str
    version: str
    database_connected: bool
    total_documents: int
    total_chunks: int
    embedding_provider: str
    llm_provider: str
