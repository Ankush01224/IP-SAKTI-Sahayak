import re
from typing import List, Tuple, Dict, Any
from app.models.schemas import CitationItem
from app.models.db_models import DocumentChunk
from app.utils.logger import logger

class CitationFormatter:
    """Attaches and verifies source document, jurisdiction, and section references."""

    @staticmethod
    def build_citations(retrieved_items: List[Tuple[DocumentChunk, float]]) -> List[CitationItem]:
        citations = []
        for chunk, score in retrieved_items:
            doc = chunk.document
            doc_title = doc.title if doc else "Ayurvedic Regulatory Corpus"
            jurisdiction = doc.jurisdiction if doc else "India"

            # Create an excerpt snippet of the chunk (up to 220 chars)
            snippet = chunk.content.strip()
            if len(snippet) > 220:
                snippet = snippet[:217] + "..."

            citations.append(CitationItem(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                document_title=doc_title,
                section_number=chunk.section_number or "General Section",
                section_title=chunk.section_title or "Statutory Provisions",
                jurisdiction=jurisdiction,
                snippet=snippet,
                page_number=chunk.page_number,
                similarity_score=round(float(score), 3)
            ))
        return citations

    @staticmethod
    def format_context_for_prompt(retrieved_items: List[Tuple[DocumentChunk, float]]) -> str:
        """
        Creates a structured prompt context block where each chunk is labeled with [Source N].
        """
        context_blocks = []
        for idx, (chunk, _) in enumerate(retrieved_items, start=1):
            doc = chunk.document
            title = doc.title if doc else "Ayurveda Regulatory Document"
            jurisdiction = doc.jurisdiction if doc else "India"
            sec_num = chunk.section_number or "Section"
            sec_title = chunk.section_title or ""

            header = f"[Source {idx}]: {title} ({jurisdiction}) | {sec_num}"
            if sec_title and sec_title != sec_num:
                header += f" - {sec_title}"

            block = f"{header}\n\"\"\"\n{chunk.content}\n\"\"\""
            context_blocks.append(block)

        return "\n\n".join(context_blocks)
