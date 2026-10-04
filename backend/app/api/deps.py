"""
FastAPI Dependency Guards for Role-Based Access Control (RBAC).
Provides user authentication, token validation, and role enforcement (Citizen vs. Admin).
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodes JWT Bearer token, validates claims, and retrieves user from database.
    Raises 401 Unauthorized if token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_email: Optional[str] = payload.get("sub")
    user_id: Optional[int] = payload.get("id")

    if not user_email and not user_id:
        raise credentials_exception

    # Query user by email or ID
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(User).filter(User.email == user_email).first()

    if not user or not user.is_active:
        raise credentials_exception

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication guard for endpoints accessible by both guests and authenticated users.
    Returns User if valid token provided; returns None if unauthenticated.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("id")
    user_email = payload.get("sub")

    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    elif user_email:
        user = db.query(User).filter(User.email == user_email, User.is_active == True).first()
    else:
        return None

    return user


def get_current_active_citizen(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verifies that the caller has an active CITIZEN or ADMIN role.
    """
    if current_user.role not in ("CITIZEN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active citizen account required.",
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Strictly verifies that the caller has an active ADMIN role.
    Returns 403 Forbidden for citizen tokens or unauthorized callers.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required. Citizen access forbidden.",
        )
    return current_user
