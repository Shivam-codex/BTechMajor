"""
FastAPI Integration Test Suite.
Tests all REST endpoints: complaints (manual & upload), dashboard stats,
knowledge base inspection, and the Non-ML Municipal Assistant.
"""

import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import get_db


@pytest.fixture(scope="module")
def client(test_db_engine):
    """Provides a TestClient using in-memory SQLite database override."""
    from sqlalchemy.orm import sessionmaker

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Non-ML" in data["architecture"]


def test_manual_complaint_submission(client):
    payload = {
        "complaint_text": "There are dangerous potholes on MG road near bus stand causing vehicle damage.",
        "citizen_name": "Aarav Sharma",
        "location": "MG Road, Ward 4",
    }
    response = client.post("/api/complaints", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("CMP-")
    assert data["category"] == "Road/Pothole"
    assert data["department"] == "Roads and Infrastructure Department"
    assert data["rule_match_score"] > 0.60
    assert len(data["matched_keywords"]) > 0
    assert data["citizen_name"] == "Aarav Sharma"


def test_document_upload_complaint(client, sample_txt_bytes):
    files = {
        "file": ("urgent_pipeline_leak.txt", io.BytesIO(sample_txt_bytes), "text/plain")
    }
    data = {
        "citizen_name": "Rohan Joshi",
        "location": "Sinhagad Road",
    }
    response = client.post("/api/complaints/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["id"] is not None
    assert res_data["source_type"] == "TXT"
    assert res_data["source_file_name"] == "urgent_pipeline_leak.txt"


def test_list_complaints_and_filtering(client):
    # Retrieve all
    response = client.get("/api/complaints?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

    # Filter by category
    cat_response = client.get("/api/complaints?category=Road/Pothole")
    assert cat_response.status_code == 200
    cat_data = cat_response.json()
    assert all(item["category"] == "Road/Pothole" for item in cat_data["items"])


def test_get_single_complaint_detail(client):
    # First create a complaint
    payload = {
        "complaint_text": "Street light pole SL-102 is completely off creating dark spot at night.",
        "citizen_name": "Deepak Verma",
        "location": "Kothrud",
    }
    create_res = client.post("/api/complaints", json=payload)
    cid = create_res.json()["id"]

    # Retrieve single
    get_res = client.get(f"/api/complaints/{cid}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == cid
    assert data["category"] == "Street Light"
    assert data["department"] == "Electrical Department"
    assert "classification_reason" in data


def test_update_complaint_lifecycle(client):
    # Create complaint
    create_res = client.post(
        "/api/complaints",
        json={"complaint_text": "Sewage gutter is overflowing on public road near clinic."},
    )
    cid = create_res.json()["id"]

    # Update status to In Progress, then Resolved with notes
    update_payload = {
        "status": "In Progress",
        "resolution_notes": "Inspection crew dispatched with jetting machine.",
    }
    put_res = client.put(f"/api/complaints/{cid}", json=update_payload)
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "In Progress"
    assert "jetting machine" in put_res.json()["resolution_notes"]

    # Resolve
    resolve_payload = {"status": "Resolved"}
    resolve_res = client.put(f"/api/complaints/{cid}", json=resolve_payload)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "Resolved"
    assert resolve_res.json()["resolved_at"] is not None


def test_dashboard_stats(client):
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_complaints"] >= 3
    assert len(data["by_category"]) > 0
    assert len(data["by_department"]) > 0
    assert len(data["by_priority"]) > 0


def test_knowledge_base_documents_endpoints(client):
    # List all documents
    list_res = client.get("/api/knowledge-base/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 14
    assert any(d["document_id"] == "KB-001" for d in docs)

    # Get single document details
    single_res = client.get("/api/knowledge-base/documents/KB-001")
    assert single_res.status_code == 200
    doc_detail = single_res.json()
    assert doc_detail["document_id"] == "KB-001"
    assert doc_detail["title"] == "Water Supply Complaint Procedure"
    assert len(doc_detail["chunks"]) > 0


def test_assistant_query_endpoint(client):
    query_payload = {"question": "How do I report a pothole on my street?"}
    response = client.post("/api/assistant/query", json=query_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["has_answer"] is True
    assert data["confidence"] > 0.15
    assert len(data["sources"]) > 0
    assert "Sample Municipal Knowledge Base" in data["answer"]
