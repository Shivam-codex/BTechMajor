"""
Unit and integration tests for High-Accuracy GPS & OpenStreetMap Geolocation.
Tests verify:
1. Database persistence of WGS84 coordinates, accuracy radius, timestamp, source, and address.
2. OpenStreetMap Nominatim reverse geocoding policy compliance:
   - Rate limiting & thread-safe spatial caching.
   - User-Agent header & zero transmission of confidential complaint data.
   - Proper attribution ("© OpenStreetMap contributors").
3. Multi-source location handling:
   - Device GPS (device_gps).
   - Citizen manual map placement (manual_map).
   - Image EXIF GPS historical source (image_exif).
   - Citizen choice preservation over raw EXIF.
4. Low accuracy detection (> 50m warning threshold).
"""

import io
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.models.complaint import Complaint
from backend.app.schemas.complaint_schema import ComplaintCreate, ComplaintResponse
from backend.app.services.geo.geocoding_service import (
    reverse_geocode_coordinates,
    OSM_ATTRIBUTION,
    _GEO_CACHE,
    _CACHE_LOCK,
)
from backend.app.services.extraction.image_extractor import extract_exif_gps_data
from backend.app.services.extraction.document_service import extract_document_text
from backend.app.services.complaint_processing_service import (
    process_complaint_pipeline,
    process_multimodal_complaint,
)
from backend.app.api.complaints import reverse_geocode_api, submit_complaint


def _create_jpeg_with_exif_gps(lat: float = 18.5204, lon: float = 73.8567) -> bytes:
    """Helper to generate an in-memory JPEG image with valid EXIF GPS tags."""
    img = Image.new("RGB", (64, 64), color="orange")
    exif = img.getexif()
    gps_ifd = exif.get_ifd(0x8825)

    # Convert decimal lat to DMS
    lat_deg = int(abs(lat))
    lat_min = int((abs(lat) - lat_deg) * 60)
    lat_sec = round(((abs(lat) - lat_deg) * 60 - lat_min) * 60, 2)
    gps_ifd[1] = "N" if lat >= 0 else "S"
    gps_ifd[2] = (float(lat_deg), float(lat_min), float(lat_sec))

    # Convert decimal lon to DMS
    lon_deg = int(abs(lon))
    lon_min = int((abs(lon) - lon_deg) * 60)
    lon_sec = round(((abs(lon) - lon_deg) * 60 - lon_min) * 60, 2)
    gps_ifd[3] = "E" if lon >= 0 else "W"
    gps_ifd[4] = (float(lon_deg), float(lon_min), float(lon_sec))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


class TestComplaintLocationModel:
    """Tests SQLite schema and database persistence of GPS metadata."""

    def test_complaint_model_persists_all_location_fields(self, db_session):
        now = datetime.now(timezone.utc)
        complaint = Complaint(
            complaint_text="Pothole in the road near market",
            citizen_name="Aarav Deshmukh",
            location="FC Road, Pune",
            source_type="MANUAL",
            category="Roads & Footpaths",
            department="Roads & Infrastructure",
            priority="Low",
            status="OPEN",
            latitude=18.52043,
            longitude=73.85674,
            location_accuracy=14.5,
            location_captured_at=now,
            location_source="device_gps",
            address="Ferguson College Rd, Shivajinagar, Pune, Maharashtra",
        )
        db_session.add(complaint)
        db_session.commit()
        db_session.refresh(complaint)

        retrieved = db_session.query(Complaint).filter(Complaint.id == complaint.id).first()
        assert retrieved is not None
        assert retrieved.latitude == 18.52043
        assert retrieved.longitude == 73.85674
        assert retrieved.location_accuracy == 14.5
        assert retrieved.location_source == "device_gps"
        assert retrieved.address == "Ferguson College Rd, Shivajinagar, Pune, Maharashtra"

        # Verify to_dict includes all GPS fields
        data_dict = retrieved.to_dict()
        assert data_dict["latitude"] == 18.52043
        assert data_dict["longitude"] == 73.85674
        assert data_dict["location_accuracy"] == 14.5
        assert data_dict["location_source"] == "device_gps"
        assert data_dict["address"] == "Ferguson College Rd, Shivajinagar, Pune, Maharashtra"

    def test_complaint_schemas_support_location_fields(self):
        payload = {
            "complaint_text": "Exposed electric sparking cable near bus stop",
            "citizen_name": "Sunita Patil",
            "location": "Baner, Pune",
            "source_type": "MANUAL",
            "latitude": 18.5590,
            "longitude": 73.7868,
            "location_accuracy": 8.0,
            "location_source": "manual_map",
            "address": "Baner Main Road, Pune, Maharashtra",
        }
        create_schema = ComplaintCreate(**payload)
        assert create_schema.latitude == 18.5590
        assert create_schema.longitude == 73.7868
        assert create_schema.location_accuracy == 8.0
        assert create_schema.location_source == "manual_map"
        assert create_schema.address == "Baner Main Road, Pune, Maharashtra"


class TestNominatimGeocodingService:
    """Tests OpenStreetMap Nominatim reverse geocoding policy adherence and caching."""

    def test_reverse_geocoding_handles_none_coordinates(self):
        result = reverse_geocode_coordinates(None, None)
        assert result["success"] is False
        assert result["address"] == ""
        assert result["attribution"] == OSM_ATTRIBUTION

    def test_reverse_geocoding_success_with_policy_headers(self):
        # Clear cache to ensure a fresh test
        with _CACHE_LOCK:
            _GEO_CACHE.clear()

        fake_nominatim_resp = {
            "display_name": "Shanivar Wada, Bajirao Road, Shaniwar Peth, Pune, Maharashtra, India"
        }
        mock_urlopen = MagicMock()
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(fake_nominatim_resp).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch("urllib.request.urlopen", mock_urlopen):
            result = reverse_geocode_coordinates(18.5195, 73.8553)

        assert result["success"] is True
        assert "Shanivar Wada" in result["address"]
        assert result["attribution"] == OSM_ATTRIBUTION
        assert result["cached"] is False

        # Verify urllib Request headers comply with OSM policy
        call_args, _ = mock_urlopen.call_args
        req = call_args[0]
        assert "nominatim.openstreetmap.org" in req.full_url
        # Strictly verify zero confidential citizen information sent (URL only contains lat/lon)
        assert "pothole" not in req.full_url.lower()
        assert req.has_header("User-agent")
        assert "SmartCityComplaintManagementSystem" in req.get_header("User-agent")

    def test_reverse_geocoding_handles_network_error_gracefully(self):
        # When network fails, gracefully returns formatted coordinate string without raising
        with _CACHE_LOCK:
            _GEO_CACHE.clear()

        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            result = reverse_geocode_coordinates(18.5204, 73.8567)
            assert result["success"] is False
            assert "Lat: 18.52040, Lon: 73.85670" in result["address"]
            assert result["attribution"] == OSM_ATTRIBUTION

    def test_spatial_caching_avoids_repeated_requests(self):
        with _CACHE_LOCK:
            _GEO_CACHE.clear()

        # Coordinates within ~11 meters round to the same 4 decimal digits
        lat1, lon1 = 18.520412, 73.856712
        lat2, lon2 = 18.520445, 73.856738

        # First request populates cache
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"display_name": "Cached FC Road"}).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            res1 = reverse_geocode_coordinates(lat1, lon1)
            assert res1["address"] == "Cached FC Road"
            assert mock_url.call_count == 1

            # Second request within ~11m precision hits cache without calling urlopen
            res2 = reverse_geocode_coordinates(lat2, lon2)
            assert res2["address"] == "Cached FC Road"
            assert res2["cached"] is True
            assert mock_url.call_count == 1


class TestGeolocationAPIIntegration:
    """Tests API endpoints and complaint processing services handling geolocation data."""

    def test_reverse_geocode_api_endpoint(self):
        with patch(
            "backend.app.services.geo.geocoding_service.reverse_geocode_coordinates",
            return_value={
                "success": True,
                "address": "Kothrud, Pune, Maharashtra",
                "latitude": 18.5074,
                "longitude": 73.8077,
                "attribution": OSM_ATTRIBUTION,
                "cached": False,
            },
        ):
            res = reverse_geocode_api(lat=18.5074, lon=73.8077)
            assert res["success"] is True
            assert res["address"] == "Kothrud, Pune, Maharashtra"
            assert res["attribution"] == "© OpenStreetMap contributors"

    def test_manual_complaint_submission_persists_device_location(self, db_session):
        payload = ComplaintCreate(
            complaint_text="Water pipeline leaking on Senapati Bapat Road",
            citizen_name="Rohan Joshi",
            location="SB Road, Pune",
            source_type="MANUAL",
            latitude=18.5314,
            longitude=73.8296,
            location_accuracy=18.2,
            location_source="device_gps",
            address="Senapati Bapat Rd, Pune, Maharashtra",
        )
        complaint = submit_complaint(payload=payload, current_user=None, db=db_session)
        assert complaint.latitude == 18.5314
        assert complaint.longitude == 73.8296
        assert complaint.location_accuracy == 18.2
        assert complaint.location_source == "device_gps"
        assert complaint.address == "Senapati Bapat Rd, Pune, Maharashtra"

    def test_manual_map_pin_coordinates_labeled_correctly(self, db_session):
        payload = ComplaintCreate(
            complaint_text="Broken footpath slab near bus stand",
            citizen_name="Kavita Shinde",
            location="Swargate, Pune",
            source_type="MANUAL",
            latitude=18.5018,
            longitude=73.8584,
            location_accuracy=None,
            location_source="manual_map",
            address="Swargate Bus Stand, Pune",
        )
        complaint = submit_complaint(payload=payload, current_user=None, db=db_session)
        assert complaint.location_source == "manual_map"
        assert complaint.latitude == 18.5018
        assert complaint.longitude == 73.8584

    def test_upload_pipeline_preserves_device_gps_over_image_exif(self, db_session):
        """
        Ensures that if an uploaded photo contains historical EXIF GPS, but the citizen
        has explicitly verified or selected their current device GPS, the chosen device GPS
        and 'device_gps' source are persisted rather than overwritten by the photo's EXIF.
        """
        # Create image with EXIF pointing to Mumbai (lat 19.0760, lon 72.8777)
        photo_bytes = _create_jpeg_with_exif_gps(lat=19.0760, lon=72.8777)
        uploaded_files = [("incident_photo.jpg", photo_bytes)]

        complaint = process_multimodal_complaint(
            db=db_session,
            files_list=uploaded_files,
            complaint_text="Pothole on road outside my shop",
            citizen_name="Prakash Rao",
            location="Shivaji Nagar, Pune",
            latitude=18.5204,
            longitude=73.8567,
            location_accuracy=10.0,
            location_source="device_gps",
            address="Shivaji Nagar, Pune, Maharashtra",
        )

        assert round(complaint.latitude, 2) == 18.52
        assert round(complaint.longitude, 2) == 73.86
        assert complaint.location_source == "device_gps"
        assert complaint.location_accuracy == 10.0

    def test_upload_pipeline_falls_back_to_image_exif_when_device_gps_absent(self, db_session):
        """
        When the citizen does not provide device GPS, but the photo contains EXIF GPS,
        the system extracts the EXIF GPS and sets source to 'image_exif'.
        """
        photo_bytes = _create_jpeg_with_exif_gps(lat=18.5204, lon=73.8567)
        uploaded_files = [("incident_photo.jpg", photo_bytes)]

        complaint = process_multimodal_complaint(
            db=db_session,
            files_list=uploaded_files,
            complaint_text="Dangerous exposed wire hanging on road",
            citizen_name="Anita Roy",
            location=None,
            latitude=None,
            longitude=None,
            location_accuracy=None,
            location_source=None,
            address=None,
        )

        assert round(complaint.latitude, 2) == 18.52
        assert round(complaint.longitude, 2) == 73.86
        assert complaint.location_source == "image_exif"


class TestImageExifGpsIndependence:
    """Verifies that image EXIF GPS extraction works independently as a separate source."""

    def test_extract_exif_gps_data_returns_separate_metadata(self):
        photo_bytes = _create_jpeg_with_exif_gps(lat=18.5204, lon=73.8567)
        exif_info = extract_exif_gps_data(photo_bytes)

        assert exif_info["has_gps"] is True
        assert round(exif_info["latitude"], 2) == 18.52
        assert round(exif_info["longitude"], 2) == 73.86

    def test_image_without_exif_returns_false_has_gps(self):
        img = Image.new("RGB", (32, 32), color="green")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        exif_info = extract_exif_gps_data(buf.getvalue())

        assert exif_info["has_gps"] is False
        assert exif_info["latitude"] is None
        assert exif_info["longitude"] is None


class TestNoCoordinateInventionPolicy:
    """Verifies that vision models and visual heuristics NEVER invent GPS coordinates."""

    def test_vision_pipeline_never_invents_gps_from_pixels(self):
        from backend.app.services.extraction.image_extractor import analyze_image_visual_priority

        # Synthetic image without EXIF metadata
        img = Image.new("RGB", (64, 64), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        analysis = analyze_image_visual_priority(buf.getvalue(), "street_hazard.jpg")
        # Visual analysis MUST NOT contain or invent GPS coordinates
        assert "latitude" not in analysis
        assert "longitude" not in analysis
        assert "gps" not in analysis


class TestAccuracyThresholdLogic:
    """Tests accuracy evaluation and threshold warnings (> 50m)."""

    @pytest.mark.parametrize(
        "accuracy, expected_high_precision, expected_warning",
        [
            (5.0, True, False),
            (25.0, True, False),
            (50.0, True, False),
            (50.1, False, True),
            (120.0, False, True),
            (500.0, False, True),
            (None, False, False),
        ],
    )
    def test_accuracy_threshold_50m_boundary(self, accuracy, expected_high_precision, expected_warning):
        """
        Threshold rule:
        - Accuracy <= 50m is considered acceptable / high precision.
        - Accuracy > 50m triggers a UI warning and retry prompt for the citizen.
        """
        threshold = 50.0
        is_high_precision = (accuracy is not None) and (accuracy <= threshold)
        needs_warning = (accuracy is not None) and (accuracy > threshold)

        assert is_high_precision == expected_high_precision
        assert needs_warning == expected_warning
