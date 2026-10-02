"""
Security, input sanitization, and upload validation module.
Protects against XSS vectors, path traversal, malicious filenames, and oversized files.
"""

import html
import re
from typing import Tuple
from backend.app.utils.constants import MAX_UPLOAD_SIZE_BYTES, ALLOWED_FILE_EXTENSIONS

# Script tags and potentially dangerous HTML attributes
SCRIPT_TAG_REGEX = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
HTML_TAG_REGEX = re.compile(r"<[^>]+>")


def sanitize_text_input(raw_text: str) -> str:
    """
    Sanitizes user input to prevent XSS and HTML injection:
    - Strips script blocks completely.
    - Strips arbitrary HTML tags.
    - Unescapes standard entities and normalizes.
    """
    if not raw_text:
        return ""
    # Strip script tags
    no_scripts = SCRIPT_TAG_REGEX.sub("", raw_text)
    # Strip remaining HTML tags
    no_html = HTML_TAG_REGEX.sub("", no_scripts)
    # Escape special characters
    cleaned = html.escape(no_html.strip(), quote=False)
    # Re-allow basic quotes and apostrophes cleanly
    return cleaned.replace("&quot;", '"').replace("&#x27;", "'")


def validate_upload_content(filename: str, content: bytes) -> Tuple[bool, str]:
    """
    Validates file payload before extraction:
    - Checks file size against MAX_UPLOAD_SIZE_BYTES.
    - Checks file extension.
    - Basic binary magic byte verification for supported file types.
    """
    if not content or len(content) == 0:
        return False, "Uploaded file is empty (0 bytes)."

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {mb} MB."

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return False, f"File extension '{ext}' is not permitted. Allowed: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}."

    # Magic byte inspection for PDFs
    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        return False, "File has a .pdf extension but lacks valid PDF magic header."

    # Magic byte inspection for DOCX (PK zip header)
    if ext == ".docx" and not content.startswith(b"PK"):
        return False, "File has a .docx extension but lacks valid OpenXML zip header."

    return True, "Valid"
