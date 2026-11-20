import re
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any, Union
from app.models.schemas import QueryClassificationResult
from app.utils.logger import logger

class DomainCategory(str, Enum):
    IP_DOMAIN = "IP_DOMAIN"
    REGULATORY_DOMAIN = "REGULATORY_DOMAIN"
    GENERAL = "GENERAL"

class SubDomain(str, Enum):
    # IP_DOMAIN sub-domains
    PATENT = "Patent"
    TRADEMARK = "Trademark"
    COPYRIGHT = "Copyright"
    TRADITIONAL_KNOWLEDGE = "Traditional Knowledge"

    # REGULATORY_DOMAIN sub-domains
    AYUSH = "AYUSH"
    CDSCO = "CDSCO"
    EXPORT = "Export"
    MARKET_REGULATORY = "Market/Regulatory requirements"

    # GENERAL
    GENERAL = "General / Clarification Needed"

class QueryClassifier:
    """
    Lightweight, fast, and deterministic query classifier.
    Categorizes incoming queries into:
      - IP_DOMAIN (Patent, Trademark, Copyright, Traditional Knowledge)
      - REGULATORY_DOMAIN (AYUSH, CDSCO, Export, Market/Regulatory requirements)
      - GENERAL (Greetings, chitchat, or topics unrelated to Ayush IP/regulations)
    """

    # Keyword taxonomies with weights
    TAXONOMY: Dict[DomainCategory, Dict[SubDomain, List[str]]] = {
        DomainCategory.IP_DOMAIN: {
            SubDomain.PATENT: [
                "patent", "patents", "patenting", "patented", "patentable", "patentability",
                "section 3(p)", "section 3p", "section 3(d)", "section 3(e)", "prior art",
                "inventive step", "novelty", "claims", "specification", "cgpdtm",
                "controller general", "patent office", "provisional application", "patent act"
            ],
            SubDomain.TRADEMARK: [
                "trademark", "trade mark", "trademarks", "trade marks", "brand name", "logo",
                "trade name", "madrid protocol", "device mark", "service mark",
                "distinctiveness", "deceptive similarity", "infringement of trademark", "brand registration"
            ],
            SubDomain.COPYRIGHT: [
                "copyright", "copyrights", "literary work", "ancient manuscript", "manuscripts",
                "translation rights", "authorship", "original expression", "samhita text",
                "copyright act", "moral rights"
            ],
            SubDomain.TRADITIONAL_KNOWLEDGE: [
                "traditional knowledge", "tkdl", "traditional medicine", "charaka", "charak",
                "sushruta", "ashtanga", "sharangadhara", "bhavaprakasha", "classical formulation",
                "classical formulations", "biopiracy", "biological diversity", "nba", "sbb",
                "abs", "access and benefit sharing", "benefit claimer", "benefit claimers",
                "bmc", "biodiversity act", "prior informed consent", "indigenous knowledge", "folklore"
            ]
        },
        DomainCategory.REGULATORY_DOMAIN: {
            SubDomain.AYUSH: [
                "ayush", "ministry of ayush", "asu", "asudtab", "ayurvedic pharmacopoeia", "api",
                "schedule t", "rule 158-b", "rule 158b", "rule 158", "gmp", "good manufacturing practice",
                "classical asu", "patent or proprietary", "p&p", "bhasma", "asava", "arishta",
                "rasashastra", "dravyaguna", "state licensing authority", "sla", "drug inspector",
                "ayush license", "ayurvedic license", "ayurveda drug"
            ],
            SubDomain.CDSCO: [
                "cdsco", "dcgi", "drugs controller general", "clinical trial", "clinical trials",
                "gcp", "good clinical practice", "new drug", "investigational new drug", "ind",
                "ethics committee", "central drugs standard", "bioavailability", "bioequivalence"
            ],
            SubDomain.EXPORT: [
                "export", "exporting", "imported", "importing", "copp", "certificate of pharmaceutical product",
                "who-gmp", "who gmp", "ayush standard mark", "ayush premium mark", "fda", "us fda",
                "botanical drug", "cder", "thmpd", "ema", "european medicines agency", "heavy metal limits",
                "aflatoxin", "aflatoxins", "microbial limits", "pesticide residue", "qci",
                "quality council of india", "foreign market", "international trade"
            ],
            SubDomain.MARKET_REGULATORY: [
                "labeling", "labelling", "packaging", "shelf life", "expiry date", "misbranded",
                "adulterated", "spurious", "adulteration", "manufacturing license", "recall",
                "cosmetics", "drugs and cosmetics act", "chapter iv-a", "chapter iva",
                "statutory compliance", "nabl", "quality testing", "batch manufacturing record"
            ]
        }
    }

    GENERAL_CHITCHAT_PATTERNS = [
        r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day))[\s!.]*$",
        r"^(who\s+are\s+you|what\s+is\s+your\s+name|what\s+can\s+you\s+do|how\s+can\s+you\s+help)[\s?.]*$",
        r"^(help|test|testing|ping)[\s!.]*$",
        r"^(thank\s+you|thanks|bye|goodbye)[\s!.]*$"
    ]

    OUT_OF_DOMAIN_PATTERNS = [
        r"\b(weather|forecast|temperature|rain)\b",
        r"\b(capital\s+of\s+[a-z]+)\b",
        r"\b(crypto|cryptocurrency|bitcoin|ethereum|stock\s+price)\b",
        r"\b(movie|film|song|music|cricket|football|fifa|ipl)\b",
        r"\b(python\s+code|javascript\s+code|write\s+a\s+program|quicksort|binary\s+tree)\b",
        r"\b(recipe\s+for|cook|cake|pizza|burger)\b",
        r"\b(president\s+of|prime\s+minister\s+of\s+(?!india))\b"
    ]

    @classmethod
    def classify(cls, query: str) -> QueryClassificationResult:
        """
        Classifies query into IP_DOMAIN, REGULATORY_DOMAIN, or GENERAL.
        Returns QueryClassificationResult with domain, sub_domain, confidence, and matched keywords.
        """
        cleaned_query = query.strip().lower()

        # 1. Quick check for greetings / general chitchat
        for pattern in cls.GENERAL_CHITCHAT_PATTERNS:
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                logger.info(f"Query classified as GENERAL (chitchat pattern matched): '{query}'")
                return QueryClassificationResult(
                    domain=DomainCategory.GENERAL.value,
                    sub_domain=SubDomain.GENERAL.value,
                    confidence=0.98,
                    matched_keywords=["greeting/chitchat"],
                    reasoning="Query matched general conversational chitchat or greeting pattern."
                )

        # 2. Score across IP_DOMAIN and REGULATORY_DOMAIN taxonomies
        scores: Dict[Tuple[DomainCategory, SubDomain], Tuple[float, List[str]]] = {}

        for domain, sub_dict in cls.TAXONOMY.items():
            for sub_domain, terms in sub_dict.items():
                matched = []
                score = 0.0
                for term in terms:
                    # Look for exact word boundary match
                    pattern = rf"\b{re.escape(term)}\b"
                    matches = re.findall(pattern, cleaned_query, re.IGNORECASE)
                    if matches:
                        matched.append(term)
                        # Multi-word and exact legal terms receive higher weight
                        weight = 2.5 if ("section" in term or " " in term or "rule" in term) else 1.2
                        score += len(matches) * weight

                if matched:
                    scores[(domain, sub_domain)] = (score, matched)

        # 3. If no IP or Regulatory terms matched, evaluate out-of-domain patterns
        if not scores:
            for pattern in cls.OUT_OF_DOMAIN_PATTERNS:
                if re.search(pattern, cleaned_query, re.IGNORECASE):
                    logger.info(f"Query classified as GENERAL (out-of-domain pattern matched): '{query}'")
                    return QueryClassificationResult(
                        domain=DomainCategory.GENERAL.value,
                        sub_domain=SubDomain.GENERAL.value,
                        confidence=0.92,
                        matched_keywords=["out-of-domain query"],
                        reasoning="Query is unrelated to Ayurveda, intellectual property, or regulatory compliance."
                    )

            # Unmatched query: default to GENERAL to avoid noisy RAG hallucination
            logger.info(f"Query classified as GENERAL (no statutory keywords matched): '{query}'")
            return QueryClassificationResult(
                domain=DomainCategory.GENERAL.value,
                sub_domain=SubDomain.GENERAL.value,
                confidence=0.70,
                matched_keywords=[],
                reasoning="No recognized IP, patent, trademark, or regulatory statutory terms were detected in the query."
            )

        # 4. Find winning domain and sub_domain
        best_key = max(scores.keys(), key=lambda k: scores[k][0])
        best_score, best_matches = scores[best_key]
        domain, sub_domain = best_key

        # Calculate confidence normalized to [0.75, 0.99]
        norm_confidence = min(0.99, 0.75 + (best_score * 0.05))

        logger.info(f"Query classified as {domain.value} -> {sub_domain.value} (score: {best_score:.2f}, keywords: {best_matches})")
        return QueryClassificationResult(
            domain=domain.value,
            sub_domain=sub_domain.value,
            confidence=round(norm_confidence, 2),
            matched_keywords=best_matches[:6],
            reasoning=f"Matched statutory keywords for {sub_domain.value}: {', '.join(best_matches[:4])}."
        )

    @staticmethod
    def get_general_clarification_response(query: Any, language: str = "en") -> str:
        """
        Generates an informative, guidance-oriented response when a query is GENERAL,
        explaining the scope of IP-SAKTI Sahayak and guiding the user to valid queries.
        """
        if isinstance(query, str):
            cleaned = query.strip().lower()
        else:
            cleaned = ""
        is_greeting = any(re.search(p, cleaned) for p in QueryClassifier.GENERAL_CHITCHAT_PATTERNS) if cleaned else False

        if is_greeting:
            if language == "hi":
                return (
                    "**नमस्ते! मैं IP-SAKTI सहायक हूँ।**\n\n"
                    "मैं आयुष मंत्रालय (Ministry of Ayush) के अंतर्गत **आयुर्वेद बौद्धिक संपदा (IP)** एवं **विनियामक अनुपालन (Regulatory Compliance)** हेतु आधिकारिक कानूनी व शोध सहायक हूँ।\n\n"
                    "आप मुझसे निम्नलिखित विषयों पर प्रमाणिक प्रश्न पूछ सकते हैं:\n"
                    "- **पेटेंट एवं पारंपरिक ज्ञान**: पेटेंट अधिनियम की धारा 3(p), चरक/सुश्रुत संहिता के योग, TKDL रक्षा।\n"
                    "- **जैव विविधता एवं NBA अनुमति**: जड़ी-बूटियों (जैसे अश्वगंधा) के व्यावसायिक उपयोग व निर्यात हेतु ABS अनुमति।\n"
                    "- **औषधि लाइसेंस (Rule 158-B)**: शास्त्रीय औषधियाँ बनाम पेटेंट प्रोप्राइटरी (P&P) दवाएं।\n"
                    "- **अंतर्राष्ट्रीय निर्यात**: WHO-GMP मानक, आयुष प्रीमियम मार्क, US FDA बॉटनिकल ड्रग गाइडेंस।"
                )
            return (
                "**Greetings! I am IP-SAKTI Sahayak.**\n\n"
                "I am your source-cited regulatory intelligence assistant developed for **SIH 2026** under the **Ministry of Ayush**, Government of India.\n\n"
                "I specialize strictly in **Ayurveda Intellectual Property (IP)** and **Regulatory Compliance** across national and international regimes.\n\n"
                "### How I can assist you:\n"
                "- **Patent Law & TKDL**: Section 3(p) non-patentability of classical texts (*Charaka Samhita*, *Sushruta Samhita*), defensive prior art.\n"
                "- **Biodiversity & ABS**: National Biodiversity Authority (NBA) approvals for commercial utilization and export under the Biological Diversity Act, 2002.\n"
                "- **Drug Manufacturing & Licensing**: Rule 158-B guidelines for Classical ASU vs Patent/Proprietary medicines, Schedule T GMP.\n"
                "- **Global Export Standards**: Ayush Premium Mark, WHO-GMP certification, permissible heavy metal/microbial limits, and US FDA Botanical Drug guidance.\n\n"
                "*Please feel free to ask an IP or regulatory compliance question to get started!*"
            )

        # Out-of-scope clarification
        if language == "hi":
            return (
                "**सामान्य जानकारी / कार्यक्षेत्र से बाहर (General Query)**\n\n"
                f"आपके द्वारा पूछा गया प्रश्न (*\"{query}\"*) आयुर्वेद बौद्धिक संपदा या विनियामक अनुपालन के दायरे से बाहर प्रतीत होता है।\n\n"
                "भ्रामक उत्तरों से बचने के लिए, **IP-SAKTI सहायक** केवल सत्यापित आयुष संहिताओं, पेटेंट अधिनियम (Section 3(p)), राष्ट्रीय जैव विविधता प्राधिकरण (NBA), और औषधि एवं प्रसाधन सामग्री अधिनियम (Chapter IV-A) के विनियामक नियमों पर ही उत्तर प्रदान करता है।\n\n"
                "कृपया आयुर्वेद पेटेंट, ट्रेडमार्क, टीकेडीएल (TKDL), या विनियामक नियमों से संबंधित प्रश्न पूछें।"
            )

        return (
            "**General Query / Domain Clarification**\n\n"
            f"Your query (*\"{query}\"*) appears to fall outside the scope of Ayurveda Intellectual Property and Regulatory Compliance.\n\n"
            "To maintain strict factual grounding and eliminate hallucinations, **IP-SAKTI Sahayak** does not answer generic or non-regulatory questions.\n\n"
            "### Recommended Regulatory Topics to Ask:\n"
            "1. **Patents Act §3(p)**: *\"Can a classical formulation from Charaka Samhita be patented in India?\"*\n"
            "2. **Biodiversity & ABS**: *\"What permissions are required under the Biological Diversity Act for exporting Ashwagandha?\"*\n"
            "3. **ASU Drug Licensing**: *\"What is the difference between classical and proprietary ASU medicines under Rule 158-B?\"*\n"
            "4. **TKDL Defensive Shield**: *\"How does TKDL protect traditional Ayurvedic medicine in USPTO and EPO?\"*\n"
            "5. **Export & Quality Norms**: *\"What heavy metal limits are required for the Ayush Premium Mark?\"*\n\n"
            "*Please submit a query related to Ayush IP or regulatory compliance to receive source-cited guidance.*"
        )

query_classifier = QueryClassifier()
