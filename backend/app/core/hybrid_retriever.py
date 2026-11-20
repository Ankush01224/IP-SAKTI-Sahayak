import re
import math
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db_models import Document, DocumentChunk
from app.core.embeddings import embeddings_manager
from app.utils.logger import logger

STOP_WORDS = {
    'what', 'is', 'the', 'and', 'of', 'in', 'to', 'for', 'a', 'an', 'be', 'by', 'under',
    'its', 'can', 'it', 'this', 'that', 'with', 'as', 'on', 'at', 'from', 'or', 'are', 'was',
    'were', 'will', 'how', 'does', 'do', 'did', 'having', 'who', 'which', 'where', 'when'
}

# Special statutory tokens that receive significant boost when matched verbatim
STATUTORY_BOOSTS: Dict[str, float] = {
    "section 3(p)": 4.5,
    "section 3p": 4.5,
    "section 3(d)": 4.0,
    "section 3(e)": 4.0,
    "rule 158-b": 4.5,
    "rule 158b": 4.5,
    "schedule t": 4.0,
    "chapter iv-a": 4.0,
    "chapter iva": 4.0,
    "tkdl": 3.5,
    "nba": 3.5,
    "abs": 3.0,
    "copp": 3.5,
    "who-gmp": 3.5,
    "cdsco": 3.5,
    "dcgi": 3.0,
    "ayush standard mark": 3.5,
    "ayush premium mark": 3.5,
    "charaka samhita": 3.0,
    "sushruta samhita": 3.0,
    "patent": 2.2,
    "trademark": 2.2,
    "copyright": 2.2,
    "ayush": 2.0,
    "ashwagandha": 2.5
}

class BM25Index:
    """
    Self-contained Okapi BM25 keyword search index built over active DocumentChunks.
    Supports phrase-level statutory term boosting.
    """

    def __init__(self, chunks: List[DocumentChunk], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks = chunks
        self.doc_count = len(chunks)
        self.doc_lengths: Dict[int, int] = {}
        self.doc_term_freqs: Dict[int, Dict[str, int]] = {}
        self.doc_full_texts: Dict[int, str] = {}
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.avg_doc_len = 0.0

        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        tokens = [
            t.lower() for t in re.findall(r'[a-zA-Z0-9\(\)\.\-]+', text)
            if len(t) > 1 and t.lower() not in STOP_WORDS
        ]
        return tokens

    def _build_index(self):
        if not self.chunks:
            return

        total_length = 0
        for chunk in self.chunks:
            # Combine title, section number, section title, and content for rich keyword matching
            full_text = f"{chunk.document.title if chunk.document else ''} {chunk.section_number} {chunk.section_title} {chunk.content}".lower()
            self.doc_full_texts[chunk.id] = full_text
            tokens = self._tokenize(full_text)
            self.doc_lengths[chunk.id] = len(tokens)
            total_length += len(tokens)

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freqs[chunk.id] = tf

            for t in tf.keys():
                self.df[t] = self.df.get(t, 0) + 1

        self.avg_doc_len = total_length / self.doc_count if self.doc_count > 0 else 0.0

        # Compute Robertson-Spärck Jones IDF
        for t, count in self.df.items():
            self.idf[t] = math.log(1.0 + (self.doc_count - count + 0.5) / (count + 0.5))

    def search(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """Scores all chunks against query using BM25 with statutory phrase boosting."""
        if not self.chunks:
            return []

        q_lower = query.lower()
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        chunk_map = {c.id: c for c in self.chunks}
        scores: Dict[int, float] = {}

        for chunk_id, tf in self.doc_term_freqs.items():
            doc_len = self.doc_lengths.get(chunk_id, 0)
            score = 0.0

            # 1. Standard BM25 term frequency summation
            for t in query_tokens:
                if t in tf:
                    freq = tf[t]
                    idf = self.idf.get(t, 0.1)
                    denom = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                    score += idf * (freq * (self.k1 + 1.0)) / denom

            # 2. Statutory Exact Phrase Boost
            full_text = self.doc_full_texts.get(chunk_id, "")
            for phrase, boost in STATUTORY_BOOSTS.items():
                if phrase in q_lower and phrase in full_text:
                    score += boost * 2.0

            if score > 0:
                scores[chunk_id] = score

        if not scores:
            return []

        # Normalize BM25 scores to [0.0, 1.0]
        max_score = max(scores.values())
        ranked = sorted(
            [(chunk_map[cid], round(score / max_score, 4)) for cid, score in scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        return ranked[:top_k]

class HybridRetriever:
    """
    Orchestrates Hybrid Retrieval:
    1. Vector Cosine Similarity
    2. BM25 Keyword Matching with statutory term boosting
    3. Metadata Filtering (Jurisdiction, Category, SubDomain)
    4. Reciprocal Rank Fusion (RRF) deduplication & combined scoring
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    @staticmethod
    def reciprocal_rank_fusion(
        vector_candidates: List[Tuple[DocumentChunk, float]],
        bm25_candidates: List[Tuple[DocumentChunk, float]],
        top_k: int = 10,
        k: int = 60
    ) -> List[Tuple[DocumentChunk, float]]:
        """Combines two ranked candidate lists using Reciprocal Rank Fusion."""
        rrf_scores: Dict[int, float] = {}
        chunk_map: Dict[int, DocumentChunk] = {}

        for rank, (chunk, _) in enumerate(vector_candidates, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))

        for rank, (chunk, _) in enumerate(bm25_candidates, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))

        if not rrf_scores:
            return []

        max_rrf = max(rrf_scores.values())
        ranked = sorted(
            [(chunk_map[cid], round(score / max_rrf, 4)) for cid, score in rrf_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        return ranked[:top_k]

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        sub_domain: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Executes hybrid retrieval combining vector search and BM25 using RRF.
        Returns a deduplicated, ranked list of (DocumentChunk, hybrid_score).
        """
        if not self.db:
            logger.error("Database session is required for retrieve().")
            return []

        # Fetch active chunks
        query_builder = (
            self.db.query(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.is_active == True)
        )

        # Optional Hard Metadata Filtering
        if jurisdiction and jurisdiction.lower() != "all":
            query_builder = query_builder.filter(Document.jurisdiction.ilike(f"%{jurisdiction}%"))
        if category and category.lower() != "all":
            query_builder = query_builder.filter(Document.category.ilike(f"%{category}%"))

        chunks = query_builder.all()
        if not chunks:
            logger.warning("No active document chunks found in database.")
            return []

        # 1. Semantic Vector Search
        query_vec = embeddings_manager.get_query_embedding(query)
        vector_scored: List[Tuple[DocumentChunk, float]] = []
        for c in chunks:
            chunk_vec = c.embedding
            if chunk_vec:
                sim = embeddings_manager.cosine_similarity(query_vec, chunk_vec)
                if sim > 0:
                    vector_scored.append((c, sim))

        vector_scored.sort(key=lambda x: x[1], reverse=True)

        # 2. BM25 Keyword Search
        bm25_index = BM25Index(chunks, k1=settings.BM25_K1, b=settings.BM25_B)
        bm25_scored = bm25_index.search(query, top_k=len(chunks))

        # 3. Reciprocal Rank Fusion (RRF) Combination
        rrf_scores: Dict[int, float] = {}
        chunk_map: Dict[int, DocumentChunk] = {c.id: c for c in chunks}
        k = settings.RRF_K

        # Vector RRF contribution
        for rank, (chunk, _) in enumerate(vector_scored, start=1):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))

        # BM25 RRF contribution
        for rank, (chunk, _) in enumerate(bm25_scored, start=1):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))

        # 4. Soft Metadata Category Boost
        if sub_domain:
            for cid in rrf_scores.keys():
                c = chunk_map[cid]
                cat = (c.document.category if c.document else "").lower()
                title = (c.document.title if c.document else "").lower()
                sd = sub_domain.lower()

                if "patent" in sd and ("patent" in cat or "patent" in title):
                    rrf_scores[cid] *= 1.25
                elif "traditional" in sd and ("tkdl" in cat or "traditional" in cat or "biodiversity" in cat):
                    rrf_scores[cid] *= 1.25
                elif "ayush" in sd and ("ayush" in cat or "cosmetics" in cat):
                    rrf_scores[cid] *= 1.25
                elif "export" in sd and ("export" in cat or "fda" in cat or "who" in cat):
                    rrf_scores[cid] *= 1.25

        if not rrf_scores:
            return []

        # Normalize RRF scores to [0.0, 1.0]
        max_rrf = max(rrf_scores.values())
        ranked_candidates = sorted(
            [(chunk_map[cid], round(score / max_rrf, 4)) for cid, score in rrf_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        logger.info(
            f"Hybrid retrieval produced {len(ranked_candidates)} unique candidates "
            f"(Vector pool: {len(vector_scored)}, BM25 pool: {len(bm25_scored)})."
        )
        return ranked_candidates[:top_k]
