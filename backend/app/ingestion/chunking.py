import re
from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import logger

class RegulatoryChunker:
    """
    Intelligently splits regulatory/legal documents by sections, rules, chapters,
    and clauses, ensuring context boundaries are preserved.
    """

    # Matches Section 3(p), Rule 158-B, Chapter IV-A, Article 27, Clause 4, etc.
    SECTION_PATTERN = re.compile(
        r'(?m)^(?:#{1,4}\s+|(?=(?:Section|Chapter|Rule|Article|Clause|Schedule)\s+[\dIVXLCDM\(\)\.\-]+))([^\n]+)'
    )

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_document(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw_text = doc_data.get("raw_text", "")
        pages = doc_data.get("pages", [])
        
        # If pages are provided, track page mapping
        chunks = []
        
        # Split text into logical section blocks
        sections = self._split_by_sections(raw_text)
        
        chunk_idx = 0
        for sec in sections:
            sec_num = sec["section_number"]
            sec_title = sec["section_title"]
            content = sec["content"].strip()
            
            if not content:
                continue

            # If section content is within limits, make it one chunk
            words = content.split()
            if len(words) <= self.chunk_size:
                page_num = self._estimate_page(content, pages)
                chunks.append({
                    "chunk_index": chunk_idx,
                    "section_number": sec_num,
                    "section_title": sec_title,
                    "content": content,
                    "token_count": len(words),
                    "page_number": page_num
                })
                chunk_idx += 1
            else:
                # Sub-chunk with overlap
                sub_chunks = self._sliding_window_split(words, self.chunk_size, self.chunk_overlap)
                for part_idx, part_words in enumerate(sub_chunks):
                    sub_text = " ".join(part_words)
                    page_num = self._estimate_page(sub_text, pages)
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "section_number": f"{sec_num} (Part {part_idx + 1})" if sec_num else f"Part {part_idx + 1}",
                        "section_title": sec_title,
                        "content": sub_text,
                        "token_count": len(part_words),
                        "page_number": page_num
                    })
                    chunk_idx += 1

        logger.info(f"Chunked document '{doc_data.get('filename')}' into {len(chunks)} regulatory chunks.")
        return chunks

    def _split_by_sections(self, text: str) -> List[Dict[str, Any]]:
        lines = text.split("\n")
        sections = []
        current_sec_num = "Overview"
        current_sec_title = "Preamble & General Context"
        current_lines = []

        for line in lines:
            trimmed = line.strip()
            # Check for Markdown headers or Section identifiers
            header_match = re.match(r'^(#{1,4})\s+(.+)$', trimmed)
            legal_match = re.match(
                r'^(Section|Chapter|Rule|Article|Clause|Schedule)\s+([A-Za-z0-9\(\)\.\-]+)[:\s\-]*(.*)$',
                trimmed,
                re.IGNORECASE
            )

            if header_match:
                if current_lines:
                    sections.append({
                        "section_number": current_sec_num,
                        "section_title": current_sec_title,
                        "content": "\n".join(current_lines)
                    })
                    current_lines = []
                
                title_text = header_match.group(2).strip()
                # Parse if section number is embedded, e.g. "Section 3(p) - Traditional Knowledge"
                if legal_match_title := re.match(r'^(Section|Chapter|Rule|Article)\s+([A-Za-z0-9\(\)\.\-]+)[:\s\-]*(.*)$', title_text, re.IGNORECASE):
                    current_sec_num = f"{legal_match_title.group(1)} {legal_match_title.group(2)}"
                    current_sec_title = legal_match_title.group(3).strip() or title_text
                else:
                    current_sec_num = "Section"
                    current_sec_title = title_text

            elif legal_match and len(trimmed) < 120:
                if current_lines:
                    sections.append({
                        "section_number": current_sec_num,
                        "section_title": current_sec_title,
                        "content": "\n".join(current_lines)
                    })
                    current_lines = []

                current_sec_num = f"{legal_match.group(1)} {legal_match.group(2)}"
                current_sec_title = legal_match.group(3).strip() or current_sec_num
                current_lines.append(line)
            else:
                current_lines.append(line)

        if current_lines:
            sections.append({
                "section_number": current_sec_num,
                "section_title": current_sec_title,
                "content": "\n".join(current_lines)
            })

        return sections

    def _sliding_window_split(self, words: List[str], size: int, overlap: int) -> List[List[str]]:
        result = []
        start = 0
        step = max(1, size - overlap)
        while start < len(words):
            end = min(start + size, len(words))
            result.append(words[start:end])
            if end == len(words):
                break
            start += step
        return result

    def _estimate_page(self, text_snippet: str, pages: List[Dict[str, Any]]) -> int:
        if not pages:
            return 1
        sample = text_snippet[:60].strip()
        for p in pages:
            if sample in p.get("text", ""):
                return p.get("page_number", 1)
        return pages[0].get("page_number", 1)
