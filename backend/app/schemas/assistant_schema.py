"""
Pydantic schemas for the Conversational Municipal Assistant.
Supports structured answer, source explainability, detected intent,
interactive action cards, and quick replies (Amazon/Flipkart style).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ConversationMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class AssistantQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1500, description="Citizen municipal inquiry")
    conversation_history: Optional[List[ConversationMessage]] = Field(
        default=None,
        description="Optional recent chat history for multi-turn conversational context",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "I want to raise a complaint related to electricity",
                "conversation_history": [
                    {"role": "user", "content": "Hi"},
                    {"role": "assistant", "content": "Hello! How can I assist you with municipal services today?"}
                ]
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


class AssistantActionCard(BaseModel):
    label: str
    action_type: str = Field(..., description="'link', 'tel', or 'button'")
    url: str
    icon: Optional[str] = "arrow-right"


class AssistantQueryResponse(BaseModel):
    query: str
    answer: str
    confidence: float
    has_answer: bool
    detected_category: Optional[str] = None
    detected_department: Optional[str] = None
    intent: Optional[str] = None
    sources: List[AssistantSource] = Field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_actions: List[AssistantActionCard] = Field(default_factory=list)
    quick_replies: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
