"""
Security and file handling utilities.
Implements filename sanitization and safe file checks.
"""

import os
import re
import unicodedata
from pathlib import Path
from typing import Tuple
from backend.app.utils.constants import ALLOWED_FILE_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and filesystem attacks.
    Removes path separators, null bytes, and unsafe characters.
    """
    if not filename:
        return "unnamed_document.txt"

    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename)
    
    # Strip any directory path components (both / and \)
    filename = os.path.basename(filename)
    filename = filename.replace("/", "").replace("\\", "").replace("\x00", "")

    # Retain stem and extension
    path_obj = Path(filename)
    extension = path_obj.suffix.lower()
    stem = path_obj.stem

    # Remove non-alphanumeric except safe symbols (dash, underscore)
    safe_stem = re.sub(r"[^a-zA-Z0-9_\- ]", "_", stem).strip()
    if not safe_stem:
        safe_stem = "uploaded_document"

    # Limit stem length
    safe_stem = safe_stem[:100]

    return f"{safe_stem}{extension}"


def validate_file_metadata(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    Validates file extension and size before processing.
    """
    if file_size <= 0:
        return False, "File is empty (0 bytes)."

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {max_mb} MB."

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))
        return False, f"Unsupported file extension '{ext}'. Allowed extensions: {allowed}."

    return True, "Valid"
