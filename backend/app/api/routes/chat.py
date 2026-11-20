from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.models.db_models import ChatLog
from app.core.rag_pipeline import RAGPipeline
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Ayurveda Q&A"])

@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main RAG Q&A endpoint:
    - Answers strictly grounded in curated Ayush & IP documents.
    - Cites source document name, section, and jurisdiction.
    - Below confidence threshold, triggers explicit 'insufficient evidence' response.
    """
    try:
        pipeline = RAGPipeline(db)
        response = pipeline.answer_query(
            query=request.query,
            language=request.language,
            session_id=request.session_id,
            max_citations=request.max_citations
        )
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while evaluating your regulatory query: {str(e)}"
        )

@router.get("/history")
def get_chat_history(limit: int = 20, db: Session = Depends(get_db)):
    """Retrieves recent queries and responses for audit trail and compliance verification."""
    logs = db.query(ChatLog).order_by(ChatLog.created_at.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]
