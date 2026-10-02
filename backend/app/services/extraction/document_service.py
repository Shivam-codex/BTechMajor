"""
Unified Document Extraction Service.
Validates file types, sanitizes filenames, and routes to format-specific extractors.
Computes document statistics and paragraph preservation.
"""

from pathlib import Path
from backend.app.schemas.extraction_schema import ExtractionResult
from backend.app.services.extraction.pdf_extractor import extract_text_from_pdf
from backend.app.services.extraction.docx_extractor import extract_text_from_docx
from backend.app.services.extraction.txt_extractor import extract_text_from_txt
from backend.app.utils.file_utils import sanitize_filename, validate_file_metadata
from backend.app.utils.constants import SourceType
from backend.app.core.logging import log_event


def clean_extracted_text(text: str) -> str:
    """
    Cleans raw extracted document text:
    - Normalizes consecutive blank lines to double newlines
    - Removes non-printable control characters (except standard newlines/tabs)
    - Strips leading and trailing whitespace
    """
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines()]
    # Collapse multiple consecutive empty lines into one
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False

    return "\n".join(cleaned_lines).strip()


def extract_document_text(filename: str, file_bytes: bytes) -> ExtractionResult:
    """
    Main extraction interface.
    Accepts original filename and binary content.
    Returns structured ExtractionResult.
    """
    safe_name = sanitize_filename(filename)
    file_size = len(file_bytes) if file_bytes else 0

    # 1. Validation
    is_valid, validation_msg = validate_file_metadata(safe_name, file_size)
    if not is_valid:
        return ExtractionResult(
            success=False,
            source_file_name=safe_name,
            source_type=SourceType.MANUAL.value,
            error=validation_msg,
        )

    ext = Path(safe_name).suffix.lower()

    # 2. Routing to extractor
    if ext == ".pdf":
        source_type = SourceType.PDF.value
        success, raw_text, paragraphs, error_msg = extract_text_from_pdf(file_bytes)
    elif ext == ".docx":
        source_type = SourceType.DOCX.value
        success, raw_text, paragraphs, error_msg = extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        source_type = SourceType.TXT.value
        success, raw_text, paragraphs, error_msg = extract_text_from_txt(file_bytes)
    else:
        return ExtractionResult(
            success=False,
            source_file_name=safe_name,
            source_type=SourceType.MANUAL.value,
            error=f"Unsupported format '{ext}'",
        )

    if not success or not raw_text.strip():
        return ExtractionResult(
            success=False,
            source_file_name=safe_name,
            source_type=source_type,
            error=error_msg or "Failed to extract text from document.",
        )

    # 3. Post-process extracted text
    cleaned = clean_extracted_text(raw_text)
    words = cleaned.split()

    log_event("DOCUMENT_EXTRACTED", {
        "file": safe_name,
        "type": source_type,
        "word_count": len(words),
        "char_count": len(cleaned),
    })

    return ExtractionResult(
        success=True,
        source_file_name=safe_name,
        source_type=source_type,
        raw_text=raw_text,
        cleaned_text=cleaned,
        char_count=len(cleaned),
        word_count=len(words),
        line_count=len(cleaned.splitlines()),
        paragraphs=paragraphs,
        error=None,
    )
