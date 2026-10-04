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
    """Creates a citizen user, super admin, and departmental admin with access tokens."""
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
    dept_admin = User(
        full_name="Water Dept Officer",
        email="water.officer@smartcity.gov",
        hashed_password=hash_password("WaterPass@1"),
        role="ADMIN",
        department="Water Supply Department",
        is_active=True,
    )
    db_session.add_all([citizen, admin, dept_admin])
    db_session.commit()
    db_session.refresh(citizen)
    db_session.refresh(admin)
    db_session.refresh(dept_admin)

    citizen_token = create_access_token({"sub": citizen.email, "id": citizen.id, "role": citizen.role})
    admin_token = create_access_token({"sub": admin.email, "id": admin.id, "role": admin.role})
    dept_admin_token = create_access_token({"sub": dept_admin.email, "id": dept_admin.id, "role": dept_admin.role})

    return {
        "citizen": citizen,
        "admin": admin,
        "dept_admin": dept_admin,
        "citizen_token": citizen_token,
        "admin_token": admin_token,
        "dept_admin_token": dept_admin_token,
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


def test_knowledge_base_super_admin_allowed(client, sample_users):
    """Super Administrator must be permitted to inspect knowledge base documents."""
    super_admin_headers = {"Authorization": f"Bearer {sample_users['admin_token']}"}
    resp = client.get("/api/knowledge-base/documents", headers=super_admin_headers)
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) >= 14


def test_knowledge_base_dept_admin_forbidden(client, sample_users):
    """Departmental administrator must be rejected with 403 Forbidden."""
    dept_headers = {"Authorization": f"Bearer {sample_users['dept_admin_token']}"}
    resp = client.get("/api/knowledge-base/documents", headers=dept_headers)
    assert resp.status_code == 403
    assert "Super Administrator privileges required" in resp.json()["detail"]


def test_knowledge_base_citizen_forbidden(client, sample_users):
    """Citizen must be rejected with 403 Forbidden when accessing knowledge base documents."""
    citizen_headers = {"Authorization": f"Bearer {sample_users['citizen_token']}"}
    resp = client.get("/api/knowledge-base/documents", headers=citizen_headers)
    assert resp.status_code == 403
    assert "Super Administrator privileges required" in resp.json()["detail"]


def test_knowledge_base_unauthenticated_unauthorized(client):
    """Unauthenticated caller must be rejected with 401 Unauthorized."""
    resp = client.get("/api/knowledge-base/documents")
    assert resp.status_code == 401


def test_department_admin_complaint_isolation(client, db_session, sample_users):
    """
    Departmental admin (Water Supply) can ONLY view complaints assigned to Water Supply Department.
    Complaints assigned to Roads/Electrical must NOT be visible or editable.
    """
    cmp_water = Complaint(
        id="CMP-TEST-WATER01",
        complaint_text="Low water pressure on 5th floor",
        category=ComplaintCategory.WATER_SUPPLY.value,
        department=DepartmentName.WATER_SUPPLY.value,
        priority=ComplaintPriority.MEDIUM.value,
        status=ComplaintStatus.SUBMITTED.value,
    )
    cmp_road = Complaint(
        id="CMP-TEST-ROAD01",
        complaint_text="Huge crater on Baner main road",
        category=ComplaintCategory.ROAD_POTHOLE.value,
        department=DepartmentName.ROADS_INFRASTRUCTURE.value,
        priority=ComplaintPriority.HIGH.value,
        status=ComplaintStatus.SUBMITTED.value,
    )
    db_session.add_all([cmp_water, cmp_road])
    db_session.commit()

    dept_headers = {"Authorization": f"Bearer {sample_users['dept_admin_token']}"}

    # 1. List complaints: must only return water complaints
    list_resp = client.get("/api/complaints", headers=dept_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert all(c["department"] == DepartmentName.WATER_SUPPLY.value for c in items)
    assert any(c["id"] == "CMP-TEST-WATER01" for c in items)
    assert not any(c["id"] == "CMP-TEST-ROAD01" for c in items)

    # 2. Get single complaint: water allowed, road forbidden
    get_water = client.get("/api/complaints/CMP-TEST-WATER01", headers=dept_headers)
    assert get_water.status_code == 200

    get_road = client.get("/api/complaints/CMP-TEST-ROAD01", headers=dept_headers)
    assert get_road.status_code == 403
    assert "restricted to viewing complaints within your assigned department" in get_road.json()["detail"]

    # 3. Update complaint: road forbidden
    put_road = client.put(
        "/api/complaints/CMP-TEST-ROAD01",
        json={"status": "In Progress"},
        headers=dept_headers,
    )
    assert put_road.status_code == 403

    # 4. Delete complaint: road forbidden
    del_road = client.delete("/api/complaints/CMP-TEST-ROAD01", headers=dept_headers)
    assert del_road.status_code == 403


def test_department_admin_dashboard_stats_isolation(client, db_session, sample_users):
    """
    Departmental admin requesting /api/dashboard/stats sees stats scoped strictly to their department.
    """
    cmp_water = Complaint(
        id="CMP-TEST-WTR99",
        complaint_text="Muddy water in pipeline",
        category=ComplaintCategory.WATER_SUPPLY.value,
        department=DepartmentName.WATER_SUPPLY.value,
        priority=ComplaintPriority.HIGH.value,
        status=ComplaintStatus.IN_PROGRESS.value,
    )
    cmp_road = Complaint(
        id="CMP-TEST-RD99",
        complaint_text="Bridge expansion joint issue",
        category=ComplaintCategory.ROAD_POTHOLE.value,
        department=DepartmentName.ROADS_INFRASTRUCTURE.value,
        priority=ComplaintPriority.CRITICAL.value,
        status=ComplaintStatus.SUBMITTED.value,
    )
    db_session.add_all([cmp_water, cmp_road])
    db_session.commit()

    dept_headers = {"Authorization": f"Bearer {sample_users['dept_admin_token']}"}
    stats_resp = client.get("/api/dashboard/stats", headers=dept_headers)
    assert stats_resp.status_code == 200
    data = stats_resp.json()

    # In by_department distribution, ONLY Water Supply Department should exist
    for d in data["by_department"]:
        assert d["department"] == DepartmentName.WATER_SUPPLY.value


def test_all_departmental_admins_authentication_and_isolation(client, db_session):
    """
    Verify all municipal departments have working admin accounts and are properly isolated.
    """
    departments = [
        ("water.admin@smartcity.gov", DepartmentName.WATER_SUPPLY.value),
        ("sanitation.admin@smartcity.gov", DepartmentName.SANITATION.value),
        ("roads.admin@smartcity.gov", DepartmentName.ROADS_INFRASTRUCTURE.value),
        ("electrical.admin@smartcity.gov", DepartmentName.ELECTRICAL.value),
        ("drainage.admin@smartcity.gov", DepartmentName.DRAINAGE.value),
        ("health.admin@smartcity.gov", DepartmentName.PUBLIC_HEALTH.value),
        ("traffic.admin@smartcity.gov", DepartmentName.TRAFFIC.value),
    ]

    for email, dept_name in departments:
        user = User(
            full_name=f"{dept_name} Officer",
            email=email,
            hashed_password=hash_password("Admin@12345"),
            role="ADMIN",
            department=dept_name,
            is_active=True,
        )
        db_session.add(user)
    db_session.commit()

    for email, dept_name in departments:
        # 1. Login
        login_resp = client.post("/api/auth/login", json={"email": email, "password": "Admin@12345"})
        assert login_resp.status_code == 200, f"Failed to login for {email}"
        data = login_resp.json()
        assert data["user"]["role"] == "ADMIN"
        assert data["user"]["department"] == dept_name
        token = data["access_token"]

        # 2. Query Dashboard Stats
        headers = {"Authorization": f"Bearer {token}"}
        stats_resp = client.get("/api/dashboard/stats", headers=headers)
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        # Verify that all returned department distributions match only this admin's department
        for d in stats.get("by_department", []):
            assert d["department"] == dept_name

