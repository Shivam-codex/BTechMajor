"""
Deterministic Response Generator for the Municipal Assistant.
Assembles accurate, explainable citizen responses exclusively from retrieved knowledge chunks.
ZERO MACHINE LEARNING / NO GENERATIVE LLM.
"""

from typing import List, Dict, Any
from backend.app.services.retrieval.ranking import RetrievalResult


def format_deterministic_response(
    query: str,
    retrieved_chunks: List[RetrievalResult],
) -> Dict[str, Any]:
    """
    Synthesizes a transparent, fact-based response purely from retrieved knowledge chunks.
    If no chunks meet the relevance threshold, returns a safe out-of-domain fallback.
    """
    if not retrieved_chunks:
        return {
            "answer": (
                "I could not find sufficient information about this question in the "
                "Sample Municipal Knowledge Base. Please contact the General Grievance Cell "
                "or call the Central Municipal Helpline at 1800-233-0001 (Toll-Free, 24/7)."
            ),
            "sources": [],
            "retrieved_chunks": [],
            "confidence": 0.0,
            "has_answer": False,
        }

    top_chunk = retrieved_chunks[0]

    # Synthesize factual response from top matching chunks
    paragraphs: List[str] = []
    paragraphs.append(
        f"According to the **Sample Municipal Knowledge Base** "
        f"(*{top_chunk.title}*, {top_chunk.department}):\n"
    )

    # Add core content from primary chunk
    paragraphs.append(top_chunk.text)

    # If a distinct secondary document provides additional context, append it
    if len(retrieved_chunks) > 1:
        secondary_chunk = retrieved_chunks[1]
        if secondary_chunk.document_id != top_chunk.document_id and secondary_chunk.score >= 0.15:
            paragraphs.append(
                f"\n**Additional Information from {secondary_chunk.title} ({secondary_chunk.department}):**\n"
                f"{secondary_chunk.text}"
            )

    # Format sources for academic transparency
    sources_summary = []
    seen_docs = set()
    for chunk in retrieved_chunks:
        if chunk.document_id not in seen_docs:
            sources_summary.append({
                "document_id": chunk.document_id,
                "title": chunk.title,
                "category": chunk.category,
                "department": chunk.department,
                "score": chunk.score,
                "source": chunk.source,
            })
            seen_docs.add(chunk.document_id)

    full_answer = "\n".join(paragraphs)

    return {
        "answer": full_answer,
        "sources": sources_summary,
        "retrieved_chunks": [c.to_dict() for c in retrieved_chunks],
        "confidence": top_chunk.score,
        "has_answer": True,
    }
