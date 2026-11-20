import re
from typing import Tuple, Dict
from app.config import settings
from app.utils.logger import logger

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "sa": "संस्कृतम् (Sanskrit)",
    "ta": "தமிழ் (Tamil)",
    "te": "తెలుగు (Telugu)",
    "mr": "मराठी (Marathi)",
    "bn": "বাংলা (Bengali)",
    "gu": "ગુજરાતી (Gujarati)",
    "kn": "ಕನ್ನಡ (Kannada)"
}

# Domain vocabulary for offline Ayush IP translation
OFFLINE_TERM_MAP = {
    "पेटेंट": "patent",
    "पेटेन्ट": "patent",
    "चरक संहिता": "Charaka Samhita",
    "सुश्रुत संहिता": "Sushruta Samhita",
    "आयुर्वेद": "Ayurveda",
    "आयुर्वेदिक": "Ayurvedic",
    "योगों": "formulations",
    "योग": "formulation",
    "दवा": "drug medicine",
    "औषधि": "medicine drug",
    "जैव विविधता": "biological diversity",
    "प्राधिकरण": "authority",
    "अनुमति": "approval permission",
    "निर्यात": "export",
    "अश्वगंधा": "Ashwagandha",
    "पारंपरिक ज्ञान": "traditional knowledge",
    "डिजिटल लाइब्रेरी": "digital library TKDL",
    "मानक": "standard mark",
    "गुणवत्ता": "quality GMP",
    "लाइसेंस": "license",
    "अधिनियम": "Act",
    "धारा": "Section",
    "नियम": "Rule"
}

class MultilingualService:
    """
    Multilingual layer:
    1. Translates non-English queries into English for semantic vector retrieval.
    2. Preserves domain-specific Sanskrit/Ayurvedic terms (e.g. Asava, Arishta, Bhasma, Dravyaguna).
    3. Translates the final grounded answer back into the requested language.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.use_llm = bool(self.api_key and HAS_GENAI)

    def prepare_query(self, query: str, language: str) -> str:
        """Translates query to English if necessary to match the statutory corpus."""
        if language == "en" or not query.strip():
            return query

        if self.use_llm:
            try:
                prompt = (
                    f"Translate the following user query from {SUPPORTED_LANGUAGES.get(language, language)} into clear English. "
                    f"Preserve technical legal and Ayurvedic botanical terms (like Charaka Samhita, Ashwagandha, NBA, Patent Act). "
                    f"Output ONLY the English translation.\n\nQuery: {query}"
                )
                model = genai.GenerativeModel(settings.GEMINI_MODEL)
                res = model.generate_content(prompt)
                if res and res.text:
                    translated = res.text.strip()
                    logger.info(f"Translated query ({language} -> en): '{query}' -> '{translated}'")
                    return translated
            except Exception as e:
                logger.warning(f"Translation failed via LLM: {e}. Using offline vocabulary mapping.")

        # High-fidelity offline domain mapping for Indian languages
        query_lower = query.lower()
        english_terms = []
        for indic_term, eng in OFFLINE_TERM_MAP.items():
            if indic_term in query or indic_term.lower() in query_lower:
                english_terms.append(eng)

        if english_terms:
            translated = f"{query} {' '.join(english_terms)}"
            logger.info(f"Augmented query with domain terms: '{translated}'")
            return translated

        return query

    def localize_answer(self, answer: str, target_language: str) -> str:
        """Translates grounded answer to target language while keeping citations intact."""
        if target_language == "en" or not answer.strip():
            return answer

        if self.use_llm:
            try:
                prompt = (
                    f"Translate the following legal and regulatory guidance into {SUPPORTED_LANGUAGES.get(target_language, target_language)}. "
                    f"IMPORTANT RULES:\n"
                    f"1. KEEP ALL CITATION TAGS EXACTLY AS THEY ARE (e.g. [Source 1], [Source 2], Section 3(p)).\n"
                    f"2. Maintain statutory precision and formal legal tone.\n"
                    f"3. Output ONLY the translated text.\n\nText:\n{answer}"
                )
                model = genai.GenerativeModel(settings.GEMINI_MODEL)
                res = model.generate_content(prompt)
                if res and res.text:
                    return res.text.strip()
            except Exception as e:
                logger.warning(f"Answer localization failed via LLM: {e}. Returning English.")

        return answer

multilingual_service = MultilingualService()
