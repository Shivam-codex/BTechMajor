"""
Knowledge Base Inspection API.
Allows citizens and administrators to inspect municipal procedures and document chunks.
"""

from typing import List, Dict
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.knowledge_schema import (
    KnowledgeDocumentSummary,
    KnowledgeDocumentDetail,
    KnowledgeChunkResponse,
)
from backend.app.services.knowledge.knowledge_loader import load_and_chunk_knowledge_base

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


@router.get(
    "/documents",
    response_model=List[KnowledgeDocumentSummary],
    summary="List all official municipal knowledge base documents",
)
def list_knowledge_documents():
    """
    Returns summaries of all 14 ingested municipal guideline documents.
    """
    chunks = load_and_chunk_knowledge_base()
    docs: Dict[str, dict] = {}

    for c in chunks:
        if c.document_id not in docs:
            docs[c.document_id] = {
                "document_id": c.document_id,
                "title": c.title,
                "category": c.category,
                "department": c.department,
                "source": c.source,
                "chunk_count": 0,
            }
        docs[c.document_id]["chunk_count"] += 1

    return list(docs.values())


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentDetail,
    summary="Get full document text and individual chunks",
)
def get_knowledge_document(document_id: str):
    """
    Returns document details along with all indexed semantic chunks.
    """
    chunks = load_and_chunk_knowledge_base()
    matching_chunks = [c for c in chunks if c.document_id.upper() == document_id.upper()]

    if not matching_chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with ID '{document_id}' not found.",
        )

    first = matching_chunks[0]
    return KnowledgeDocumentDetail(
        document_id=first.document_id,
        title=first.title,
        category=first.category,
        department=first.department,
        source=first.source,
        chunk_count=len(matching_chunks),
        chunks=[KnowledgeChunkResponse(**c.to_dict()) for c in matching_chunks],
    )
