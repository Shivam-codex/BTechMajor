"""
Image Grievance Extractor and Visual Inspector.
Extracts:
1. EXIF GPS coordinates and resolves location via reverse-geocoding.
2. Visual scene analysis and civic hazard detection for deterministic priority prediction.
Uses Google GenAI SDK (gemini-2.5-flash) multimodal inspection when GEMINI_API_KEY is configured,
with robust local Pillow EXIF and metadata fallback when offline or without API key.
"""

import os
import io
import json
import logging
import urllib.request
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ExifTags
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


def reverse_geocode(lat: float, lon: float, timeout_sec: float = 2.5) -> str:
    """
    Reverse-geocodes GPS coordinates to human-readable address using OpenStreetMap Nominatim.
    Falls back cleanly to coordinate string if network request fails or times out.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SmartCityComplaintSystem/1.0 (academic-project)"}
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            display_name = data.get("display_name")
            if display_name:
                return display_name
    except Exception as exc:
        logger.debug("Reverse geocoding timed out or failed: %s", exc)

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

            # 1. Try modern Pillow IFD extraction
            exif = img.getexif() if hasattr(img, "getexif") else None
            gps_info = {}

            if exif is not None:
                # 0x8825 is ExifTags.IFD.GPSInfo
                try:
                    gps_ifd = exif.get_ifd(0x8825)
                    if gps_ifd:
                        gps_info = dict(gps_ifd)
                except Exception:
                    pass

                # Camera Make / Model / DateTime
                result["camera_make"] = exif.get(271)  # Make
                result["camera_model"] = exif.get(272)  # Model
                result["date_time"] = exif.get(306)    # DateTime

            # 2. Fallback to legacy _getexif()
            if not gps_info and hasattr(img, "_getexif"):
                legacy_exif = img._getexif()
                if legacy_exif:
                    for tag_id, val in legacy_exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag_name == "GPSInfo" and isinstance(val, dict):
                            gps_info = val
                            break

            # 3. Resolve Lat / Long
            # Tag 1: GPSLatitudeRef, Tag 2: GPSLatitude, Tag 3: GPSLongitudeRef, Tag 4: GPSLongitude
            # Or by name if keyed by name
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
        logger.warning("Error reading image EXIF data: %s", exc)

    return result


def _analyze_image_pixels(file_bytes: bytes) -> Dict[str, Any]:
    """
    Local computer-vision inspection using Pillow to extract image metrics:
    - Luminance / average brightness (dark street / night light failure)
    - Edge density and gradient roughness (potholes, road craters, cracked pavement, debris heaps)
    - Color distribution & saturation (electrical hazard sparks, fire, waste)
    """
    features: Dict[str, Any] = {
        "luminance": 128.0,
        "edge_density": 0.0,
        "is_dark": False,
        "has_high_edges": False,
        "hazard_color": False,
        "detected_priority": "Medium",
        "category_hint": "Other",
        "hazard_markers": [],
        "visual_summary": "",
    }
    if not file_bytes:
        return features

    try:
        from PIL import ImageFilter, ImageStat

        with Image.open(io.BytesIO(file_bytes)) as img:
            rgb_img = img.convert("RGB")
            # Resize thumbnail for fast deterministic processing (<15ms)
            thumb = rgb_img.resize((160, 160))
            gray = thumb.convert("L")

            # 1. Luminance
            stat_gray = ImageStat.Stat(gray)
            lum = float(stat_gray.mean[0])
            features["luminance"] = round(lum, 2)

            # 2. Edge / texture density (crop 2-pixel border to eliminate filter boundary artifacts)
            edges = gray.filter(ImageFilter.FIND_EDGES)
            cropped_edges = edges.crop((2, 2, 158, 158))
            edge_stat = ImageStat.Stat(cropped_edges)
            edge_density = float(edge_stat.mean[0])
            features["edge_density"] = round(edge_density, 2)

            # 3. Color saturation & hazard tones (red / orange / yellow warning cues)
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
                # Fire / sparks / exposed copper / red warning signs: high R, low B
                if r > 160 and g < 100 and b < 70:
                    hazard_color_count += 1
                elif r > 190 and g > 150 and b < 50:  # bright yellow/spark
                    hazard_color_count += 1

            stat_rgb = ImageStat.Stat(thumb)
            max_channel = float(max(stat_rgb.mean[:3]))

            hazard_ratio = hazard_color_count / float(total_px or 1)
            dark_ratio = dark_pixels / float(total_px or 1)

            # Heuristic decision tree:
            # A. Critical: Sparking / fire / exposed live wire or high hazard saturation
            if hazard_ratio > 0.07:
                features["hazard_color"] = True
                features["detected_priority"] = "Critical"
                features["category_hint"] = "Electricity"
                features["hazard_markers"].append("visual_high_saturation_spark_or_flame_pattern")
                features["visual_summary"] = (
                    f"Visual electrical hazard / spark pattern detected ({round(hazard_ratio * 100, 1)}% intense saturation). "
                    f"Assessed as Critical priority requiring prompt electrical inspection."
                )

            # B. High: Rough cracked road surface / pothole crater / debris heap
            elif edge_density > 6.0 or (edge_density > 4.5 and lum < 120 and max_channel > 55.0):
                features["has_high_edges"] = True
                features["detected_priority"] = "High"
                features["category_hint"] = "Road/Pothole"
                features["hazard_markers"].append("visual_road_crater_texture_and_edge_roughness")
                features["visual_summary"] = (
                    f"Severe road crater / asphalt surface roughness detected (edge roughness metric: {round(edge_density, 1)}). "
                    f"Visual priority assessed as High for road and pothole repair."
                )

            # C. High: Dark street / night scene / light failure
            elif max_channel < 55.0 and (lum < 45.0 or dark_ratio > 0.65):
                features["is_dark"] = True
                features["detected_priority"] = "High"
                features["category_hint"] = "Street Light"
                features["hazard_markers"].append("visual_low_lux_dark_street_or_light_failure")
                features["visual_summary"] = (
                    f"Low illumination / dark scene detected (lux mean: {round(lum, 1)}). "
                    f"Assessed as High priority for street lighting maintenance."
                )

            # D. Medium baseline
            else:
                features["detected_priority"] = "Medium"
                features["category_hint"] = "Other"
                features["visual_summary"] = (
                    f"Grievance photograph inspected. Surface texture edge density: {round(edge_density, 1)}, "
                    f"luminance: {round(lum, 1)}. Visual priority assessed as Medium."
                )

    except Exception as exc:
        logger.debug("Local pixel analysis fallback skipped: %s", exc)

    return features


def analyze_image_visual_priority(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Analyzes visual content of an uploaded grievance photo to detect hazards,
    determine municipal category, and predict visual priority level.
    Uses:
    1. Local Pillow computer vision inspection (edge density, luminance, color saturation).
    2. Google GenAI SDK (gemini-2.5-flash) multimodal vision inspection when GEMINI_API_KEY is configured.
    3. Filename semantic keyword triggers for explicit civic issues.
    """
    # 1. Run local computer vision analysis on image pixels
    pixel_features = _analyze_image_pixels(file_bytes)

    result: Dict[str, Any] = {
        "visual_priority": pixel_features.get("detected_priority", "Medium"),
        "category_hint": pixel_features.get("category_hint", "Other"),
        "hazard_markers": list(pixel_features.get("hazard_markers", [])),
        "visual_summary": pixel_features.get("visual_summary", ""),
        "ocr_text": "",
    }

    # 2. Filename keyword reinforcement
    fn_lower = filename.lower()
    if any(k in fn_lower for k in ["wire", "electric", "spark", "shock", "fire", "blast", "danger", "urgent", "manhole"]):
        result["visual_priority"] = "Critical"
        if result["category_hint"] == "Other":
            result["category_hint"] = "Electricity" if "wire" in fn_lower or "electric" in fn_lower else "Road/Pothole"
        if "visual_inspection_hazard" not in result["hazard_markers"]:
            result["hazard_markers"].append("visual_inspection_hazard")
    elif any(k in fn_lower for k in ["pothole", "crater", "sewage", "flood", "leak", "garbage"]):
        if result["visual_priority"] != "Critical":
            result["visual_priority"] = "High"
        if result["category_hint"] == "Other":
            result["category_hint"] = "Road/Pothole" if "pothole" in fn_lower or "crater" in fn_lower else "Garbage/Waste Management"
        if "infrastructure_damage_observed" not in result["hazard_markers"]:
            result["hazard_markers"].append("infrastructure_damage_observed")

    # 3. Google GenAI Multimodal Vision Inspection (if GEMINI_API_KEY is configured)
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    ext = Path(filename).suffix.lower()
    mime_type = IMAGE_MIME_TYPES.get(ext, "image/jpeg")

    if api_key and len(file_bytes) > 64:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            image_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

            prompt = (
                "You are an expert Smart City Municipal Field Inspector. Analyze this civic complaint photograph thoroughly.\n"
                "Provide a rigorous structural assessment of the municipal issue.\n\n"
                "EVALUATE AND REPORT IN THIS EXACT FORMAT:\n"
                "CATEGORY: <Choose one: Road/Pothole, Street Light, Garbage/Waste Management, Water Supply, Drainage/Sewerage, Electricity, Public Toilet, Traffic, Other>\n"
                "PRIORITY: <Choose one: Critical, High, Medium, Low>\n"
                "HAZARD_INDICATORS: <Comma-separated list of visual hazards, e.g. exposed electrical wire, sparking, open manhole, deep crater, severe flooding, massive garbage accumulation>\n"
                "VISIBLE_TEXT: <Any street signs, pole numbers, banner texts visible>\n"
                "SUMMARY: <Concise, factual description of the damage, obstruction, and urgency>\n\n"
                "PRIORITY GUIDELINES:\n"
                "- Critical: Immediate danger to life (exposed/sparking electric wires, deep open manholes on paths, severe road cave-in, live fire/gas risk, hospital access cut off).\n"
                "- High: Major public disruption (major water pipeline burst, overflowing raw sewage near homes, completely impassable road crater, massive rotting garbage dump blocking lane).\n"
                "- Medium: Standard municipal issue (typical pothole, broken street light pole, overflowing localized dustbin, minor gutter block).\n"
                "- Low: Minor cosmetic wear, faint road marking, harmless debris."
            )

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL or "gemini-2.5-flash",
                contents=[image_part, prompt],
            )

            if response and response.text:
                raw_output = response.text.strip()
                for line in raw_output.splitlines():
                    line_s = line.strip()
                    if line_s.upper().startswith("CATEGORY:"):
                        cat = line_s.split(":", 1)[1].strip()
                        if cat and cat != "Other":
                            result["category_hint"] = cat
                    elif line_s.upper().startswith("PRIORITY:"):
                        pri = line_s.split(":", 1)[1].strip().capitalize()
                        if pri in ["Critical", "High", "Medium", "Low"]:
                            result["visual_priority"] = pri
                    elif line_s.upper().startswith("HAZARD_INDICATORS:"):
                        hazards = line_s.split(":", 1)[1].strip()
                        if hazards and hazards.lower() != "none":
                            for h in hazards.split(","):
                                h_clean = h.strip()
                                if h_clean and h_clean not in result["hazard_markers"]:
                                    result["hazard_markers"].append(h_clean)
                    elif line_s.upper().startswith("VISIBLE_TEXT:"):
                        txt = line_s.split(":", 1)[1].strip()
                        if txt and txt.lower() != "none":
                            result["ocr_text"] = txt
                    elif line_s.upper().startswith("SUMMARY:"):
                        summary = line_s.split(":", 1)[1].strip()
                        if summary:
                            result["visual_summary"] = summary

                if not result["visual_summary"]:
                    result["visual_summary"] = raw_output[:300]
                return result
        except Exception as exc:
            logger.warning("Gemini visual analysis failed: %s. Using local computer vision inspection.", exc)

    if not result["visual_summary"]:
        result["visual_summary"] = (
            f"Grievance photograph '{filename}' attached for field inspection. "
            f"Visual priority assessed as {result['visual_priority']}."
        )

    return result


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

    # 3. Synthesize structured text for deterministic NLP intake
    paragraphs = []
    header = f"[Visual Inspection of Attached Photo: {filename}]"
    paragraphs.append(header)

    analysis_bullets = [
        f"- Identified Category: {visual_analysis['category_hint']}",
        f"- Visual Priority Level: {visual_analysis['visual_priority']}",
    ]
    if visual_analysis["hazard_markers"]:
        analysis_bullets.append(f"- Visual Hazard Indicators: {', '.join(visual_analysis['hazard_markers'])}")
    if visual_analysis["ocr_text"]:
        analysis_bullets.append(f"- Visible On-Site Text: {visual_analysis['ocr_text']}")
    if visual_analysis["visual_summary"]:
        analysis_bullets.append(f"- Visual Evidence Details: {visual_analysis['visual_summary']}")

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
