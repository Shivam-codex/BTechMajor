"""
Unit tests for document extraction services (PDF, DOCX, TXT).
Verifies parsing accuracy, security checks, and error boundaries.
"""

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


def test_validate_audio_metadata():
    valid, msg = validate_file_metadata("voice_complaint.mp3", 1024)
    assert valid

    valid_wav, msg = validate_file_metadata("recording.wav", 2048)
    assert valid_wav

    valid_m4a, msg = validate_file_metadata("audio.m4a", 4096)
    assert valid_m4a


def test_extract_audio_fallback():
    dummy_audio_bytes = b"ID3\x03\x00\x00\x00\x00\x00\x00DummyAudioContent"
    res = extract_document_text("citizen_voice.mp3", dummy_audio_bytes)
    assert res.success
    assert res.source_type == "AUDIO"
    assert "citizen_voice.mp3" in res.cleaned_text


def test_audio_generic_name_does_not_extract_numbers_as_keywords():
    dummy_webm = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08"
    res = extract_document_text("recorded_audio_10-45-12.webm", dummy_webm)
    assert res.success
    assert res.source_type == "AUDIO"
    meta = res.metadata
    # Generic numbers and audio stems should not be in filtered keywords
    assert "10" not in meta.get("filtered_keywords", [])
    assert "45" not in meta.get("filtered_keywords", [])
    assert "recorded" not in meta.get("filtered_keywords", [])
    assert "audio" not in meta.get("filtered_keywords", [])


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



