import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import Document, DocumentChunk
from app.ingestion.loaders import DocumentLoader
from app.ingestion.chunking import RegulatoryChunker
from app.core.embeddings import embeddings_manager
from app.utils.logger import logger

class IngestPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.chunker = RegulatoryChunker()

    def ingest_file(
        self,
        file_path: Path,
        title: Optional[str] = None,
        jurisdiction: str = "India",
        category: str = "Ayurveda Regulatory",
        version: str = "1.0"
    ) -> Dict[str, Any]:
        """Ingests a single document from filesystem into the database."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Compute file hash
        file_hash = self._compute_sha256(file_path)
        file_size = file_path.stat().st_size
        doc_title = title or file_path.stem.replace("_", " ").title()

        # Check for existing document with this hash
        existing_doc = self.db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing_doc:
            logger.info(f"Document '{doc_title}' already exists with hash {file_hash[:8]}. Returning existing record.")
            return {
                "status": "already_exists",
                "document": existing_doc,
                "chunks_created": len(existing_doc.chunks)
            }

        # Load file
        doc_data = DocumentLoader.load_file(file_path)

        # Create Document record
        doc = Document(
            title=doc_title,
            filename=file_path.name,
            jurisdiction=jurisdiction,
            category=category,
            file_hash=file_hash,
            file_size=file_size,
            file_path=str(file_path),
            version=version
        )
        self.db.add(doc)
        self.db.flush()  # to obtain doc.id

        # Chunk document
        chunks_data = self.chunker.chunk_document(doc_data)

        # Embed and save chunks
        created_chunks = []
        for c in chunks_data:
            embedding = embeddings_manager.get_embedding(c["content"])
            chunk_obj = DocumentChunk(
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                section_number=c["section_number"],
                section_title=c["section_title"],
                content=c["content"],
                token_count=c["token_count"],
                page_number=c.get("page_number", 1)
            )
            chunk_obj.embedding = embedding
            self.db.add(chunk_obj)
            created_chunks.append(chunk_obj)

        self.db.commit()
        self.db.refresh(doc)
        logger.info(f"Successfully ingested '{doc.title}' (ID: {doc.id}) with {len(created_chunks)} chunks.")

        return {
            "status": "created",
            "document": doc,
            "chunks_created": len(created_chunks)
        }

    def ingest_directory(self, dir_path: Path) -> List[Dict[str, Any]]:
        """Scans a directory for .pdf, .md, .txt files and ingests them all."""
        results = []
        if not dir_path.exists():
            logger.warning(f"Corpus directory {dir_path} does not exist.")
            return results

        valid_extensions = {".pdf", ".md", ".txt", ".markdown"}
        for file in sorted(dir_path.iterdir()):
            if file.is_file() and file.suffix.lower() in valid_extensions:
                try:
                    # Detect jurisdiction and category from filename heuristics
                    fname = file.name.lower()
                    jurisdiction = "India"
                    category = "Ayurveda IP & Regulatory"
                    if "fda" in fname or "us" in fname:
                        jurisdiction = "United States"
                        category = "FDA Botanical Regulations"
                    elif "who" in fname or "international" in fname or "wipo" in fname:
                        jurisdiction = "International (WHO / WIPO)"
                        category = "Global Traditional Medicine"
                    elif "tkdl" in fname:
                        category = "Traditional Knowledge & Biopiracy"
                    elif "patent" in fname:
                        category = "Patent Law & Section 3(p)"
                    elif "biodiversity" in fname or "nba" in fname:
                        category = "Biological Diversity & ABS"
                    elif "cosmetics" in fname or "drug" in fname:
                        category = "Drugs & Cosmetics Act"

                    res = self.ingest_file(
                        file_path=file,
                        jurisdiction=jurisdiction,
                        category=category
                    )
                    results.append(res)
                except Exception as e:
                    logger.error(f"Failed to ingest file {file.name}: {e}")

        return results

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
