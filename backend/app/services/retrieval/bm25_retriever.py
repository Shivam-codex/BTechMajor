"""
Pure Python Okapi BM25 Information Retrieval implementation.
Deterministic probabilistic relevance framework without neural networks or embeddings.
"""

import math
from typing import List, Tuple, Dict
from backend.app.services.knowledge.chunker import KnowledgeChunk
from backend.app.services.nlp.tokenizer import tokenize_words
from backend.app.services.nlp.keyword_utils import filter_stopwords


class BM25Retriever:
    """
    Okapi BM25 lexical ranking engine.
    Uses term frequency saturation and document length normalization.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[KnowledgeChunk] = []
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lens: List[int] = []
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}

    def build_index(self, chunks: List[KnowledgeChunk]):
        """Builds term frequency and IDF structures for BM25."""
        if not chunks:
            return

        self.chunks = chunks
        self.corpus_size = len(chunks)
        total_len = 0
        self.doc_lens = []
        self.doc_term_freqs = []
        df: Dict[str, int] = {}

        for chunk in chunks:
            # Emphasize title and category
            full_text = f"{chunk.title} {chunk.title} {chunk.category} {chunk.text}"
            tokens = filter_stopwords(tokenize_words(full_text))
            doc_len = len(tokens)
            self.doc_lens.append(doc_len)
            total_len += doc_len

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freqs.append(tf)

            for term in tf.keys():
                df[term] = df.get(term, 0) + 1

        self.avg_doc_len = total_len / self.corpus_size if self.corpus_size > 0 else 1.0

        # Calculate Okapi IDF
        self.idf = {}
        for term, freq in df.items():
            idf_val = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))
            self.idf[term] = max(0.01, idf_val)

    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[KnowledgeChunk, float]]:
        """Calculates BM25 score for user query against indexed chunks."""
        if self.corpus_size == 0:
            return []

        raw_tokens = tokenize_words(query_text)
        query_tokens = filter_stopwords(raw_tokens)
        if not query_tokens:
            query_tokens = raw_tokens

        scores: List[float] = [0.0] * self.corpus_size

        for term in query_tokens:
            if term not in self.idf:
                continue
            term_idf = self.idf[term]
            for idx in range(self.corpus_size):
                tf = self.doc_term_freqs[idx].get(term, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lens[idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[idx] += term_idf * (numerator / denominator)

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        results: List[Tuple[KnowledgeChunk, float]] = []
        max_score = max(scores) if scores and max(scores) > 0 else 1.0

        for idx, score in ranked[:top_k]:
            if score <= 0.0:
                continue
            # Normalize BM25 score to [0.0, 1.0] relative to max score
            norm_score = round(min(1.0, score / (max_score + 1e-6)), 4)
            results.append((self.chunks[idx], norm_score))

        return results
