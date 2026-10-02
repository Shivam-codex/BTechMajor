"""
Integration tests for central complaint processing pipeline.
Tests text complaints and document file complaints end-to-end with DB persistence.
"""

from backend.app.services.complaint_processing_service import (
    process_complaint_pipeline,
    process_document_complaint,
)
from backend.app.utils.constants import (
    ComplaintCategory,
    DepartmentName,
    ComplaintPriority,
    ComplaintStatus,
    SourceType,
)


def test_process_text_complaint_pipeline(db_session):
    text = "Large crater and deep potholes on Karve road causing accidents and severe bike slips."
    complaint = process_complaint_pipeline(
        db=db_session,
        complaint_text=text,
        citizen_name="Rajesh Patil",
        location="Karve Road, Kothrud",
    )

    assert complaint.id.startswith("CMP-")
    assert complaint.category == ComplaintCategory.ROAD_POTHOLE.value
    assert complaint.department == DepartmentName.ROADS_INFRASTRUCTURE.value
    assert complaint.priority in [ComplaintPriority.HIGH.value, ComplaintPriority.CRITICAL.value]
    assert complaint.status == ComplaintStatus.ASSIGNED.value
    assert complaint.rule_match_score > 0.6
    assert len(complaint.matched_keywords) > 0
    assert complaint.assigned_at is not None


def test_process_document_txt_complaint(db_session, sample_txt_bytes):
    complaint = process_document_complaint(
        db=db_session,
        file_name="road_pothole_notice.txt",
        file_bytes=sample_txt_bytes,
        citizen_name="Sunil Deshmukh",
        location="MG Road",
    )

    assert complaint.id is not None
    assert complaint.source_type == SourceType.TXT.value
    assert complaint.source_file_name == "road_pothole_notice.txt"
    assert complaint.category == ComplaintCategory.ROAD_POTHOLE.value
    assert complaint.department == DepartmentName.ROADS_INFRASTRUCTURE.value


def test_process_document_docx_complaint(db_session, sample_docx_bytes):
    complaint = process_document_complaint(
        db=db_session,
        file_name="garbage_letter.docx",
        file_bytes=sample_docx_bytes,
        citizen_name="Pooja Sharma",
        location="Shivaji Nagar",
    )

    assert complaint.source_type == SourceType.DOCX.value
    assert complaint.category == ComplaintCategory.GARBAGE_WASTE.value
    assert complaint.department == DepartmentName.SANITATION.value
