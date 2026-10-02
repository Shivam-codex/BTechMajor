"""
Metadata extraction and management for knowledge base documents.
Parses structured header blocks and attaches verified academic attributions.
"""

import re
from typing import Dict, Tuple

HEADER_PATTERN = re.compile(
    r"^DOCUMENT ID:\s*(?P<id>.*)\n"
    r"TITLE:\s*(?P<title>.*)\n"
    r"CATEGORY:\s*(?P<category>.*)\n"
    r"DEPARTMENT:\s*(?P<department>.*)\n"
    r"SOURCE:\s*(?P<source>.*)\n",
    re.MULTILINE,
)


def extract_document_metadata(raw_text: str, fallback_title: str) -> Tuple[Dict[str, str], str]:
    """
    Extracts metadata dictionary and body content from document text.
    """
    match = HEADER_PATTERN.search(raw_text)
    if match:
        meta = {
            "document_id": match.group("id").strip(),
            "title": match.group("title").strip(),
            "category": match.group("category").strip(),
            "department": match.group("department").strip(),
            "source": match.group("source").strip(),
        }
        # Body text starts after the end of header boundary
        parts = raw_text.split("================================================================================")
        body = parts[-1].strip() if len(parts) >= 3 else raw_text[match.end():].strip()
        return meta, body

    # Fallback if standard header not present
    meta = {
        "document_id": "KB-GENERIC",
        "title": fallback_title.replace("_", " ").replace(".txt", ""),
        "category": "Other",
        "department": "General Grievance Cell",
        "source": "Sample Municipal Knowledge Base – Academic Project",
    }
    return meta, raw_text.strip()
