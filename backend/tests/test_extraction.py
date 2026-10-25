"""
Unit tests for document extraction services (PDF, DOCX, TXT).
Verifies parsing accuracy, security checks, and error boundaries.
"""

import pytest
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


# ---------------------------------------------------------------------------
# Uploaded-audio decoding + Faster-Whisper transcription pipeline tests
# (covers MP3 / WAV / M4A / WEBM uploads, Marathi + English speech, and the
#  transcription error/notice paths surfaced to the UI.)
# ---------------------------------------------------------------------------

def _transcode_audio(wav_bytes: bytes, container: str) -> bytes:
    """
    Transcodes a 16 kHz mono WAV buffer into the requested container with the locally
    installed FFmpeg build (imageio-ffmpeg). Returns None when the codec is missing
    from the installed build so callers can skip instead of reporting a false failure.
    """
    import os
    import subprocess
    import tempfile

    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

    codec_args = {
        "mp3": ["-acodec", "libmp3lame"],
        "m4a": ["-acodec", "aac"],
        "webm": ["-acodec", "libopus"],
    }.get(container)
    if codec_args is None:
        return None

    tmp_in = None
    tmp_out = None
    try:
        fd, tmp_in = tempfile.mkstemp(prefix="sc_test_in_", suffix=".wav")
        with os.fdopen(fd, "wb") as fh:
            fh.write(wav_bytes)
        fd, tmp_out = tempfile.mkstemp(prefix="sc_test_out_", suffix=f".{container}")
        os.close(fd)

        proc = subprocess.run(
            [ffmpeg_exe, "-y", "-loglevel", "error", "-i", tmp_in, *codec_args, tmp_out],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if proc.returncode != 0:
            return None
        with open(tmp_out, "rb") as fh:
            data = fh.read()
        return data or None
    except Exception:
        return None
    finally:
        for path in (tmp_in, tmp_out):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass


@pytest.fixture
def whisper_mock():
    """Injects a mock Faster-Whisper model (no model download / no inference) and restores it."""
    from unittest.mock import MagicMock
    from backend.app.services.extraction import audio_extractor

    previous = audio_extractor._cached_whisper_model

    def _install(text="", language="en", segments=None, side_effect=None):
        mock = MagicMock()
        if side_effect is not None:
            mock.transcribe.side_effect = side_effect
        else:
            if segments is None:
                segments = []
                if text:
                    seg = MagicMock()
                    seg.text = f" {text}"
                    segments = [seg]
            info = MagicMock()
            info.language = language
            mock.transcribe.return_value = (segments, info)
        audio_extractor.set_mock_whisper_model(mock)
        return mock

    yield _install
    audio_extractor.set_mock_whisper_model(previous)


def test_convert_to_wav_pcm_and_float32_decoding():
    from backend.app.services.extraction.audio_extractor import (
        convert_to_wav_pcm,
        decode_wav_pcm_to_float32,
        _extract_wav_pcm,
    )

    wav_bytes = _generate_test_wav(0.5, silent=False)
    ok, pcm_wav, notice = convert_to_wav_pcm(wav_bytes)
    assert ok
    assert notice == ""
    assert len(_extract_wav_pcm(pcm_wav)) > 0

    samples = decode_wav_pcm_to_float32(pcm_wav)
    assert samples.dtype.name == "float32"
    assert samples.size >= 7000  # 0.5 s of 16 kHz mono audio
    assert samples.min() >= -1.0
    assert samples.max() <= 1.0


@pytest.mark.parametrize("container", ["wav", "mp3", "m4a", "webm"])
def test_convert_to_wav_pcm_uploaded_containers(container):
    """FFmpeg must decode every supported uploaded container into non-empty 16 kHz PCM."""
    from backend.app.services.extraction.audio_extractor import (
        convert_to_wav_pcm,
        decode_wav_pcm_to_float32,
    )

    if container == "wav":
        payload = _generate_test_wav(0.6, silent=False)
    else:
        payload = _transcode_audio(_generate_test_wav(0.6, silent=False), container)
        if payload is None:
            pytest.skip(f"Installed FFmpeg build has no {container} encoder to synthesise a fixture.")

    ok, pcm_wav, notice = convert_to_wav_pcm(payload)
    assert ok, f"{container} upload failed to decode: {notice}"
    assert notice == ""
    assert decode_wav_pcm_to_float32(pcm_wav).size > 1000


@pytest.mark.parametrize("container", ["wav", "mp3", "m4a"])
def test_uploaded_audio_transcription_english(container, whisper_mock):
    """MP3/WAV/M4A uploads are transcribed by the mocked model and classified downstream."""
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio

    spoken = "Street light bulb broken and sparking exposed wire on road"
    if container == "wav":
        payload = _generate_test_wav(0.6, silent=False)
    else:
        payload = _transcode_audio(_generate_test_wav(0.6, silent=False), container)
        if payload is None:
            pytest.skip(f"Installed FFmpeg build has no {container} encoder to synthesise a fixture.")

    whisper_mock(text=spoken, language="en")
    ok, full_text, paragraphs, err, meta = extract_text_from_audio(payload, f"citizen_voice.{container}")

    assert ok and err == ""
    assert meta["speech_detected"] is True
    assert meta["transcription"] == spoken
    assert meta["transcription_error"] is None
    assert meta["detected_language"] == "en"
    assert meta["transcription_source"] == "faster_whisper_en"
    assert meta["duration_seconds"] is not None
    # Downstream deterministic classification runs on the extracted transcript
    assert meta["category_hint"] == "Street Light"
    assert meta["audio_priority"] == "Critical"
    assert "exposed wire" in meta["hazard_keywords"]
    assert spoken in full_text  # transcript is rendered into the complaint dossier


def test_uploaded_audio_transcription_marathi(whisper_mock):
    """Marathi speech is transcribed verbatim (Devanagari preserved) and classified."""
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio

    spoken = "स्टेशन रोडवर खूप मोठा खड्डा आहे, गाड्या उलटत आहेत"
    whisper_mock(text=spoken, language="mr")
    ok, full_text, paragraphs, err, meta = extract_text_from_audio(
        _generate_test_wav(0.6, silent=False), "marathi_voice_complaint.wav"
    )

    assert ok
    assert meta["speech_detected"] is True
    assert meta["transcription"] == spoken
    assert meta["detected_language"] == "mr"
    assert meta["transcription_source"] == "faster_whisper_mr"
    assert meta["category_hint"] == "Road/Pothole"
    assert meta["audio_priority"] == "High"
    assert "खड्डा" in full_text


def test_audio_transcript_downstream_department_and_priority(whisper_mock):
    """Whisper transcript must drive category -> department routing and priority."""
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio
    from backend.app.services.classification.department_router import assign_department

    whisper_mock(text="Street light bulb broken and sparking exposed wire on road", language="en")
    ok, _text, _paras, _err, meta = extract_text_from_audio(
        _generate_test_wav(0.6, silent=False), "voice_note.wav"
    )

    assert ok
    department, reason = assign_department(meta["category_hint"])
    assert meta["category_hint"] == "Street Light"
    assert department == "Electrical Department"
    assert "Electrical Department" in reason
    assert meta["audio_priority"] == "Critical"


def test_marathi_audio_transcript_routes_to_drainage_department(whisper_mock):
    """Marathi audio transcript routes to the correct municipal department."""
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio
    from backend.app.services.classification.department_router import assign_department

    whisper_mock(
        text="बाजारामागे दहा दिवसांपासून कचरा उचलला नाही, गटार तुंबले आहे",
        language="mr",
    )
    ok, _text, _paras, _err, meta = extract_text_from_audio(
        _generate_test_wav(0.6, silent=False), "kacra_voice.wav"
    )

    assert ok
    assert meta["category_hint"] == "Drainage/Sewerage"
    department, _reason = assign_department(meta["category_hint"])
    assert department == "Drainage Department"


def test_audio_no_speech_detected_reports_clear_error(whisper_mock):
    """A decode that yields no speech must surface a clear, non-fatal error."""
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio

    whisper_mock(segments=[], language="en")  # VAD filtered every frame out
    ok, _text, _paras, _err, meta = extract_text_from_audio(
        _generate_test_wav(0.6, silent=False), "empty_room_recording.wav"
    )

    assert ok  # dossier is still returned so the citizen can type words manually
    assert meta["speech_detected"] is False
    assert meta["transcription_error"] == "No intelligible speech detected in the recording."
    assert "no_speech_detected_in_audio" in meta["uncertainty_indicators"]
    assert meta["transcription_source"] == "filename_semantic_tokens"


def test_audio_whisper_model_unavailable_reports_error():
    """When the local model cannot load, a clear error must be reported (not a fake transcript)."""
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio

    with patch(
        "backend.app.services.extraction.audio_extractor.get_whisper_model",
        return_value=None,
    ):
        ok, _text, _paras, _err, meta = extract_text_from_audio(
            _generate_test_wav(0.6, silent=False), "power_cut_report.wav"
        )

    assert ok
    assert meta["speech_detected"] is False
    assert "unavailable" in (meta["transcription_error"] or "").lower()
    assert "whisper_model_unavailable" in meta["uncertainty_indicators"]
    assert meta["transcription_source"] == "filename_semantic_tokens"


def test_audio_transcription_failure_reports_error(whisper_mock):
    """An unexpected inference crash must be captured as a user-visible transcription error."""
    from backend.app.services.extraction.audio_extractor import extract_text_from_audio

    whisper_mock(side_effect=RuntimeError("decoder exploded"))
    ok, _text, _paras, _err, meta = extract_text_from_audio(
        _generate_test_wav(0.6, silent=False), "garbage_voice.wav"
    )

    assert ok
    assert meta["speech_detected"] is False
    assert "speech recognition failed" in (meta["transcription_error"] or "").lower()
    assert "faster_whisper_transcription_error" in meta["uncertainty_indicators"]


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




