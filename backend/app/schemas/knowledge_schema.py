"""
Pydantic schemas for municipal knowledge base documents and chunks.
"""

from typing import List
from pydantic import BaseModel, ConfigDict


class KnowledgeDocumentSummary(BaseModel):
    document_id: str
    title: str
    category: str
    department: str
    source: str
    chunk_count: int

    model_config = ConfigDict(from_attributes=True)


class KnowledgeChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    category: str
    department: str
    source: str
    text: str
    word_count: int

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentDetail(BaseModel):
    document_id: str
    title: str
    category: str
    department: str
    source: str
    chunk_count: int
    chunks: List[KnowledgeChunkResponse]

    model_config = ConfigDict(from_attributes=True)
