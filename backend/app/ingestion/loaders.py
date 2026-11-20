import os
from pathlib import Path
from typing import Dict, Any, List
from pypdf import PdfReader
from app.utils.logger import logger

class DocumentLoader:
    """Extracts raw text and metadata from files (PDF, MD, TXT)."""

    @staticmethod
    def load_file(file_path: Path) -> Dict[str, Any]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return DocumentLoader.load_pdf(file_path)
        elif suffix in [".md", ".markdown", ".txt"]:
            return DocumentLoader.load_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def load_pdf(file_path: Path) -> Dict[str, Any]:
        text_pages = []
        try:
            reader = PdfReader(str(file_path))
            for idx, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                if extracted.strip():
                    text_pages.append({
                        "page_number": idx + 1,
                        "text": extracted.strip()
                    })
            logger.info(f"Loaded PDF '{file_path.name}' with {len(text_pages)} non-empty pages.")
            return {
                "filename": file_path.name,
                "file_path": str(file_path),
                "pages": text_pages,
                "raw_text": "\n\n".join(p["text"] for p in text_pages)
            }
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise e

    @staticmethod
    def load_text(file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "filename": file_path.name,
                "file_path": str(file_path),
                "pages": [{"page_number": 1, "text": content.strip()}],
                "raw_text": content.strip()
            }
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise e
