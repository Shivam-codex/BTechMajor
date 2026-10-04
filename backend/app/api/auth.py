"""
Authentication REST API Endpoints.
Provides citizen registration, login, and user profile verification.
100% Local Authentication with standard JWT and passlib bcrypt.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    sanitize_text_input,
)
from backend.app.models.user import User
from backend.app.schemas.auth_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new citizen account",
)
def register_citizen(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Registers a new citizen user.
    Role is strictly enforced as 'CITIZEN' (administrators must be provisioned internally).
    """
    clean_email = payload.email.lower().strip()
    clean_name = sanitize_text_input(payload.full_name)
    clean_phone = sanitize_text_input(payload.phone) if payload.phone else None

    # Check for existing account
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash password and create citizen user
    new_user = User(
        full_name=clean_name,
        email=clean_email,
        phone=clean_phone,
        hashed_password=hash_password(payload.password),
        role="CITIZEN",
        department=None,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue access token
    token_claims = {
        "sub": new_user.email,
        "id": new_user.id,
        "role": new_user.role,
        "department": new_user.department,
    }
    access_token = create_access_token(data=token_claims)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Citizen & Administrator Login",
)
def login_user(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates Citizen or Municipal Administrator credentials.
    Returns standard Bearer JWT containing identity, role, and department claims.
    """
    clean_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact municipal support.",
        )

    token_claims = {
        "sub": user.email,
        "id": user.id,
        "role": user.role,
        "department": user.department,
    }
    access_token = create_access_token(data=token_claims)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the authenticated user's profile details.
    """
    return UserResponse.model_validate(current_user)
