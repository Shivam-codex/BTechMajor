"""
Unit tests for database models and schema serialization.
"""

from backend.app.models.complaint import Complaint, generate_complaint_id
from backend.app.utils.constants import ComplaintCategory, ComplaintPriority, ComplaintStatus, SourceType


def test_complaint_id_generation():
    cid = generate_complaint_id()
    assert cid.startswith("CMP-")
    assert len(cid) >= 12


def test_complaint_crud_lifecycle(db_session):
    new_complaint = Complaint(
        complaint_text="Pothole on Main Road causing traffic issues.",
        extracted_text=None,
        source_file_name=None,
        source_type=SourceType.MANUAL.value,
        language="en",
        category=ComplaintCategory.ROAD_POTHOLE.value,
        rule_match_score=0.88,
        matched_keywords=["pothole", "road"],
        matched_phrases=["pothole on"],
        classification_reason="Road-related keywords matched.",
        department="Roads and Infrastructure Department",
        priority=ComplaintPriority.HIGH.value,
        priority_reason="High traffic risk reported.",
        status=ComplaintStatus.SUBMITTED.value,
        citizen_name="Aarav Sharma",
        location="MG Road, Ward 5",
    )

    db_session.add(new_complaint)
    db_session.commit()
    db_session.refresh(new_complaint)

    assert new_complaint.id is not None
    assert new_complaint.created_at is not None

    # Retrieve and verify
    retrieved = db_session.query(Complaint).filter(Complaint.id == new_complaint.id).first()
    assert retrieved is not None
    assert retrieved.category == ComplaintCategory.ROAD_POTHOLE.value
    assert retrieved.matched_keywords == ["pothole", "road"]

    # Test dictionary serialization
    comp_dict = retrieved.to_dict()
    assert comp_dict["id"] == new_complaint.id
    assert comp_dict["rule_match_score"] == 0.88
    assert comp_dict["citizen_name"] == "Aarav Sharma"
