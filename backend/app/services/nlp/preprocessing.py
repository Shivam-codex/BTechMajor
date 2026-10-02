"""
Deterministic NLP Preprocessing Pipeline.
Processes citizen complaint text across English, Marathi, and mixed dialects.
Preserves original input while extracting structured tokens, n-grams, and canonical lemmas.
"""

from typing import List, Set
from dataclasses import dataclass, field
from backend.app.services.nlp.normalization import clean_text
from backend.app.services.nlp.tokenizer import (
    detect_language,
    tokenize_words,
    split_sentences,
    generate_ngrams,
    extract_all_phrases,
)
from backend.app.services.nlp.keyword_utils import (
    lemmatize_token,
    filter_stopwords,
)


@dataclass
class NLPPreprocessedResult:
    original_text: str
    normalized_text: str
    language: str  # "en", "mr", "mixed"
    tokens: List[str] = field(default_factory=list)
    filtered_tokens: List[str] = field(default_factory=list)
    lemmatized_tokens: List[str] = field(default_factory=list)
    bigrams: List[str] = field(default_factory=list)
    trigrams: List[str] = field(default_factory=list)
    all_phrases: List[str] = field(default_factory=list)
    sentences: List[str] = field(default_factory=list)
    word_count: int = 0
    token_set: Set[str] = field(default_factory=set)
    lemmatized_set: Set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "language": self.language,
            "tokens": self.tokens,
            "filtered_tokens": self.filtered_tokens,
            "lemmatized_tokens": self.lemmatized_tokens,
            "bigrams": self.bigrams,
            "trigrams": self.trigrams,
            "sentences": self.sentences,
            "word_count": self.word_count,
        }


def preprocess_complaint(text: str) -> NLPPreprocessedResult:
    """
    Main deterministic preprocessing entry point.
    1. Preserves original raw text.
    2. Cleans and normalizes unicode and whitespace.
    3. Detects language (English, Marathi, or code-mixed).
    4. Tokenizes into words and sentences.
    5. Filters stopwords while retaining sentiment/negation.
    6. Generates canonical lemmas and n-grams.
    """
    if not text:
        text = ""

    # Preserve exact raw complaint
    original = text

    # Normalization
    cleaned = clean_text(text)

    # Language Identification
    lang = detect_language(cleaned)

    # Word and Sentence tokenization
    tokens = tokenize_words(cleaned, lowercase=True)
    sentences = split_sentences(cleaned)

    # Stopword filtering
    filtered = filter_stopwords(tokens)

    # Lemmatization for canonical municipal matching
    lemmatized = [lemmatize_token(t) for t in tokens]
    filtered_lemmatized = [lemmatize_token(t) for t in filtered]

    # N-gram generation for phrase matching
    bigrams = generate_ngrams(tokens, 2)
    trigrams = generate_ngrams(tokens, 3)
    all_phrases = extract_all_phrases(tokens, max_n=3)

    return NLPPreprocessedResult(
        original_text=original,
        normalized_text=cleaned,
        language=lang,
        tokens=tokens,
        filtered_tokens=filtered,
        lemmatized_tokens=lemmatized,
        bigrams=bigrams,
        trigrams=trigrams,
        all_phrases=all_phrases,
        sentences=sentences,
        word_count=len(tokens),
        token_set=set(tokens),
        lemmatized_set=set(lemmatized) | set(filtered_lemmatized),
    )
