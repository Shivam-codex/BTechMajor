"""
Text cleaning utilities for knowledge base documents.
Standardizes Unicode, cleans repetitive whitespace, and removes formatting artifacts.
"""

import re
import unicodedata

MULTIPLE_SPACES = re.compile(r"[ \t]+")
MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def clean_knowledge_text(text: str) -> str:
    """Cleans knowledge text, preserving paragraph and bullet boundaries."""
    if not text:
        return ""
    # Canonical Unicode NFC
    text = unicodedata.normalize("NFC", text)
    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Clean whitespace per line
    lines = [MULTIPLE_SPACES.sub(" ", line).strip() for line in text.split("\n")]
    joined = "\n".join(lines)
    return MULTIPLE_NEWLINES.sub("\n\n", joined).strip()
