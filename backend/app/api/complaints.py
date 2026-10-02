"""
Complaint API Endpoints.
Provides citizen grievance submission (manual text and document upload),
admin filtering/searching, individual complaint inspection, and status updates.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.database import get_db
from backend.app.models.complaint import Complaint
from backend.app.models.base import utc_now
from backend.app.schemas.complaint_schema import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ComplaintListResponse,
)
from backend.app.services.complaint_processing_service import (
    process_complaint_pipeline,
    process_document_complaint,
    ComplaintProcessingError,
)
from backend.app.core.security import sanitize_text_input, validate_upload_content
from backend.app.utils.constants import ComplaintStatus

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "/upload",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload citizen complaint document (PDF, DOCX, TXT)",
)
async def upload_complaint_document(
    file: UploadFile = File(..., description="Complaint document (PDF, DOCX, TXT) up to 10 MB"),
    citizen_name: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Accepts complaint files, extracts text, runs deterministic NLP classification,
    assigns department, detects priority, and saves record to SQLite.
    """
    file_bytes = await file.read()
    filename = file.filename or "uploaded_complaint.txt"

    # Security and file validation
    is_valid, err_msg = validate_upload_content(filename, file_bytes)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    clean_name = sanitize_text_input(citizen_name) if citizen_name else None
    clean_loc = sanitize_text_input(location) if location else None

    try:
        complaint = process_document_complaint(
            db=db,
            file_name=filename,
            file_bytes=file_bytes,
            citizen_name=clean_name,
            location=clean_loc,
        )
        return complaint
    except ComplaintProcessingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing failed: {str(e)}")


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit manual citizen complaint text",
)
def submit_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
):
    """
    Accepts raw grievance text, runs NLP preprocessing, rule-based classification,
    priority detection, department routing, and stores to database.
    """
    clean_text = sanitize_text_input(payload.complaint_text)
    clean_name = sanitize_text_input(payload.citizen_name) if payload.citizen_name else None
    clean_loc = sanitize_text_input(payload.location) if payload.location else None

    if len(clean_text) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint description is too short (minimum 5 characters).",
        )

    try:
        complaint = process_complaint_pipeline(
            db=db,
            complaint_text=clean_text,
            citizen_name=clean_name,
            location=clean_loc,
            source_type=payload.source_type.value,
            source_file_name=payload.source_file_name,
            extracted_text=payload.extracted_text,
        )
        return complaint
    except ComplaintProcessingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing failed: {str(e)}")


@router.get(
    "",
    response_model=ComplaintListResponse,
    summary="List complaints with search and filters",
)
def list_complaints(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated complaints with filtering across category, department,
    priority, lifecycle status, and keyword search.
    """
    query = db.query(Complaint)

    if category:
        query = query.filter(Complaint.category == category)
    if department:
        query = query.filter(Complaint.department == department)
    if priority:
        query = query.filter(Complaint.priority == priority)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Complaint.id.ilike(search_term),
                Complaint.complaint_text.ilike(search_term),
                Complaint.citizen_name.ilike(search_term),
                Complaint.location.ilike(search_term),
            )
        )

    total = query.count()
    offset = (page - 1) * limit
    items = query.order_by(Complaint.created_at.desc()).offset(offset).limit(limit).all()

    return ComplaintListResponse(
        total=total,
        items=items,
        page=page,
        limit=limit,
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get single complaint details with rule explainability",
)
def get_complaint(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Complaint '{complaint_id}' not found.")
    return complaint


@router.put(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Update complaint status, department, priority, or resolution notes",
)
def update_complaint(
    complaint_id: str,
    payload: ComplaintUpdate,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Complaint '{complaint_id}' not found.")

    if payload.status is not None:
        complaint.status = payload.status.value
        if payload.status.value == ComplaintStatus.RESOLVED.value:
            complaint.resolved_at = utc_now()

    if payload.department is not None:
        complaint.department = payload.department.value
        complaint.assigned_at = utc_now()

    if payload.priority is not None:
        complaint.priority = payload.priority.value

    if payload.resolution_notes is not None:
        complaint.resolution_notes = sanitize_text_input(payload.resolution_notes)

    db.commit()
    db.refresh(complaint)
    return complaint


@router.delete(
    "/{complaint_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a complaint record",
)
def delete_complaint(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Complaint '{complaint_id}' not found.")

    db.delete(complaint)
    db.commit()
    return {"message": f"Complaint '{complaint_id}' successfully removed.", "deleted_id": complaint_id}
