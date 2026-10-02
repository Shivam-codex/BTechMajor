"""
TXT Document Extractor.
Extracts text from plain text files with automatic multi-encoding fallback
(UTF-8, UTF-16, Latin-1, CP1252) to handle multilingual Devanagari and English content.
"""

from typing import Tuple, List

ENCODINGS = ["utf-8", "utf-16", "cp1252", "latin-1"]


def extract_text_from_txt(file_bytes: bytes) -> Tuple[bool, str, List[str], str]:
    """
    Extract text from plain text file bytes.
    Returns: (success, raw_text, paragraphs, error_message)
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "", [], "Empty TXT file provided."

    decoded_text = ""
    for enc in ENCODINGS:
        try:
            decoded_text = file_bytes.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if not decoded_text:
        return False, "", [], "Unable to decode text file with supported encodings."

    # Normalize line endings
    normalized = decoded_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return False, "", [], "TXT file contains no text after cleaning."

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in normalized.split("\n") if line.strip()]

    return True, normalized, paragraphs, ""
