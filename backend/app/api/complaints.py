"""
Complaint API Endpoints.
Provides citizen grievance submission (manual text and document upload),
admin filtering/searching, individual complaint inspection, and status updates.
"""

import mimetypes
from typing import Optional, List, Tuple
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.config import settings

from backend.app.core.database import get_db
from backend.app.models.complaint import Complaint
from backend.app.models.user import User
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
    process_multimodal_complaint,
    ComplaintProcessingError,
)
from backend.app.core.security import sanitize_text_input, validate_upload_content
from backend.app.utils.constants import ComplaintStatus, IMAGE_EXTENSIONS, AUDIO_EXTENSIONS
from backend.app.api.deps import (
    get_current_user,
    get_optional_current_user,
    get_current_admin,
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get(
    "/reverse-geocode",
    summary="Reverse geocode WGS84 coordinates to address via OpenStreetMap Nominatim",
)
def reverse_geocode_api(
    lat: float = Query(..., ge=-90.0, le=90.0, description="WGS84 Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="WGS84 Longitude"),
):
    """
    Reverse geocodes coordinates using OpenStreetMap Nominatim with rate-limiting,
    in-memory caching, and zero confidential data transmission.
    """
    from backend.app.services.geo.geocoding_service import reverse_geocode_coordinates
    return reverse_geocode_coordinates(lat=lat, lon=lon)


@router.post(
    "/inspect-image",
    summary="Inspect uploaded photo for EXIF GPS location and visual hazard priority",
)
async def inspect_uploaded_image(
    file: UploadFile = File(..., description="Grievance photo (JPG, PNG, WEBP) to inspect for GPS & priority"),
):
    """
    Inspects image before final submission to extract:
    1. EXIF GPS location (if present in image tags).
    2. Visual hazard indicators & predicted priority (Critical, High, Medium, Low).
    """
    file_bytes = await file.read()
    filename = file.filename or "photo.jpg"

    is_valid, err_msg = validate_upload_content(filename, file_bytes)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    ext = Path(filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files (.jpg, .jpeg, .png, .webp, .bmp) can be inspected here.",
        )

    from backend.app.services.extraction.image_extractor import extract_exif_gps_data, analyze_image_visual_priority

    exif_data = extract_exif_gps_data(file_bytes)
    visual_data = analyze_image_visual_priority(file_bytes, filename)

    return {
        "filename": filename,
        "has_gps": exif_data.get("has_gps", False),
        "latitude": exif_data.get("latitude"),
        "longitude": exif_data.get("longitude"),
        "location_name": exif_data.get("location_name"),
        "predicted_priority": visual_data.get("visual_priority", "Medium"),
        "category_hint": visual_data.get("category_hint", "Other"),
        "hazard_markers": visual_data.get("hazard_markers", []),
        "apparent_damage": visual_data.get("apparent_damage", "none"),
        "uncertainty_indicators": visual_data.get("uncertainty_indicators", []),
        "confidence": visual_data.get("confidence", 0.5),
        "vision_source": visual_data.get("vision_source", "offline_heuristic"),
        "visual_summary": visual_data.get("visual_summary", ""),
        "ocr_text": visual_data.get("ocr_text", ""),
    }


@router.post(
    "/inspect-audio",
    summary="Inspect recorded or uploaded audio: transcribe speech, extract words via NLP, and predict urgency",
)
async def inspect_uploaded_audio(
    file: UploadFile = File(..., description="Recorded or uploaded audio file (WAV, MP3, WEBM, M4A, OGG, AAC)"),
    transcript: Optional[str] = Form(None, description="Optional spoken transcription (e.g. from Web Speech API or citizen edit)"),
):
    """
    Inspects recorded or uploaded audio before submission:
    1. Transcribes speech verbatim (preserving English, Marathi, or Hindi).
    2. Runs deterministic NLP word tokenization and stopword-filtered keyword extraction.
    3. Identifies municipal hazard words and predicts urgency level.
    """
    file_bytes = await file.read()
    filename = file.filename or "recording.webm"

    is_valid, err_msg = validate_upload_content(filename, file_bytes)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    ext = Path(filename).suffix.lower()
    if ext not in AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only audio files ({', '.join(sorted(AUDIO_EXTENSIONS))}) can be inspected here.",
        )

    from backend.app.services.extraction.audio_extractor import extract_text_from_audio

    success, raw_text, paragraphs, error_msg, meta = extract_text_from_audio(
        file_bytes, filename, transcript=transcript
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "Failed to transcribe or extract words from audio.",
        )

    return {
        "filename": filename,
        "transcription": meta.get("transcription", ""),
        "extracted_words": meta.get("extracted_words", []),
        "filtered_keywords": meta.get("filtered_keywords", []),
        "hazard_keywords": meta.get("hazard_keywords", []),
        "predicted_priority": meta.get("audio_priority", "Medium"),
        "apparent_damage": meta.get("apparent_damage", "none"),
        "uncertainty_indicators": meta.get("uncertainty_indicators", []),
        "detected_language": meta.get("detected_language", "en"),
        "transcription_source": meta.get("transcription_source", "whisper_base"),
        "transcription_error": meta.get("transcription_error"),
        "speech_detected": meta.get("speech_detected", False),
        "spoken_location": meta.get("spoken_location"),
        "category_hint": meta.get("category_hint", "Other"),
        "duration_seconds": meta.get("duration_seconds"),
        "word_count": len(meta.get("extracted_words", [])),
    }


@router.post(
    "/upload",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload citizen complaint with mandatory image and optional audio/document attachments",
)
async def upload_complaint_document(
    files: Optional[List[UploadFile]] = File(None, description="Multiple attachments: mandatory image(s) + optional audio/documents (up to 10 MB each)"),
    file: Optional[UploadFile] = File(None, description="Single complaint attachment (backward compatibility)"),
    complaint_text: Optional[str] = Form(None),
    citizen_name: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None, description="WGS84 latitude coordinate"),
    longitude: Optional[float] = Form(None, description="WGS84 longitude coordinate"),
    location_accuracy: Optional[float] = Form(None, description="Reported GPS accuracy radius in metres"),
    location_captured_at: Optional[str] = Form(None, description="ISO timestamp of location capture"),
    location_source: Optional[str] = Form(None, description="Origin: device_gps, image_exif, manual_map, manual_text"),
    address: Optional[str] = Form(None, description="Human readable address or landmark"),
    visual_priority: Optional[str] = Form(None, description="Citizen-specified or UI-confirmed visual priority level"),
    require_image: bool = Form(False, description="When true, enforces that at least one uploaded file is an image"),
    transcript: Optional[str] = Form(None, description="Optional spoken transcription for attached audio"),
    audio_transcripts: Optional[str] = Form(None, description="Optional JSON map of filename to spoken transcript"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts one or more complaint attachments (mandatory image + optional audio recordings and documents),
    validates file types/sizes, extracts and correlates multimodal content across all files,
    runs deterministic NLP classification, assigns department, detects priority, and saves record to SQLite.
    """
    upload_items: List[UploadFile] = []
    if files:
        upload_items.extend([f for f in files if f and f.filename])
    if file and file.filename:
        upload_items.append(file)

    if not upload_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory Image Upload Required: Please upload at least one image (.jpg, .jpeg, .png, .webp, .bmp) to file a complaint.",
        )

    validated_files: List[Tuple[str, bytes]] = []
    has_image = False

    for upload_obj in upload_items:
        f_bytes = await upload_obj.read()
        f_name = upload_obj.filename or "uploaded_attachment"

        is_valid, err_msg = validate_upload_content(f_name, f_bytes)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attachment '{f_name}' validation failed: {err_msg}",
            )

        ext = Path(f_name).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            has_image = True

        validated_files.append((f_name, f_bytes))

    # Enforce mandatory image upload when required by the Complaint Section or when multiple files are attached
    if (require_image or len(validated_files) > 1) and not has_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory Image Upload Required: You must upload at least one image (.jpg, .jpeg, .png, .webp, .bmp) to file a complaint. Audio and document attachments are optional.",
        )

    clean_text = sanitize_text_input(complaint_text) if complaint_text else None
    clean_name = sanitize_text_input(citizen_name) if citizen_name else (current_user.full_name if current_user else None)
    clean_loc = sanitize_text_input(location) if location else None

    # Parse audio transcripts mapping
    transcripts_dict: Dict[str, str] = {}
    if audio_transcripts:
        try:
            import json
            parsed = json.loads(audio_transcripts)
            if isinstance(parsed, dict):
                transcripts_dict = {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            pass
    if transcript:
        for fname, _ in validated_files:
            if Path(fname).suffix.lower() in AUDIO_EXTENSIONS:
                transcripts_dict[fname] = transcript

    try:
        complaint = process_multimodal_complaint(
            db=db,
            files_list=validated_files,
            complaint_text=clean_text,
            citizen_name=clean_name,
            location=clean_loc,
            user_id=current_user.id if current_user else None,
            require_image=require_image or len(validated_files) > 1,
            audio_transcripts=transcripts_dict,
            visual_priority=visual_priority,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            location_captured_at=location_captured_at,
            location_source=location_source,
            address=address,
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
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts raw grievance text, runs NLP preprocessing, rule-based classification,
    priority detection, department routing, and stores to database.
    Attaches user_id if authenticated.
    """
    clean_text = sanitize_text_input(payload.complaint_text)
    clean_name = sanitize_text_input(payload.citizen_name) if payload.citizen_name else (current_user.full_name if current_user else None)
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
            user_id=current_user.id if current_user else None,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_accuracy=payload.location_accuracy,
            location_captured_at=payload.location_captured_at,
            location_source=payload.location_source,
            address=payload.address,
        )
        return complaint
    except ComplaintProcessingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing failed: {str(e)}")


@router.get(
    "",
    response_model=ComplaintListResponse,
    summary="List complaints with search, filters, and role-based segregation",
)
def list_complaints(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    my_only: bool = Query(False, description="Filter complaints submitted by current user"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated complaints with role-based filtering:
    - CITIZEN: Strictly views ONLY their own submitted grievances (WHERE user_id == current_user.id).
    - ADMIN: Views all complaints across municipal departments (or scoped to their department).
    """
    query = db.query(Complaint)

    # Role-Based Data Segregation
    if current_user.role == "CITIZEN" or my_only:
        query = query.filter(Complaint.user_id == current_user.id)
    elif current_user.role == "ADMIN":
        # Strict Departmental Administrator Segregation:
        # If not Super Admin, the department administrator is strictly restricted to their own department!
        if not current_user.is_super_admin and current_user.department:
            query = query.filter(Complaint.department == current_user.department)
        elif department:
            query = query.filter(Complaint.department == department)

    if category:
        query = query.filter(Complaint.category == category)
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
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Complaint '{complaint_id}' not found.")

    # Guard: Citizen cannot inspect other citizens' complaints
    if current_user and current_user.role == "CITIZEN" and complaint.user_id is not None and complaint.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view your own submitted grievances.",
        )

    # Guard: Department Admin can only view complaints within their assigned department
    if current_user and current_user.role == "ADMIN" and not current_user.is_super_admin and current_user.department:
        if complaint.department != current_user.department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: You are restricted to viewing complaints within your assigned department ({current_user.department}).",
            )

    return complaint


@router.get(
    "/{complaint_id}/attachment",
    summary="Download or view uploaded complaint attachment (photo, audio, document)",
)
def get_complaint_attachment(
    complaint_id: str,
    index: int = Query(0, ge=0, description="Attachment index (0-based)"),
    download: bool = Query(False, description="Set to true to force download"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Complaint '{complaint_id}' not found.")

    # Guard: Citizen cannot view other citizens' private attachments
    if current_user and current_user.role == "CITIZEN" and complaint.user_id is not None and complaint.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view your own submitted grievances.",
        )

    # Guard: Department Admin can only view complaints within their assigned department
    if current_user and current_user.role == "ADMIN" and not current_user.is_super_admin and current_user.department:
        if complaint.department != current_user.department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: You are restricted to viewing complaints within your assigned department ({current_user.department}).",
            )

    # Locate attachment file on disk (supports indexed multi-attachments + legacy single attachment)
    file_path = None
    target_file_name = None

    attachments = complaint.attachments if isinstance(complaint.attachments, list) else []
    if attachments:
        if index >= len(attachments):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment index {index} out of range for complaint '{complaint_id}' (total: {len(attachments)}).",
            )
        att_entry = attachments[index]
        target_file_name = att_entry.get("file_name")
        att_stored_path = att_entry.get("file_path")
        if att_stored_path:
            candidate = settings.UPLOAD_DIR / att_stored_path
            if candidate.is_file():
                file_path = candidate
        if not file_path and target_file_name:
            for candidate_name in [
                f"{complaint.id}_{index}_{target_file_name}",
                f"{complaint.id}_{target_file_name}",
                target_file_name,
            ]:
                candidate = settings.UPLOAD_DIR / candidate_name
                if candidate.is_file():
                    file_path = candidate
                    break

    # Legacy fallback for index 0
    if not file_path and index == 0:
        if complaint.source_file_path:
            candidate = settings.UPLOAD_DIR / complaint.source_file_path
            if candidate.is_file():
                file_path = candidate

        if not file_path and complaint.source_file_name:
            for candidate_name in [
                f"{complaint.id}_{complaint.source_file_name}",
                complaint.source_file_name,
            ]:
                candidate = settings.UPLOAD_DIR / candidate_name
                if candidate.is_file():
                    file_path = candidate
                    break

    if not file_path or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stored attachment file found for complaint '{complaint_id}' at index {index}.",
        )

    # Determine media type
    media_type, _ = mimetypes.guess_type(str(file_path))
    if not media_type:
        ext = file_path.suffix.lower()
        if ext in [".jpg", ".jpeg"]:
            media_type = "image/jpeg"
        elif ext == ".png":
            media_type = "image/png"
        elif ext == ".webp":
            media_type = "image/webp"
        elif ext == ".bmp":
            media_type = "image/bmp"
        elif ext == ".mp3":
            media_type = "audio/mpeg"
        elif ext == ".wav":
            media_type = "audio/wav"
        elif ext in [".m4a", ".aac"]:
            media_type = "audio/mp4"
        elif ext == ".ogg":
            media_type = "audio/ogg"
        elif ext == ".webm":
            media_type = "audio/webm"
        elif ext == ".pdf":
            media_type = "application/pdf"
        elif ext == ".docx":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif ext == ".txt":
            media_type = "text/plain"
        else:
            media_type = "application/octet-stream"

    filename = target_file_name or complaint.source_file_name or file_path.name
    disposition = "attachment" if download else "inline"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        content_disposition_type=disposition,
    )


@router.put(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Update complaint status, department, priority, or resolution notes (Admin Only)",
)
def update_complaint(
    complaint_id: str,
    payload: ComplaintUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Updates complaint status, reassignment, or resolution.
    STRICTLY RESTRICTED TO MUNICIPAL ADMINISTRATORS.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Complaint '{complaint_id}' not found.")

    # Guard: Department Admin can only update complaints within their assigned department
    if not current_user.is_super_admin and current_user.department:
        if complaint.department != current_user.department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: You can only update complaints within your assigned department ({current_user.department}).",
            )
        # Department Admin cannot reassign complaints to a different department
        if payload.department is not None and payload.department.value != current_user.department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Department administrators cannot reassign complaints outside ({current_user.department}).",
            )

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
    summary="Delete a complaint record (Admin Only)",
)
def delete_complaint(
    complaint_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Removes a complaint record.
    STRICTLY RESTRICTED TO MUNICIPAL ADMINISTRATORS.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Complaint '{complaint_id}' not found.")

    # Guard: Department Admin can only delete complaints within their assigned department
    if not current_user.is_super_admin and current_user.department:
        if complaint.department != current_user.department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: You can only delete complaints within your assigned department ({current_user.department}).",
            )

    db.delete(complaint)
    db.commit()
    return {"message": f"Complaint '{complaint_id}' successfully removed.", "deleted_id": complaint_id}
