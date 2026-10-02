"""
Pydantic schemas for document text extraction and validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    success: bool
    source_file_name: str
    source_type: str
    raw_text: str = ""
    cleaned_text: str = ""
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    paragraphs: List[str] = Field(default_factory=list)
    error: Optional[str] = None
