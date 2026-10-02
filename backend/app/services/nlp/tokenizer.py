"""
Deterministic tokenizer for English, Marathi (Devanagari), and code-mixed scripts.
Extracts words, sentences, n-grams, and detects script ratios without ML.
"""

import re
from typing import List, Tuple

# Regex to capture Latin words, numbers, and Devanagari character sequences
# \u0900-\u097F covers the Unicode Devanagari block
WORD_REGEX = re.compile(r"[\u0900-\u097Fa-zA-Z0-9]+(?:[-_][\u0900-\u097Fa-zA-Z0-9]+)*", re.UNICODE)

# Sentence terminators: English . ! ? and Marathi danda । (U+0964)
SENTENCE_SPLIT_REGEX = re.compile(r"[.!?।\n]+", re.UNICODE)

# Devanagari character range check
DEVANAGARI_CHAR_REGEX = re.compile(r"[\u0900-\u097F]")
LATIN_CHAR_REGEX = re.compile(r"[a-zA-Z]")


def detect_language(text: str) -> str:
    """
    Deterministically detects whether text is:
    - 'mr' (predominantly Marathi / Devanagari script)
    - 'en' (predominantly English / Latin script)
    - 'mixed' (code-mixed Marathi-English, transliterated, or bilingual grievance)
    """
    if not text:
        return "en"

    devanagari_count = len(DEVANAGARI_CHAR_REGEX.findall(text))
    latin_count = len(LATIN_CHAR_REGEX.findall(text))
    total_letters = devanagari_count + latin_count

    if total_letters == 0:
        return "en"

    devanagari_ratio = devanagari_count / total_letters
    latin_ratio = latin_count / total_letters

    if devanagari_ratio > 0.60:
        return "mr"
    elif latin_ratio > 0.85:
        # Check for Marathi transliteration keywords in latin text (e.g. "khadde", "paani", "kachra")
        lower_text = text.lower()
        transliterated_markers = ["khadda", "khadde", "paani", "pani", "kachra", "rasta", "nighala", "nahi", "yeu", "galli"]
        if any(marker in lower_text for marker in transliterated_markers):
            return "mixed"
        return "en"
    else:
        return "mixed"


def tokenize_words(text: str, lowercase: bool = True) -> List[str]:
    """
    Deterministically tokenizes text into word tokens.
    Handles both Latin and Devanagari scripts seamlessly.
    """
    if not text:
        return []
    if lowercase:
        text = text.lower()
    return WORD_REGEX.findall(text)


def split_sentences(text: str) -> List[str]:
    """
    Splits text into sentences using standard English and Devanagari punctuation.
    """
    if not text:
        return []
    sentences = SENTENCE_SPLIT_REGEX.split(text)
    return [s.strip() for s in sentences if s.strip()]


def generate_ngrams(tokens: List[str], n: int) -> List[str]:
    """
    Generates contiguous n-grams from a list of tokens.
    """
    if n <= 0 or len(tokens) < n:
        return []
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def extract_all_phrases(tokens: List[str], max_n: int = 3) -> List[str]:
    """
    Extracts all unigrams, bigrams, and trigrams for comprehensive phrase matching.
    """
    phrases: List[str] = []
    for n in range(1, max_n + 1):
        phrases.extend(generate_ngrams(tokens, n))
    return phrases
