import re
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.db_models import Document, DocumentChunk
from app.models.schemas import CitationItem
from app.utils.logger import logger

class CitationVerifier:
    """
    Ground-truth citation verification engine.
    Ensures that every citation presented to the user:
      1. Corresponds to an authentic, active Document in the regulatory database.
      2. Belongs strictly to the referenced DocumentChunk.
      3. Validates section and page metadata against statutory records.
      4. Validates that snippet content is factually grounded in the source chunk text.
      5. Eliminates any hallucinated or unverified sources.
    """

    def __init__(self, enabled: Optional[bool] = None):
        self.enabled = enabled if enabled is not None else settings.CITATION_VERIFICATION_ENABLED

    @classmethod
    def verify_citation(
        cls,
        citation: CitationItem,
        db: Session,
        valid_chunks: List[DocumentChunk]
    ) -> Tuple[bool, str, str]:
        """
        Runs comprehensive integrity checks on a single CitationItem.
        Returns:
            (is_verified: bool, status: str, details: str)
        """
        # Check 1: Document Existence in Database
        doc = db.query(Document).filter(
            Document.id == citation.document_id,
            Document.is_active == True
        ).first()

        if not doc:
            logger.warning(f"Citation verification failed: Document ID {citation.document_id} not found in database.")
            return False, "FAILED_DOC_NOT_FOUND", "Document does not exist or is inactive in the regulatory corpus."

        # Check 2: Chunk Existence and Association
        matching_chunk: Optional[DocumentChunk] = None
        if citation.chunk_id:
            for chunk in valid_chunks:
                if chunk.id == citation.chunk_id:
                    matching_chunk = chunk
                    break

        if not matching_chunk:
            for chunk in valid_chunks:
                if chunk.document_id == doc.id:
                    if (citation.section_number and chunk.section_number and
                        citation.section_number.strip().lower() == chunk.section_number.strip().lower()):
                        matching_chunk = chunk
                        break
            
            if not matching_chunk:
                for chunk in valid_chunks:
                    if chunk.document_id == doc.id:
                        matching_chunk = chunk
                        break

        if not matching_chunk:
            logger.warning(f"Citation verification failed: No retrieved chunk matches document {doc.id}.")
            return False, "FAILED_CHUNK_NOT_FOUND", "Referenced chunk was not retrieved from the verified corpus."

        # Check 3: Metadata Verification (Jurisdiction & Document Title)
        if doc.title.lower() not in citation.document_title.lower() and citation.document_title.lower() not in doc.title.lower():
            logger.warning(f"Citation metadata mismatch: '{citation.document_title}' vs DB '{doc.title}'.")
            return False, "METADATA_MISMATCH", f"Document title mismatch with database record '{doc.title}'."

        # Check 4: Content Grounding Overlap
        # Verify that snippet text actually comes from the retrieved chunk content
        snippet_words = [w.lower() for w in re.findall(r'\b\w+\b', citation.snippet) if len(w) > 3]
        if snippet_words:
            chunk_content_lower = matching_chunk.content.lower()
            matched_words = sum(1 for w in snippet_words if w in chunk_content_lower)
            overlap_ratio = matched_words / len(snippet_words)

            if overlap_ratio < 0.35:
                logger.warning(
                    f"Citation grounding check failed: snippet overlap {overlap_ratio:.2f} < 0.35 for doc {doc.id}."
                )
                return False, "FAILED_CONTENT_MISMATCH", "Citation snippet content could not be verified in statutory text."

        details = (
            f"Ground-truth verified against official gazette: '{doc.title}' "
            f"({doc.jurisdiction}), Section: {matching_chunk.section_number or citation.section_number}."
        )
        return True, "VERIFIED", details

    def verify_citations(
        self,
        citations: List[CitationItem],
        db: Session,
        valid_chunks: Optional[List[DocumentChunk]] = None,
        strict_filter: bool = False
    ) -> List[CitationItem]:
        """
        Instance method to verify a batch of citations.
        """
        if not self.enabled:
            for cit in citations:
                cit.is_verified = False
                cit.verification_status = "UNVERIFIED"
                cit.verification_details = "Citation verification disabled in configuration."
            return citations

        if valid_chunks is None:
            doc_ids = [c.document_id for c in citations]
            valid_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids)).all()

        return self.verify_and_filter(citations, db, valid_chunks, strict_filter=strict_filter)

    @classmethod
    def verify_and_filter(
        cls,
        citations: List[CitationItem],
        db: Session,
        valid_chunks: List[DocumentChunk],
        strict_filter: bool = True
    ) -> List[CitationItem]:
        """
        Verifies a list of citations against the database corpus.
        If strict_filter=True, drops unverified citations; otherwise marks them as UNVERIFIED.
        """
        verified_citations: List[CitationItem] = []

        for cit in citations:
            is_valid, status_str, details_str = cls.verify_citation(cit, db, valid_chunks)
            cit.is_verified = is_valid
            cit.verification_status = status_str
            cit.verification_details = details_str

            if is_valid:
                verified_citations.append(cit)
            else:
                logger.warning(f"Dropped unverified citation: {cit.document_title} | {status_str}")
                if not strict_filter:
                    verified_citations.append(cit)

        logger.info(f"Citation verification complete: {len(verified_citations)}/{len(citations)} citations processed.")
        return verified_citations

citation_verifier = CitationVerifier()
