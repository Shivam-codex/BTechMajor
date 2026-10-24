"""
Audio Document Extractor & Speech Analyzer.
Extracts, transcribes, and analyzes spoken citizen grievances from uploaded audio files
(MP3, WAV, M4A, OGG, WEBM, AAC).
Supports:
1. Direct client-side speech transcripts (from browser Web Speech API SpeechRecognition).
2. Google GenAI SDK (gemini-2.5-flash) multimodal audio analysis when GEMINI_API_KEY is configured.
3. Free Google Speech-to-Text via Python SpeechRecognition for WAV/PCM audio.
4. Intelligent filename token filtering and deterministic NLP keyword & priority extraction.
"""

import os
import io
import re
import wave
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
}

GENERIC_AUDIO_TOKENS = {
    "recorded", "audio", "recording", "voice", "memo", "clip", "sound",
    "track", "whatsapp", "ptt", "aud", "temp", "file", "new", "test",
    "grievance", "statement", "regarding", "citizen", "uploaded", "attachment"
}


def convert_to_wav_pcm(file_bytes: bytes) -> bytes:
    """Converts any audio file (WEBM, MP3, M4A, OGG, AAC, WAV) to 16kHz mono 16-bit PCM WAV in memory using imageio-ffmpeg."""
    if not file_bytes or len(file_bytes) < 16:
        return b""
    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe,
            "-y",
            "-loglevel", "error",
            "-i", "pipe:0",
            "-vn",
            "-f", "wav",
            "-ar", "16000",
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
            timeout=10,
        )
        return proc.stdout
    except Exception as exc:
        logger.debug("FFmpeg in-memory audio conversion skipped or failed: %s", exc)
        return b""


def _inspect_audio_metadata(file_bytes: bytes, ext: str) -> Dict[str, Any]:
    """Inspects basic audio file properties (size, format, and WAV duration if applicable)."""
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
    Extracts transcribed speech, relevant grievance details, and metadata from an audio file.
    Resolves transcription via:
    1. Client Web Speech API transcript (if provided).
    2. Gemini multimodal API (if GEMINI_API_KEY is set).
    3. Google Speech-to-Text via speech_recognition (for WAV files).
    4. Meaningful filename tokens (excluding generic audio markers/numbers).
    Returns: (success, raw_text, paragraphs, error_message, metadata)
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "", [], "Empty audio file provided.", {}

    clean_name = Path(filename).name
    ext = Path(clean_name).suffix.lower()
    mime_type = AUDIO_MIME_TYPES.get(ext, "audio/wav")

    audio_meta: Dict[str, Any] = {
        **_inspect_audio_metadata(file_bytes, ext),
        "transcription": "",
        "transcription_source": "none",
        "category_hint": "Other",
        "audio_priority": "Medium",
        "spoken_location": None,
        "key_points": [],
    }

    # 1. Check if client-side transcript was supplied
    clean_transcript = (transcript or "").strip()
    if clean_transcript:
        audio_meta["transcription"] = clean_transcript
        audio_meta["transcription_source"] = "client_speech_recognition"

    # 2. If no client transcript, attempt Gemini multimodal audio analysis
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not audio_meta["transcription"] and api_key and len(file_bytes) > 64:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            audio_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

            prompt = (
                "You are an expert Smart City Municipal Grievance Analyst. Listen carefully to this citizen audio recording.\n"
                "Transcribe the speech verbatim (preserving English, Marathi मराठी, or Hindi) and extract structured grievance details.\n\n"
                "FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:\n"
                "TRANSCRIPTION: <Exact verbatim transcription of the spoken audio>\n"
                "CATEGORY: <Choose one: Road/Pothole, Street Light, Garbage/Waste Management, Water Supply, Drainage/Sewerage, Electricity, Public Toilet, Traffic, Other>\n"
                "PRIORITY: <Choose one: Critical, High, Medium, Low>\n"
                "LOCATION: <Any street name, area, ward, or landmark mentioned in speech, or None>\n"
                "KEY_INFO: <Concise summary of the civic issue, hazards, and duration mentioned>"
            )

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL or "gemini-2.5-flash",
                contents=[audio_part, prompt],
            )

            if response and response.text and response.text.strip():
                raw_output = response.text.strip()
                transcription = ""
                key_info = ""

                for line in raw_output.splitlines():
                    line_s = line.strip()
                    if line_s.upper().startswith("TRANSCRIPTION:"):
                        transcription = line_s.split(":", 1)[1].strip()
                    elif line_s.upper().startswith("CATEGORY:"):
                        cat = line_s.split(":", 1)[1].strip()
                        if cat:
                            audio_meta["category_hint"] = cat
                    elif line_s.upper().startswith("PRIORITY:"):
                        pri = line_s.split(":", 1)[1].strip().capitalize()
                        if pri in ["Critical", "High", "Medium", "Low"]:
                            audio_meta["audio_priority"] = pri
                    elif line_s.upper().startswith("LOCATION:"):
                        loc = line_s.split(":", 1)[1].strip()
                        if loc and loc.lower() not in ["none", "n/a", "not mentioned", "unknown"]:
                            audio_meta["spoken_location"] = loc
                    elif line_s.upper().startswith("KEY_INFO:"):
                        key_info = line_s.split(":", 1)[1].strip()
                        if key_info:
                            audio_meta["key_points"] = [key_info]

                if not transcription:
                    transcription = raw_output
                audio_meta["transcription"] = transcription
                audio_meta["transcription_source"] = "gemini_multimodal"
        except Exception as exc:
            logger.warning("Gemini audio transcription failed: %s.", str(exc))

    # 3. If still no transcription, convert audio to 16kHz mono WAV and perform Google STT via SpeechRecognition
    if not audio_meta["transcription"] and len(file_bytes) > 64:
        wav_pcm_bytes = b""
        if ext == ".wav":
            wav_pcm_bytes = file_bytes
        else:
            wav_pcm_bytes = convert_to_wav_pcm(file_bytes)

        if wav_pcm_bytes and len(wav_pcm_bytes) > 44:
            try:
                import speech_recognition as sr

                recognizer = sr.Recognizer()
                with sr.AudioFile(io.BytesIO(wav_pcm_bytes)) as source:
                    audio_content = recognizer.record(source)

                for lang_code in ["en-IN", "hi-IN", "mr-IN", "en-US"]:
                    try:
                        stt_text = recognizer.recognize_google(audio_content, language=lang_code)
                        if stt_text and stt_text.strip():
                            audio_meta["transcription"] = stt_text.strip()
                            audio_meta["transcription_source"] = f"google_stt_{lang_code}"
                            break
                    except Exception:
                        continue
            except Exception as exc:
                logger.debug("Speech recognition fallback skipped: %s", str(exc))

    # 4. Filename token heuristic (strictly filter out generic audio stems and numbers)
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

    # Perform Deterministic NLP Preprocessing and Word Extraction
    from backend.app.services.nlp.preprocessing import preprocess_complaint
    from backend.app.services.classification.classifier import classify_complaint
    from backend.app.services.classification.priority_detector import detect_priority

    nlp_res = preprocess_complaint(transcription_text)

    # Classify category using our deterministic rule classifier if category_hint is unset or Other
    classification = classify_complaint(nlp_res)
    if classification.category != "Other" or audio_meta.get("category_hint") == "Other":
        audio_meta["category_hint"] = classification.category
        audio_meta["matched_civic_keywords"] = classification.matched_keywords
        audio_meta["rule_match_score"] = classification.rule_match_score

    # Compute urgency priority from spoken hazard triggers
    priority_res = detect_priority(nlp_res)
    if priority_res.priority in ["Critical", "High"]:
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
    paragraphs.append(f"- Verbatim Speech Transcription: {transcription_text}")
    if filtered_words:
        paragraphs.append(f"- NLP Extracted Key Words: {', '.join(filtered_words[:20])}")
    if priority_res.detected_keywords:
        paragraphs.append(f"- Spoken Hazard Markers Detected: {', '.join(priority_res.detected_keywords[:8])}")
    if audio_meta.get("category_hint") and audio_meta["category_hint"] != "Other":
        paragraphs.append(f"- Audio Identified Category: {audio_meta['category_hint']}")
    if audio_meta.get("audio_priority"):
        paragraphs.append(f"- Audio Urgency Assessment: {audio_meta['audio_priority']}")
    if audio_meta.get("spoken_location"):
        paragraphs.append(f"- Spoken Location Mentioned: {audio_meta['spoken_location']}")
    if audio_meta.get("duration_seconds"):
        paragraphs.append(f"- Recording Duration: {audio_meta['duration_seconds']}s")

    full_text = "\n".join(paragraphs)
    return True, full_text, paragraphs, "", audio_meta
