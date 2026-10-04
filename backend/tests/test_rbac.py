"""
Integration tests for Role-Based Access Control (RBAC).
Verifies strict separation between Citizen privileges and Municipal Administrator privileges:
- Citizen cannot access /api/dashboard/stats (403 Forbidden)
- Admin can access /api/dashboard/stats (200 OK)
- Citizen querying /api/complaints sees ONLY their own submitted grievances
- Admin querying /api/complaints sees all complaints
- Citizen cannot update or delete complaints (403 Forbidden)
- Admin can update and delete complaints (200 OK)
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.core.security import hash_password, create_access_token
from backend.app.models.user import User
from backend.app.models.complaint import Complaint
from backend.app.utils.constants import ComplaintStatus, ComplaintPriority, ComplaintCategory, DepartmentName


@pytest.fixture
def client(db_session):
    """Test client with overridden database dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_users(db_session):
    """Creates a citizen user and an admin user with access tokens."""
    citizen = User(
        full_name="Citizen One",
        email="citizen1@example.com",
        hashed_password=hash_password("CitizenPass@1"),
        role="CITIZEN",
        is_active=True,
    )
    admin = User(
        full_name="Admin Officer",
        email="admin1@smartcity.gov",
        hashed_password=hash_password("AdminPass@1"),
        role="ADMIN",
        department="General Grievance Cell",
        is_active=True,
    )
    db_session.add_all([citizen, admin])
    db_session.commit()
    db_session.refresh(citizen)
    db_session.refresh(admin)

    citizen_token = create_access_token({"sub": citizen.email, "id": citizen.id, "role": citizen.role})
    admin_token = create_access_token({"sub": admin.email, "id": admin.id, "role": admin.role})

    return {
        "citizen": citizen,
        "admin": admin,
        "citizen_token": citizen_token,
        "admin_token": admin_token,
    }


def test_dashboard_stats_requires_admin(client, sample_users):
    """Citizen must be rejected with 403 Forbidden when requesting dashboard stats."""
    citizen_headers = {"Authorization": f"Bearer {sample_users['citizen_token']}"}
    resp = client.get("/api/dashboard/stats", headers=citizen_headers)
    assert resp.status_code == 403
    assert "Administrative privileges required" in resp.json()["detail"]


def test_dashboard_stats_admin_allowed(client, sample_users):
    """Municipal administrator must be permitted to view dashboard stats."""
    admin_headers = {"Authorization": f"Bearer {sample_users['admin_token']}"}
    resp = client.get("/api/dashboard/stats", headers=admin_headers)
    assert resp.status_code == 200
    assert "total_complaints" in resp.json()


def test_citizen_complaint_segregation(client, db_session, sample_users):
    """
    Verifies that a citizen can ONLY view complaints associated with their user_id.
    Other complaints must NOT be visible to them.
    """
    citizen = sample_users["citizen"]

    # Complaint owned by citizen
    cmp_own = Complaint(
        id="CMP-2026-OWN001",
        complaint_text="Water leakage outside my gate",
        category=ComplaintCategory.WATER_SUPPLY.value,
        department=DepartmentName.WATER_SUPPLY.value,
        priority=ComplaintPriority.MEDIUM.value,
        status=ComplaintStatus.SUBMITTED.value,
        user_id=citizen.id,
    )
    # Complaint owned by another citizen
    cmp_other = Complaint(
        id="CMP-2026-OTH002",
        complaint_text="Street light broken on 5th cross",
        category=ComplaintCategory.STREET_LIGHT.value,
        department=DepartmentName.ELECTRICAL.value,
        priority=ComplaintPriority.LOW.value,
        status=ComplaintStatus.SUBMITTED.value,
        user_id=9999,
    )
    db_session.add_all([cmp_own, cmp_other])
    db_session.commit()

    citizen_headers = {"Authorization": f"Bearer {sample_users['citizen_token']}"}
    resp = client.get("/api/complaints", headers=citizen_headers)
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]

    # Citizen must see only their 1 complaint
    assert len(items) == 1
    assert items[0]["id"] == "CMP-2026-OWN001"


def test_admin_views_all_complaints(client, db_session, sample_users):
    """Administrator sees complaints across all users and departments."""
    cmp1 = Complaint(
        id="CMP-2026-ALL001",
        complaint_text="Garbage pile up near temple",
        category=ComplaintCategory.GARBAGE_WASTE.value,
        department=DepartmentName.SANITATION.value,
        priority=ComplaintPriority.HIGH.value,
        status=ComplaintStatus.SUBMITTED.value,
        user_id=sample_users["citizen"].id,
    )
    cmp2 = Complaint(
        id="CMP-2026-ALL002",
        complaint_text="Pothole on airport road",
        category=ComplaintCategory.ROAD_POTHOLE.value,
        department=DepartmentName.ROADS_INFRASTRUCTURE.value,
        priority=ComplaintPriority.CRITICAL.value,
        status=ComplaintStatus.SUBMITTED.value,
        user_id=9999,
    )
    db_session.add_all([cmp1, cmp2])
    db_session.commit()

    admin_headers = {"Authorization": f"Bearer {sample_users['admin_token']}"}
    resp = client.get("/api/complaints", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    ids = [item["id"] for item in data["items"]]
    assert "CMP-2026-ALL001" in ids
    assert "CMP-2026-ALL002" in ids


def test_citizen_forbidden_to_update_or_delete_complaint(client, db_session, sample_users):
    """Citizens cannot update status/department or delete complaint records."""
    cmp = Complaint(
        id="CMP-2026-MOD001",
        complaint_text="Open drain hazard",
        category=ComplaintCategory.DRAINAGE_SEWERAGE.value,
        department=DepartmentName.DRAINAGE.value,
        priority=ComplaintPriority.HIGH.value,
        status=ComplaintStatus.SUBMITTED.value,
        user_id=sample_users["citizen"].id,
    )
    db_session.add(cmp)
    db_session.commit()

    citizen_headers = {"Authorization": f"Bearer {sample_users['citizen_token']}"}

    # Attempt PUT
    put_resp = client.put(
        f"/api/complaints/{cmp.id}",
        json={"status": "Resolved", "resolution_notes": "Citizen trying to self-resolve"},
        headers=citizen_headers,
    )
    assert put_resp.status_code == 403

    # Attempt DELETE
    del_resp = client.delete(f"/api/complaints/{cmp.id}", headers=citizen_headers)
    assert del_resp.status_code == 403


def test_admin_can_update_and_delete_complaint(client, db_session, sample_users):
    """Administrator can successfully update status and resolution notes, and delete complaints."""
    cmp = Complaint(
        id="CMP-2026-ADM001",
        complaint_text="Fallen tree on electrical wire",
        category=ComplaintCategory.ELECTRICITY.value,
        department=DepartmentName.ELECTRICAL.value,
        priority=ComplaintPriority.CRITICAL.value,
        status=ComplaintStatus.SUBMITTED.value,
    )
    db_session.add(cmp)
    db_session.commit()

    admin_headers = {"Authorization": f"Bearer {sample_users['admin_token']}"}

    # PUT Update
    put_resp = client.put(
        f"/api/complaints/{cmp.id}",
        json={"status": "In Progress", "resolution_notes": "Electrical team dispatched with safety crane"},
        headers=admin_headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["status"] == "In Progress"

    # DELETE
    del_resp = client.delete(f"/api/complaints/{cmp.id}", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_id"] == "CMP-2026-ADM001"
