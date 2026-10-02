"""Extraction services for PDF, DOCX, and TXT documents."""

from backend.app.services.extraction.document_service import extract_document_text

__all__ = ["extract_document_text"]
