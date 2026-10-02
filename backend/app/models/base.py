"""
Base SQLAlchemy declarative mixins for timestamps and audit columns.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from backend.app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
