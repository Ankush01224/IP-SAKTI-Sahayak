import pytest
from app.core.query_classifier import QueryClassifier

@pytest.fixture
def classifier():
    return QueryClassifier()

class TestQueryClassifier:
    def test_ip_domain_patent(self, classifier):
        res = classifier.classify("Can I patent an Ayurvedic formulation under Section 3(p)?")
        assert res.domain == "IP_DOMAIN"
        assert res.sub_domain == "Patent"
        assert res.confidence >= 0.70
        assert any("patent" in kw.lower() or "section 3(p)" in kw.lower() for kw in res.matched_keywords)

    def test_ip_domain_trademark(self, classifier):
        res = classifier.classify("How do I register a brand trademark for herbal cosmetics in Class 5?")
        assert res.domain == "IP_DOMAIN"
        assert res.sub_domain == "Trademark"
        assert res.confidence >= 0.70

    def test_ip_domain_copyright(self, classifier):
        res = classifier.classify("Is my Ayurvedic manuscript translation protected by copyright law?")
        assert res.domain == "IP_DOMAIN"
        assert res.sub_domain == "Copyright"
        assert res.confidence >= 0.70

    def test_ip_domain_traditional_knowledge(self, classifier):
        res = classifier.classify("How does the TKDL protect indigenous medicinal knowledge from biopiracy?")
        assert res.domain == "IP_DOMAIN"
        assert res.sub_domain == "Traditional Knowledge"
        assert res.confidence >= 0.70

    def test_regulatory_domain_ayush(self, classifier):
        res = classifier.classify("What are the manufacturing license requirements for ASU drugs under Rule 158-B?")
        assert res.domain == "REGULATORY_DOMAIN"
        assert res.sub_domain == "AYUSH"
        assert res.confidence >= 0.70

    def test_regulatory_domain_cdsco(self, classifier):
        res = classifier.classify("What clinical trial regulations are enforced by CDSCO for phytopharmaceuticals?")
        assert res.domain == "REGULATORY_DOMAIN"
        assert res.sub_domain == "CDSCO"
        assert res.confidence >= 0.70

    def test_regulatory_domain_export(self, classifier):
        res = classifier.classify("What are the requirements for Ayush Premium Mark export to the United States?")
        assert res.domain == "REGULATORY_DOMAIN"
        assert res.sub_domain == "Export"
        assert res.confidence >= 0.70

    def test_regulatory_domain_market(self, classifier):
        res = classifier.classify("What are the mandatory labeling, packaging, and shelf life requirements?")
        assert res.domain == "REGULATORY_DOMAIN"
        assert res.sub_domain == "Market/Regulatory requirements"
        assert res.confidence >= 0.70

    def test_general_query_greeting(self, classifier):
        query = "Hello, good morning! Who are you?"
        res = classifier.classify(query)
        assert res.domain == "GENERAL"
        clarification = classifier.get_general_clarification_response(query)
        assert "IP-SAKTI Sahayak" in clarification
        assert "Ayush" in clarification or "AYUSH" in clarification

    def test_general_query_out_of_domain(self, classifier):
        res = classifier.classify("What is the capital of France and what is the weather today?")
        assert res.domain == "GENERAL"
