"""
Unit tests for Classical Non-ML Information Retrieval (TF-IDF & BM25).
Verifies index integrity, cosine similarity ranking, and threshold filtering.
"""

from backend.app.services.knowledge.knowledge_loader import load_and_chunk_knowledge_base
from backend.app.services.retrieval.tfidf_retriever import TFIDFRetriever
from backend.app.services.retrieval.bm25_retriever import BM25Retriever
from backend.app.services.retrieval.ranking import retrieve_relevant_chunks


def test_knowledge_base_loading():
    chunks = load_and_chunk_knowledge_base()
    assert len(chunks) >= 14
    for c in chunks:
        assert c.chunk_id is not None
        assert c.document_id is not None
        assert c.title is not None
        assert c.category is not None
        assert c.department is not None
        assert c.source == "Sample Municipal Knowledge Base – Academic Project"
        assert len(c.text) > 20


def test_tfidf_retriever_query():
    retriever = TFIDFRetriever()
    chunks = load_and_chunk_knowledge_base()
    retriever.build_index(chunks)

    results = retriever.query("How to report a pothole on road?", top_k=3)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert score > 0.15
    assert any(term in top_chunk.title.lower() for term in ["road", "pothole", "faq"])


def test_bm25_retriever_query():
    bm25 = BM25Retriever()
    chunks = load_and_chunk_knowledge_base()
    bm25.build_index(chunks)

    results = bm25.query("drinking water pipeline leakage", top_k=3)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert score > 0.0
    assert any(term in (top_chunk.title + " " + top_chunk.text).lower() for term in ["water", "pipeline", "leak"])
    assert any(any(term in chunk.title.lower() for term in ["water", "supply", "responsibilities"]) for chunk, _ in results)


def test_retrieve_relevant_chunks_threshold_filtering():
    # Relevant query returns matches
    matches = retrieve_relevant_chunks("garbage truck collection schedule", top_k=3, threshold=0.10)
    assert len(matches) > 0
    assert any("garbage" in m.title.lower() for m in matches)

    # Completely irrelevant query should be filtered out by threshold
    nonsense_matches = retrieve_relevant_chunks("how to bake a chocolate cake in oven", top_k=3, threshold=0.20)
    assert len(nonsense_matches) == 0
