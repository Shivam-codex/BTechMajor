"""
Retrieval-Augmented Conversational Municipal Assistant Service Coordinator.
Orchestrates:
1. User Question -> Intent Recognition & Query Expansion (Flipkart/Amazon style)
2. Classical TF-IDF Retrieval over local municipal knowledge base (data/knowledge_base/)
3. Passing retrieved reference chunks to Google GenAI (gemini-2.5-flash) for fluent, articulate synthesis
4. Returning complete answer alongside transparent source metadata, action cards, and quick replies.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from backend.app.services.nlp.preprocessing import preprocess_complaint
from backend.app.services.retrieval.ranking import retrieve_relevant_chunks, RetrievalResult
from backend.app.services.assistant.intent_and_expansion import detect_user_intent, expand_retrieval_query
from backend.app.services.assistant.response_generator import (
    generate_llm_response,
    format_deterministic_response,
    format_conversational_fallback,
)
from backend.app.core.logging import log_event


@dataclass
class AssistantAnswer:
    query: str
    answer: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    has_answer: bool = False
    detected_category: Optional[str] = None
    detected_department: Optional[str] = None
    intent: Optional[str] = None
    suggested_actions: List[Dict[str, Any]] = field(default_factory=list)
    quick_replies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "answer": self.answer,
            "sources": self.sources,
            "retrieved_chunks": self.retrieved_chunks,
            "confidence": self.confidence,
            "has_answer": self.has_answer,
            "detected_category": self.detected_category,
            "detected_department": self.detected_department,
            "intent": self.intent,
            "suggested_actions": self.suggested_actions,
            "quick_replies": self.quick_replies,
        }


def search_knowledge_base(
    question: str,
    top_k: int = 4,
    threshold: Optional[float] = None,
) -> List[RetrievalResult]:
    """
    Executes classical TF-IDF retrieval against the local knowledge base chunks.
    Applies domain synonym expansion for high recall while preserving deterministic indexing.
    """
    clean_question = (question or "").strip()
    if not clean_question:
        return []

    # Domain query expansion (e.g. 'electricity' -> 'electrical power supply transformer 1912')
    expanded_q = expand_retrieval_query(clean_question)
    nlp_res = preprocess_complaint(expanded_q)

    # Use flexible threshold (0.05 default) to avoid rigid discarding of citizen questions
    eff_threshold = threshold if threshold is not None else 0.05

    return retrieve_relevant_chunks(
        query=nlp_res.normalized_text,
        top_k=top_k,
        threshold=eff_threshold,
    )


def query_municipal_assistant(
    question: str,
    top_k: int = 4,
    threshold: Optional[float] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AssistantAnswer:
    """
    Main conversational interface for citizen assistant inquiries.
    Pipeline:
      1. Intent Recognition & Category Detection (LODGE, TRACK, GREETING, EMERGENCY, PROCEDURAL)
      2. TF-IDF Lexical Retrieval over municipal guidelines chunks with query expansion
      3. Action Card Generation (deep links to lodge complaint, track status, call helpline)
      4. Synthesize articulate answer via Gemini 2.5 Flash (or local platform-grade fallback)
      5. Return structured AssistantAnswer with complete answer, interactive cards, and source transparency.
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
            detected_category=None,
            detected_department=None,
            intent=None,
            suggested_actions=[],
            quick_replies=[],
        )

    # 1. Detect conversational intent, category, and action cards
    intent_info = detect_user_intent(clean_question)
    intent = intent_info.get("intent", "PROCEDURAL_QUERY")
    category = intent_info.get("category")
    department = intent_info.get("department")
    actions = intent_info.get("suggested_actions", [])
    replies = intent_info.get("quick_replies", [])

    # 2. Classical TF-IDF Retrieval with query expansion
    relevant_chunks = search_knowledge_base(clean_question, top_k=top_k, threshold=threshold)

    # If no chunks passed threshold, but category was detected, pull the official charter for that category
    if not relevant_chunks and category:
        from backend.app.services.retrieval.tfidf_retriever import tfidf_retriever
        if tfidf_retriever.is_ready():
            cat_chunks = [c for c in tfidf_retriever.chunks if c.category == category]
            if cat_chunks:
                c = cat_chunks[0]
                relevant_chunks = [
                    RetrievalResult(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        title=c.title,
                        category=c.category,
                        department=c.department,
                        source=c.source,
                        score=0.25,
                        text=c.text,
                    )
                ]

    # Handle out of domain (e.g. poetry, recipes)
    if intent == "OUT_OF_DOMAIN" or (not relevant_chunks and intent not in ["GREETING", "TRACK_STATUS"]):
        fallback_data = format_deterministic_response(clean_question, [], intent_info)
        log_event("ASSISTANT_QUERY_NO_MATCH", {
            "query": clean_question[:60],
            "intent": intent,
            "has_answer": False,
        })
        return AssistantAnswer(
            query=clean_question,
            answer=fallback_data["answer"],
            sources=[],
            retrieved_chunks=[],
            confidence=0.0,
            has_answer=False,
            detected_category=category,
            detected_department=department,
            intent=intent,
            suggested_actions=actions,
            quick_replies=replies,
        )

    # 3. Extract transparent source metadata for academic explainability
    sources_summary: List[Dict[str, Any]] = []
    seen_docs = set()
    for chunk in relevant_chunks:
        c_dict = chunk.to_dict() if hasattr(chunk, "to_dict") else chunk
        doc_id = c_dict.get("document_id")
        if doc_id and doc_id not in seen_docs:
            sources_summary.append({
                "document_id": doc_id,
                "title": c_dict.get("title", ""),
                "category": c_dict.get("category", ""),
                "department": c_dict.get("department", ""),
                "score": round(float(c_dict.get("score", 0.0)), 4),
                "source": c_dict.get("source", ""),
            })
            seen_docs.add(doc_id)

    top_chunk = relevant_chunks[0] if relevant_chunks else None
    top_score = top_chunk.score if top_chunk else (1.0 if intent == "GREETING" else 0.0)

    # 4. Synthesize articulate answer via Gemini 2.5 Flash (or platform-grade local fallback)
    answer_text = generate_llm_response(
        question=clean_question,
        retrieved_chunks=relevant_chunks,
        intent_info=intent_info,
        conversation_history=conversation_history,
    )

    log_event("ASSISTANT_QUERY_ANSWERED", {
        "query": clean_question[:60],
        "intent": intent,
        "category": category,
        "has_answer": True,
        "confidence": top_score,
        "sources_count": len(sources_summary),
    })

    return AssistantAnswer(
        query=clean_question,
        answer=answer_text,
        sources=sources_summary,
        retrieved_chunks=[c.to_dict() if hasattr(c, "to_dict") else c for c in relevant_chunks],
        confidence=top_score,
        has_answer=True,
        detected_category=category,
        detected_department=department,
        intent=intent,
        suggested_actions=actions,
        quick_replies=replies,
    )
