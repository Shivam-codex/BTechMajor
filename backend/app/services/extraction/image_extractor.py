"""
Local-First Image Grievance Extractor and Visual Inspector.
Architecture:
1. Camera EXIF Metadata: GPS coordinate extraction & reverse-geocoding.
2. Local Vision AI: Ollama with Gemma 3 Vision (gemma3:4b) for zero-cost, private incident scene inspection.
3. Robust Offline Fallback: OpenCV & Pillow computer vision (Laplacian blur detection, luminance, texture & color metrics).
4. No external paid vision API dependencies. Does not invent GPS or injuries from pixels alone.
"""

import io
import json
import base64
import logging
import urllib.request
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ExifTags, ImageStat, ImageFilter
import cv2
import numpy as np

from backend.app.core.config import settings

logger = logging.getLogger("smart_city_backend")

IMAGE_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def _dms_to_decimal(dms, ref: Optional[str]) -> Optional[float]:
    """Convert degrees, minutes, seconds tuple/list to decimal degrees."""
    if not dms or len(dms) < 3:
        return None
    try:
        deg = float(dms[0])
        minute = float(dms[1])
        sec = float(dms[2])
        decimal = deg + (minute / 60.0) + (sec / 3600.0)
        if ref and ref.strip().upper() in ["S", "W"]:
            decimal = -decimal
        return round(decimal, 6)
    except Exception as exc:
        logger.debug("Failed to convert DMS to decimal: %s", exc)
        return None


def reverse_geocode(lat: float, lon: float, timeout_sec: float = 1.5) -> str:
    """
    Reverse-geocodes GPS coordinates to human-readable address using OpenStreetMap Nominatim.
    Uses strict 1.5s timeout; falls back cleanly to coordinate string if offline or unreachable.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SmartCityComplaintSystem/1.0 (local-academic-project)"}
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            display_name = data.get("display_name")
            if display_name:
                return display_name
    except Exception as exc:
        logger.debug("Reverse geocoding timed out or offline: %s", exc)

    return f"Lat: {lat:.5f}, Lon: {lon:.5f}"


def extract_exif_gps_data(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts GPS tags, camera details, and resolves location name from image EXIF data.
    """
    result: Dict[str, Any] = {
        "has_gps": False,
        "latitude": None,
        "longitude": None,
        "location_name": None,
        "width": 0,
        "height": 0,
        "format": "UNKNOWN",
        "camera_make": None,
        "camera_model": None,
        "date_time": None,
    }

    if not file_bytes:
        return result

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            result["width"], result["height"] = img.size
            result["format"] = img.format or "JPEG"

            # IFD extraction
            exif = img.getexif() if hasattr(img, "getexif") else None
            gps_info = {}

            if exif is not None:
                try:
                    gps_ifd = exif.get_ifd(0x8825)
                    if gps_ifd:
                        gps_info = dict(gps_ifd)
                except Exception:
                    pass

                result["camera_make"] = exif.get(271)
                result["camera_model"] = exif.get(272)
                result["date_time"] = exif.get(306)

            if not gps_info and hasattr(img, "_getexif"):
                legacy_exif = img._getexif()
                if legacy_exif:
                    for tag_id, val in legacy_exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag_name == "GPSInfo" and isinstance(val, dict):
                            gps_info = val
                            break

            lat_raw = gps_info.get(2) or gps_info.get("GPSLatitude")
            lat_ref = gps_info.get(1) or gps_info.get("GPSLatitudeRef")
            lon_raw = gps_info.get(4) or gps_info.get("GPSLongitude")
            lon_ref = gps_info.get(3) or gps_info.get("GPSLongitudeRef")

            if lat_raw and lon_raw:
                lat = _dms_to_decimal(lat_raw, lat_ref)
                lon = _dms_to_decimal(lon_raw, lon_ref)

                if lat is not None and lon is not None:
                    result["has_gps"] = True
                    result["latitude"] = lat
                    result["longitude"] = lon
                    result["location_name"] = reverse_geocode(lat, lon)
    except Exception as exc:
        logger.debug("Error reading image EXIF: %s", exc)

    return result


# -------------------------------------------------------------------------
# Ollama + Gemma 3 Vision Client
# -------------------------------------------------------------------------

def query_ollama_vision(file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """
    Queries local Ollama server running Gemma 3 Vision (e.g. gemma3:4b).
    Extracts structured factual observations:
    - incident_type
    - visible_hazards
    - apparent_damage (none, minor, moderate, severe)
    - severity_hint (Critical, High, Medium, Low, Review Required)
    - description
    - confidence (0.0 to 1.0)
    - uncertainty_indicators
    Returns None if Ollama is unreachable, times out, or output is malformed.
    """
    if not file_bytes or len(file_bytes) < 32:
        return None

    try:
        import httpx

        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        api_url = f"{base_url}/api/generate"
        b64_image = base64.b64encode(file_bytes).decode("utf-8")

        prompt = (
            "You are an expert Smart City Municipal Field Inspector. Analyze this civic incident photograph thoroughly.\n"
            "Report physical evidence factually. DO NOT invent injuries, financial loss, or invisible internal damage.\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "incident_type": "Road/Pothole" | "Street Light" | "Garbage/Waste Management" | "Water Supply" | "Drainage/Sewerage" | "Electricity" | "Public Toilet" | "Traffic" | "Other" | "Clean/No Damage",\n'
            '  "visible_hazards": ["list", "of", "physically", "visible", "hazards"],\n'
            '  "apparent_damage": "none" | "minor" | "moderate" | "severe",\n'
            '  "severity_hint": "Critical" | "High" | "Medium" | "Low" | "Review Required",\n'
            '  "description": "Factual description of physical damage and physical obstruction visible in the image.",\n'
            '  "confidence": 0.85,\n'
            '  "uncertainty_indicators": ["blur", "glare", "obstruction", "ambiguous_scene"]\n'
            "}"
        )

        payload = {
            "model": settings.OLLAMA_VISION_MODEL,
            "prompt": prompt,
            "images": [b64_image],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 256,
            }
        }

        with httpx.Client(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            resp = client.post(api_url, json=payload)
            if resp.status_code == 200:
                raw_json = resp.json().get("response", "{}")
                data = json.loads(raw_json)
                if isinstance(data, dict) and "incident_type" in data:
                    return {
                        "incident_type": str(data.get("incident_type", "Other")),
                        "visible_hazards": list(data.get("visible_hazards", [])),
                        "apparent_damage": str(data.get("apparent_damage", "moderate")).lower(),
                        "severity_hint": str(data.get("severity_hint", "Medium")),
                        "description": str(data.get("description", "")),
                        "confidence": float(data.get("confidence", 0.85)),
                        "uncertainty_indicators": list(data.get("uncertainty_indicators", [])),
                        "vision_source": "ollama_gemma3",
                    }
    except Exception as exc:
        logger.debug("Ollama Gemma 3 Vision query skipped/failed (%s): %s", type(exc).__name__, exc)

    return None


# -------------------------------------------------------------------------
# OpenCV & Pillow Local Computer Vision Fallback
# -------------------------------------------------------------------------

def analyze_image_local_cv(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Calibrated local computer-vision inspection using Pillow and OpenCV.
    Evaluates:
    - Blur / Image focus sharpness (Laplacian variance via OpenCV).
    - Luminance & dark-scene detection (low lux Street Light outage).
    - Color saturation for intense sparking wire / fire cues.
    - Surface edge roughness (calibrated texture analysis, avoiding false Highs on normal asphalt).
    """
    features: Dict[str, Any] = {
        "incident_type": "Other",
        "visible_hazards": [],
        "apparent_damage": "minor",
        "severity_hint": "Medium",
        "description": "",
        "confidence": 0.70,
        "uncertainty_indicators": [],
        "vision_source": "local_cv_fallback",
    }

    if not file_bytes:
        features["uncertainty_indicators"].append("empty_image_bytes")
        features["severity_hint"] = "Review Required"
        return features

    try:
        # 1. OpenCV Image Quality / Blur Check
        nparr = np.frombuffer(file_bytes, np.uint8)
        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if cv_img is not None:
            gray_cv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            laplacian_var = float(cv2.Laplacian(gray_cv, cv2.CV_64F).var())
            if laplacian_var < 30.0:
                features["uncertainty_indicators"].append("image_blurred_or_low_focus")

        # 2. Pillow Luminance & Texture Analysis
        with Image.open(io.BytesIO(file_bytes)) as img:
            rgb_img = img.convert("RGB")
            thumb = rgb_img.resize((160, 160))
            gray = thumb.convert("L")

            # Average luminance & RGB channel maxima
            stat_gray = ImageStat.Stat(gray)
            lum = float(stat_gray.mean[0])
            stat_rgb = ImageStat.Stat(thumb)
            max_channel = float(max(stat_rgb.mean[:3]))

            # Edge texture density (with 2-pixel border crop)
            edges = gray.filter(ImageFilter.FIND_EDGES)
            cropped_edges = edges.crop((2, 2, 158, 158))
            edge_density = float(ImageStat.Stat(cropped_edges).mean[0])

            # Pixel color distribution (spark / flame / dark pixels)
            if hasattr(thumb, "get_flattened_data"):
                pixels = list(thumb.get_flattened_data())
            else:
                pixels = list(thumb.getdata())

            total_px = len(pixels)
            hazard_color_count = 0
            dark_pixels = 0

            for r, g, b in pixels:
                if r < 40 and g < 40 and b < 40:
                    dark_pixels += 1
                # Fire / sparks / exposed copper: intense red/yellow saturation
                if (r > 180 and g < 90 and b < 60) or (r > 200 and g > 160 and b < 40):
                    hazard_color_count += 1

            hazard_ratio = hazard_color_count / float(total_px or 1)
            dark_ratio = dark_pixels / float(total_px or 1)

            # Heuristic decision tree (calibrated to prevent false HIGHs):
            # A. Critical: Active spark / fire pattern
            if hazard_ratio > 0.08:
                features["incident_type"] = "Electricity"
                features["apparent_damage"] = "severe"
                features["severity_hint"] = "Critical"
                features["visible_hazards"].append("visual_spark_or_flame_pattern")
                features["description"] = "Visible electrical hazard / spark pattern detected from intense color saturation."

            # B. High: Severe asphalt crater / deep destruction (requires very high edge density > 18)
            elif edge_density > 18.0:
                features["incident_type"] = "Road/Pothole"
                features["apparent_damage"] = "severe"
                features["severity_hint"] = "High"
                features["visible_hazards"].append("severe_surface_fracture_crater")
                features["description"] = f"Severe road crater or deep asphalt fracture observed (edge variance: {round(edge_density, 1)})."

            # C. High: Dark street at night (light failure)
            elif max_channel < 55.0 and (lum < 35.0 or dark_ratio > 0.70):
                features["incident_type"] = "Street Light"
                features["apparent_damage"] = "moderate"
                features["severity_hint"] = "High"
                features["visible_hazards"].append("low_lux_street_lighting_failure")
                features["description"] = f"Very low illumination / dark street scene detected (lux mean: {round(lum, 1)})."

            # D. Medium: Moderate pothole / standard road roughness
            elif edge_density > 6.0:
                features["incident_type"] = "Road/Pothole"
                features["apparent_damage"] = "moderate"
                features["severity_hint"] = "Medium"
                features["visible_hazards"].append("road_surface_pothole")
                features["description"] = f"Standard road pothole or surface roughness observed (edge metric: {round(edge_density, 1)})."

            # E. Low: Smooth / minor damage or clean road
            elif edge_density < 3.0:
                features["incident_type"] = "Clean/No Damage"
                features["apparent_damage"] = "none"
                features["severity_hint"] = "Low"
                features["description"] = "Photograph shows an ordinary surface without prominent visible damage."

            else:
                features["incident_type"] = "Other"
                features["apparent_damage"] = "minor"
                features["severity_hint"] = "Low"
                features["description"] = "Attached photograph inspected. Minor surface texture observed without acute hazards."

    except Exception as exc:
        logger.debug("Local CV inspection failed: %s", exc)
        features["uncertainty_indicators"].append("cv_inspection_error")

    # Filename keyword hints as supporting cues
    fn_lower = filename.lower()
    if any(k in fn_lower for k in ["wire", "electric", "spark"]):
        if features["incident_type"] == "Other":
            features["incident_type"] = "Electricity"
    elif any(k in fn_lower for k in ["pothole", "crater"]):
        if features["incident_type"] == "Other":
            features["incident_type"] = "Road/Pothole"

    return features


def analyze_image_visual_priority(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Main image visual inspection handler.
    1. Attempts Ollama Gemma 3 Vision query (gemma3:4b).
    2. Falls back cleanly to local OpenCV + Pillow computer vision.
    Returns structured visual evidence.
    """
    # 1. Try Ollama local vision model first
    ollama_result = query_ollama_vision(file_bytes, filename)
    if ollama_result is not None:
        return {
            "visual_priority": ollama_result["severity_hint"],
            "category_hint": ollama_result["incident_type"],
            "apparent_damage": ollama_result["apparent_damage"],
            "hazard_markers": ollama_result["visible_hazards"],
            "visual_summary": ollama_result["description"],
            "confidence": ollama_result["confidence"],
            "uncertainty_indicators": ollama_result["uncertainty_indicators"],
            "ocr_text": "",
            "vision_source": "ollama_gemma3",
        }

    # 2. Local computer vision fallback
    local_result = analyze_image_local_cv(file_bytes, filename)
    return {
        "visual_priority": local_result["severity_hint"],
        "category_hint": local_result["incident_type"],
        "apparent_damage": local_result["apparent_damage"],
        "hazard_markers": local_result["visible_hazards"],
        "visual_summary": local_result["description"],
        "confidence": local_result["confidence"],
        "uncertainty_indicators": local_result["uncertainty_indicators"],
        "ocr_text": "",
        "vision_source": "local_cv_fallback",
    }


def extract_text_from_image(file_bytes: bytes, filename: str) -> Tuple[bool, str, List[str], str, Dict[str, Any]]:
    """
    Main image extraction and inspection handler.
    Combines EXIF GPS location extraction and multimodal visual priority analysis.
    Returns: (success, cleaned_text, paragraphs, error_message, metadata)
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "", [], "Empty image file provided.", {}

    # 1. EXIF GPS and metadata
    exif_meta = extract_exif_gps_data(file_bytes)

    # 2. Visual analysis & priority prediction
    visual_analysis = analyze_image_visual_priority(file_bytes, filename)

    # 3. Synthesize structured text (without artificially injecting 'Visual Priority Level: High' to avoid circular overrides)
    paragraphs = []
    header = f"[Visual Inspection of Attached Photo: {filename}]"
    paragraphs.append(header)

    analysis_bullets = [
        f"- Physical Evidence Observed: {visual_analysis['visual_summary'] or 'Field photo inspected.'}",
        f"- Identified Incident Type: {visual_analysis['category_hint']}",
        f"- Apparent Physical Damage: {visual_analysis.get('apparent_damage', 'moderate')}",
    ]
    if visual_analysis["hazard_markers"]:
        analysis_bullets.append(f"- Visible Hazard Markers: {', '.join(visual_analysis['hazard_markers'])}")
    if visual_analysis.get("uncertainty_indicators"):
        analysis_bullets.append(f"- Image Quality / Uncertainty Flags: {', '.join(visual_analysis['uncertainty_indicators'])}")

    paragraphs.append("\n".join(analysis_bullets))

    if exif_meta["has_gps"]:
        location_clause = (
            f"[Image EXIF Location Detected]: {exif_meta['location_name']} "
            f"(Coordinates: {exif_meta['latitude']:.5f}, {exif_meta['longitude']:.5f})"
        )
        paragraphs.append(location_clause)

    full_text = "\n\n".join(paragraphs)

    combined_meta = {
        **exif_meta,
        **visual_analysis,
    }

    return True, full_text, paragraphs, "", combined_meta
