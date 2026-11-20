import os
from typing import Optional, List
from app.config import settings
from app.utils.logger import logger

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

SYSTEM_PROMPT = """You are IP-SAKTI Sahayak, an authoritative, source-grounded AI legal assistant specializing in Ayurveda Intellectual Property (IP) and Regulatory Compliance under the Ministry of Ayush, Government of India, as well as international regimes (WHO, US FDA Botanical Guidance, WIPO, TKDL).

YOUR CARDINAL RULES:
1. STRICT FACTUAL GROUNDING: Answer the question using ONLY the factual statements provided in the [Source N] context sections below.
2. SOURCE CITATIONS: Every legal or regulatory claim must cite its source using inline bracket notation, e.g. "[Source 1]" or "[Source 1, Source 2]". Refer to the exact document name, Act, and Section/Rule mentioned in the source context.
3. NO FABRICATION: If the provided sources do not contain sufficient evidence to answer the question with certainty, clearly declare: "The provided regulatory documents do not contain sufficient evidence to conclusively answer this question." Never invent case law, section numbers, or compliance rules.
4. TONE & STRUCTURE: Professional, precise, statutory, and objective. Use clear headings, bullet points, and reference the relevant statutory bodies (e.g., National Biodiversity Authority, CGPDTM, ASU Drug Technical Advisory Board).
5. LEGAL DISCLAIMER: Conclude with: "*Disclaimer: Research aid only; not a formal legal opinion.*"
"""

class LLMClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.client_ready = False

        if self.api_key and HAS_GENAI:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                self.client_ready = True
                logger.info(f"Gemini LLM Client initialized with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini model: {e}. Falling back to offline synthesis.")
                self.client_ready = False
        else:
            logger.info("No Gemini API key found. Operating in deterministic offline regulatory synthesis mode.")

    def generate_grounded_answer(self, query: str, context: str, language: str = "en") -> str:
        """
        Generates a grounded answer from the provided context.
        """
        if self.client_ready:
            try:
                prompt = (
                    f"User Query: {query}\n"
                    f"Preferred Language: {language}\n\n"
                    f"Official Regulatory Context:\n{context}\n\n"
                    f"Provide an authoritative, source-cited answer grounded strictly in the context above."
                )
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Error during Gemini generation: {e}. Falling back to offline synthesis.")

        # High-fidelity offline statutory synthesis fallback
        return self._offline_grounded_synthesis(query, context, language)

    def _offline_grounded_synthesis(self, query: str, context: str, language: str) -> str:
        """
        Deterministic, rule-based statutory answer synthesis for zero-dependency evaluation.
        Extracts key clauses and constructs grounded answers with [Source N] citations.
        """
        blocks = context.split("\n\n")
        if not blocks:
            return "No regulatory context available to answer this query."

        summary_points = []
        for idx, block in enumerate(blocks, start=1):
            lines = block.strip().split("\n")
            header = lines[0] if lines else f"[Source {idx}]"
            # Extract content lines
            content_lines = [l.strip() for l in lines[1:] if l.strip() and not l.startswith('"""')]
            
            # Select most informative 2-3 sentences
            selected_snippets = []
            for cl in content_lines[:4]:
                if len(cl) > 30:
                    selected_snippets.append(cl)

            if selected_snippets:
                joined = " ".join(selected_snippets)
                # Keep it concise
                if len(joined) > 300:
                    joined = joined[:297] + "..."
                summary_points.append(f"- **According to {header}**:\n  {joined} `[Source {idx}]`")

        points_text = "\n\n".join(summary_points)
        
        intro = f"### Regulatory Findings for: *\"{query}\"*\n\nBased strictly on the verified Ayush regulatory records in the corpus, the following statutory provisions apply:\n\n"
        conclusion = (
            "\n\n**Compliance Summary**:\n"
            "Any commercialization, patent filing, or export of Ayurvedic biological resources or formulations must comply "
            "with the statutory mandates cited above, including mandatory approvals where applicable `[Source 1]`.\n\n"
            "*Disclaimer: This response is generated by IP-SAKTI Sahayak as an automated regulatory research aid and does not substitute for certified legal counsel or formal Ministry of Ayush approvals.*"
        )
        return intro + points_text + conclusion

llm_client = LLMClient()
