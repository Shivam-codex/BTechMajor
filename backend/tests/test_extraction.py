"""
Unit tests for document extraction services (PDF, DOCX, TXT).
Verifies parsing accuracy, security checks, and error boundaries.
"""

from backend.app.services.extraction.document_service import extract_document_text
from backend.app.utils.file_utils import sanitize_filename, validate_file_metadata


def test_sanitize_filename_prevents_traversal():
    unsafe_name = "../../etc/passwd/../../../malicious_script.sh.pdf"
    clean = sanitize_filename(unsafe_name)
    assert "/" not in clean
    assert "\\" not in clean
    assert ".." not in clean
    assert clean.endswith(".pdf")


def test_validate_file_metadata():
    # Empty file
    valid, msg = validate_file_metadata("test.txt", 0)
    assert not valid
    assert "empty" in msg.lower()

    # Oversized file (> 10MB)
    valid, msg = validate_file_metadata("large.pdf", 15 * 1024 * 1024)
    assert not valid
    assert "exceeds" in msg.lower()

    # Invalid extension
    valid, msg = validate_file_metadata("malware.exe", 100)
    assert not valid
    assert "unsupported" in msg.lower()

    # Valid file
    valid, msg = validate_file_metadata("complaint.docx", 2048)
    assert valid


def test_extract_txt(sample_txt_bytes):
    res = extract_document_text("pothole_issue.txt", sample_txt_bytes)
    assert res.success
    assert res.source_type == "TXT"
    assert "pothole on MG Road" in res.cleaned_text
    assert res.word_count > 10
    assert len(res.paragraphs) >= 1


def test_extract_marathi_txt(sample_marathi_txt_bytes):
    res = extract_document_text("water_issue.txt", sample_marathi_txt_bytes)
    assert res.success
    assert res.source_type == "TXT"
    assert "पाणी पुरवठा" in res.cleaned_text
    assert res.char_count > 20


def test_extract_docx(sample_docx_bytes):
    res = extract_document_text("garbage_complaint.docx", sample_docx_bytes)
    assert res.success
    assert res.source_type == "DOCX"
    assert "Overflowing Garbage" in res.cleaned_text
    assert "Shivaji Nagar" in res.cleaned_text  # Extracted from table
    assert res.word_count > 15


def test_extract_pdf(sample_pdf_bytes):
    res = extract_document_text("street_light.pdf", sample_pdf_bytes)
    assert res.success
    assert res.source_type == "PDF"
    assert "Street lights" in res.cleaned_text
    assert res.word_count > 5


def test_extract_corrupted_file():
    corrupted_bytes = b"Corrupted broken bytes not matching pdf binary format"
    res = extract_document_text("bad.pdf", corrupted_bytes)
    assert not res.success
    assert res.error is not None
