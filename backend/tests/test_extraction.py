"""
Unit tests for document extraction services (PDF, DOCX, TXT).
Verifies parsing accuracy, security checks, and error boundaries.
"""

from unittest.mock import patch
from backend.app.services.extraction.document_service import extract_document_text
from backend.app.utils.file_utils import sanitize_filename, validate_file_metadata


def test_sanitize_filename_prevents_traversal():
    unsafe_name = "../../etc/passwd/../../../malicious_script.sh.pdf"
    clean = sanitize_filename(unsafe_name)
    assert "/" not in clean
    assert "\\" not in clean
    assert ".." not in clean
    assert clean.endswith(".pdf")


def test_validate_file_metadata():
    # Empty file
    valid, msg = validate_file_metadata("test.txt", 0)
    assert not valid
    assert "empty" in msg.lower()

    # Oversized file (> 10MB)
    valid, msg = validate_file_metadata("large.pdf", 15 * 1024 * 1024)
    assert not valid
    assert "exceeds" in msg.lower()

    # Invalid extension
    valid, msg = validate_file_metadata("malware.exe", 100)
    assert not valid
    assert "unsupported" in msg.lower()

    # Valid file
    valid, msg = validate_file_metadata("complaint.docx", 2048)
    assert valid


def test_extract_txt(sample_txt_bytes):
    res = extract_document_text("pothole_issue.txt", sample_txt_bytes)
    assert res.success
    assert res.source_type == "TXT"
    assert "pothole on MG Road" in res.cleaned_text
    assert res.word_count > 10
    assert len(res.paragraphs) >= 1


def test_extract_marathi_txt(sample_marathi_txt_bytes):
    res = extract_document_text("water_issue.txt", sample_marathi_txt_bytes)
    assert res.success
    assert res.source_type == "TXT"
    assert "पाणी पुरवठा" in res.cleaned_text
    assert res.char_count > 20


def test_extract_docx(sample_docx_bytes):
    res = extract_document_text("garbage_complaint.docx", sample_docx_bytes)
    assert res.success
    assert res.source_type == "DOCX"
    assert "Overflowing Garbage" in res.cleaned_text
    assert "Shivaji Nagar" in res.cleaned_text  # Extracted from table
    assert res.word_count > 15


def test_extract_pdf(sample_pdf_bytes):
    res = extract_document_text("street_light.pdf", sample_pdf_bytes)
    assert res.success
    assert res.source_type == "PDF"
    assert "Street lights" in res.cleaned_text
    assert res.word_count > 5


def test_extract_corrupted_file():
    corrupted_bytes = b"Corrupted broken bytes not matching pdf binary format"
    res = extract_document_text("bad.pdf", corrupted_bytes)
    assert not res.success
    assert res.error is not None


def _generate_test_wav(duration_s: float = 0.5, silent: bool = False) -> bytes:
    import io, wave, math, struct
    sample_rate = 16000
    num_samples = int(sample_rate * duration_s)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        if silent:
            frames = b"\x00\x00" * num_samples
        else:
            frames = bytearray()
            for i in range(num_samples):
                val = int(8000 * math.sin(2 * math.pi * 440 * i / sample_rate))
                frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return buf.getvalue()


def test_validate_audio_metadata():
    valid, msg = validate_file_metadata("voice_complaint.mp3", 1024)
    assert valid

    valid_wav, msg = validate_file_metadata("recording.wav", 2048)
    assert valid_wav

    valid_m4a, msg = validate_file_metadata("audio.m4a", 4096)
    assert valid_m4a

    valid_mp4, msg = validate_file_metadata("evidence_clip.mp4", 8192)
    assert valid_mp4


def test_extract_audio_valid_decoding():
    wav_bytes = _generate_test_wav(0.5, silent=False)
    res = extract_document_text(
        "citizen_voice.wav",
        wav_bytes,
        transcript="Deep pothole on MG Road causing severe traffic hazard",
    )
    assert res.success
    assert res.source_type == "AUDIO"
    assert "pothole" in res.cleaned_text.lower()
    assert res.metadata.get("transcription") == "Deep pothole on MG Road causing severe traffic hazard"


def test_extract_audio_corrupted_rejected():
    corrupted_bytes = b"NOT_A_VALID_AUDIO_CONTAINER_OR_BITSTREAM"
    res = extract_document_text("broken.wav", corrupted_bytes)
    assert not res.success
    assert "audio decoding failed" in res.error.lower() or "invalid" in res.error.lower()


def test_extract_audio_silent_recording_flagged():
    silent_wav = _generate_test_wav(1.0, silent=True)
    res = extract_document_text("silent_mic.wav", silent_wav)
    assert not res.success
    assert "silent" in res.error.lower()


def test_validate_image_metadata():
    valid_jpg, _ = validate_file_metadata("broken_pipe.jpg", 1024)
    assert valid_jpg

    valid_png, _ = validate_file_metadata("pothole_photo.png", 2048)
    assert valid_png

    valid_webp, _ = validate_file_metadata("street_wire.webp", 4096)
    assert valid_webp


def test_extract_image_with_exif_gps():
    import io
    from PIL import Image

    img = Image.new("RGB", (50, 50), color="blue")
    exif = img.getexif()
    gps_ifd = exif.get_ifd(0x8825)
    gps_ifd[1] = "N"
    gps_ifd[2] = (18.0, 31.0, 13.44)  # 18.5204 N
    gps_ifd[3] = "E"
    gps_ifd[4] = (73.0, 51.0, 24.12)  # 73.8567 E

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    img_bytes = buf.getvalue()

    res = extract_document_text("electric_hazard_wire.jpg", img_bytes)
    assert res.success
    assert res.source_type == "IMAGE"
    assert res.metadata.get("has_gps") is True
    assert round(res.metadata.get("latitude"), 2) == 18.52
    assert round(res.metadata.get("longitude"), 2) == 73.86
    assert res.metadata.get("visual_priority") in ["Critical", "High", "Medium", "Low"]


def test_visual_inspection_rough_pothole_texture_predicts_high():
    import io
    import random
    from PIL import Image

    # Synthetic image with high edge variance (broken asphalt/pothole texture)
    img = Image.new("RGB", (160, 160), color=(80, 80, 80))
    pixels = img.load()
    for x in range(160):
        for y in range(160):
            noise = random.randint(-45, 45)
            pixels[x, y] = (max(0, min(255, 80 + noise)), max(0, min(255, 80 + noise)), max(0, min(255, 80 + noise)))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    # File name does NOT contain "pothole" or "crater"
    with patch("backend.app.services.extraction.image_extractor.query_ollama_vision", return_value=None):
        res = extract_document_text("IMG_20261021_001.jpg", buf.getvalue())
    assert res.success
    assert res.source_type == "IMAGE"
    assert res.metadata.get("visual_priority") == "High"
    assert res.metadata.get("category_hint") == "Road/Pothole"


def test_visual_inspection_dark_street_predicts_high():
    import io
    from PIL import Image

    # Very dark image simulating night street / street light failure
    img = Image.new("RGB", (160, 160), color=(20, 20, 25))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    with patch("backend.app.services.extraction.image_extractor.query_ollama_vision", return_value=None):
        res = extract_document_text("camera_photo_night.jpg", buf.getvalue())
    assert res.success
    assert res.source_type == "IMAGE"
    assert res.metadata.get("visual_priority") == "High"
    assert res.metadata.get("category_hint") == "Street Light"


def test_visual_inspection_sparking_flame_pattern_predicts_critical():
    import io
    from PIL import Image

    # Image with vibrant red/yellow fire/spark pattern
    img = Image.new("RGB", (160, 160), color=(40, 40, 40))
    pixels = img.load()
    for x in range(40, 120):
        for y in range(40, 120):
            pixels[x, y] = (240, 40, 20)  # Bright spark / fire

    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    with patch("backend.app.services.extraction.image_extractor.query_ollama_vision", return_value=None):
        res = extract_document_text("IMG_hazard.jpg", buf.getvalue())
    assert res.success
    assert res.source_type == "IMAGE"
    assert res.metadata.get("visual_priority") == "Critical"
    assert res.metadata.get("category_hint") == "Electricity"


def test_audio_verbatim_speech_transcript_and_nlp_words():
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio

    dummy_audio = b"RIFF" + b"\x00" * 100
    spoken_text = "There is an exposed electrical wire sparking near the primary school on Station Road"
    success, full_text, paragraphs, err, meta = extract_text_from_audio(
        dummy_audio, "recording_station_road.webm", transcript=spoken_text
    )
    assert success
    assert meta["transcription"] == spoken_text
    assert meta["audio_priority"] == "Critical"
    assert "wire" in meta["filtered_keywords"] or "electrical" in meta["filtered_keywords"]
    assert len(meta["hazard_keywords"]) > 0
    assert "primary school" in full_text.lower() or "station road" in full_text.lower()


def test_ollama_vision_mock_and_fallback():
    from unittest.mock import patch, MagicMock
    import json
    from backend.app.services.extraction.image_extractor import query_ollama_vision, analyze_image_visual_priority

    dummy_img = b"\xff\xd8\xff\xe0" + b"\x00" * 100

    # Test 1: Successful Ollama Gemma 3 vision inference
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": json.dumps({
            "incident_type": "Road/Pothole",
            "apparent_damage": "moderate",
            "visible_hazards": ["deep pothole in middle of lane"],
            "severity_hint": "Medium",
            "description": "Deep asphalt crater visible in lane.",
            "confidence": 0.88,
            "uncertainty_indicators": []
        })
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.__enter__.return_value = mock_client

    with patch("httpx.Client", return_value=mock_client):
        obs = query_ollama_vision(dummy_img, "test.jpg")
        assert obs is not None
        assert obs["incident_type"] == "Road/Pothole"
        assert obs["apparent_damage"] == "moderate"
        assert "deep pothole in middle of lane" in obs["visible_hazards"]

    # Test 2: Offline fallback when Ollama is unavailable
    fail_client = MagicMock()
    fail_client.post.side_effect = Exception("Connection refused to Ollama")
    fail_client.__enter__.return_value = fail_client

    with patch("httpx.Client", return_value=fail_client):
        obs_fallback = query_ollama_vision(dummy_img, "test.jpg")
        assert obs_fallback is None

        # Full analyze_image_visual_priority falls back cleanly
        res = analyze_image_visual_priority(dummy_img, "test_pothole.jpg")
        assert res["visual_priority"] in ["Critical", "High", "Medium", "Low", "Review Required"]
        assert "vision_source" in res




