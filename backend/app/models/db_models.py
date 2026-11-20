from datetime import datetime, timezone
from typing import List, Optional
import json
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, Index
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    jurisdiction = Column(String(100), default="India", index=True)
    category = Column(String(100), default="Ayurveda Regulatory", index=True)
    file_hash = Column(String(64), unique=True, index=True, nullable=False)
    file_size = Column(Integer, default=0)
    file_path = Column(String(500), nullable=True)
    version = Column(String(50), default="1.0")
    uploaded_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "jurisdiction": self.jurisdiction,
            "category": self.category,
            "file_size": self.file_size,
            "version": self.version,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "chunk_count": len(self.chunks) if self.chunks else 0,
            "is_active": self.is_active
        }

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    section_number = Column(String(100), default="General", index=True)
    section_title = Column(String(255), default="General Provisions")
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    embedding_json = Column(Text, nullable=True)  # Store JSON-serialized float list for cross-DB compatibility
    page_number = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)

    document = relationship("Document", back_populates="chunks")

    @property
    def embedding(self) -> List[float]:
        if self.embedding_json:
            try:
                return json.loads(self.embedding_json)
            except Exception:
                return []
        return []

    @embedding.setter
    def embedding(self, vec: List[float]):
        self.embedding_json = json.dumps(vec) if vec is not None else None

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "document_title": self.document.title if self.document else None,
            "jurisdiction": self.document.jurisdiction if self.document else None,
            "chunk_index": self.chunk_index,
            "section_number": self.section_number,
            "section_title": self.section_title,
            "content": self.content,
            "page_number": self.page_number
        }

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    language = Column(String(20), default="en")
    confidence_score = Column(Float, default=0.0)
    confidence_status = Column(String(50), default="INSUFFICIENT_EVIDENCE")
    citations_json = Column(Text, nullable=True)
    retrieved_chunks_count = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "query": self.query,
            "response": self.response,
            "language": self.language,
            "confidence_score": self.confidence_score,
            "confidence_status": self.confidence_status,
            "citations": json.loads(self.citations_json) if self.citations_json else [],
            "retrieved_chunks_count": self.retrieved_chunks_count,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
