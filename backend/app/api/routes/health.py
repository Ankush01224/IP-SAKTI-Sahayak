from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.models.schemas import HealthResponse
from app.models.db_models import Document, DocumentChunk
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """System uptime, database status, and corpus metric check."""
    db_connected = False
    doc_count = 0
    chunk_count = 0
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        doc_count = db.query(Document).filter(Document.is_active == True).count()
        chunk_count = db.query(DocumentChunk).count()
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        project_name=settings.PROJECT_NAME,
        version="1.0.0",
        database_connected=db_connected,
        total_documents=doc_count,
        total_chunks=chunk_count,
        embedding_provider="Google Gemini (text-embedding-004)" if settings.GEMINI_API_KEY else "Local Semantic Vectorizer",
        llm_provider="Google Gemini (1.5 Flash)" if settings.GEMINI_API_KEY else "Offline Statutory Synthesizer"
    )
