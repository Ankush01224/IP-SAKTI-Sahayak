from app.core.confidence import ConfidenceEvaluator

class MockChunk:
    def __init__(self, content="Test clause"):
        self.content = content
        self.document = None

def test_confidence_insufficient_evidence():
    # Top score below threshold (0.60)
    mock_candidates = [(MockChunk(), 0.45), (MockChunk(), 0.35)]
    result = ConfidenceEvaluator.evaluate(mock_candidates)
    assert result["is_confident"] is False
    assert result["status"] == "INSUFFICIENT_EVIDENCE"

def test_confidence_high():
    # Top score >= 0.75
    mock_candidates = [(MockChunk(), 0.88), (MockChunk(), 0.82)]
    result = ConfidenceEvaluator.evaluate(mock_candidates)
    assert result["is_confident"] is True
    assert result["status"] == "HIGH_CONFIDENCE"
    assert result["score"] >= 0.75

def test_confidence_empty():
    result = ConfidenceEvaluator.evaluate([])
    assert result["is_confident"] is False
    assert result["status"] == "INSUFFICIENT_EVIDENCE"

def test_fallback_message_generation():
    msg_en = ConfidenceEvaluator.get_insufficient_evidence_fallback("some query", "en")
    assert "Insufficient Regulatory Evidence" in msg_en
    assert "National Biodiversity Authority" in msg_en
