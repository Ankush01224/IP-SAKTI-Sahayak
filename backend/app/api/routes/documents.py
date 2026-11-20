import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import settings
from app.models.db_models import Document
from app.models.schemas import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.ingestion.ingest_pipeline import IngestPipeline
from app.utils.logger import logger

router = APIRouter(prefix="/documents", tags=["Regulatory Documents"])

@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)):
    """Returns all registered regulatory corpus documents with chunk metrics."""
    docs = db.query(Document).filter(Document.is_active == True).order_by(Document.uploaded_at.desc()).all()
    results = [
        DocumentResponse(
            id=d.id,
            title=d.title,
            filename=d.filename,
            jurisdiction=d.jurisdiction,
            category=d.category,
            file_size=d.file_size,
            version=d.version,
            uploaded_at=d.uploaded_at.isoformat() if d.uploaded_at else None,
            updated_at=d.updated_at.isoformat() if d.updated_at else None,
            chunk_count=len(d.chunks),
            is_active=d.is_active
        )
        for d in docs
    ]
    return DocumentListResponse(documents=results, total_count=len(results))

@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    jurisdiction: str = Form("India"),
    category: str = Form("Ayurveda Regulatory"),
    version: str = Form("1.0"),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a new regulatory document (PDF/MD/TXT) into searchable grounded chunks.
    """
    # Validate extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".pdf", ".md", ".txt", ".markdown"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file_ext}'. Please upload PDF, Markdown (.md), or plain text (.txt)."
        )

    # Save to storage directory
    dest_path = settings.STORAGE_DIR / file.filename
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file to server storage.")

    pipeline = IngestPipeline(db)
    try:
        result = pipeline.ingest_file(
            file_path=dest_path,
            title=title or file.filename.rsplit(".", 1)[0].replace("_", " ").title(),
            jurisdiction=jurisdiction,
            category=category,
            version=version
        )
        doc = result["document"]
        doc_resp = DocumentResponse(
            id=doc.id,
            title=doc.title,
            filename=doc.filename,
            jurisdiction=doc.jurisdiction,
            category=doc.category,
            file_size=doc.file_size,
            version=doc.version,
            uploaded_at=doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
            chunk_count=result["chunks_created"],
            is_active=doc.is_active
        )
        return DocumentUploadResponse(
            message=f"Document '{doc.title}' processed into {result['chunks_created']} regulatory chunks.",
            document=doc_resp,
            chunks_created=result["chunks_created"]
        )
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Deactivates and removes a document and its vector chunks from the corpus."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc_title = doc.title
    db.delete(doc)
    db.commit()
    logger.info(f"Deleted document ID {document_id} ('{doc_title}') and all associated chunks.")
    return {"message": f"Document '{doc_title}' removed successfully."}

@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_corpus_endpoint(db: Session = Depends(get_db)):
    """Triggers batch ingestion of all documents in the seed corpus folder."""
    pipeline = IngestPipeline(db)
    results = pipeline.ingest_directory(settings.SEED_CORPUS_DIR)
    total_chunks = sum(r.get("chunks_created", 0) for r in results)
    return {
        "message": f"Ingested {len(results)} seed regulatory documents ({total_chunks} total chunks).",
        "details": [{"title": r["document"].title, "chunks": r["chunks_created"]} for r in results if "document" in r]
    }
