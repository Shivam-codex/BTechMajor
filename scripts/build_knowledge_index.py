"""
CLI Script to build and persist the Non-ML TF-IDF Knowledge Base Index.
Command:
    python scripts/build_knowledge_index.py

Executes:
1. Load knowledge-base documents from data/knowledge_base/
2. Clean text and parse metadata
3. Chunk documents into cohesive retrieval segments
4. Fit TF-IDF matrix across all chunks
5. Serialize and save index artifacts locally in backend/app/data/index/
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.core.config import settings
from backend.app.services.knowledge.knowledge_loader import load_and_chunk_knowledge_base
from backend.app.services.retrieval.tfidf_retriever import tfidf_retriever


def main():
    print("=" * 70)
    print("  Smart City Municipal Knowledge Base Index Builder (Non-ML TF-IDF)")
    print("=" * 70)

    kb_dir = settings.KNOWLEDGE_BASE_DIR
    index_dir = settings.INDEX_DIR

    print(f"\n[1/4] Scanning knowledge base directory: {kb_dir}")
    chunks = load_and_chunk_knowledge_base(kb_dir)
    if not chunks:
        print(f"ERROR: No knowledge documents found in {kb_dir}!")
        sys.exit(1)

    print(f"      Successfully extracted {len(chunks)} chunks across all documents.")

    print("\n[2/4] Initializing Classical TF-IDF Vectorizer...")
    tfidf_retriever.build_index(chunks)

    print(f"\n[3/4] Persisting index artifacts to {index_dir}...")
    tfidf_retriever.save_index(index_dir)

    print("\n[4/4] Verification check...")
    test_queries = [
        "How to report a pothole?",
        "Water pipeline burst emergency",
        "Garbage collection truck timing",
        "Exposed electrical wire danger",
    ]
    for q in test_queries:
        results = tfidf_retriever.query(q, top_k=2)
        top_match = results[0] if results else None
        if top_match:
            chunk, score = top_match
            print(f"      Q: '{q}' -> [{chunk.title}] (Score: {score})")

    print("\n" + "=" * 70)
    print("  Index build completed successfully! Local index is ready for retrieval.")
    print("=" * 70)


if __name__ == "__main__":
    main()
