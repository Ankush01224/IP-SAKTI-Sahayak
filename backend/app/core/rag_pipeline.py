import time
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db_models import Document, DocumentChunk, ChatLog
from app.models.schemas import ChatResponse, CitationItem, QueryClassificationResult
from app.core.query_classifier import query_classifier, DomainCategory
from app.core.hybrid_retriever import HybridRetriever
from app.core.reranker import reranker
from app.core.citation_verifier import citation_verifier
from app.core.embeddings import embeddings_manager
from app.core.confidence import ConfidenceEvaluator
from app.core.citation import CitationFormatter
from app.core.llm_client import llm_client
from app.core.translation import multilingual_service
from app.utils.logger import logger

class RAGPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.hybrid_retriever = HybridRetriever(db)

    def answer_query(
        self,
        query: str,
        language: str = "en",
        session_id: Optional[str] = None,
        max_citations: int = 4
    ) -> ChatResponse:
        start_time = time.time()
        logger.info(f"Processing query: '{query}' [Language: {language}]")

        # -------------------------------------------------------------
        # 1. Query Classification Layer
        # -------------------------------------------------------------
        classification = query_classifier.classify(query)
        logger.info(f"Query Classification: {classification.domain} -> {classification.sub_domain} (conf: {classification.confidence})")

        # -------------------------------------------------------------
        # 2. General Query Short-Circuit (Bypass RAG if out-of-domain)
        # -------------------------------------------------------------
        if classification.domain == DomainCategory.GENERAL.value:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            clarification_text = query_classifier.get_general_clarification_response(query, language)

            self._log_interaction(
                session_id=session_id,
                query=query,
                response=clarification_text,
                language=language,
                confidence_score=0.0,
                confidence_status="GENERAL_QUERY",
                citations=[],
                chunks_count=0,
                latency_ms=latency_ms,
                classification=classification
            )

            return ChatResponse(
                answer=clarification_text,
                citations=[],
                confidence_score=0.0,
                confidence_status="GENERAL_QUERY",
                language=language,
                latency_ms=latency_ms,
                timestamp=datetime.now(timezone.utc).isoformat(),
                query_classification=classification,
                retrieval_strategy="general_bypass"
            )

        # -------------------------------------------------------------
        # 3. Multilingual Query Normalization (Indic -> English search)
        # -------------------------------------------------------------
        search_query = multilingual_service.prepare_query(query, language)

        # -------------------------------------------------------------
        # 4. Hybrid Retrieval (Vector + BM25 + Metadata Filtering via RRF)
        # -------------------------------------------------------------
        candidate_limit = max(settings.RERANKER_CANDIDATES, max_citations * 2)
        candidates = self.hybrid_retriever.retrieve(
            query=search_query,
            top_k=candidate_limit,
            sub_domain=classification.sub_domain
        )

        if not candidates:
            logger.warning("No relevant regulatory chunks found in database.")
            latency_ms = round((time.time() - start_time) * 1000, 2)
            fallback_text = ConfidenceEvaluator.get_insufficient_evidence_fallback(query, language)
            return ChatResponse(
                answer=fallback_text,
                citations=[],
                confidence_score=0.0,
                confidence_status="INSUFFICIENT_EVIDENCE",
                language=language,
                latency_ms=latency_ms,
                timestamp=datetime.now(timezone.utc).isoformat(),
                query_classification=classification,
                retrieval_strategy="hybrid_vector_bm25_rrf"
            )

        # -------------------------------------------------------------
        # 5. Reranking Layer (Cross-Interaction Relevance Scorer)
        # -------------------------------------------------------------
        reranked_chunks = reranker.rerank(
            query=search_query,
            candidates=candidates,
            top_k=max_citations
        )

        # -------------------------------------------------------------
        # 6. Grounding Confidence Evaluation
        # -------------------------------------------------------------
        confidence_result = ConfidenceEvaluator.evaluate(reranked_chunks)
        confidence_score = confidence_result["score"]
        confidence_status = confidence_result["status"]
        is_confident = confidence_result["is_confident"]

        # Strict Grounding Constraint Check
        if not is_confident:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            fallback_text = ConfidenceEvaluator.get_insufficient_evidence_fallback(query, language)
            
            self._log_interaction(
                session_id=session_id,
                query=query,
                response=fallback_text,
                language=language,
                confidence_score=confidence_score,
                confidence_status=confidence_status,
                citations=[],
                chunks_count=0,
                latency_ms=latency_ms,
                classification=classification
            )

            return ChatResponse(
                answer=fallback_text,
                citations=[],
                confidence_score=confidence_score,
                confidence_status=confidence_status,
                language=language,
                latency_ms=latency_ms,
                timestamp=datetime.now(timezone.utc).isoformat(),
                query_classification=classification,
                retrieval_strategy="hybrid_vector_bm25_rrf"
            )

        # -------------------------------------------------------------
        # 7. Prompt Context Assembly & Raw Citations
        # -------------------------------------------------------------
        raw_citations = CitationFormatter.build_citations(reranked_chunks)
        context_block = CitationFormatter.format_context_for_prompt(reranked_chunks)

        # -------------------------------------------------------------
        # 8. LLM Grounded Generation
        # -------------------------------------------------------------
        raw_answer = llm_client.generate_grounded_answer(
            query=search_query,
            context=context_block,
            language=language
        )

        # -------------------------------------------------------------
        # 9. Citation Verification Layer (Ground-Truth Integrity Check)
        # -------------------------------------------------------------
        valid_chunks_list = [c for c, _ in reranked_chunks]
        verified_citations = citation_verifier.verify_and_filter(
            citations=raw_citations,
            db=self.db,
            valid_chunks=valid_chunks_list,
            strict_filter=True
        )

        # -------------------------------------------------------------
        # 10. Localization if requested
        # -------------------------------------------------------------
        final_answer = multilingual_service.localize_answer(raw_answer, language)

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # -------------------------------------------------------------
        # 11. Audit Logging & Final Response
        # -------------------------------------------------------------
        self._log_interaction(
            session_id=session_id,
            query=query,
            response=final_answer,
            language=language,
            confidence_score=confidence_score,
            confidence_status=confidence_status,
            citations=[c.dict() for c in verified_citations],
            chunks_count=len(reranked_chunks),
            latency_ms=latency_ms,
            classification=classification
        )

        return ChatResponse(
            answer=final_answer,
            citations=verified_citations,
            confidence_score=confidence_score,
            confidence_status=confidence_status,
            language=language,
            latency_ms=latency_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
            query_classification=classification,
            retrieval_strategy="hybrid_vector_bm25_rrf"
        )

    def _log_interaction(
        self,
        session_id: Optional[str],
        query: str,
        response: str,
        language: str,
        confidence_score: float,
        confidence_status: str,
        citations: List[Dict[str, Any]],
        chunks_count: int,
        latency_ms: float,
        classification: Optional[QueryClassificationResult] = None
    ):
        try:
            log_entry = ChatLog(
                session_id=session_id,
                query=query,
                response=response,
                language=language,
                confidence_score=confidence_score,
                confidence_status=confidence_status,
                citations_json=json.dumps(citations),
                retrieved_chunks_count=chunks_count,
                latency_ms=latency_ms
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to record ChatLog: {e}")
            self.db.rollback()
