"""
Unit and Integration tests for Authentication API and Security utilities.
Verifies citizen registration, password hashing, JWT generation, and profile retrieval.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from backend.app.models.user import User


@pytest.fixture
def client(db_session):
    """Test client with overridden database dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_password_hashing():
    """Verify password hashing generates unique hashes and validates plaintext correctly."""
    plain = "SecurePass@123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_creation_and_decoding():
    """Verify JWT access token packaging and payload claims."""
    claims = {
        "sub": "test@smartcity.gov",
        "id": 42,
        "role": "ADMIN",
        "department": "Water Supply Department",
    }
    token = create_access_token(claims)
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "test@smartcity.gov"
    assert decoded["id"] == 42
    assert decoded["role"] == "ADMIN"
    assert decoded["department"] == "Water Supply Department"


def test_register_citizen_success(client, db_session):
    """Verify citizen self-registration creates citizen user and returns valid JWT."""
    payload = {
        "full_name": "Ananya Deshmukh",
        "email": "ananya@example.com",
        "password": "Password@123",
        "phone": "+91 91234 56789",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "ananya@example.com"
    assert data["user"]["full_name"] == "Ananya Deshmukh"
    assert data["user"]["role"] == "CITIZEN"

    # Verify user exists in database with hashed password
    user = db_session.query(User).filter(User.email == "ananya@example.com").first()
    assert user is not None
    assert user.hashed_password != "Password@123"
    assert verify_password("Password@123", user.hashed_password) is True


def test_register_duplicate_email_fails(client):
    """Verify registering an already-registered email returns 400 Bad Request."""
    payload = {
        "full_name": "Test User",
        "email": "duplicate@example.com",
        "password": "Password@123",
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()


def test_login_success(client, db_session):
    """Verify registered user can log in and receive valid token."""
    user = User(
        full_name="Karan Patel",
        email="karan@example.com",
        hashed_password=hash_password("Karan@12345"),
        role="CITIZEN",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/auth/login", json={"email": "karan@example.com", "password": "Karan@12345"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "karan@example.com"


def test_login_invalid_password(client, db_session):
    """Verify invalid password returns 401 Unauthorized."""
    user = User(
        full_name="Karan Patel",
        email="karan2@example.com",
        hashed_password=hash_password("CorrectPassword@1"),
        role="CITIZEN",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/auth/login", json={"email": "karan2@example.com", "password": "WrongPassword"})
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_auth_me_endpoint(client, db_session):
    """Verify GET /api/auth/me returns current token holder's profile."""
    user = User(
        full_name="Officer Sharma",
        email="sharma@smartcity.gov",
        hashed_password=hash_password("Pass@123"),
        role="ADMIN",
        department="Roads and Infrastructure Department",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.email, "id": user.id, "role": user.role})
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "sharma@smartcity.gov"
    assert data["role"] == "ADMIN"
    assert data["department"] == "Roads and Infrastructure Department"


def test_auth_me_unauthorized(client):
    """Verify GET /api/auth/me without token returns 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
