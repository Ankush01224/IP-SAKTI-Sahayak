import pytest
from app.core.hybrid_retriever import BM25Index, HybridRetriever
from app.models.db_models import DocumentChunk

class TestBM25Index:
    def test_bm25_exact_and_boost(self):
        chunks = [
            DocumentChunk(
                id=1,
                document_id=1,
                chunk_index=0,
                content="Under Section 3(p) of the Patents Act 1970, traditional knowledge is non-patentable subject matter.",
                section_title="Section 3(p)",
                token_count=20
            ),
            DocumentChunk(
                id=2,
                document_id=2,
                chunk_index=0,
                content="Rule 158-B prescribes regulatory requirements for Ayurvedic, Siddha, and Unani drugs under Drugs and Cosmetics Rules.",
                section_title="Rule 158-B",
                token_count=20
            ),
            DocumentChunk(
                id=3,
                document_id=3,
                chunk_index=0,
                content="Quality certification for Ayush Premium Mark involves heavy metal testing and microbial limits.",
                section_title="Quality Standards",
                token_count=20
            )
        ]

        index = BM25Index(chunks)
        results = index.search("Section 3(p) patentability of traditional knowledge", top_k=2)

        assert len(results) > 0
        top_chunk, score = results[0]
        assert top_chunk.id == 1
        assert score > 0

    def test_bm25_empty_query_and_empty_corpus(self):
        index = BM25Index([])
        assert index.search("anything") == []

        chunks = [
            DocumentChunk(
                id=1,
                document_id=1,
                chunk_index=0,
                content="Some test content",
                section_title="Intro",
                token_count=5
            )
        ]
        index2 = BM25Index(chunks)
        assert index2.search("") == []

class TestHybridRetrieverRRF:
    def test_reciprocal_rank_fusion_deduplication(self):
        chunk_a = DocumentChunk(id=1, document_id=1, chunk_index=0, content="A", section_title="A", token_count=1)
        chunk_b = DocumentChunk(id=2, document_id=1, chunk_index=1, content="B", section_title="B", token_count=1)
        chunk_c = DocumentChunk(id=3, document_id=2, chunk_index=0, content="C", section_title="C", token_count=1)

        # Vector rankings: A (1), B (2)
        vector_results = [(chunk_a, 0.95), (chunk_b, 0.85)]
        # BM25 rankings: B (1), C (2)
        bm25_results = [(chunk_b, 4.2), (chunk_c, 3.1)]

        retriever = HybridRetriever()
        fused = retriever.reciprocal_rank_fusion(vector_results, bm25_results, top_k=3, k=60)

        assert len(fused) == 3
        # chunk_b appears in both rank 2 and rank 1, so it should have the highest combined RRF score:
        # score(chunk_b) = 1/(60+2) + 1/(60+1) = 0.016129 + 0.016393 = ~0.0325
        # score(chunk_a) = 1/(60+1) = ~0.01639
        # score(chunk_c) = 1/(60+2) = ~0.01612
        assert fused[0][0].id == chunk_b.id
        assert fused[0][1] > fused[1][1]
