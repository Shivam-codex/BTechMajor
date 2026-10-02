"""
Unified Ranking and Retrieval Coordinator.
Retrieves and ranks relevant knowledge-base chunks against incoming inquiries using TF-IDF.
Ensures explainability, source attribution, and threshold filtering.
"""

from typing import List
from dataclasses import dataclass
from backend.app.services.retrieval.tfidf_retriever import tfidf_retriever
from backend.app.services.knowledge.knowledge_loader import load_and_chunk_knowledge_base
from backend.app.core.config import settings
from backend.app.core.logging import log_event


@dataclass
class RetrievalResult:
    chunk_id: str
    document_id: str
    title: str
    category: str
    department: str
    source: str
    score: float
    text: str

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "category": self.category,
            "department": self.department,
            "source": self.source,
            "score": self.score,
            "text": self.text,
        }


def initialize_retriever_if_needed():
    """Ensures the TF-IDF retriever index is loaded or constructed."""
    if not tfidf_retriever.is_ready():
        # Attempt to load from disk
        loaded = tfidf_retriever.load_index()
        if not loaded:
            # Build dynamically from knowledge base directory
            chunks = load_and_chunk_knowledge_base()
            if chunks:
                tfidf_retriever.build_index(chunks)
                tfidf_retriever.save_index()


def retrieve_relevant_chunks(
    query: str,
    top_k: int = None,
    threshold: float = None,
) -> List[RetrievalResult]:
    """
    Ranks knowledge chunks against query using TF-IDF cosine similarity.
    Requires minimum similarity threshold AND minimum lexical query term coverage.
    """
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K
    if threshold is None:
        threshold = settings.SIMILARITY_THRESHOLD

    initialize_retriever_if_needed()

    raw_matches = tfidf_retriever.query(query, top_k=top_k)

    # Tokenize meaningful non-stopword query tokens for coverage check
    from backend.app.services.nlp.tokenizer import tokenize_words
    from backend.app.services.nlp.keyword_utils import filter_stopwords

    query_tokens = filter_stopwords(tokenize_words(query))
    total_query_tokens = len(query_tokens)

    results: List[RetrievalResult] = []
    for chunk, score in raw_matches:
        if score >= threshold:
            # Check lexical term coverage
            chunk_corpus = f"{chunk.title} {chunk.category} {chunk.department} {chunk.text}".lower()
            if total_query_tokens > 1:
                matched_terms = [t for t in query_tokens if t in chunk_corpus]
                coverage = len(matched_terms) / total_query_tokens
                # If less than 30% of content words match and score is low, discard as incidental overlap
                if coverage < 0.30 and score < 0.25:
                    continue

            results.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    category=chunk.category,
                    department=chunk.department,
                    source=chunk.source,
                    score=score,
                    text=chunk.text,
                )
            )

    log_event("RETRIEVAL_EXECUTED", {
        "query_length": len(query),
        "matches_found": len(results),
        "top_score": results[0].score if results else 0.0,
    })

    return results
