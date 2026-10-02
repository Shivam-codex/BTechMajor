"""
Deterministic text normalization module.
Handles Unicode canonical decomposition/composition (NFC/NFKC),
whitespace cleansing, and bilingual punctuation standardization (Devanagari & Latin).
"""

import re
import unicodedata


# Zero-width spaces and invisible characters
ZERO_WIDTH_CHARS = re.compile(r"[\u200B-\u200D\uFEFF]")

# Multiple whitespace pattern
WHITESPACE_PATTERN = re.compile(r"[ \t\f\v]+")
MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def normalize_unicode(text: str) -> str:
    """
    Standardize text to Unicode Normalization Form C (NFC).
    Ensures that composed Devanagari characters (matras, conjuncts) are canonical.
    Strips zero-width characters and invisible joiners where appropriate.
    """
    if not text:
        return ""
    # Strip zero-width characters
    cleaned = ZERO_WIDTH_CHARS.sub("", text)
    # NFC normalization ensures characters and combining diacritics are canonical
    return unicodedata.normalize("NFC", cleaned)


def normalize_whitespace(text: str) -> str:
    """
    Cleans tabs, repetitive spaces, and normalizes newline characters.
    """
    if not text:
        return ""
    # Standardize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces
    text = text.replace("\u00A0", " ")
    # Collapse multiple inline spaces to single space
    lines = [WHITESPACE_PATTERN.sub(" ", line).strip() for line in text.split("\n")]
    # Collapse 3+ newlines to 2 newlines
    combined = "\n".join(lines)
    return MULTIPLE_NEWLINES.sub("\n\n", combined).strip()


def normalize_punctuation(text: str) -> str:
    """
    Normalizes typographic quotes, dashes, and Marathi danda marks.
    Preserves Devanagari danda '।' (U+0964) as a sentence terminator.
    """
    if not text:
        return ""
    # Normalize fancy quotes
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # Normalize dashes
    text = text.replace("—", " - ").replace("–", " - ")
    # Replace double danda with period
    text = text.replace("\u0965", "।")
    return text


def clean_text(text: str) -> str:
    """
    Full text cleaning pipeline combining Unicode, whitespace, and punctuation normalization.
    """
    text = normalize_unicode(text)
    text = normalize_punctuation(text)
    text = normalize_whitespace(text)
    return text
