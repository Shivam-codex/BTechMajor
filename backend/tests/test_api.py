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


from backend.app.core.security import hash_password, create_access_token
from backend.app.models.user import User
from backend.tests.test_extraction import _generate_test_wav


@pytest.fixture(autouse=True)
def mock_external_calls():
    """Mocks external network calls (Nominatim reverse-geocoding and Whisper download) for fast offline testing."""
    from unittest.mock import patch, MagicMock
    from backend.app.services.extraction.audio_extractor import set_mock_whisper_model

    mock_whisper = MagicMock()
    mock_seg = MagicMock()
    mock_seg.text = "Street light bulb broken and sparking exposed wire on road"
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_whisper.transcribe.return_value = ([mock_seg], mock_info)
    set_mock_whisper_model(mock_whisper)

    with patch(
        "backend.app.services.extraction.image_extractor.reverse_geocode",
        return_value="Baner Road, Pune, Maharashtra",
    ):
        yield


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


@pytest.fixture(scope="module")
def admin_token(test_db_engine):
    """Generates an administrative bearer token for integration tests."""
    from sqlalchemy.orm import sessionmaker

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    db = TestingSessionLocal()
    admin_user = User(
        id=999,
        full_name="Test Administrator",
        email="test_admin@smartcity.gov",
        hashed_password=hash_password("Admin@123"),
        role="ADMIN",
        department="General Grievance Cell",
        is_active=True,
    )
    db.merge(admin_user)
    db.commit()
    token = create_access_token({"sub": admin_user.email, "id": admin_user.id, "role": "ADMIN"})
    db.close()
    return token


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
    assert res_data["attachment_url"] == f"/api/complaints/{res_data['id']}/attachment"

    # Test downloading / viewing attachment
    att_resp = client.get(f"/api/complaints/{res_data['id']}/attachment")
    assert att_resp.status_code == 200
    assert att_resp.content == sample_txt_bytes


def test_audio_and_combined_upload_complaint(client):
    fake_audio = _generate_test_wav(0.5, silent=False)
    files = {
        "file": ("voice_memo.wav", io.BytesIO(fake_audio), "audio/wav")
    }
    data = {
        "citizen_name": "Anita Kulkarni",
        "location": "Baner Road",
        "complaint_text": "Street lights not working near Baner police station for 3 days."
    }
    response = client.post("/api/complaints/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["id"] is not None
    assert res_data["source_type"] == "AUDIO"
    assert res_data["source_file_name"] == "voice_memo.wav"
    assert res_data["category"] == "Street Light"
    assert res_data["department"] == "Electrical Department"


def test_inspect_uploaded_image_endpoint(client):
    from PIL import Image
    img = Image.new("RGB", (60, 60), color="yellow")
    exif = img.getexif()
    gps_ifd = exif.get_ifd(0x8825)
    gps_ifd[1] = "N"
    gps_ifd[2] = (18.0, 31.0, 13.44)
    gps_ifd[3] = "E"
    gps_ifd[4] = (73.0, 51.0, 24.12)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    img_bytes = buf.getvalue()

    files = {"file": ("sparking_pole_evidence.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    response = client.post("/api/complaints/inspect-image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["has_gps"] is True
    assert round(data["latitude"], 2) == 18.52
    assert "predicted_priority" in data
    assert data["predicted_priority"] in ["Critical", "High", "Medium", "Low"]


def test_upload_complaint_with_image_and_gps_and_priority(client):
    from PIL import Image
    img = Image.new("RGB", (60, 60), color="red")
    exif = img.getexif()
    gps_ifd = exif.get_ifd(0x8825)
    gps_ifd[1] = "N"
    gps_ifd[2] = (18.0, 31.0, 13.44)
    gps_ifd[3] = "E"
    gps_ifd[4] = (73.0, 51.0, 24.12)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    img_bytes = buf.getvalue()

    files = {"file": ("exposed_live_wire.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    data = {
        "citizen_name": "Suresh Kale",
        "complaint_text": "Exposed electrical wire sparking on road near school gate.",
        "location": "Device Location"  # Will be resolved to image GPS
    }
    response = client.post("/api/complaints/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["id"] is not None
    assert res_data["source_type"] == "IMAGE"
    assert res_data["category"] == "Electricity"
    assert res_data["priority"] == "Critical"
    assert res_data["location"] != "Device Location"  # Prioritized image GPS location


def test_mandatory_image_validation_when_required(client, sample_txt_bytes):
    """Ensure complaint submission fails with 400 when require_image=true and no image is attached."""
    files = [
        ("files", ("only_document.txt", io.BytesIO(sample_txt_bytes), "text/plain")),
    ]
    data = {
        "citizen_name": "Kiran Deshmukh",
        "require_image": "true",
    }
    response = client.post("/api/complaints/upload", files=files, data=data)
    assert response.status_code == 400
    assert "Mandatory Image Upload Required" in response.json()["detail"]


def test_multimodal_upload_image_audio_and_document(client):
    """Ensure image + optional audio + optional document can be uploaded together and correlated."""
    from PIL import Image

    img = Image.new("RGB", (60, 60), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    fake_audio = _generate_test_wav(0.5, silent=False)
    water_doc_bytes = (
        b"Inspection Report: Major water supply pipeline burst near Kothrud Ward 10. "
        b"Drinking water is leaking continuously onto the street."
    )

    files = [
        ("files", ("burst_water_pipe.jpg", io.BytesIO(img_bytes), "image/jpeg")),
        ("files", ("urgent_water_leak_voice.wav", io.BytesIO(fake_audio), "audio/wav")),
        ("files", ("pipeline_inspection.txt", io.BytesIO(water_doc_bytes), "text/plain")),
    ]
    data = {
        "citizen_name": "Meera Joshi",
        "location": "Kothrud Ward 10",
        "complaint_text": "Major water pipeline burst flooding the lane.",
        "require_image": "true",
    }
    response = client.post("/api/complaints/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    cid = res_data["id"]
    assert res_data["source_type"] == "MULTIMODAL"
    assert res_data["category"] == "Water Supply"
    assert len(res_data["attachments"]) == 3
    assert res_data["attachments"][0]["media_category"] == "image"
    assert res_data["attachments"][1]["media_category"] == "audio"
    assert res_data["attachments"][2]["media_category"] == "document"

    # Verify all 3 files can be retrieved by index
    r0 = client.get(f"/api/complaints/{cid}/attachment?index=0")
    assert r0.status_code == 200
    assert r0.content == img_bytes

    r1 = client.get(f"/api/complaints/{cid}/attachment?index=1")
    assert r1.status_code == 200
    assert r1.content == fake_audio

    r2 = client.get(f"/api/complaints/{cid}/attachment?index=2")
    assert r2.status_code == 200
    assert r2.content == water_doc_bytes


def test_inspect_uploaded_audio_endpoint(client):
    """Ensure /api/complaints/inspect-audio transcribes speech and extracts words via NLP."""
    fake_audio = _generate_test_wav(0.5, silent=False)
    files = {"file": ("sparking_exposed_wire_emergency.wav", io.BytesIO(fake_audio), "audio/wav")}
    response = client.post("/api/complaints/inspect-audio", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    assert "extracted_words" in data
    assert "filtered_keywords" in data
    assert "hazard_keywords" in data
    assert data["predicted_priority"] in ["Critical", "High", "Medium", "Low"]
    # Check that hazard words were detected from the filename/transcription
    assert any("wire" in k or "spark" in k or "emergency" in k for k in data["hazard_keywords"])


def test_inspect_uploaded_audio_with_client_transcript(client):
    """Ensure /api/complaints/inspect-audio accepts client transcript and performs NLP word & hazard extraction."""
    fake_webm = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08"
    files = {"file": ("recorded_audio_10-45-12.webm", io.BytesIO(fake_webm), "audio/webm")}
    data = {
        "transcript": "Heavy water leakage from burst main pipeline flooding MG road near school gate."
    }
    response = client.post("/api/complaints/inspect-audio", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert "burst main pipeline" in res["transcription"]
    assert res["category_hint"] == "Water Supply"
    assert res["predicted_priority"] in ["Critical", "High"]
    # Verify NLP extracted words contain meaningful civic tokens
    assert any(w in res["filtered_keywords"] for w in ["water", "leakage", "pipeline", "flooding"])
    # Verify numbers/generic stems are NOT treated as keywords
    assert "10" not in res["filtered_keywords"]
    assert "45" not in res["filtered_keywords"]
    assert "recorded" not in res["filtered_keywords"]


def test_upload_with_audio_transcripts_json(client):
    """Ensure /api/complaints/upload processes audio with audio_transcripts JSON map."""
    import json
    from PIL import Image

    img = Image.new("RGB", (60, 60), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    fake_webm = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08"

    files = [
        ("files", ("street_view.jpg", io.BytesIO(img_bytes), "image/jpeg")),
        ("files", ("citizen_recording.webm", io.BytesIO(fake_webm), "audio/webm")),
    ]
    data = {
        "citizen_name": "Deepak Patil",
        "location": "Aundh Ward 2",
        "require_image": "true",
        "audio_transcripts": json.dumps({
            "citizen_recording.webm": "Big deep road crater pothole causing vehicle accidents on bridge."
        }),
    }
    response = client.post("/api/complaints/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["category"] == "Road/Pothole"
    assert res_data["priority"] in ["Critical", "High", "Review Required"]


def test_priority_decision_from_audio_words_and_photo(client):
    """Ensure priority is decided by correlating words from audio and visual features from photo."""
    from PIL import Image

    # Standard photo (without EXIF GPS or critical markers)
    img = Image.new("RGB", (60, 60), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    # Audio with critical hazard tokens in filename/speech
    fake_audio = _generate_test_wav(0.5, silent=False)

    files = [
        ("files", ("standard_street_photo.jpg", io.BytesIO(img_bytes), "image/jpeg")),
        ("files", ("exposed_electrical_wire_sparking_accident.wav", io.BytesIO(fake_audio), "audio/wav")),
    ]
    data = {
        "citizen_name": "Ramesh Thorat",
        "require_image": "true",
    }
    response = client.post("/api/complaints/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    # Spoken audio words identified 'exposed electrical wire', 'sparking', 'accident' -> Priority Critical!
    assert res_data["priority"] == "Critical"
    assert "hazard" in res_data["priority_reason"].lower() or "wire" in res_data["priority_reason"].lower()


def test_list_complaints_and_filtering(client, admin_token):
    # Retrieve all using admin credentials
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/complaints?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

    # Filter by category
    cat_response = client.get("/api/complaints?category=Road/Pothole", headers=headers)
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


def test_update_complaint_lifecycle(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
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
    put_res = client.put(f"/api/complaints/{cid}", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "In Progress"
    assert "jetting machine" in put_res.json()["resolution_notes"]

    # Resolve
    resolve_payload = {"status": "Resolved"}
    resolve_res = client.put(f"/api/complaints/{cid}", json=resolve_payload, headers=headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "Resolved"
    assert resolve_res.json()["resolved_at"] is not None


def test_dashboard_stats(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_complaints"] >= 3
    assert len(data["by_category"]) > 0
    assert len(data["by_department"]) > 0
    assert len(data["by_priority"]) > 0


def test_knowledge_base_documents_endpoints(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # List all documents
    list_res = client.get("/api/knowledge-base/documents", headers=headers)
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 14
    assert any(d["document_id"] == "KB-001" for d in docs)

    # Get single document details
    single_res = client.get("/api/knowledge-base/documents/KB-001", headers=headers)
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
