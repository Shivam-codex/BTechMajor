"""
Pydantic Schemas for Authentication and Authorization.
Supports Citizen Registration, Authentication, and Token responses.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=128, description="Citizen full name")
    email: str = Field(..., pattern=EMAIL_REGEX, description="Unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Account password (min 6 characters)")
    phone: Optional[str] = Field(None, max_length=32, description="Optional phone contact number")


class UserLoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    role: str
    department: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
