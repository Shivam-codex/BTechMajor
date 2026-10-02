"""
Classical TF-IDF Information Retrieval Engine.
Uses deterministic TfidfVectorizer (unigram + bigram) and cosine similarity to index
and rank knowledge-base chunks against citizen inquiries.
ZERO MACHINE LEARNING — purely statistical lexical frequencies.
"""

import pickle
from pathlib import Path
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.services.knowledge.chunker import KnowledgeChunk
from backend.app.core.config import settings
from backend.app.core.logging import logger


class TFIDFRetriever:
    """
    Classical non-ML Information Retriever using Term Frequency - Inverse Document Frequency.
    """

    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.chunks: List[KnowledgeChunk] = []

    def build_index(self, chunks: List[KnowledgeChunk]):
        """
        Builds the TF-IDF representation across all knowledge chunk texts.
        Uses sublinear term frequency scaling and bigram capture.
        """
        if not chunks:
            raise ValueError("Cannot build TF-IDF index with empty chunks list.")

        from backend.app.services.nlp.keyword_utils import ENGLISH_STOPWORDS

        self.chunks = chunks
        corpus = [f"{c.title} {c.category} {c.department} {c.text}" for c in chunks]

        # Strictly deterministic mathematical vectorizer with stop words
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            lowercase=True,
            stop_words=list(ENGLISH_STOPWORDS),
            max_df=0.90,
            min_df=1,
            token_pattern=r"(?u)\b[\w\u0900-\u097F]+\b",  # Supports Devanagari and Latin words
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        logger.info(f"Built TF-IDF index: {self.tfidf_matrix.shape[0]} documents, {self.tfidf_matrix.shape[1]} features.")

    def save_index(self, index_dir: Path = None):
        """Persists the vocabulary, IDF vector, and chunk metadata locally."""
        if index_dir is None:
            index_dir = settings.INDEX_DIR
        index_dir.mkdir(parents=True, exist_ok=True)

        index_file = index_dir / "tfidf_index.pkl"
        payload = {
            "vectorizer": self.vectorizer,
            "tfidf_matrix": self.tfidf_matrix,
            "chunks": self.chunks,
        }
        with open(index_file, "wb") as f:
            pickle.dump(payload, f)
        logger.info(f"Saved TF-IDF index to {index_file}")

    def load_index(self, index_dir: Path = None) -> bool:
        """Loads serialized TF-IDF index from disk."""
        if index_dir is None:
            index_dir = settings.INDEX_DIR

        index_file = index_dir / "tfidf_index.pkl"
        if not index_file.exists():
            return False

        try:
            with open(index_file, "rb") as f:
                payload = pickle.load(f)
            self.vectorizer = payload["vectorizer"]
            self.tfidf_matrix = payload["tfidf_matrix"]
            self.chunks = payload["chunks"]
            logger.info(f"Loaded TF-IDF index with {len(self.chunks)} chunks.")
            return True
        except Exception as e:
            logger.error(f"Failed to load TF-IDF index: {e}")
            return False

    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Calculates cosine similarity between user query vector and knowledge chunk vectors.
        Returns top-K matching chunks paired with their similarity score in [0.0, 1.0].
        """
        if not self.is_ready():
            return []

        query_clean = query_text.strip()
        if not query_clean:
            return []

        # Vectorize incoming query
        query_vector = self.vectorizer.transform([query_clean])
        # Compute cosine similarities deterministically
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]

        # Rank indices descending by similarity
        ranked_indices = similarities.argsort()[::-1]

        results: List[Tuple[KnowledgeChunk, float]] = []
        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            results.append((self.chunks[idx], round(score, 4)))

        return results

    def is_ready(self) -> bool:
        return self.vectorizer is not None and self.tfidf_matrix is not None and len(self.chunks) > 0


# Singleton retriever instance
tfidf_retriever = TFIDFRetriever()
