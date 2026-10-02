"""
Complaint SQLAlchemy Model.
Stores grievance details, document metadata, deterministic rule classification,
priority detection, and administrative lifecycle status.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, JSON, DateTime
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, utc_now
from backend.app.utils.constants import (
    ComplaintCategory,
    DepartmentName,
    ComplaintPriority,
    ComplaintStatus,
    SourceType,
)


def generate_complaint_id() -> str:
    """Generate a clean, professional complaint tracking ID (e.g., CMP-2026-AB12CD)."""
    year = datetime.now(timezone.utc).year
    suffix = uuid.uuid4().hex[:6].upper()
    return f"CMP-{year}-{suffix}"


class Complaint(Base, TimestampMixin):
    __tablename__ = "complaints"

    # Primary Tracking ID
    id = Column(String(32), primary_key=True, default=generate_complaint_id, index=True)

    # Core grievance text
    complaint_text = Column(Text, nullable=False)
    extracted_text = Column(Text, nullable=True)

    # Origin document information
    source_file_name = Column(String(255), nullable=True)
    source_type = Column(String(32), default=SourceType.MANUAL.value, nullable=False)
    language = Column(String(16), default="en", nullable=False)  # "en", "mr", "mixed"

    # Deterministic Rule-Based Classification Results
    category = Column(String(64), default=ComplaintCategory.OTHER.value, nullable=False, index=True)
    rule_match_score = Column(Float, default=0.0, nullable=False)
    matched_keywords = Column(JSON, default=list, nullable=False)
    matched_phrases = Column(JSON, default=list, nullable=False)
    classification_reason = Column(Text, nullable=True)

    # Automatic Department Routing
    department = Column(String(128), default=DepartmentName.GENERAL_GRIEVANCE.value, nullable=False, index=True)

    # Deterministic Priority Detection
    priority = Column(String(32), default=ComplaintPriority.MEDIUM.value, nullable=False, index=True)
    priority_reason = Column(Text, nullable=True)

    # Administrative Tracking
    status = Column(String(32), default=ComplaintStatus.SUBMITTED.value, nullable=False, index=True)
    citizen_name = Column(String(128), nullable=True)
    location = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Lifecycle Timestamps
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert model record to dictionary representation."""
        return {
            "id": self.id,
            "complaint_text": self.complaint_text,
            "extracted_text": self.extracted_text,
            "source_file_name": self.source_file_name,
            "source_type": self.source_type,
            "language": self.language,
            "category": self.category,
            "rule_match_score": round(self.rule_match_score, 4),
            "matched_keywords": self.matched_keywords or [],
            "matched_phrases": self.matched_phrases or [],
            "classification_reason": self.classification_reason,
            "department": self.department,
            "priority": self.priority,
            "priority_reason": self.priority_reason,
            "status": self.status,
            "citizen_name": self.citizen_name,
            "location": self.location,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
