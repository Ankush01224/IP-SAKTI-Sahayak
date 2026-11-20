import pytest
from app.core.citation_verifier import CitationVerifier
from app.models.schemas import CitationItem
from app.models.db_models import Document, DocumentChunk

class TestCitationVerifier:
    def test_verified_citation(self, test_db):
        # Insert test doc and chunk
        doc = Document(
            title="Patents Act 1970",
            filename="patents_act_1970.pdf",
            file_hash="hash_patents_1970",
            jurisdiction="India",
            category="Patent Law"
        )
        test_db.add(doc)
        test_db.flush()

        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            section_number="Section 3(p)",
            section_title="Section 3(p)",
            content="Section 3(p) provides that an invention which in effect is traditional knowledge is not an invention.",
            token_count=18
        )
        test_db.add(chunk)
        test_db.commit()

        verifier = CitationVerifier(enabled=True)
        citations = [
            CitationItem(
                document_id=doc.id,
                chunk_id=chunk.id,
                document_title=doc.title,
                section_number=chunk.section_number,
                section_title=chunk.section_title,
                jurisdiction="India",
                snippet="traditional knowledge is not an invention",
                similarity_score=0.92
            )
        ]

        verified = verifier.verify_citations(citations, test_db, strict_filter=False)
        assert len(verified) == 1
        assert verified[0].is_verified is True
        assert verified[0].verification_status == "VERIFIED"
        assert "Ground-truth verified" in (verified[0].verification_details or "")

    def test_fake_document_rejection(self, test_db):
        verifier = CitationVerifier(enabled=True)
        citations = [
            CitationItem(
                document_id=99999,
                chunk_id=1,
                document_title="Fake Document Act",
                section_number="Section 99",
                section_title="Section 99",
                jurisdiction="India",
                snippet="Completely fabricated citation text",
                similarity_score=0.95
            )
        ]

        verified = verifier.verify_citations(citations, test_db, strict_filter=False)
        assert len(verified) == 1
        assert verified[0].is_verified is False
        assert verified[0].verification_status == "FAILED_DOC_NOT_FOUND"

    def test_tampered_content_rejection(self, test_db):
        doc = Document(
            title="Biological Diversity Act 2002",
            filename="bio_diversity_2002.pdf",
            file_hash="hash_bio_2002",
            jurisdiction="India",
            category="Biodiversity"
        )
        test_db.add(doc)
        test_db.flush()

        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            section_number="Section 6",
            section_title="Section 6",
            content="Section 6 requires prior approval of the National Biodiversity Authority before applying for IP.",
            token_count=15
        )
        test_db.add(chunk)
        test_db.commit()

        verifier = CitationVerifier(enabled=True)
        citations = [
            CitationItem(
                document_id=doc.id,
                chunk_id=chunk.id,
                document_title=doc.title,
                section_number=chunk.section_number,
                section_title=chunk.section_title,
                jurisdiction="India",
                snippet="Quantum computing algorithms applied to aerospace telemetry transmissions",
                similarity_score=0.88
            )
        ]

        verified = verifier.verify_citations(citations, test_db, strict_filter=False)
        assert len(verified) == 1
        assert verified[0].is_verified is False
        assert verified[0].verification_status == "FAILED_CONTENT_MISMATCH"

    def test_verifier_disabled(self, test_db):
        verifier = CitationVerifier(enabled=False)
        citations = [
            CitationItem(
                document_id=1,
                chunk_id=1,
                document_title="Any",
                section_number="1",
                section_title="Any",
                jurisdiction="India",
                snippet="Any",
                similarity_score=0.5
            )
        ]
        result = verifier.verify_citations(citations, test_db, strict_filter=False)
        assert result[0].verification_status == "UNVERIFIED"
