"""
Document Chunking Service.
Splits municipal knowledge base documents into cohesive, retrieval-ready chunks.
Preserves all parent metadata (document ID, title, category, department, source).
NO VECTOR EMBEDDINGS — pure textual chunking.
"""

from typing import List, Dict
from dataclasses import dataclass, asdict
import re

SECTION_SPLIT_REGEX = re.compile(r"\n(?=[0-9]+\.\s+[A-Z\s]+|Q[0-9]+:)", re.MULTILINE)


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    title: str
    category: str
    department: str
    source: str
    text: str
    word_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def chunk_document(body_text: str, metadata: Dict[str, str], max_words: int = 220) -> List[KnowledgeChunk]:
    """
    Chunks document body using semantic section boundaries and paragraph groupings.
    """
    chunks: List[KnowledgeChunk] = []
    doc_id = metadata.get("document_id", "KB-GEN")
    title = metadata.get("title", "Municipal Guide")
    category = metadata.get("category", "Other")
    dept = metadata.get("department", "General Grievance Cell")
    source = metadata.get("source", "Sample Municipal Knowledge Base – Academic Project")

    # Split by section headers if present
    sections = SECTION_SPLIT_REGEX.split(body_text)
    sub_chunks: List[str] = []

    for section in sections:
        sec_text = section.strip()
        if not sec_text:
            continue
        words = sec_text.split()
        if len(words) <= max_words:
            sub_chunks.append(sec_text)
        else:
            # Further split long sections by paragraphs
            paragraphs = sec_text.split("\n\n")
            current_buffer = []
            current_word_count = 0
            for p in paragraphs:
                p_clean = p.strip()
                p_words = len(p_clean.split())
                if current_word_count + p_words <= max_words:
                    current_buffer.append(p_clean)
                    current_word_count += p_words
                else:
                    if current_buffer:
                        sub_chunks.append("\n\n".join(current_buffer))
                    current_buffer = [p_clean]
                    current_word_count = p_words
            if current_buffer:
                sub_chunks.append("\n\n".join(current_buffer))

    # Form final KnowledgeChunk objects
    for idx, text_content in enumerate(sub_chunks, start=1):
        chunk_words = len(text_content.split())
        if chunk_words < 5:  # skip trivial stubs
            continue
        chunk = KnowledgeChunk(
            chunk_id=f"{doc_id}_chk_{idx:02d}",
            document_id=doc_id,
            title=title,
            category=category,
            department=dept,
            source=source,
            text=text_content,
            word_count=chunk_words,
        )
        chunks.append(chunk)

    return chunks
