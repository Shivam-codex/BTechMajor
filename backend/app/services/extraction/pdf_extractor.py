"""
PDF Document Extractor.
Extracts text and tables from PDF documents using pdfplumber with fallback to pypdf
and multimodal OCR fallback for scanned PDF documents.
Preserves paragraph structures and eliminates excessive whitespace.
"""

import os
import io
from typing import Tuple, List
import pdfplumber
import pypdf
from backend.app.core.config import settings


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[bool, str, List[str], str]:
    """
    Extract text and structured paragraphs from PDF file bytes.
    Returns: (success, raw_text, paragraphs, error_message)
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "", [], "Empty PDF file provided."

    paragraphs: List[str] = []
    extracted_text_chunks: List[str] = []
    has_pages = False

    # Attempt extraction via pdfplumber (text + tables)
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                return False, "", [], "PDF file contains no pages."
            has_pages = True

            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text_chunks.append(page_text)
                    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                    if lines:
                        paragraphs.append("\n".join(lines))

                # Also extract any embedded tables on the page
                try:
                    tables = page.extract_tables() or []
                    for tbl in tables:
                        for row in tbl:
                            if row:
                                row_cells = [str(cell).strip() for cell in row if cell and str(cell).strip()]
                                if row_cells:
                                    row_line = " | ".join(row_cells)
                                    if row_line not in page_text if page_text else True:
                                        extracted_text_chunks.append(row_line)
                                        paragraphs.append(row_line)
                except Exception:
                    pass

        raw_text = "\n\n".join(extracted_text_chunks).strip()
        if raw_text:
            return True, raw_text, paragraphs, ""

    except Exception as e:
        # Fallback to pypdf on pdfplumber failure
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            if reader.is_encrypted:
                return False, "", [], "PDF is encrypted/password protected."
            if len(reader.pages) > 0:
                has_pages = True

            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    extracted_text_chunks.append(txt)
                    paragraphs.append(txt.strip())

            raw_text = "\n\n".join(extracted_text_chunks).strip()
            if raw_text:
                return True, raw_text, paragraphs, ""
            if not has_pages:
                return False, "", [], f"No text could be extracted from PDF: {str(e)}"
        except Exception as fallback_err:
            return False, "", [], f"Failed to extract PDF text: {str(fallback_err)}"

    # If the PDF is valid and has pages, but contains scanned images instead of selectable text
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if has_pages and api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            pdf_part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
            prompt = (
                "Extract all readable text, headings, tables, and civic grievance details from this PDF document. "
                "Preserve the original language (English, Marathi, or Hindi)."
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL or "gemini-2.5-flash",
                contents=[pdf_part, prompt],
            )
            if response and response.text and response.text.strip():
                ocr_text = response.text.strip()
                paras = [p.strip() for p in ocr_text.split("\n\n") if p.strip()]
                return True, ocr_text, paras, ""
        except Exception:
            pass

    return False, "", [], "PDF contains no readable text."
