"""
Local-First Audio Document Extractor & Speech Analyzer.
Architecture:
1. Universal Audio & Video Container Decoding via FFmpeg (MP3, WAV, M4A, OGG, WEBM, AAC, MP4).
2. Local Multilingual Speech-to-Text via Faster-Whisper (CPU-friendly, quantized INT8, Marathi, Hindi, English).
3. Silence & Corrupted Stream Validation (RMS amplitude checking).
4. Deterministic NLP Word Tokenization, Keyword Filtering, and Severity Assessment.
5. Zero external cloud speech API dependencies. Zero citizen audio uploads to third-party services.
"""

import io
import re
import wave
import math
import struct
import logging
import subprocess
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

from backend.app.core.config import settings

logger = logging.getLogger("smart_city_backend")

AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".aac": "audio/aac",
    ".mp4": "video/mp4",
}

GENERIC_AUDIO_TOKENS = {
    "recorded", "audio", "recording", "voice", "memo", "clip", "sound",
    "track", "whatsapp", "ptt", "aud", "temp", "file", "new", "test",
    "grievance", "statement", "regarding", "citizen", "uploaded", "attachment"
}

# Global cached Faster-Whisper model singleton
_cached_whisper_model = None


def get_whisper_model():
    """Lazy-loads and caches the Faster-Whisper model on CPU using int8 quantization."""
    global _cached_whisper_model
    if _cached_whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info("Initializing local Faster-Whisper model '%s' on %s (%s)...",
                        settings.WHISPER_MODEL_SIZE, settings.WHISPER_DEVICE, settings.WHISPER_COMPUTE_TYPE)
            _cached_whisper_model = WhisperModel(
                model_size_or_path=settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
            )
        except Exception as exc:
            logger.warning("Failed to initialize Faster-Whisper model: %s", exc)
            return None
    return _cached_whisper_model


def set_mock_whisper_model(mock_model):
    """Allows unit tests to inject a fast mock model without model downloads."""
    global _cached_whisper_model
    _cached_whisper_model = mock_model


def convert_to_wav_pcm(file_bytes: bytes) -> Tuple[bool, bytes, str]:
    """
    Decodes any audio file or MP4 video container to 16kHz mono 16-bit PCM WAV in memory using imageio-ffmpeg.
    Returns: (success, wav_bytes, error_or_notice)
    """
    if not file_bytes or len(file_bytes) < 16:
        return False, b"", "Empty or invalid audio bytes provided."

    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe,
            "-y",
            "-loglevel", "error",
            "-i", "pipe:0",
            "-vn",              # strip video track if present (e.g. mp4)
            "-f", "wav",
            "-ar", "16000",     # resample to standard 16kHz mono
            "-ac", "1",
            "-acodec", "pcm_s16le",
            "pipe:1"
        ]
        proc = subprocess.run(
            cmd,
            input=file_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=12,
        )
        wav_bytes = proc.stdout
        if not wav_bytes or len(wav_bytes) <= 44:
            return False, b"", "No audible audio stream found in container."

        # Compute RMS energy from PCM samples to detect silent recordings
        data_idx = wav_bytes.find(b"data")
        if data_idx != -1:
            raw_samples = wav_bytes[data_idx + 8:]
        else:
            raw_samples = wav_bytes[44:]
        num_samples = len(raw_samples) // 2
        if num_samples > 0:
            shorts = struct.unpack(f"<{num_samples}h", raw_samples[:num_samples * 2])
            sum_sq = sum(float(s) * float(s) for s in shorts)
            rms = math.sqrt(sum_sq / float(num_samples))
            if rms < 15.0:  # virtually dead silence / no microphone signal
                return True, wav_bytes, "SILENT_RECORDING"

        return True, wav_bytes, ""

    except subprocess.CalledProcessError as cpe:
        err_msg = cpe.stderr.decode("utf-8", errors="replace").strip() or "FFmpeg decoding failed."
        logger.debug("FFmpeg decoding error: %s", err_msg)
        return False, b"", f"Audio decoding failed: {err_msg}"
    except Exception as exc:
        logger.debug("Audio conversion exception: %s", exc)
        return False, b"", f"Audio conversion error: {str(exc)}"


def _inspect_audio_metadata(file_bytes: bytes, ext: str) -> Dict[str, Any]:
    """Inspects basic audio container properties (size, format, WAV duration)."""
    info: Dict[str, Any] = {
        "format": ext.lstrip(".").upper() or "AUDIO",
        "size_bytes": len(file_bytes),
        "duration_seconds": None,
    }
    if ext == ".wav" and len(file_bytes) > 44:
        try:
            with wave.open(io.BytesIO(file_bytes), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    info["duration_seconds"] = round(frames / float(rate), 2)
        except Exception:
            pass
    return info


def extract_text_from_audio(
    file_bytes: bytes,
    filename: str = "voice_complaint.wav",
    transcript: Optional[str] = None,
) -> Tuple[bool, str, List[str], str, Dict[str, Any]]:
    """
    Extracts transcribed speech, relevant civic details, and metadata from an audio file.
    Downstream processing:
    1. Client-side transcript (from browser Web Speech API SpeechRecognition during live recording).
    2. Local Faster-Whisper multilingual speech recognition (offline, local-first).
    3. Meaningful filename semantic tokens as fallback.
    Returns: (success, raw_text, paragraphs, error_message, metadata)
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "", [], "Empty audio file provided.", {}

    clean_name = Path(filename).name
    ext = Path(clean_name).suffix.lower()

    audio_meta: Dict[str, Any] = {
        **_inspect_audio_metadata(file_bytes, ext),
        "transcription": "",
        "transcription_source": "none",
        "detected_language": "en",
        "category_hint": "Other",
        "audio_priority": "Medium",
        "spoken_location": None,
        "key_points": [],
        "uncertainty_indicators": [],
    }

    # 1. Check if client-side transcript was supplied (from browser live microphone)
    clean_transcript = (transcript or "").strip()
    if clean_transcript:
        audio_meta["transcription"] = clean_transcript
        audio_meta["transcription_source"] = "client_speech_recognition"

    # 2. Decode audio with FFmpeg to 16kHz mono WAV and transcribe locally with Faster-Whisper
    if not audio_meta["transcription"]:
        conv_ok, wav_pcm_bytes, conv_notice = convert_to_wav_pcm(file_bytes)

        if not conv_ok:
            # Corrupted or unreadable audio format
            audio_meta["uncertainty_indicators"].append("corrupted_or_unsupported_audio")
            return False, "", [], conv_notice or "Failed to decode audio file.", audio_meta

        if conv_notice == "SILENT_RECORDING":
            audio_meta["uncertainty_indicators"].append("silent_recording_no_audible_speech")
            audio_meta["transcription_source"] = "silent_audio"
            return False, "", [], "Silent recording detected: audio contains no audible speech.", audio_meta

        # Calculate exact duration from converted 16kHz WAV
        if len(wav_pcm_bytes) > 44:
            audio_meta["duration_seconds"] = round((len(wav_pcm_bytes) - 44) / 32000.0, 2)

        # Transcribe with local Faster-Whisper
        whisper = get_whisper_model()
        if whisper is not None:
            try:
                segments, info = whisper.transcribe(
                    io.BytesIO(wav_pcm_bytes),
                    beam_size=3,
                    language=None,  # auto-detect language (supports Marathi, Hindi, English)
                    vad_filter=True,
                )
                text_parts = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
                extracted_speech = " ".join(text_parts).strip()

                if extracted_speech:
                    audio_meta["transcription"] = extracted_speech
                    audio_meta["detected_language"] = getattr(info, "language", "en")
                    audio_meta["transcription_source"] = f"faster_whisper_{audio_meta['detected_language']}"
            except Exception as exc:
                logger.debug("Faster-Whisper transcription failed: %s", exc)
                audio_meta["uncertainty_indicators"].append("faster_whisper_transcription_error")

    # 3. Filename semantic token heuristic as fallback
    stem_raw = Path(clean_name).stem.replace("_", " ").replace("-", " ")
    raw_tokens = re.findall(r"[a-zA-Z\u0900-\u097F]+", stem_raw)
    meaningful_tokens = [
        t.lower() for t in raw_tokens
        if t.lower() not in GENERIC_AUDIO_TOKENS and len(t) > 2 and not t.isdigit()
    ]

    transcription_text = (audio_meta.get("transcription") or "").strip()
    if not transcription_text:
        if meaningful_tokens:
            transcription_text = f"Audio grievance statement regarding {' '.join(meaningful_tokens)}."
            audio_meta["transcription"] = transcription_text
            audio_meta["transcription_source"] = "filename_semantic_tokens"
        else:
            transcription_text = f"Audio grievance voice recording ({clean_name})."
            audio_meta["transcription"] = transcription_text
            audio_meta["transcription_source"] = "generic_audio_file"
            audio_meta["uncertainty_indicators"].append("no_speech_extracted_from_audio")

    # 4. Perform Deterministic NLP Preprocessing and Word Extraction
    from backend.app.services.nlp.preprocessing import preprocess_complaint
    from backend.app.services.classification.classifier import classify_complaint
    from backend.app.services.classification.priority_detector import detect_priority

    nlp_res = preprocess_complaint(transcription_text)

    # Classify category using deterministic rule classifier
    classification = classify_complaint(nlp_res)
    if classification.category != "Other" or audio_meta.get("category_hint") == "Other":
        audio_meta["category_hint"] = classification.category
        audio_meta["matched_civic_keywords"] = classification.matched_keywords
        audio_meta["rule_match_score"] = classification.rule_match_score

    # Compute urgency priority from spoken hazard triggers
    priority_res = detect_priority(nlp_res, audio_evidence=audio_meta, citizen_text=transcription_text)
    audio_meta["audio_priority"] = priority_res.priority
    audio_meta["hazard_keywords"] = priority_res.detected_keywords

    # Filter out generic audio words and digits from user-facing NLP keywords
    filtered_words = [
        w for w in nlp_res.filtered_tokens
        if w.lower() not in GENERIC_AUDIO_TOKENS and not w.isdigit() and len(w) > 1
    ]
    lemmatized_words = [
        w for w in nlp_res.lemmatized_tokens
        if w.lower() not in GENERIC_AUDIO_TOKENS and not w.isdigit() and len(w) > 1
    ]

    audio_meta["extracted_words"] = [w for w in nlp_res.tokens if w.lower() not in GENERIC_AUDIO_TOKENS and not w.isdigit()]
    audio_meta["filtered_keywords"] = filtered_words
    audio_meta["lemmatized_tokens"] = lemmatized_words

    # Build structured text paragraphs for complaint dossier
    paragraphs = [f"[Audio Grievance Recording ({clean_name}) — Speech & NLP Analysis]"]
    paragraphs.append(f"- Spoken Speech Transcription: {transcription_text}")
    if filtered_words:
        paragraphs.append(f"- NLP Extracted Key Words: {', '.join(filtered_words[:20])}")
    if priority_res.detected_keywords:
        paragraphs.append(f"- Spoken Hazard Markers Detected: {', '.join(priority_res.detected_keywords[:8])}")
    if audio_meta.get("category_hint") and audio_meta["category_hint"] != "Other":
        paragraphs.append(f"- Audio Identified Category: {audio_meta['category_hint']}")
    if audio_meta.get("audio_priority"):
        paragraphs.append(f"- Audio Urgency Assessment: {audio_meta['audio_priority']}")
    if audio_meta.get("duration_seconds"):
        paragraphs.append(f"- Recording Duration: {audio_meta['duration_seconds']}s")

    full_text = "\n".join(paragraphs)
    return True, full_text, paragraphs, "", audio_meta
