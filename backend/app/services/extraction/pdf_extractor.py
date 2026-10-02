"""
PDF Document Extractor.
Extracts text from PDF documents using pdfplumber with fallback to pypdf.
Preserves paragraph structures and eliminates excessive whitespace.
"""

import io
from typing import Tuple, List
import pdfplumber
import pypdf


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[bool, str, List[str], str]:
    """
    Extract text and structured paragraphs from PDF file bytes.
    Returns: (success, raw_text, paragraphs, error_message)
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "", [], "Empty PDF file provided."

    paragraphs: List[str] = []
    extracted_text_chunks: List[str] = []

    # Attempt extraction via pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                return False, "", [], "PDF file contains no pages."

            for page_idx, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text_chunks.append(page_text)
                    # Split into logical paragraphs
                    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                    if lines:
                        paragraphs.append("\n".join(lines))

        raw_text = "\n\n".join(extracted_text_chunks).strip()
        if raw_text:
            return True, raw_text, paragraphs, ""

    except Exception as e:
        # Fallback to pypdf on pdfplumber failure
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            if reader.is_encrypted:
                return False, "", [], "PDF is encrypted/password protected."

            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    extracted_text_chunks.append(txt)
                    paragraphs.append(txt.strip())

            raw_text = "\n\n".join(extracted_text_chunks).strip()
            if raw_text:
                return True, raw_text, paragraphs, ""
            return False, "", [], f"No text could be extracted from PDF: {str(e)}"
        except Exception as fallback_err:
            return False, "", [], f"Failed to extract PDF text: {str(fallback_err)}"

    return False, "", [], "PDF contains no readable text."
