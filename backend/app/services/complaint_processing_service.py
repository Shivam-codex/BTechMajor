"""
Central Complaint Processing Service.
Coordinates the end-to-end deterministic grievance intake pipeline:
  Text Extraction (if document)
  -> NLP Preprocessing
  -> Rule-Based Classification
  -> Priority Detection
  -> Department Assignment
  -> Database Persistence
Ensures uniform business logic across all API endpoints and batch scripts.
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.complaint import Complaint, generate_complaint_id
from backend.app.services.extraction.document_service import extract_document_text
from backend.app.services.nlp.preprocessing import preprocess_complaint
from backend.app.services.classification.classifier import classify_complaint
from backend.app.services.classification.department_router import assign_department
from backend.app.services.classification.priority_detector import detect_priority
from backend.app.utils.constants import SourceType, ComplaintStatus
from backend.app.core.logging import log_event
from backend.app.models.base import utc_now


class ComplaintProcessingError(Exception):
    """Raised when an unrecoverable error occurs during complaint ingestion."""
    pass


def process_complaint_pipeline(
    db: Session,
    complaint_text: str,
    citizen_name: Optional[str] = None,
    location: Optional[str] = None,
    source_type: str = SourceType.MANUAL.value,
    source_file_name: Optional[str] = None,
    extracted_text: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Complaint:
    """
    Executes complete deterministic processing on complaint text and persists record.
    """
    clean_text = (complaint_text or "").strip()
    if not clean_text:
        raise ComplaintProcessingError("Complaint text cannot be empty.")

    # 1. Deterministic NLP Preprocessing
    nlp_result = preprocess_complaint(clean_text)

    # 2. Rule-Based Classification
    classification = classify_complaint(nlp_result)

    # 3. Automatic Department Assignment
    department, routing_reason = assign_department(classification.category)

    # 4. Deterministic Priority Detection
    priority_res = detect_priority(nlp_result)

    # 5. Determine initial status
    initial_status = classification.status
    if initial_status == ComplaintStatus.CLASSIFIED.value:
        initial_status = ComplaintStatus.ASSIGNED.value

    # 6. Build and persist Complaint model
    complaint = Complaint(
        id=generate_complaint_id(),
        user_id=user_id,
        complaint_text=clean_text,
        extracted_text=extracted_text,
        source_file_name=source_file_name,
        source_type=source_type,
        language=nlp_result.language,
        category=classification.category,
        rule_match_score=classification.rule_match_score,
        matched_keywords=classification.matched_keywords,
        matched_phrases=classification.matched_phrases,
        classification_reason=classification.reason,
        department=department,
        priority=priority_res.priority,
        priority_reason=priority_res.priority_reason,
        status=initial_status,
        citizen_name=citizen_name,
        location=location,
        assigned_at=utc_now() if initial_status == ComplaintStatus.ASSIGNED.value else None,
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    log_event("COMPLAINT_PROCESSED", {
        "id": complaint.id,
        "user_id": complaint.user_id,
        "category": complaint.category,
        "score": complaint.rule_match_score,
        "priority": complaint.priority,
        "department": complaint.department,
        "status": complaint.status,
    })

    return complaint


def process_document_complaint(
    db: Session,
    file_name: str,
    file_bytes: bytes,
    citizen_name: Optional[str] = None,
    location: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Complaint:
    """
    Handles file upload: extracts text -> executes complaint pipeline -> saves to DB.
    """
    extraction_res = extract_document_text(file_name, file_bytes)
    if not extraction_res.success:
        raise ComplaintProcessingError(extraction_res.error or "Failed to extract text from document.")

    return process_complaint_pipeline(
        db=db,
        complaint_text=extraction_res.cleaned_text,
        citizen_name=citizen_name,
        location=location,
        source_type=extraction_res.source_type,
        source_file_name=extraction_res.source_file_name,
        extracted_text=extraction_res.cleaned_text,
        user_id=user_id,
    )
