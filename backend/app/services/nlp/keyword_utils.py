"""
Deterministic keyword, lemma, and phrase utility functions.
Maintains curated dictionaries for bilingual municipal domain vocabulary without ML.
"""

from typing import List, Set, Dict

# English non-critical stopwords (preserves negation words like 'no', 'not', 'never', 'none')
ENGLISH_STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
    "by", "of", "from", "as", "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "this", "that", "these", "those",
    "it", "its", "there", "their", "please", "kindly", "sir", "madam", "dear",
    "regarding", "about", "respectfully", "urgently", "i", "we", "my", "our",
}

# Marathi non-critical stopwords (preserves negation words like 'नाही', 'न', 'नसून')
MARATHI_STOPWORDS: Set[str] = {
    "आहे", "आहेत", "होते", "होती", "होता", "होत्या", "करा", "करावे", "कृपया",
    "व", "आणि", "किंवा", "या", "तो", "ती", "ते", "त्या", "हा", "ही", "हे",
    "मध्ये", "वरून", "कडे", "पासून", "ने", "नी", "साठी", "तर", "पण",
    "माझे", "आमचे", "आपला", "आपली", "आपले", "साहेब", "महोदय",
}

# Deterministic lemma/stemming mapping for municipal keywords (English, Marathi & Transliteration)
MUNICIPAL_LEMMA_MAP: Dict[str, str] = {
    # English lemmas
    "potholes": "pothole",
    "roads": "road",
    "streets": "street",
    "lights": "light",
    "lamps": "lamp",
    "pipes": "pipe",
    "pipelines": "pipeline",
    "leaks": "leak",
    "leaking": "leakage",
    "leakages": "leakage",
    "drains": "drain",
    "drainages": "drainage",
    "sewers": "sewer",
    "sewerages": "sewerage",
    "gutters": "gutter",
    "toilets": "toilet",
    "urinals": "urinal",
    "wires": "wire",
    "cables": "cable",
    "transformers": "transformer",
    "signals": "signal",
    "jams": "jam",
    "traffic jams": "traffic jam",
    "garbages": "garbage",
    "wastes": "waste",
    "bins": "bin",
    "dustbins": "dustbin",
    
    # Marathi lemmas (inflectional suffixes)
    "खड्डे": "खड्डा",
    "खड्ड्यांचे": "खड्डा",
    "खड्ड्यात": "खड्डा",
    "खड्ड्यांमुळे": "खड्डा",
    "रस्ते": "रस्ता",
    "रस्त्याची": "रस्ता",
    "रस्त्यावरील": "रस्ता",
    "रस्त्यावर": "रस्ता",
    "पाणी": "पाणी",
    "पाण्याची": "पाणी",
    "पाण्याचा": "पाणी",
    "पाण्यात": "पाणी",
    "पाण्यामुळे": "पाणी",
    "कचरा": "कचरा",
    "कचऱ्याची": "कचरा",
    "कचऱ्याचे": "कचरा",
    "कचऱ्याचा": "कचरा",
    "कचऱ्यात": "कचरा",
    "कचराकुंडी": "कचराकुंडी",
    "कचराकुंड्या": "कचराकुंडी",
    "दिवे": "दिवा",
    "दिव्याची": "दिवा",
    "दिव्यांचे": "दिवा",
    "पथदिवे": "पथदिवा",
    "पथदिव्याची": "पथदिवा",
    "गळती": "गळती",
    "गळतीची": "गळती",
    "गटारे": "गटार",
    "गटाराचे": "गटार",
    "गटारातील": "गटार",
    "गटारात": "गटार",
    "शौचालये": "शौचालय",
    "शौचालयाची": "शौचालय",
    "शौचालयात": "शौचालय",
    "विज": "वीज",
    "विजेची": "वीज",
    "विजेचे": "वीज",
    "वाहने": "वाहन",
    "वाहनांची": "वाहन",

    # Transliteration lemmas
    "khadde": "khadda",
    "paani": "pani",
    "raste": "rasta",
    "diwe": "diwa",
    "gatare": "gatar",
}


def lemmatize_token(token: str) -> str:
    """Returns canonical base form for municipal terminology."""
    return MUNICIPAL_LEMMA_MAP.get(token.lower(), token.lower())


def filter_stopwords(tokens: List[str]) -> List[str]:
    """Filters non-critical stopwords while preserving complaint indicators."""
    combined_stopwords = ENGLISH_STOPWORDS | MARATHI_STOPWORDS
    return [t for t in tokens if t.lower() not in combined_stopwords]


def match_phrases(text: str, candidate_phrases: List[str]) -> List[str]:
    """
    Finds exact substring matches for candidate multi-word phrases.
    Deterministic and case-insensitive.
    """
    lower_text = f" {text.lower()} "
    matches = []
    for phrase in candidate_phrases:
        pattern = f" {phrase.lower()} "
        if pattern in lower_text or phrase.lower() in text.lower():
            matches.append(phrase)
    return matches
