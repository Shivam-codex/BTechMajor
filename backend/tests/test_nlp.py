"""
Unit tests for deterministic NLP preprocessing pipeline.
Tests tokenization, normalization, bilingual script detection, and lemma mapping.
"""

from backend.app.services.nlp.normalization import clean_text, normalize_unicode, normalize_whitespace
from backend.app.services.nlp.tokenizer import (
    detect_language,
    tokenize_words,
    split_sentences,
    generate_ngrams,
)
from backend.app.services.nlp.keyword_utils import lemmatize_token, filter_stopwords
from backend.app.services.nlp.preprocessing import preprocess_complaint


def test_unicode_and_whitespace_normalization():
    raw = "Road   potholes \u00A0 are severe.\n\n\n\nDangerous for two-wheelers!"
    cleaned = clean_text(raw)
    assert "  " not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Road potholes are severe." in cleaned


def test_language_detection():
    english_text = "The water pipeline is broken and leaking severely on Main Road."
    marathi_text = "आमच्या भागात पाण्याचा प्रचंड तुटवडा निर्माण झाला आहे."
    mixed_text = "Road var khadde ahet ani street light working nahi aahe."

    assert detect_language(english_text) == "en"
    assert detect_language(marathi_text) == "mr"
    assert detect_language(mixed_text) == "mixed"


def test_tokenization_and_ngrams():
    text = "Severe water leakage on Sinhagad road."
    tokens = tokenize_words(text)
    assert tokens == ["severe", "water", "leakage", "on", "sinhagad", "road"]

    bigrams = generate_ngrams(tokens, 2)
    assert "water leakage" in bigrams
    assert "leakage on" in bigrams


def test_marathi_tokenization_and_danda():
    text = "रस्त्यावर मोठा खड्डा पडला आहे। अपघात होण्याची शक्यता आहे."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    tokens = tokenize_words(text)
    assert "खड्डा" in tokens
    assert "अपघात" in tokens


def test_negation_preservation_in_stopwords():
    tokens = ["there", "is", "no", "water", "and", "light", "is", "not", "working"]
    filtered = filter_stopwords(tokens)
    # Crucial: negation markers 'no' and 'not' must NOT be dropped!
    assert "no" in filtered
    assert "not" in filtered
    assert "the" not in filtered
    assert "is" not in filtered


def test_marathi_negation_preservation():
    tokens = ["पाणी", "येत", "नाही"]
    filtered = filter_stopwords(tokens)
    assert "नाही" in filtered


def test_municipal_lemmatization():
    assert lemmatize_token("potholes") == "pothole"
    assert lemmatize_token("pipes") == "pipe"
    assert lemmatize_token("खड्डे") == "खड्डा"
    assert lemmatize_token("रस्ते") == "रस्ता"
    assert lemmatize_token("दिवे") == "दिवा"


def test_preprocess_complaint_pipeline():
    raw_input = "  Major leakage in water pipeline near building 5. No water supply since 2 days!  "
    result = preprocess_complaint(raw_input)

    assert result.original_text == raw_input  # Original must be intact
    assert result.language == "en"
    assert "water" in result.tokens
    assert "leakage" in result.lemmatized_set
    assert "water supply" in result.all_phrases
    assert result.word_count > 5
