from typing import List, Tuple, Dict, Any
from app.config import settings
from app.utils.logger import logger

class ConfidenceEvaluator:
    """
    Evaluates grounding confidence based on semantic similarity of retrieved chunks.
    Enforces the zero-hallucination constraint: if evidence is insufficient,
    the pipeline short-circuits to an explicit 'not enough information' answer.
    """

    HIGH_THRESHOLD = 0.75

    @classmethod
    def evaluate(cls, scored_chunks: List[Tuple[Any, float]]) -> Dict[str, Any]:
        """
        Args:
            scored_chunks: List of (DocumentChunk, similarity_score) sorted descending by score.
        Returns:
            Dict containing confidence_score, status, and is_confident flag.
        """
        if not scored_chunks:
            return {
                "score": 0.0,
                "status": "INSUFFICIENT_EVIDENCE",
                "is_confident": False,
                "reason": "No regulatory document chunks matched the query."
            }

        top_score = scored_chunks[0][1]
        threshold = settings.CONFIDENCE_THRESHOLD

        # Calculate weighted confidence average across top chunks
        weights = [0.5, 0.3, 0.15, 0.05][:len(scored_chunks)]
        norm_weights = [w / sum(weights) for w in weights]
        weighted_score = sum(s * w for (_, s), w in zip(scored_chunks, norm_weights))

        # Overall confidence is dominated by top match but smoothed
        final_score = round(float(0.7 * top_score + 0.3 * weighted_score), 3)

        if top_score < threshold:
            logger.info(f"Confidence score {final_score:.3f} (top: {top_score:.3f}) is below threshold {threshold:.2f}.")
            return {
                "score": final_score,
                "status": "INSUFFICIENT_EVIDENCE",
                "is_confident": False,
                "reason": f"Top similarity score ({top_score:.2f}) is below statutory grounding threshold ({threshold:.2f})."
            }
        elif final_score >= cls.HIGH_THRESHOLD:
            return {
                "score": final_score,
                "status": "HIGH_CONFIDENCE",
                "is_confident": True,
                "reason": "Strong statutory evidence identified in regulatory corpus."
            }
        else:
            return {
                "score": final_score,
                "status": "PARTIAL_EVIDENCE",
                "is_confident": True,
                "reason": "Partial evidence found; response is strictly constrained to matching clauses."
            }

    @staticmethod
    def get_insufficient_evidence_fallback(query: str, language: str = "en") -> str:
        """Standardized non-hallucinatory fallback response."""
        fallbacks = {
            "en": (
                "**Insufficient Regulatory Evidence**\n\n"
                "The current curated Ayush and intellectual property regulatory corpus does not contain "
                "sufficient statutory provisions or guidelines to conclusively answer your query.\n\n"
                "To uphold legal accuracy and avoid fabrication, IP-SAKTI Sahayak cannot extrapolate an answer. "
                "Please consider:\n"
                "- Refining your query with specific legal terms (e.g., Section 3(p), Chapter IV-A, NBA approval, or TKDL classification).\n"
                "- Consulting the official gazettes of the **Ministry of Ayush**, **National Biodiversity Authority (NBA)**, or the **Controller General of Patents, Designs & Trade Marks (CGPDTM)**."
            ),
            "hi": (
                "**अपर्याप्त विनियामक साक्ष्य (Insufficient Regulatory Evidence)**\n\n"
                "वर्तमान आयुष एवं बौद्धिक संपदा विनियामक संग्रह (Corpus) में आपके प्रश्न का प्रामाणिक उत्तर देने हेतु "
                "पर्याप्त कानूनी धाराएं या दिशानिर्देश उपलब्ध नहीं हैं।\n\n"
                "भ्रामक जानकारी से बचने के लिए, सहायक अनुमान पर आधारित उत्तर नहीं देता। कृपया संबंधित सरकारी गजट, "
                "**आयुष मंत्रालय**, अथवा **राष्ट्रीय जैव विविधता प्राधिकरण (NBA)** से परामर्श लें।"
            ),
            "sa": (
                "**अपर्याप्तम् विनियामक प्रमाणम् (Insufficient Evidence)**\n\n"
                "अस्मिन आयुष-नियामक-ग्रन्थे भवतः प्रश्नस्य प्रामाणिक-उत्तराय पर्याप्त-नियमाः न प्राप्यन्ते। "
                "आयुष-मन्त्रालयस्य अधिकृत-अधिसूचनां पश्यतु।"
            )
        }
        return fallbacks.get(language, fallbacks["en"])
