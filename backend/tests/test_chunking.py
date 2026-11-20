from app.ingestion.chunking import RegulatoryChunker

def test_regulatory_chunker_section_split():
    sample_text = """# The Patents Act, 1970
## Section 3(p) - Traditional Knowledge
An invention which in effect is traditional knowledge is not patentable.
Classical formulations in Charaka Samhita are in the public domain.

## Section 3(e) - Admixtures
A mere admixture resulting only in aggregation of properties is not an invention.
Synergy must be established through empirical pharmacological evidence.
"""
    chunker = RegulatoryChunker(chunk_size=200, chunk_overlap=20)
    chunks = chunker.chunk_document({
        "raw_text": sample_text,
        "filename": "test_patents.md",
        "pages": [{"page_number": 1, "text": sample_text}]
    })

    assert len(chunks) >= 2
    section_numbers = [c["section_number"] for c in chunks]
    assert any("Section 3(p)" in s for s in section_numbers)
    assert any("Section 3(e)" in s for s in section_numbers)
