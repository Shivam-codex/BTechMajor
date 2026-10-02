"""
Non-ML Retrieval-Augmented Municipal Assistant Service.
Processes user questions, executes classical TF-IDF retrieval over knowledge chunks,
and generates structured, grounded answers with full source transparency.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from backend.app.services.nlp.preprocessing import preprocess_complaint
from backend.app.services.retrieval.ranking import retrieve_relevant_chunks
from backend.app.services.assistant.response_generator import format_deterministic_response
from backend.app.core.logging import log_event


@dataclass
class AssistantAnswer:
    query: str
    answer: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    has_answer: bool = False

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "answer": self.answer,
            "sources": self.sources,
            "retrieved_chunks": self.retrieved_chunks,
            "confidence": self.confidence,
            "has_answer": self.has_answer,
        }


def query_municipal_assistant(
    question: str,
    top_k: int = 4,
    threshold: Optional[float] = None,
) -> AssistantAnswer:
    """
    Main interface for citizen assistant queries.
    Pipeline: Question -> NLP Preprocessing -> TF-IDF Retrieval -> Deterministic Response.
    """
    clean_question = (question or "").strip()
    if not clean_question:
        return AssistantAnswer(
            query="",
            answer="Please enter a question regarding municipal procedures or civic services.",
            sources=[],
            retrieved_chunks=[],
            confidence=0.0,
            has_answer=False,
        )

    # 1. Deterministic NLP Preprocessing on user question
    nlp_res = preprocess_complaint(clean_question)

    # 2. Retrieve relevant chunks using classical TF-IDF
    relevant_chunks = retrieve_relevant_chunks(
        query=nlp_res.normalized_text,
        top_k=top_k,
        threshold=threshold,
    )

    # 3. Deterministic response formatting
    response_data = format_deterministic_response(clean_question, relevant_chunks)

    log_event("ASSISTANT_QUERY_ANSWERED", {
        "query": clean_question[:50],
        "has_answer": response_data["has_answer"],
        "confidence": response_data["confidence"],
        "sources_count": len(response_data["sources"]),
    })

    return AssistantAnswer(
        query=clean_question,
        answer=response_data["answer"],
        sources=response_data["sources"],
        retrieved_chunks=response_data["retrieved_chunks"],
        confidence=response_data["confidence"],
        has_answer=response_data["has_answer"],
    )
