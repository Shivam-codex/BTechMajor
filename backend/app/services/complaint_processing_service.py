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

from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.complaint import Complaint, generate_complaint_id
from backend.app.services.extraction.document_service import extract_document_text
from backend.app.services.nlp.preprocessing import preprocess_complaint
from backend.app.services.classification.classifier import classify_complaint
from backend.app.services.classification.department_router import assign_department
from backend.app.services.classification.priority_detector import detect_priority
from backend.app.utils.constants import (
    SourceType,
    ComplaintStatus,
    ComplaintPriority,
    IMAGE_EXTENSIONS,
    AUDIO_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
)
from backend.app.core.logging import log_event, logger
from backend.app.models.base import utc_now
from backend.app.core.config import settings
from backend.app.utils.file_utils import sanitize_filename


class ComplaintProcessingError(Exception):
    """Raised when an unrecoverable error occurs during complaint ingestion."""
    pass


PRIORITY_RANK = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


def process_complaint_pipeline(
    db: Session,
    complaint_text: str,
    citizen_name: Optional[str] = None,
    location: Optional[str] = None,
    source_type: str = SourceType.MANUAL.value,
    source_file_name: Optional[str] = None,
    source_file_path: Optional[str] = None,
    extracted_text: Optional[str] = None,
    user_id: Optional[int] = None,
    visual_priority: Optional[str] = None,
    complaint_id: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    visual_evidence: Optional[Dict[str, Any]] = None,
    audio_evidence: Optional[Dict[str, Any]] = None,
    citizen_text: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_accuracy: Optional[float] = None,
    location_captured_at: Optional[Any] = None,
    location_source: Optional[str] = None,
    address: Optional[str] = None,
) -> Complaint:
    """
    Executes complete deterministic processing on complaint text and persists record.
    """
    clean_text = (complaint_text or "").strip()
    if not clean_text:
        raise ComplaintProcessingError("Complaint text cannot be empty.")

    # Parse location timestamp if provided
    parsed_captured_at = None
    if location_captured_at:
        from datetime import datetime
        if isinstance(location_captured_at, datetime):
            parsed_captured_at = location_captured_at
        elif isinstance(location_captured_at, str):
            try:
                from dateutil import parser as dt_parser
                parsed_captured_at = dt_parser.parse(location_captured_at)
            except Exception:
                pass

    # 1. Deterministic NLP Preprocessing
    nlp_result = preprocess_complaint(clean_text)

    # 2. Rule-Based Classification
    classification = classify_complaint(nlp_result)

    # 3. Automatic Department Assignment
    department, routing_reason = assign_department(classification.category)

    # 4. Deterministic Priority Detection (with multimodal visual & audio context)
    priority_res = detect_priority(
        nlp_result,
        visual_priority=visual_priority,
        visual_evidence=visual_evidence,
        audio_evidence=audio_evidence,
        citizen_text=citizen_text,
    )

    # 5. Determine initial status: if priority is Review Required, mark Needs Review
    initial_status = classification.status
    if priority_res.priority == ComplaintPriority.REVIEW_REQUIRED.value:
        initial_status = ComplaintStatus.NEEDS_REVIEW.value
    elif initial_status == ComplaintStatus.CLASSIFIED.value:
        initial_status = ComplaintStatus.ASSIGNED.value

    # 6. Build and persist Complaint model
    complaint = Complaint(
        id=complaint_id or generate_complaint_id(),
        user_id=user_id,
        complaint_text=clean_text,
        extracted_text=extracted_text,
        source_file_name=source_file_name,
        source_file_path=source_file_path,
        source_type=source_type,
        attachments=attachments or [],
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
        location=location or address,
        latitude=latitude,
        longitude=longitude,
        location_accuracy=location_accuracy,
        location_captured_at=parsed_captured_at,
        location_source=location_source,
        address=address or location,
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
        "attachment_count": len(complaint.attachments or []),
    })

    return complaint


def process_multimodal_complaint(
    db: Session,
    files_list: List[Tuple[str, bytes]],
    complaint_text: Optional[str] = None,
    citizen_name: Optional[str] = None,
    location: Optional[str] = None,
    user_id: Optional[int] = None,
    require_image: bool = True,
    audio_transcripts: Optional[Dict[str, str]] = None,
    visual_priority: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_accuracy: Optional[float] = None,
    location_captured_at: Optional[Any] = None,
    location_source: Optional[str] = None,
    address: Optional[str] = None,
) -> Complaint:
    """
    Processes a complaint containing one or more uploaded attachments (mandatory image(s) + optional audio/documents).
    1. Enforces mandatory image upload when require_image=True.
    2. Extracts text, audio speech transcription, document tables/text, and image EXIF GPS / visual hazard markers.
    3. Correlates evidence across all uploaded attachments and optional citizen text.
    4. Persists all uploaded files to disk and stores structured attachment metadata on the Complaint record.
    """
    if not files_list:
        raise ComplaintProcessingError("At least one image file must be uploaded to submit a complaint.")

    has_image = any(
        Path(sanitize_filename(fname)).suffix.lower() in IMAGE_EXTENSIONS
        for fname, _ in files_list
    )
    if require_image and not has_image:
        raise ComplaintProcessingError(
            "Mandatory Image Upload Required: Please upload at least one image (.jpg, .jpeg, .png, .webp, .bmp) to file a complaint."
        )

    cid = generate_complaint_id()
    try:
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create upload directory: {e}")

    attachments_list: List[Dict[str, Any]] = []
    extracted_sections: List[str] = []
    source_types_seen: List[str] = []
    highest_multimodal_priority: Optional[str] = None
    exif_gps_location: Optional[str] = None
    spoken_audio_location: Optional[str] = None
    primary_visual_meta: Optional[Dict[str, Any]] = None
    primary_audio_meta: Optional[Dict[str, Any]] = None

    transcripts_map = audio_transcripts or {}

    for idx, (file_name, file_bytes) in enumerate(files_list):
        safe_lookup = sanitize_filename(file_name)
        file_transcript = transcripts_map.get(file_name) or transcripts_map.get(safe_lookup)
        extraction_res = extract_document_text(file_name, file_bytes, transcript=file_transcript)
        if not extraction_res.success:
            raise ComplaintProcessingError(
                f"Failed to process attachment '{file_name}': {extraction_res.error or 'Unable to extract content.'}"
            )

        safe_name = extraction_res.source_file_name
        ext = Path(safe_name).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            media_category = "image"
        elif ext in AUDIO_EXTENSIONS:
            media_category = "audio"
        else:
            media_category = "document"

        stored_name = f"{cid}_{safe_name}" if idx == 0 else f"{cid}_{idx}_{safe_name}"
        stored_path = None
        try:
            disk_target = settings.UPLOAD_DIR / stored_name
            disk_target.write_bytes(file_bytes)
            stored_path = stored_name
        except Exception as e:
            logger.warning(f"Could not persist upload '{safe_name}' to disk: {e}")

        meta = extraction_res.metadata or {}
        cleaned_content = extraction_res.cleaned_text

        # Track primary metadata for visual and audio evidence
        if ext in IMAGE_EXTENSIONS and primary_visual_meta is None:
            primary_visual_meta = meta
        if ext in AUDIO_EXTENSIONS and primary_audio_meta is None:
            primary_audio_meta = meta

        # Track location hints from Image EXIF GPS and Audio transcription
        if meta.get("has_gps") and meta.get("location_name") and not exif_gps_location:
            exif_gps_location = meta["location_name"]
        if meta.get("spoken_location") and not spoken_audio_location:
            spoken_audio_location = meta["spoken_location"]

        # Track highest priority across Image visual inspection and Audio urgency analysis
        candidate_priority = meta.get("visual_priority") or meta.get("audio_priority")
        if candidate_priority in PRIORITY_RANK:
            if (
                highest_multimodal_priority is None
                or PRIORITY_RANK[candidate_priority] > PRIORITY_RANK.get(highest_multimodal_priority, 0)
            ):
                highest_multimodal_priority = candidate_priority

        source_types_seen.append(extraction_res.source_type)
        if len(files_list) == 1:
            extracted_sections.append(cleaned_content)
        else:
            extracted_sections.append(
                f"--- [{extraction_res.source_type} Attachment #{idx + 1}: {safe_name}] ---\n{cleaned_content}"
            )

        attachments_list.append({
            "index": idx,
            "file_name": safe_name,
            "file_path": stored_path,
            "source_type": extraction_res.source_type,
            "media_category": media_category,
            "extracted_text": cleaned_content,
            "metadata": meta,
            "url": f"/api/complaints/{cid}/attachment?index={idx}",
        })

    # Factor in explicit citizen / UI visual priority selection if provided
    if visual_priority and visual_priority.strip().capitalize() in PRIORITY_RANK:
        vp_cap = visual_priority.strip().capitalize()
        if (
            highest_multimodal_priority is None
            or PRIORITY_RANK[vp_cap] > PRIORITY_RANK.get(highest_multimodal_priority, 0)
        ):
            highest_multimodal_priority = vp_cap

    # Location resolution:
    # 1. If explicit coordinates are provided (from device GPS or manual map selection), preserve them
    # 2. If no coordinates were supplied, check photo EXIF GPS as separate fallback source
    # 3. Finally fall back to spoken audio or location text
    resolved_lat = latitude
    resolved_lon = longitude
    resolved_acc = location_accuracy
    resolved_time = location_captured_at
    resolved_source = location_source
    resolved_address = address
    resolved_location = location

    if resolved_lat is not None and resolved_lon is not None:
        if not resolved_location:
            resolved_location = resolved_address or f"Lat: {resolved_lat:.5f}, Lon: {resolved_lon:.5f}"
        if not resolved_source:
            resolved_source = "device_gps"
    elif exif_gps_location:
        # Photo contains EXIF GPS; if citizen provided no explicit location, use as image_exif source
        if not resolved_location or not resolved_location.strip() or "device location" in resolved_location.lower():
            resolved_location = exif_gps_location
            resolved_address = exif_gps_location
            resolved_source = "image_exif"
            if primary_visual_meta:
                resolved_lat = primary_visual_meta.get("latitude")
                resolved_lon = primary_visual_meta.get("longitude")
    elif spoken_audio_location and (not resolved_location or not resolved_location.strip()):
        resolved_location = spoken_audio_location
        resolved_source = "spoken_audio"

    combined_extracted_text = "\n\n".join(extracted_sections)

    # Build unified complaint text correlating manual description + all attachments
    if len(files_list) == 1:
        single_att = attachments_list[0]
        if complaint_text and complaint_text.strip():
            final_text = (
                f"{complaint_text.strip()}\n\n"
                f"[Attached {single_att['source_type']} ({single_att['file_name']}) Content]:\n{combined_extracted_text}"
            )
        else:
            final_text = combined_extracted_text
    else:
        attachment_blocks = [
            f"[Attached {att['source_type']} ({att['file_name']}) Content]:\n{att['extracted_text']}"
            for att in attachments_list
        ]
        joined_blocks = "\n\n".join(attachment_blocks)
        if complaint_text and complaint_text.strip():
            final_text = f"{complaint_text.strip()}\n\n{joined_blocks}"
        else:
            final_text = joined_blocks

    # Determine primary source_type and primary file metadata for backward compatibility
    unique_types = set(source_types_seen)
    if len(unique_types) == 1:
        primary_source_type = source_types_seen[0]
    else:
        primary_source_type = SourceType.MULTIMODAL.value

    primary_attachment = attachments_list[0]

    citizen_statements = []
    if complaint_text and complaint_text.strip():
        citizen_statements.append(complaint_text.strip())
    for att in attachments_list:
        if att.get("source_type") == "AUDIO" and att.get("metadata", {}).get("transcription"):
            t = att["metadata"]["transcription"]
            if t and t not in citizen_statements:
                citizen_statements.append(t)
    effective_citizen_text = " ".join(citizen_statements) if citizen_statements else complaint_text

    return process_complaint_pipeline(
        db=db,
        complaint_id=cid,
        complaint_text=final_text,
        citizen_name=citizen_name,
        location=resolved_location,
        source_type=primary_source_type,
        source_file_name=primary_attachment["file_name"],
        source_file_path=primary_attachment["file_path"],
        extracted_text=combined_extracted_text,
        user_id=user_id,
        visual_priority=highest_multimodal_priority,
        attachments=attachments_list,
        visual_evidence=primary_visual_meta,
        audio_evidence=primary_audio_meta,
        citizen_text=effective_citizen_text,
        latitude=resolved_lat,
        longitude=resolved_lon,
        location_accuracy=resolved_acc,
        location_captured_at=resolved_time,
        location_source=resolved_source,
        address=resolved_address,
    )


def process_document_complaint(
    db: Session,
    file_name: str,
    file_bytes: bytes,
    complaint_text: Optional[str] = None,
    citizen_name: Optional[str] = None,
    location: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Complaint:
    """
    Single-file complaint processing wrapper (delegates to process_multimodal_complaint).
    Preserves backward compatibility with existing single-file tests and callers.
    """
    return process_multimodal_complaint(
        db=db,
        files_list=[(file_name, file_bytes)],
        complaint_text=complaint_text,
        citizen_name=citizen_name,
        location=location,
        user_id=user_id,
        require_image=False,
    )


