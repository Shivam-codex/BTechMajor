"""Models package export."""

from backend.app.models.base import Base, TimestampMixin
from backend.app.models.complaint import Complaint, generate_complaint_id

__all__ = ["Base", "TimestampMixin", "Complaint", "generate_complaint_id"]
