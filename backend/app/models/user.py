"""
User SQLAlchemy Model for Role-Based Authentication.
Supports Citizen self-service and Municipal Administrator roles.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(32), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), default="CITIZEN", nullable=False, index=True)  # "CITIZEN", "ADMIN"
    department = Column(String(128), nullable=True)  # For municipal officials, e.g. "Water Supply Department"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    complaints = relationship("Complaint", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_super_admin(self) -> bool:
        """Determines if the user possesses Super Administrator privileges."""
        if self.role == "SUPER_ADMIN":
            return True
        if self.role == "ADMIN":
            if self.email in ("admin@smartcity.gov", "test_admin@smartcity.gov"):
                return True
            if self.department in ("General Grievance Cell", "Super Admin", "Administration"):
                return True
        return False

    def to_dict(self):
        """Convert user model to dictionary (excluding sensitive password hash)."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "department": self.department,
            "is_super_admin": self.is_super_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
