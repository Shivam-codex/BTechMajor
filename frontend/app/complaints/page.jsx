"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Sparkles,
  Building2,
  ShieldCheck,
  Eye,
  FileCode,
  Tag,
  Clock,
  UserCheck,
  Mic,
  MicOff,
  Music,
  Trash2,
  Paperclip,
  Volume2,
  Image as ImageIcon,
  Camera,
  MapPin,
  Crosshair,
  AlertTriangle,
  RefreshCw,
  Plus,
  Square,
  Radio,
} from "lucide-react";
import API_BASE_URL, { fetchApi } from "../../utils/api";
import { useAuth } from "../../context/AuthContext";

const IMAGE_EXTS = [".jpg", ".jpeg", ".png", ".webp", ".bmp"];
const AUDIO_EXTS = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".aac", ".mp4"];
const DOC_EXTS = [".pdf", ".docx", ".txt"];
const ALL_VALID_EXTS = [...IMAGE_EXTS, ...AUDIO_EXTS, ...DOC_EXTS];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

const PRIORITY_ORDER = {
  Critical: 5,
  High: 4,
  Medium: 3,
  "Review Required": 2,
  Low: 1,
};

function getFileExtension(filename = "") {
  const parts = filename.toLowerCase().split(".");
  return parts.length > 1 ? `.${parts.pop()}` : "";
}

function classifyFileKind(file) {
  const ext = getFileExtension(file?.name || "");
  if (IMAGE_EXTS.includes(ext) || (file?.type && file.type.startsWith("image/"))) {
    return "image";
  }
  if (AUDIO_EXTS.includes(ext) || (file?.type && (file.type.startsWith("audio/") || file.type === "video/mp4"))) {
    return "audio";
  }
  if (DOC_EXTS.includes(ext)) {
    return "document";
  }
  return "unknown";
}

function formatDuration(totalSecs) {
  const mins = Math.floor(totalSecs / 60).toString().padStart(2, "0");
  const secs = (totalSecs % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
}

export default function CitizenComplaintPage() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [complaintText, setComplaintText] = useState("");
  const [citizenName, setCitizenName] = useState("");
  const [location, setLocation] = useState("");

  // Location auto-detection states
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [deviceLocationName, setDeviceLocationName] = useState("");
  const [locationSource, setLocationSource] = useState(null); // 'DEVICE' | 'IMAGE' | 'AUDIO' | 'MANUAL'

  // Voice Typing state (dictates text into description)
  const [isListening, setIsListening] = useState(false);
  const [voiceLang, setVoiceLang] = useState("en-IN");
  const recognitionRef = useRef(null);

  // Live Audio Recording state (records actual audio files to attach)
  const [isRecordingAudio, setIsRecordingAudio] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState("");
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioStreamRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const liveSpeechRecognitionRef = useRef(null);
  const liveTranscriptRef = useRef("");

  // Multi-file attachments state:
  // 1. Mandatory Image Attachments: [{ id, file, previewUrl, analysis, isAnalyzing }]
  const [imageAttachments, setImageAttachments] = useState([]);
  // 2. Optional Audio & Document Attachments: [{ id, file, kind: 'audio'|'document', previewUrl, isAnalyzing, analysis }]
  const [supportingAttachments, setSupportingAttachments] = useState([]);

  const [imageDragActive, setImageDragActive] = useState(false);
  const [supportDragActive, setSupportDragActive] = useState(false);
  const [imageMissingError, setImageMissingError] = useState(false);

  // Submission result state
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState(null);

  const imageSectionRef = useRef(null);

  useEffect(() => {
    if (user?.full_name && !citizenName) {
      setCitizenName(user.full_name);
    }
  }, [user]);

  // Handle URL pre-fill params from Chatbot (e.g. ?category=Electricity&text=...)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const textParam = params.get("text");
      const catParam = params.get("category");
      if (textParam) {
        setComplaintText(textParam);
      } else if (catParam) {
        setComplaintText(`I am facing an issue regarding ${catParam} in my area. Please inspect and resolve.`);
      }
    }
  }, []);

  // Auto-detect device location on initial page load
  useEffect(() => {
    detectUserDeviceLocation();
  }, []);

  // Cleanup object URLs, audio streams, and speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (liveSpeechRecognitionRef.current) {
        try {
          liveSpeechRecognitionRef.current.stop();
        } catch (e) {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, []);

  // Device Geolocation Auto-Detection
  const detectUserDeviceLocation = () => {
    if (typeof window === "undefined" || !navigator.geolocation) return;

    setIsDetectingLocation(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`
          );
          if (response.ok) {
            const data = await response.json();
            if (data?.display_name) {
              const formatted = data.display_name;
              setDeviceLocationName(formatted);
              setLocation((prev) => (!prev || prev.includes("Location") || prev.includes("Lat:") ? formatted : prev));
              setLocationSource((prev) => (prev === "IMAGE" || prev === "AUDIO" ? prev : "DEVICE"));
              setIsDetectingLocation(false);
              return;
            }
          }
        } catch (err) {
          console.warn("Reverse geocode fetch failed, using coordinates:", err);
        }

        const coordStr = `Lat: ${latitude.toFixed(5)}, Lon: ${longitude.toFixed(5)} (Device Location)`;
        setDeviceLocationName(coordStr);
        setLocation((prev) => (!prev ? coordStr : prev));
        setLocationSource((prev) => (prev === "IMAGE" || prev === "AUDIO" ? prev : "DEVICE"));
        setIsDetectingLocation(false);
      },
      (err) => {
        console.warn("Geolocation permission denied or unavailable:", err.message);
        setIsDetectingLocation(false);
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
    );
  };

  // Voice Typing (Dictates text into the Description area)
  const toggleVoiceTyping = () => {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setErrorMsg("Voice typing is not supported in this browser. Please use Google Chrome, Microsoft Edge, or Safari.");
      return;
    }

    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = voiceLang;

      recognition.onstart = () => {
        setIsListening(true);
        setErrorMsg("");
      };

      recognition.onresult = (event) => {
        const lastResultIndex = event.results.length - 1;
        const transcript = event.results[lastResultIndex][0].transcript;
        if (transcript) {
          setComplaintText((prev) => {
            const trimmed = prev.trim();
            return trimmed ? `${trimmed} ${transcript.trim()}` : transcript.trim();
          });
        }
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        if (event.error !== "no-speech") {
          setErrorMsg(`Voice typing notice (${event.error}). You can continue typing description manually.`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Failed to start voice typing:", err);
      setIsListening(false);
      setErrorMsg("Could not access microphone for voice typing. Please check microphone permissions in your browser.");
    }
  };

  // Live Audio Recording (Records and attaches actual audio file to complaint)
  const startAudioRecording = async () => {
    if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setErrorMsg("Audio recording is not supported in this browser. Please upload an audio file instead.");
      return;
    }

    try {
      setErrorMsg("");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      audioChunksRef.current = [];
      liveTranscriptRef.current = "";
      setLiveTranscript("");

      let mimeType = "audio/webm";
      if (typeof MediaRecorder !== "undefined") {
        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
          mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) {
          mimeType = "audio/ogg;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
          mimeType = "audio/mp4";
        }
      }

      // Start Concurrent Web Speech Recognition alongside audio recording
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const liveRec = new SpeechRecognition();
          liveRec.continuous = true;
          liveRec.interimResults = true;
          liveRec.lang = voiceLang || "en-IN";

          liveRec.onresult = (event) => {
            let combined = "";
            for (let i = 0; i < event.results.length; i++) {
              combined += event.results[i][0].transcript + " ";
            }
            const cleanText = combined.trim();
            if (cleanText) {
              liveTranscriptRef.current = cleanText;
              setLiveTranscript(cleanText);
            }
          };

          liveRec.onerror = (ev) => {
            console.warn("Live speech recognition notice:", ev.error);
          };

          liveRec.onend = () => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
              try {
                liveRec.start();
              } catch (e) {}
            }
          };

          liveRec.start();
          liveSpeechRecognitionRef.current = liveRec;
        } catch (recErr) {
          console.warn("Could not start live speech recognition during recording:", recErr);
        }
      }

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const ext = mimeType.includes("ogg") ? ".ogg" : mimeType.includes("mp4") ? ".m4a" : ".webm";
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        const finalTranscript = (liveTranscriptRef.current || "").trim();

        if (audioBlob.size > 0) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(11, 19);
          const recordedFile = new File([audioBlob], `recorded_audio_${timestamp}${ext}`, { type: mimeType });
          addSupportingFile(recordedFile, "audio", finalTranscript);
        }
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((track) => track.stop());
          audioStreamRef.current = null;
        }
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current);
          recordingTimerRef.current = null;
        }
        setIsRecordingAudio(false);
        setRecordingSeconds(0);
        setLiveTranscript("");
      };

      recorder.start(250);
      setIsRecordingAudio(true);
      setRecordingSeconds(0);

      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Microphone access error:", err);
      setIsRecordingAudio(false);
      setErrorMsg(
        err.name === "NotAllowedError" || err.name === "PermissionDeniedError"
          ? "Microphone access denied. Please allow microphone permissions in your browser settings to record audio."
          : `Could not start audio recording: ${err.message}`
      );
    }
  };

  const stopAudioRecording = () => {
    if (liveSpeechRecognitionRef.current) {
      try {
        liveSpeechRecognitionRef.current.onend = null;
        liveSpeechRecognitionRef.current.stop();
      } catch (e) {}
      liveSpeechRecognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const cancelAudioRecording = () => {
    if (liveSpeechRecognitionRef.current) {
      try {
        liveSpeechRecognitionRef.current.onend = null;
        liveSpeechRecognitionRef.current.stop();
      } catch (e) {}
      liveSpeechRecognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    audioChunksRef.current = [];
    liveTranscriptRef.current = "";
    setLiveTranscript("");
    setIsRecordingAudio(false);
    setRecordingSeconds(0);
  };

  // Inspect uploaded photo for EXIF GPS & visual priority
  const inspectUploadedPhoto = async (attachmentId, file) => {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const inspectionData = await fetchApi("/complaints/inspect-image", {
        method: "POST",
        body: formData,
      });

      setImageAttachments((prev) =>
        prev.map((item) =>
          item.id === attachmentId
            ? { ...item, analysis: inspectionData, isAnalyzing: false }
            : item
        )
      );

      if (inspectionData.has_gps && inspectionData.location_name) {
        setLocation(inspectionData.location_name);
        setLocationSource("IMAGE");
      } else if (deviceLocationName && !location) {
        setLocation(deviceLocationName);
        setLocationSource("DEVICE");
      }
    } catch (err) {
      console.warn("Image inspection warning:", err);
      setImageAttachments((prev) =>
        prev.map((item) =>
          item.id === attachmentId ? { ...item, isAnalyzing: false } : item
        )
      );
      if (deviceLocationName && !location) {
        setLocation(deviceLocationName);
        setLocationSource("DEVICE");
      }
    }
  };

  // Inspect recorded or uploaded audio: transcribe speech & extract words via NLP
  const inspectUploadedAudio = async (attachmentId, file, customTranscript = null) => {
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (customTranscript && customTranscript.trim()) {
        formData.append("transcript", customTranscript.trim());
      }

      const inspectionData = await fetchApi("/complaints/inspect-audio", {
        method: "POST",
        body: formData,
      });

      setSupportingAttachments((prev) =>
        prev.map((item) =>
          item.id === attachmentId
            ? {
                ...item,
                analysis: inspectionData,
                customTranscript: inspectionData.transcription || customTranscript || item.customTranscript || "",
                isAnalyzing: false,
              }
            : item
        )
      );

      if (inspectionData.spoken_location && (!location || location.includes("Device Location"))) {
        setLocation(inspectionData.spoken_location);
        setLocationSource("AUDIO");
      }
    } catch (err) {
      console.warn("Audio inspection warning:", err);
      setSupportingAttachments((prev) =>
        prev.map((item) =>
          item.id === attachmentId ? { ...item, isAnalyzing: false } : item
        )
      );
    }
  };

  const handleUpdateTranscriptText = (attachmentId, newText) => {
    setSupportingAttachments((prev) =>
      prev.map((item) =>
        item.id === attachmentId ? { ...item, customTranscript: newText } : item
      )
    );
  };

  const handleReanalyzeAudio = (attachmentId) => {
    const item = supportingAttachments.find((s) => s.id === attachmentId);
    if (!item) return;
    const textToAnalyze = (item.customTranscript || item.analysis?.transcription || "").trim();
    setSupportingAttachments((prev) =>
      prev.map((s) => (s.id === attachmentId ? { ...s, isAnalyzing: true } : s))
    );
    inspectUploadedAudio(attachmentId, item.file, textToAnalyze);
  };

  const triggerDictateForAttachment = (attachmentId) => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorMsg("Voice dictation is not supported in this browser. Please type the spoken words manually.");
      return;
    }
    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = voiceLang || "en-IN";

      recognition.onresult = (ev) => {
        const text = ev.results[0][0].transcript;
        if (text) {
          handleUpdateTranscriptText(attachmentId, text);
          const item = supportingAttachments.find((s) => s.id === attachmentId);
          if (item) {
            inspectUploadedAudio(attachmentId, item.file, text);
          }
        }
      };
      recognition.start();
    } catch (e) {
      console.warn("Attachment dictation error:", e);
    }
  };

  // Handler for adding one or more files
  const handleAddFiles = (fileList, expectedCategory = "any") => {
    if (!fileList || fileList.length === 0) return;
    const incomingFiles = Array.from(fileList);

    for (const file of incomingFiles) {
      const ext = getFileExtension(file.name);
      const kind = classifyFileKind(file);

      if (!ALL_VALID_EXTS.includes(ext) || kind === "unknown") {
        setErrorMsg(
          `Unsupported file format '${ext || file.name}'. Allowed formats: Images (.jpg, .jpeg, .png, .webp, .bmp), Audio (.mp3, .wav, .m4a, .ogg, .webm, .aac), Documents (.pdf, .docx, .txt).`
        );
        continue;
      }

      if (file.size === 0) {
        setErrorMsg(`File '${file.name}' is empty (0 bytes). Please select a valid file.`);
        continue;
      }

      if (file.size > MAX_FILE_SIZE_BYTES) {
        setErrorMsg(`File '${file.name}' exceeds the maximum allowed size limit of 10 MB.`);
        continue;
      }

      if (expectedCategory === "image" && kind !== "image") {
        addSupportingFile(file, kind);
        continue;
      }

      if (kind === "image") {
        addImageFile(file);
      } else {
        addSupportingFile(file, kind);
      }
    }
  };

  const addImageFile = (file) => {
    setErrorMsg("");
    setImageMissingError(false);

    const id = `img-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const previewUrl = URL.createObjectURL(file);

    const newEntry = {
      id,
      file,
      previewUrl,
      analysis: null,
      isAnalyzing: true,
    };

    setImageAttachments((prev) => {
      const exists = prev.some((p) => p.file.name === file.name && p.file.size === file.size);
      if (exists) return prev;
      return [...prev, newEntry];
    });

    inspectUploadedPhoto(id, file);
  };

  const addSupportingFile = (file, kind, initialTranscript = "") => {
    setErrorMsg("");

    const id = `sup-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const previewUrl = kind === "audio" ? URL.createObjectURL(file) : null;

    const newEntry = {
      id,
      file,
      kind,
      previewUrl,
      isAnalyzing: kind === "audio",
      analysis: null,
      customTranscript: initialTranscript || "",
    };

    setSupportingAttachments((prev) => {
      const exists = prev.some((p) => p.file.name === file.name && p.file.size === file.size);
      if (exists) return prev;
      return [...prev, newEntry];
    });

    if (kind === "audio") {
      inspectUploadedAudio(id, file, initialTranscript);
    }
  };

  const handleRemoveImage = (id) => {
    setImageAttachments((prev) => {
      const target = prev.find((item) => item.id === id);
      if (target?.previewUrl) {
        URL.revokeObjectURL(target.previewUrl);
      }
      const remaining = prev.filter((item) => item.id !== id);
      if (remaining.length === 0 && locationSource === "IMAGE" && deviceLocationName) {
        setLocation(deviceLocationName);
        setLocationSource("DEVICE");
      }
      return remaining;
    });
  };

  const handleRemoveSupporting = (id) => {
    setSupportingAttachments((prev) => {
      const target = prev.find((item) => item.id === id);
      if (target?.previewUrl) {
        URL.revokeObjectURL(target.previewUrl);
      }
      return prev.filter((item) => item.id !== id);
    });
  };

  // Drag & Drop handlers for Mandatory Image Zone
  const handleImageDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setImageDragActive(true);
    } else if (e.type === "dragleave") {
      setImageDragActive(false);
    }
  };

  const handleImageDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setImageDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleAddFiles(e.dataTransfer.files, "image");
    }
  };

  // Drag & Drop handlers for Optional Audio & Document Zone
  const handleSupportDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setSupportDragActive(true);
    } else if (e.type === "dragleave") {
      setSupportDragActive(false);
    }
  };

  const handleSupportDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setSupportDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleAddFiles(e.dataTransfer.files, "support");
    }
  };

  const handleUpdateImagePriority = (id, newPriority) => {
    setImageAttachments((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, customPriority: newPriority } : item
      )
    );
  };

  // Multimodal projected priority calculation:
  // Combines photo visual urgency + audio NLP words urgency
  const calculateProjectedPriority = () => {
    let highest = "Medium";
    let highestScore = PRIORITY_ORDER[highest];

    for (const img of imageAttachments) {
      const p = img.customPriority || img.analysis?.predicted_priority;
      if (p && PRIORITY_ORDER[p] && PRIORITY_ORDER[p] > highestScore) {
        highest = p;
        highestScore = PRIORITY_ORDER[p];
      }
    }

    for (const sup of supportingAttachments) {
      if (sup.kind === "audio") {
        const p = sup.analysis?.predicted_priority;
        if (p && PRIORITY_ORDER[p] && PRIORITY_ORDER[p] > highestScore) {
          highest = p;
          highestScore = PRIORITY_ORDER[p];
        }
      }
    }

    return highest;
  };

  const projectedPriority = calculateProjectedPriority();
  const primaryAudioItem = supportingAttachments.find((s) => s.kind === "audio");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
    if (isRecordingAudio) {
      stopAudioRecording();
    }

    setErrorMsg("");
    setResult(null);

    // Strictly enforce Mandatory Image Upload
    if (imageAttachments.length === 0) {
      setImageMissingError(true);
      setErrorMsg(
        "Mandatory Image Required: You must upload at least one photograph (.jpg, .jpeg, .png, .webp, .bmp) of the issue to file a complaint. Audio recordings and documents are optional."
      );
      if (imageSectionRef.current) {
        imageSectionRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return;
    }

    setSubmitting(true);

    try {
      const formData = new FormData();

      // Attach all uploaded images first
      for (const imgItem of imageAttachments) {
        formData.append("files", imgItem.file);
      }

      // Attach all optional audio (recorded or uploaded) & document files alongside the image(s)
      const transcriptsMap = {};
      for (const supItem of supportingAttachments) {
        formData.append("files", supItem.file);
        if (supItem.kind === "audio") {
          const tText = (supItem.customTranscript || supItem.analysis?.transcription || "").trim();
          if (tText) {
            transcriptsMap[supItem.file.name] = tText;
          }
        }
      }

      if (Object.keys(transcriptsMap).length > 0) {
        formData.append("audio_transcripts", JSON.stringify(transcriptsMap));
        const firstVal = Object.values(transcriptsMap)[0];
        if (firstVal) {
          formData.append("transcript", firstVal);
        }
      }

      // Enforce mandatory image check on backend
      formData.append("require_image", "true");
      formData.append("visual_priority", projectedPriority);

      if (complaintText.trim()) formData.append("complaint_text", complaintText.trim());
      if (citizenName.trim()) formData.append("citizen_name", citizenName.trim());
      if (location.trim()) formData.append("location", location.trim());

      const responseData = await fetchApi("/complaints/upload", {
        method: "POST",
        body: formData,
      });

      setResult(responseData);
    } catch (err) {
      setErrorMsg(err.message || "Failed to submit grievance. Please verify your uploaded files and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const priorityColors = {
    Critical: "bg-red-100 text-red-800 border-red-200",
    High: "bg-amber-100 text-amber-800 border-amber-200",
    Medium: "bg-blue-100 text-blue-800 border-blue-200",
    Low: "bg-slate-100 text-slate-700 border-slate-200",
    "Review Required": "bg-purple-100 text-purple-800 border-purple-200",
  };

  if (authLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-slate-500 font-medium">Verifying account authentication...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="space-y-1 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Citizen Grievance Submission Portal
          </h1>
          <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold">
            Multimodal Evidence Intake
          </span>
        </div>
        <p className="text-sm text-slate-500">
          Upload a mandatory grievance photo along with recorded voice memos or uploaded audio & documents.
          Keywords are extracted from your audio using NLP, and priority is automatically decided by correlating the extracted words with the uploaded photo.
        </p>
      </div>

      {/* Validation / Error Banner */}
      {errorMsg && (
        <div
          role="alert"
          className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3 shadow-sm animate-in fade-in"
        >
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Validation Notice</p>
            <p className="text-xs mt-0.5 leading-relaxed">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Submission Result Card */}
      {result && (
        <div className="p-6 rounded-2xl bg-white border border-emerald-200 shadow-lg space-y-6 animate-in fade-in">
          <div className="flex items-start justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">Complaint Registered Successfully</h3>
                <p className="text-xs text-slate-500 font-mono">
                  Tracking ID: <span className="font-bold text-blue-600">{result.id}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {user && (
                <Link
                  href="/complaints/my"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-xs font-semibold transition-colors"
                >
                  <span>My Grievances</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              )}
              <Link
                href={`/complaints/${result.id}`}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold transition-colors"
              >
                <span>Track Grievance</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Explainability Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Detected Category
              </span>
              <span className="text-sm font-bold text-slate-900">{result.category}</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Assigned Department
              </span>
              <span className="text-sm font-bold text-blue-700">{result.department}</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Priority Triage
              </span>
              <span
                className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                  priorityColors[result.priority] || "bg-slate-100 text-slate-700"
                }`}
              >
                {result.priority}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Assigned Location
              </span>
              <span className="text-xs font-medium text-slate-800 line-clamp-2" title={result.location || "Not specified"}>
                {result.location || "Not specified"}
              </span>
            </div>
          </div>

          {/* Attached Multi-File Evidence Confirmation */}
          {(result.attachments?.length > 0 || result.source_file_name) && (
            <div className="p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl space-y-2.5 text-xs text-indigo-900">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-indigo-950">
                  <Paperclip className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                  <span>
                    Correlated Multimodal Attachments ({result.attachments?.length || 1} file
                    {(result.attachments?.length || 1) > 1 ? "s" : ""} analyzed)
                  </span>
                </div>
                <Link
                  href={`/complaints/${result.id}`}
                  className="font-bold underline text-indigo-700 hover:text-indigo-950 flex items-center gap-1 flex-shrink-0"
                >
                  <span>View All Uploaded Media</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {result.attachments && result.attachments.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {result.attachments.map((att, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-indigo-200 text-indigo-900 font-medium shadow-sm"
                    >
                      {att.media_category === "image" ? (
                        <Camera className="w-3.5 h-3.5 text-blue-600" />
                      ) : att.media_category === "audio" ? (
                        <Music className="w-3.5 h-3.5 text-purple-600" />
                      ) : (
                        <FileText className="w-3.5 h-3.5 text-amber-600" />
                      )}
                      <span className="font-mono text-[11px]">{att.file_name}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 uppercase font-bold">
                        {att.source_type}
                      </span>
                    </span>
                  ))}
                </div>
              ) : (
                <p>
                  Attached File: <strong className="font-mono">{result.source_file_name}</strong> ({result.source_type})
                </p>
              )}
            </div>
          )}

          {/* Rule Match Score Bar */}
          <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                Multimodal Correlated Rule Match Score
              </span>
              <span className="font-bold text-blue-700">{(result.rule_match_score * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-blue-600 h-full rounded-full transition-all"
                style={{ width: `${Math.min(100, Math.max(5, result.rule_match_score * 100))}%` }}
              />
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed italic">{result.classification_reason}</p>
            {result.priority_reason && (
              <p className="text-[11px] text-amber-800 leading-relaxed font-semibold bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                <strong>Priority Rationale (Words + Photo):</strong> {result.priority_reason}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Main Unified Submission Form */}
      <form onSubmit={handleSubmit} className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        {user ? (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>
                Lodging as <strong className="font-semibold">{user.full_name}</strong> ({user.email}).
                This grievance will be automatically linked to your citizen account.
              </span>
            </div>
          </div>
        ) : (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs text-slate-600">
            <span>
              Submitting as <strong>Guest</strong>. Have an account?{" "}
              <Link href="/login" className="text-blue-600 font-semibold hover:underline">
                Sign In
              </Link>{" "}
              or{" "}
              <Link href="/register" className="text-blue-600 font-semibold hover:underline">
                Register
              </Link>{" "}
              to track all grievances in your citizen dashboard.
            </span>
          </div>
        )}

        {/* Citizen Details & Location Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Citizen Name (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Rajesh Patil"
              value={citizenName}
              onChange={(e) => setCitizenName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-blue-600" />
                <span>Location / Ward (Auto-detected)</span>
              </label>

              <button
                type="button"
                onClick={detectUserDeviceLocation}
                disabled={isDetectingLocation}
                className="text-[11px] text-blue-600 hover:text-blue-800 flex items-center gap-1 font-semibold disabled:opacity-50"
                title="Detect current device location"
              >
                <RefreshCw className={`w-3 h-3 ${isDetectingLocation ? "animate-spin" : ""}`} />
                <span>{isDetectingLocation ? "Detecting..." : "Detect GPS"}</span>
              </button>
            </div>

            <div className="relative">
              <input
                type="text"
                placeholder="e.g. Kothrud, Ward 12, near Shani Mandir"
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  setLocationSource("MANUAL");
                }}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all pr-8"
              />
              <div className="absolute right-2.5 top-3 text-slate-400">
                <Crosshair className="w-4 h-4 text-blue-500" />
              </div>
            </div>

            {/* Location Source / Auto-detection Status Pill */}
            {location && (
              <div className="mt-1 flex items-center gap-1.5 text-[11px]">
                {locationSource === "IMAGE" ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                    <Camera className="w-3 h-3 text-emerald-600" />
                    Detected from Photo EXIF GPS
                  </span>
                ) : locationSource === "AUDIO" ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 font-medium">
                    <Music className="w-3 h-3 text-purple-600" />
                    Detected from Voice Recording
                  </span>
                ) : locationSource === "DEVICE" ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                    <Crosshair className="w-3 h-3 text-blue-600" />
                    Auto-detected from Device Location
                  </span>
                ) : (
                  <span className="text-slate-400">Manually edited</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Section 1: Mandatory Image Upload (REQUIRED) */}
        <div
          ref={imageSectionRef}
          className={`space-y-3 p-5 rounded-2xl border-2 transition-all ${
            imageMissingError && imageAttachments.length === 0
              ? "border-red-400 bg-red-50/30"
              : imageAttachments.length > 0
              ? "border-emerald-200 bg-emerald-50/20"
              : "border-blue-200 bg-blue-50/20"
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Camera className="w-4 h-4 text-blue-600" />
                <span>1. Grievance Photograph Upload</span>
              </label>
              <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200 text-[10px] font-extrabold uppercase tracking-wider">
                Mandatory *
              </span>
              {imageAttachments.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 text-[10px] font-bold">
                  {imageAttachments.length} Image{imageAttachments.length > 1 ? "s" : ""} Attached
                </span>
              )}
            </div>
            <span className="text-[11px] text-slate-500">
              Formats: JPG, JPEG, PNG, WEBP, BMP (Max 10 MB per image)
            </span>
          </div>

          {imageMissingError && imageAttachments.length === 0 && (
            <div className="p-3 rounded-xl bg-red-100/80 border border-red-300 text-red-800 text-xs font-semibold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
              <span>
                An image is required to submit a complaint. Please upload at least one photograph of the issue below.
              </span>
            </div>
          )}

          {/* Mandatory Image Dropzone */}
          <div
            onDragEnter={handleImageDrag}
            onDragLeave={handleImageDrag}
            onDragOver={handleImageDrag}
            onDrop={handleImageDrop}
            className={`border-2 border-dashed rounded-xl p-5 text-center transition-all ${
              imageDragActive
                ? "border-blue-500 bg-blue-100/50"
                : imageAttachments.length > 0
                ? "border-emerald-300 bg-white"
                : "border-slate-300 hover:border-blue-400 bg-white"
            }`}
          >
            <div className="space-y-2">
              <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto shadow-sm">
                <Camera className="w-5 h-5" />
              </div>
              <p className="text-sm font-medium text-slate-700">
                {imageAttachments.length > 0 ? "Add another photograph or drag & drop here, or " : "Drag & drop your grievance photograph here, or "}
                <label className="text-blue-600 cursor-pointer font-bold hover:underline">
                  browse images
                  <input
                    type="file"
                    multiple
                    accept=".jpg,.jpeg,.png,.webp,.bmp,image/*"
                    onChange={(e) => {
                      handleAddFiles(e.target.files, "image");
                      e.target.value = "";
                    }}
                    className="hidden"
                  />
                </label>
              </p>
              <p className="text-xs text-slate-400">
                At least 1 image is mandatory. Automatically extracts EXIF GPS coordinates and visual hazard severity.
              </p>
            </div>
          </div>

          {/* Attached Images Grid */}
          {imageAttachments.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {imageAttachments.map((imgItem, idx) => (
                <div
                  key={imgItem.id}
                  className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <ImageIcon className="w-4 h-4 text-blue-600 flex-shrink-0" />
                        <div className="truncate">
                          <p className="text-xs font-bold text-slate-900 truncate" title={imgItem.file.name}>
                            {imgItem.file.name}
                          </p>
                          <p className="text-[10px] text-slate-400">
                            Image #{idx + 1} • {(imgItem.file.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveImage(imgItem.id)}
                        className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors flex-shrink-0"
                        title="Remove image"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="relative rounded-lg overflow-hidden bg-slate-100 h-40 flex items-center justify-center border border-slate-200">
                      <img
                        src={imgItem.previewUrl}
                        alt={imgItem.file.name}
                        className="object-contain max-h-40 w-auto mx-auto"
                      />
                    </div>
                  </div>

                  {/* Image Inspection Status & Priority Card */}
                  {imgItem.isAnalyzing ? (
                    <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-center gap-2 text-[11px] text-blue-700 font-medium animate-pulse">
                      <div className="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                      <span>Inspecting EXIF GPS & visual hazard...</span>
                    </div>
                  ) : imgItem.analysis ? (
                    <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-left space-y-2 text-[11px]">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-slate-700 flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-blue-600" />
                          Visual Priority:
                        </span>
                        <select
                          value={imgItem.customPriority || imgItem.analysis.predicted_priority || "Medium"}
                          onChange={(e) => handleUpdateImagePriority(imgItem.id, e.target.value)}
                          className={`px-2 py-0.5 rounded-md text-[10px] font-bold border cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-sm transition-all ${
                            priorityColors[imgItem.customPriority || imgItem.analysis.predicted_priority || "Medium"]
                          }`}
                          title="Visual urgency rating (detected from photo texture/hazards; click to adjust if needed)"
                        >
                          <option value="Critical">Critical Priority</option>
                          <option value="High">High Priority</option>
                          <option value="Medium">Medium Priority</option>
                          <option value="Low">Low Priority</option>
                          <option value="Review Required">Review Required</option>
                        </select>
                      </div>

                      {imgItem.analysis.category_hint && imgItem.analysis.category_hint !== "Other" && (
                        <div className="text-[10px] text-slate-700 flex items-center gap-1 font-medium bg-white p-1 rounded border border-slate-200">
                          <Tag className="w-3 h-3 text-blue-600 flex-shrink-0" />
                          <span>Detected Civic Hazard: <strong className="text-blue-700">{imgItem.analysis.category_hint}</strong></span>
                        </div>
                      )}

                      {imgItem.analysis.has_gps ? (
                        <div className="flex items-start gap-1 text-emerald-700 font-medium">
                          <MapPin className="w-3 h-3 text-emerald-600 flex-shrink-0 mt-0.5" />
                          <span className="line-clamp-1" title={imgItem.analysis.location_name}>
                            EXIF GPS: {imgItem.analysis.location_name}
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-start gap-1 text-slate-500">
                          <Crosshair className="w-3 h-3 text-blue-500 flex-shrink-0 mt-0.5" />
                          <span>No EXIF GPS tag — using device location</span>
                        </div>
                      )}

                      {imgItem.analysis.visual_summary && (
                        <p className="text-slate-600 text-[10px] italic bg-white p-1.5 rounded border border-slate-100 line-clamp-2">
                          &ldquo;{imgItem.analysis.visual_summary}&rdquo;
                        </p>
                      )}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 2: Optional Audio Recordings (Record & Upload) & Documents */}
        <div className="space-y-3 p-5 rounded-2xl border border-slate-200 bg-slate-50/50">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <Paperclip className="w-4 h-4 text-purple-600" />
                <span>2. Supporting Audio Recordings & Documents</span>
              </label>
              <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 text-[10px] font-bold uppercase tracking-wider">
                Optional
              </span>
              {supportingAttachments.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200 text-[10px] font-bold">
                  {supportingAttachments.length} Supporting File{supportingAttachments.length > 1 ? "s" : ""} Added
                </span>
              )}
            </div>
            <span className="text-[11px] text-slate-500">
              Record voice memos or attach audio (MP3, WAV, WEBM) & docs (PDF, DOCX, TXT)
            </span>
          </div>

          {/* Audio Action Buttons: Record Audio vs Upload Audio/Doc */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {/* 1. Record Audio Button */}
            {!isRecordingAudio ? (
              <button
                type="button"
                onClick={startAudioRecording}
                className="p-4 rounded-xl border border-purple-200 bg-white hover:bg-purple-50/70 hover:border-purple-300 transition-all flex items-center gap-3 text-left group shadow-sm"
              >
                <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                  <Mic className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-slate-900 group-hover:text-purple-700">
                      Record Voice Audio
                    </span>
                    <span className="px-1.5 py-0.2 rounded bg-purple-100 text-purple-700 text-[9px] font-bold">
                      Live Mic
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Speak your complaint; NLP extracts words and urgency.
                  </p>
                </div>
              </button>
            ) : (
              /* Active Live Audio Recording Bar */
              <div className="p-4 rounded-xl border-2 border-red-400 bg-red-50/80 flex items-center justify-between gap-3 shadow-sm">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="w-3.5 h-3.5 rounded-full bg-red-600 animate-ping flex-shrink-0" />
                  <div className="min-w-0 truncate">
                    <span className="text-xs font-bold text-red-900 block flex items-center gap-1.5">
                      <Radio className="w-3.5 h-3.5 text-red-600 animate-pulse" />
                      Recording Audio... {formatDuration(recordingSeconds)}
                    </span>
                    {liveTranscript ? (
                      <span className="text-[11px] text-red-800 font-medium italic block truncate">
                        &ldquo;{liveTranscript}&rdquo;
                      </span>
                    ) : (
                      <span className="text-[10px] text-red-700 font-medium">
                        Speak clearly into your microphone (Live speech recognition active)
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    type="button"
                    onClick={stopAudioRecording}
                    className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow flex items-center gap-1.5 transition-all"
                  >
                    <Square className="w-3 h-3 fill-current" />
                    <span>Done</span>
                  </button>
                  <button
                    type="button"
                    onClick={cancelAudioRecording}
                    className="px-2.5 py-1.5 rounded-lg bg-white hover:bg-slate-100 text-slate-600 text-xs font-semibold border border-slate-200 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* 2. Upload Audio / Document Button */}
            <div
              onDragEnter={handleSupportDrag}
              onDragLeave={handleSupportDrag}
              onDragOver={handleSupportDrag}
              onDrop={handleSupportDrop}
              className={`p-4 rounded-xl border border-dashed transition-all flex items-center gap-3 bg-white ${
                supportDragActive ? "border-purple-500 bg-purple-50/50" : "border-slate-300 hover:border-purple-300"
              }`}
            >
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0">
                <Paperclip className="w-5 h-5" />
              </div>
              <div className="truncate">
                <label className="text-xs font-bold text-purple-700 hover:underline cursor-pointer block">
                  Browse Audio or Docs
                  <input
                    type="file"
                    multiple
                    accept=".mp3,.wav,.m4a,.ogg,.webm,.aac,audio/*,.pdf,.docx,.txt"
                    onChange={(e) => {
                      handleAddFiles(e.target.files, "support");
                      e.target.value = "";
                    }}
                    className="hidden"
                  />
                </label>
                <p className="text-[11px] text-slate-500 mt-0.5 truncate">
                  Or drag & drop audio / PDF / DOCX files here
                </p>
              </div>
            </div>
          </div>

          {/* Attached Audio & Document List */}
          {supportingAttachments.length > 0 && (
            <div className="space-y-3 pt-2">
              {supportingAttachments.map((item) => (
                <div
                  key={item.id}
                  className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2.5"
                >
                  <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2">
                    <div className="flex items-center gap-2.5 min-w-0">
                      {item.kind === "audio" ? (
                        <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center flex-shrink-0">
                          <Music className="w-4 h-4" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0">
                          <FileCode className="w-4 h-4" />
                        </div>
                      )}
                      <div className="truncate">
                        <div className="flex items-center gap-2 truncate">
                          <p className="text-xs font-bold text-slate-900 truncate" title={item.file.name}>
                            {item.file.name}
                          </p>
                          {item.kind === "audio" && (
                            <span className="px-1.5 py-0.2 rounded bg-purple-50 text-purple-700 text-[9px] font-semibold">
                              Audio
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-500">
                          {item.kind === "audio"
                            ? "Voice Recording (Speech & NLP Word Extraction Active)"
                            : "Supporting Document"}{" "}
                          • {(item.file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleRemoveSupporting(item.id)}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors flex-shrink-0"
                      title="Remove attachment"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Audio Controls & NLP Word Extraction Feedback */}
                  {item.kind === "audio" && (
                    <div className="space-y-2 pt-1">
                      {item.previewUrl && (
                        <audio controls src={item.previewUrl} className="w-full h-8" />
                      )}

                      {item.isAnalyzing ? (
                        <div className="p-2.5 bg-purple-50 border border-purple-200 rounded-lg flex items-center justify-center gap-2 text-[11px] text-purple-700 font-medium animate-pulse">
                          <div className="w-3.5 h-3.5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                          <span>Transcribing speech & extracting words via NLP...</span>
                        </div>
                      ) : item.analysis ? (
                        <div className="p-3 bg-purple-50/50 border border-purple-200/80 rounded-xl space-y-2 text-xs">
                          {/* Priority & Category Bar */}
                          <div className="flex items-center justify-between flex-wrap gap-1">
                            <span className="font-bold text-purple-900 flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                              NLP Audio Urgency Assessment:
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                priorityColors[item.analysis.predicted_priority] || "bg-slate-100 text-slate-700"
                              }`}
                            >
                              {item.analysis.predicted_priority} Priority
                            </span>
                          </div>

                          {/* Verbatim Speech Transcription & Editing Box */}
                          <div className="space-y-1.5 bg-white p-2.5 rounded-xl border border-purple-100 shadow-sm">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-700 flex items-center gap-1">
                                <Mic className="w-3 h-3 text-purple-600" />
                                Spoken Speech Transcription
                              </span>
                              <div className="flex items-center gap-1.5">
                                <button
                                  type="button"
                                  onClick={() => triggerDictateForAttachment(item.id)}
                                  className="text-[10px] text-purple-700 hover:text-purple-900 font-semibold flex items-center gap-1 px-2 py-0.5 rounded bg-purple-50 hover:bg-purple-100 transition-colors"
                                  title="Dictate with microphone"
                                >
                                  <Mic className="w-3 h-3" />
                                  <span>Dictate</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleReanalyzeAudio(item.id)}
                                  className="text-[10px] text-white bg-purple-600 hover:bg-purple-700 font-semibold px-2 py-0.5 rounded shadow-sm transition-colors"
                                  title="Re-extract NLP keywords from edited text"
                                >
                                  Re-extract Words
                                </button>
                              </div>
                            </div>

                            <textarea
                              rows={2}
                              value={item.customTranscript ?? (item.analysis.transcription || "")}
                              onChange={(e) => handleUpdateTranscriptText(item.id, e.target.value)}
                              placeholder="Spoken words in this audio..."
                              className="w-full text-xs p-2 rounded-lg border border-slate-200 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 outline-none resize-none text-slate-800"
                            />
                          </div>

                          {/* NLP Extracted Words & Keywords */}
                          {item.analysis.filtered_keywords && item.analysis.filtered_keywords.length > 0 ? (
                            <div className="space-y-1">
                              <span className="text-[11px] font-semibold text-slate-700 block">
                                NLP Extracted Keywords:
                              </span>
                              <div className="flex flex-wrap gap-1">
                                {item.analysis.filtered_keywords.slice(0, 15).map((word, wIdx) => (
                                  <span
                                    key={wIdx}
                                    className="px-2 py-0.5 rounded-md bg-white border border-purple-200 text-purple-800 text-[10px] font-mono font-medium"
                                  >
                                    {word}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ) : item.customTranscript && item.customTranscript.trim() ? (
                            <div className="text-[11px] text-slate-500 italic">
                              Click &ldquo;Re-extract Words&rdquo; to process edited speech into NLP keywords.
                            </div>
                          ) : null}

                          {/* Detected Hazard Words */}
                          {item.analysis.hazard_keywords && item.analysis.hazard_keywords.length > 0 && (
                            <div className="p-2 rounded-lg bg-red-50 border border-red-200 flex items-start gap-1.5 text-red-800 text-[11px]">
                              <AlertTriangle className="w-3.5 h-3.5 text-red-600 flex-shrink-0 mt-0.5" />
                              <div>
                                <span className="font-bold">Hazard Cues Detected in Speech: </span>
                                <span className="font-semibold underline">
                                  {item.analysis.hazard_keywords.join(", ")}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Spoken Location if detected */}
                          {item.analysis.spoken_location && (
                            <div className="flex items-center gap-1.5 text-emerald-700 text-[11px] font-medium">
                              <MapPin className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                              <span>
                                Spoken Location Detected: <strong>{item.analysis.spoken_location}</strong>
                              </span>
                            </div>
                          )}
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 3: Complaint Description with Typing & Voice Typing */}
        <div className="space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <label className="block text-xs font-bold text-slate-800">
                3. Complaint Description (Optional if explained in Voice Audio / Photo)
              </label>
              <span className="text-[11px] text-slate-400 font-medium">
                (Type or use Voice Typing in English, मराठी, or हिंदी)
              </span>
            </div>

            {/* Voice Typing Controls Bar */}
            <div className="flex items-center gap-2">
              <select
                value={voiceLang}
                onChange={(e) => setVoiceLang(e.target.value)}
                disabled={isListening}
                className="text-xs bg-slate-50 border border-slate-200 text-slate-700 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                title="Select Voice Typing Language"
              >
                <option value="en-IN">English (India)</option>
                <option value="mr-IN">Marathi (मराठी)</option>
                <option value="hi-IN">Hindi (हिंदी)</option>
              </select>

              <button
                type="button"
                onClick={toggleVoiceTyping}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-semibold transition-all shadow-sm ${
                  isListening
                    ? "bg-red-600 hover:bg-red-700 text-white animate-pulse"
                    : "bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200"
                }`}
                title={isListening ? "Click to Stop Voice Typing" : "Click to Start Speaking"}
              >
                {isListening ? (
                  <>
                    <MicOff className="w-3.5 h-3.5" />
                    <span>Stop Dictating</span>
                  </>
                ) : (
                  <>
                    <Mic className="w-3.5 h-3.5 text-blue-600" />
                    <span>Voice Typing</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Voice Typing Active Indicator */}
          {isListening && (
            <div className="p-2.5 rounded-xl bg-red-50 border border-red-200 flex items-center justify-between text-xs text-red-700 animate-in fade-in">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping" />
                <span className="font-semibold">Microphone Active:</span>
                <span>
                  Speak clearly in{" "}
                  {voiceLang === "mr-IN"
                    ? "Marathi (मराठी)"
                    : voiceLang === "hi-IN"
                    ? "Hindi (हिंदी)"
                    : "English"}
                  . Spoken words will appear below.
                </span>
              </div>
              <button
                type="button"
                onClick={toggleVoiceTyping}
                className="text-red-700 hover:text-red-900 font-bold text-xs underline"
              >
                Done Speaking
              </button>
            </div>
          )}

          {/* Text Area for Typing or Voice Transcription */}
          <textarea
            rows={3}
            placeholder="Describe the civic issue here or dictate using Voice Typing... (e.g., Deep pothole on Karve road causing accidents, or आमच्या कॉलनीत गेल्या ४ दिवसांपासून पाणी येत नाही...)"
            value={complaintText}
            onChange={(e) => setComplaintText(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-y leading-relaxed"
          />
        </div>

        {/* Section 4: Multimodal Priority Correlation Preview (Photo + Audio Words) */}
        {imageAttachments.length > 0 && (
          <div className="p-4 rounded-xl border border-indigo-200 bg-gradient-to-r from-blue-50/70 via-indigo-50/60 to-purple-50/70 space-y-2.5">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                Multimodal Priority Correlation (Uploaded Photo + Audio Words)
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${priorityColors[projectedPriority]}`}>
                Projected Priority: {projectedPriority}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-700">
              <div className="bg-white/80 p-2.5 rounded-lg border border-slate-200/80 flex items-center gap-2">
                <Camera className="w-4 h-4 text-blue-600 flex-shrink-0" />
                <div>
                  <span className="font-semibold block">Uploaded Photo Visual Hazard:</span>
                  <span className="text-[10px] text-slate-500">
                    {imageAttachments[0]?.analysis?.predicted_priority
                      ? `${imageAttachments[0].analysis.predicted_priority} severity`
                      : "Photo attached — ready for visual inspection"}
                  </span>
                </div>
              </div>

              <div className="bg-white/80 p-2.5 rounded-lg border border-slate-200/80 flex items-center gap-2">
                <Music className="w-4 h-4 text-purple-600 flex-shrink-0" />
                <div>
                  <span className="font-semibold block">Spoken Audio Words (NLP):</span>
                  <span className="text-[10px] text-slate-500">
                    {primaryAudioItem?.analysis?.predicted_priority
                      ? `${primaryAudioItem.analysis.predicted_priority} urgency (${
                          primaryAudioItem.analysis.hazard_keywords?.length
                            ? `Hazard words: ${primaryAudioItem.analysis.hazard_keywords.join(", ")}`
                            : `${primaryAudioItem.analysis.word_count || 0} words extracted`
                        })`
                      : primaryAudioItem
                      ? "Audio attached — ready for NLP word extraction"
                      : "No audio attached (optional)"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Submit Grievance Button */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-md hover:shadow-blue-500/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Correlating Photo Visuals & Audio Words via NLP...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4" />
              <span>
                Submit Grievance to Municipal Authority
                {imageAttachments.length > 0
                  ? ` (${imageAttachments.length} Photo${imageAttachments.length > 1 ? "s" : ""}${
                      supportingAttachments.length > 0
                        ? ` + ${supportingAttachments.length} Audio/Doc`
                        : ""
                    })`
                  : " (Photo Required *)"}
              </span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
