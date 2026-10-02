"""
Pydantic schemas for the Non-ML Municipal Assistant.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AssistantQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Citizen municipal inquiry")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How do I report a pothole on my street?"
            }
        }
    )


class AssistantSource(BaseModel):
    document_id: str
    title: str
    category: str
    department: str
    score: float
    source: str


class AssistantQueryResponse(BaseModel):
    query: str
    answer: str
    confidence: float
    has_answer: bool
    sources: List[AssistantSource] = Field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
