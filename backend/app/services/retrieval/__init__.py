"""
Classical Non-ML Information Retrieval Package.
Implements TF-IDF + Cosine Similarity and Okapi BM25 retrieval over municipal knowledge chunks.
ZERO MACHINE LEARNING / ZERO VECTOR EMBEDDINGS.
"""

from backend.app.services.retrieval.ranking import retrieve_relevant_chunks, RetrievalResult

__all__ = ["retrieve_relevant_chunks", "RetrievalResult"]
