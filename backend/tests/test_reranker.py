import pytest
from app.core.reranker import Reranker
from app.models.db_models import DocumentChunk

class TestReranker:
    def test_reranking_clause_priority(self):
        reranker = Reranker(enabled=True)

        generic_chunk = DocumentChunk(
            id=10,
            document_id=1,
            chunk_index=0,
            content="General intellectual property considerations across pharmaceuticals and medicines in India.",
            section_title="General Overview",
            token_count=15
        )

        specific_chunk = DocumentChunk(
            id=20,
            document_id=2,
            chunk_index=1,
            content="Section 3(p) of the Patents Act, 1970 explicitly excludes traditional knowledge from patentability.",
            section_title="Section 3(p) Exclusion",
            token_count=18
        )

        # Feed generic first, specific second
        candidates = [(generic_chunk, 0.90), (specific_chunk, 0.70)]
        query = "Can traditional knowledge be patented under Section 3(p)?"

        reranked = reranker.rerank(query, candidates, top_k=2)

        assert len(reranked) == 2
        # The specific chunk matching section 3(p) clause and title should jump to rank 1
        assert reranked[0][0].id == 20
        assert reranked[0][1] > reranked[1][1]

    def test_reranker_fallback_disabled(self):
        reranker = Reranker(enabled=False)
        chunk = DocumentChunk(
            id=1,
            document_id=1,
            chunk_index=0,
            content="Sample text",
            section_title="Title",
            token_count=5
        )
        candidates = [(chunk, 0.85)]
        reranked = reranker.rerank("query", candidates)
        assert reranked == candidates

    def test_reranker_empty_candidates(self):
        reranker = Reranker(enabled=True)
        assert reranker.rerank("query", []) == []
