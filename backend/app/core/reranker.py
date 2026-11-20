import re
from typing import List, Tuple, Optional
from app.config import settings
from app.models.db_models import DocumentChunk
from app.utils.logger import logger

class Reranker:
    """
    Cross-interaction relevance reranker.
    Re-scores candidate chunks retrieved by hybrid search against the user's exact query.
    Evaluates:
      - Exact statutory clause and section matches
      - Query term proximity and n-gram overlap
      - Title & section alignment
    Provides a safe, seamless fallback to hybrid retrieval rankings if unavailable.
    """

    def __init__(self, enabled: Optional[bool] = None, top_k: Optional[int] = None):
        self.enabled = enabled if enabled is not None else settings.RERANKER_ENABLED
        self.top_k = top_k if top_k is not None else settings.RERANKER_TOP_K

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[DocumentChunk, float]],
        top_k: Optional[int] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Reranks retrieved candidate chunks.
        Args:
            query: User's natural language query
            candidates: List of (DocumentChunk, initial_score) from HybridRetriever
            top_k: Number of top chunks to return (defaults to settings.RERANKER_TOP_K)
        Returns:
            Reranked list of (DocumentChunk, rerank_score) sorted descending
        """
        limit = top_k or self.top_k
        if not candidates:
            return []

        if not self.enabled:
            logger.info("Reranker is disabled in config. Returning hybrid candidates directly.")
            return candidates[:limit]

        try:
            reranked = []
            q_clean = query.lower()
            q_tokens = [w for w in re.findall(r'\b\w+\b', q_clean) if len(w) > 2]
            q_bigrams = [f"{q_tokens[i]} {q_tokens[i+1]}" for i in range(len(q_tokens) - 1)]

            for chunk, initial_score in candidates:
                doc = chunk.document
                doc_title = (doc.title if doc else "").lower()
                sec_num = (chunk.section_number or "").lower()
                sec_title = (chunk.section_title or "").lower()
                content = chunk.content.lower()

                # Base score from hybrid retrieval (40% weight)
                cross_score = initial_score * 0.40

                # 1. Exact Section / Clause match bonus
                if sec_num and sec_num != "general" and sec_num in q_clean:
                    cross_score += 0.35
                if sec_title and any(t in sec_title for t in q_tokens if len(t) > 3):
                    cross_score += 0.15

                # 2. Bigram phrase containment bonus
                matched_bigrams = sum(1 for bg in q_bigrams if bg in content)
                if q_bigrams:
                    cross_score += 0.20 * (matched_bigrams / len(q_bigrams))

                # 3. Document Title relevance
                title_matches = sum(1 for t in q_tokens if t in doc_title)
                if q_tokens:
                    cross_score += 0.10 * (title_matches / len(q_tokens))

                # 4. Proximity / Density bonus
                matched_tokens = [t for t in q_tokens if t in content]
                if matched_tokens:
                    coverage = len(matched_tokens) / len(q_tokens)
                    cross_score += 0.15 * coverage

                # Normalize score to [0.0, 1.0]
                final_score = min(0.99, max(0.1, round(cross_score, 3)))
                reranked.append((chunk, final_score))

            # Sort descending by rerank score
            reranked.sort(key=lambda x: x[1], reverse=True)
            logger.info(f"Reranked {len(candidates)} candidate chunks down to top {limit}.")
            return reranked[:limit]

        except Exception as e:
            logger.warning(f"Error during reranking: {e}. Safely falling back to hybrid retrieval order.")
            return candidates[:limit]

reranker = Reranker()
