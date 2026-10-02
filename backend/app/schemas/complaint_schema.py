"""
Pydantic schemas for Complaints, including creation, updates,
filtering queries, and detailed explainable responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.utils.constants import (
    ComplaintCategory,
    DepartmentName,
    ComplaintPriority,
    ComplaintStatus,
    SourceType,
)


class ComplaintCreate(BaseModel):
    complaint_text: str = Field(..., min_length=5, description="Full description of the municipal grievance")
    citizen_name: Optional[str] = Field(None, max_length=128)
    location: Optional[str] = Field(None, max_length=255)
    source_type: SourceType = SourceType.MANUAL
    source_file_name: Optional[str] = None
    extracted_text: Optional[str] = None


class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    department: Optional[DepartmentName] = None
    priority: Optional[ComplaintPriority] = None
    resolution_notes: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: str
    complaint_text: str
    extracted_text: Optional[str] = None
    source_file_name: Optional[str] = None
    source_type: str
    language: str
    category: str
    rule_match_score: float
    matched_keywords: List[str]
    matched_phrases: List[str]
    classification_reason: Optional[str] = None
    department: str
    priority: str
    priority_reason: Optional[str] = None
    status: str
    citizen_name: Optional[str] = None
    location: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ComplaintListResponse(BaseModel):
    total: int
    items: List[ComplaintResponse]
    page: int
    limit: int
