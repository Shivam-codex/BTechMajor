"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Building2,
  Sparkles,
  Tag,
  AlertTriangle,
  FileText,
  User,
  MapPin,
  Calendar,
  Save,
  Check,
  Shield,
  ShieldCheck,
  Lock,
  Info,
  Paperclip,
  Camera,
  Volume2,
  Download,
  ExternalLink,
  Eye,
  Maximize2,
  X,
  Music,
} from "lucide-react";
import { fetchApi, getApiBaseUrl } from "../../../utils/api";
import { useAuth } from "../../../context/AuthContext";

function inferMediaCategory(fileName = "", sourceType = "", explicitCategory = "") {
  if (explicitCategory) return explicitCategory;
  const ext = "." + (fileName.includes(".") ? fileName.split(".").pop().toLowerCase() : "");
  if ([".jpg", ".jpeg", ".png", ".webp", ".bmp"].includes(ext) || sourceType === "IMAGE") {
    return "image";
  }
  if ([".mp3", ".wav", ".m4a", ".ogg", ".webm", ".aac", ".mp4"].includes(ext) || sourceType === "AUDIO") {
    return "audio";
  }
  return "document";
}

export default function ComplaintDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAdmin, isSuperAdmin } = useAuth();
  const complaintId = params.id;

  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  // Admin edit state
  const [editStatus, setEditStatus] = useState("");
  const [editDepartment, setEditDepartment] = useState("");
  const [editPriority, setEditPriority] = useState("");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Media preview state
  const [openPdfIndexes, setOpenPdfIndexes] = useState({});
  const [lightboxAttachment, setLightboxAttachment] = useState(null);

  useEffect(() => {
    async function loadComplaint() {
      try {
        const data = await fetchApi(`/complaints/${complaintId}`);
        setComplaint(data);
        setEditStatus(data.status);
        setEditDepartment(data.department);
        setEditPriority(data.priority);
        setResolutionNotes(data.resolution_notes || "");
      } catch (err) {
        setErrorMsg(err.message || "Failed to load complaint details.");
      } finally {
        setLoading(false);
      }
    }
    if (complaintId) {
      loadComplaint();
    }
  }, [complaintId]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);

    try {
      const payload = {
        status: editStatus,
        department: editDepartment,
        priority: editPriority,
        resolution_notes: resolutionNotes.trim() || null,
      };

      const updated = await fetchApi(`/complaints/${complaintId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });

      setComplaint(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const togglePdfPreview = (idx) => {
    setOpenPdfIndexes((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const priorityColors = {
    Critical: "bg-red-100 text-red-800 border-red-200",
    High: "bg-amber-100 text-amber-800 border-amber-200",
    Medium: "bg-blue-100 text-blue-800 border-blue-200",
    Low: "bg-slate-100 text-slate-700 border-slate-200",
    "Review Required": "bg-purple-100 text-purple-800 border-purple-200",
  };

  const statusColors = {
    Submitted: "bg-slate-100 text-slate-700",
    Classified: "bg-purple-100 text-purple-700",
    Assigned: "bg-blue-100 text-blue-700",
    "In Progress": "bg-amber-100 text-amber-700",
    Resolved: "bg-emerald-100 text-emerald-700",
    Rejected: "bg-red-100 text-red-700",
    "Needs Review": "bg-rose-100 text-rose-700",
  };

  const lifecycleStages = ["Submitted", "Assigned", "In Progress", "Resolved"];

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm text-slate-500 font-medium">Loading complaint record...</p>
      </div>
    );
  }

  if (errorMsg || !complaint) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16 space-y-4">
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {errorMsg || "Complaint not found."}
        </div>
        <Link
          href={isAdmin ? "/dashboard" : "/complaints/my"}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{isAdmin ? "Return to Dashboard" : "Back to My Complaints"}</span>
        </Link>
      </div>
    );
  }

  const apiBase = getApiBaseUrl();

  // Normalize attachments array (supports multi-file complaints + legacy single-file complaints)
  const rawAttachments = Array.isArray(complaint.attachments) ? complaint.attachments : [];
  const normalizedAttachments =
    rawAttachments.length > 0
      ? rawAttachments.map((att, idx) => {
          const attIdx = typeof att.index === "number" ? att.index : idx;
          const fName = att.file_name || `Attachment_${attIdx + 1}`;
          const sType = att.source_type || complaint.source_type || "DOCUMENT";
          const mCat = inferMediaCategory(fName, sType, att.media_category);
          const viewUrl = `${apiBase}/complaints/${complaint.id}/attachment?index=${attIdx}`;
          const dlUrl = `${viewUrl}&download=true`;
          return {
            index: attIdx,
            fileName: fName,
            sourceType: sType,
            mediaCategory: mCat,
            extractedText: att.extracted_text || "",
            viewUrl,
            downloadUrl: dlUrl,
            isPdf: fName.toLowerCase().endsWith(".pdf") || sType === "PDF",
          };
        })
      : complaint.source_file_name || complaint.source_file_path
      ? [
          {
            index: 0,
            fileName: complaint.source_file_name || "Uploaded Evidence",
            sourceType: complaint.source_type || "IMAGE",
            mediaCategory: inferMediaCategory(complaint.source_file_name || "", complaint.source_type || ""),
            extractedText: complaint.extracted_text || "",
            viewUrl: `${apiBase}/complaints/${complaint.id}/attachment?index=0`,
            downloadUrl: `${apiBase}/complaints/${complaint.id}/attachment?index=0&download=true`,
            isPdf:
              (complaint.source_file_name || "").toLowerCase().endsWith(".pdf") ||
              complaint.source_type === "PDF",
          },
        ]
      : [];

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Back Button & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="space-y-1">
          <Link
            href={isAdmin ? "/dashboard" : "/complaints/my"}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>{isAdmin ? "Back to Dashboard" : "Back to My Complaints"}</span>
          </Link>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 font-mono">{complaint.id}</h1>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                statusColors[complaint.status] || "bg-slate-100 text-slate-700"
              }`}
            >
              {complaint.status}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${priorityColors[complaint.priority]}`}>
            {complaint.priority} Priority
          </span>
        </div>
      </div>

      {/* Lifecycle Progress Bar */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resolution Lifecycle</h3>
        <div className="grid grid-cols-4 gap-2">
          {lifecycleStages.map((stage, idx) => {
            const isCompleted = lifecycleStages.indexOf(complaint.status) >= idx || complaint.status === "Resolved";
            const isCurrent = complaint.status === stage;
            return (
              <div key={stage} className="text-center space-y-1.5">
                <div
                  className={`h-2 rounded-full transition-all ${
                    isCompleted ? "bg-blue-600" : "bg-slate-200"
                  }`}
                />
                <span
                  className={`text-[11px] font-medium block ${
                    isCurrent ? "text-blue-700 font-bold" : "text-slate-500"
                  }`}
                >
                  {stage}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Complaint & Rule Explainability */}
        <div className="lg:col-span-2 space-y-6">
          {/* Grievance Text Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <span>Grievance Description & Correlated Summary</span>
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap bg-slate-50 p-4 rounded-xl border border-slate-100">
              {complaint.complaint_text}
            </p>

            <div className="grid grid-cols-2 gap-4 pt-2 text-xs text-slate-500">
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>
                  Citizen: <strong className="text-slate-700">{complaint.citizen_name || "Anonymous"}</strong>
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>
                  Location: <strong className="text-slate-700">{complaint.location || "Central Ward"}</strong>
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>
                  Submitted:{" "}
                  <strong className="text-slate-700">
                    {complaint.created_at ? new Date(complaint.created_at).toLocaleString() : "Recent"}
                  </strong>
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                <span>
                  Intake:{" "}
                  <strong className="text-slate-700">
                    {complaint.source_type}{" "}
                    {normalizedAttachments.length > 0 ? `(${normalizedAttachments.length} attachment${normalizedAttachments.length > 1 ? "s" : ""})` : ""}
                  </strong>
                </span>
              </div>
            </div>
          </div>

          {/* Attached Evidence & Multimodal Media Card (Supports Multiple Images, Audio, and Documents) */}
          {normalizedAttachments.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Paperclip className="w-4 h-4 text-blue-600" />
                  <span>
                    Attached Evidence & Media ({normalizedAttachments.length}{" "}
                    {normalizedAttachments.length === 1 ? "File" : "Files"})
                  </span>
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                  {complaint.source_type}
                </span>
              </div>

              <div className="space-y-5">
                {normalizedAttachments.map((att) => (
                  <div
                    key={att.index}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3"
                  >
                    {/* PHOTOGRAPHIC EVIDENCE */}
                    {att.mediaCategory === "image" && (
                      <div className="space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <Camera className="w-4 h-4 text-emerald-600" />
                            <span className="text-xs font-semibold text-slate-800">
                              Grievance Photo #{att.index + 1}:{" "}
                              <span className="font-mono text-slate-600">{att.fileName}</span>
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => setLightboxAttachment(att)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold transition-colors"
                            >
                              <Maximize2 className="w-3.5 h-3.5" />
                              <span>Enlarge</span>
                            </button>
                            <a
                              href={att.viewUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold transition-colors"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>New Tab</span>
                            </a>
                            <a
                              href={att.downloadUrl}
                              download={att.fileName}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold transition-colors"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Download</span>
                            </a>
                          </div>
                        </div>

                        <div
                          onClick={() => setLightboxAttachment(att)}
                          className="relative group rounded-xl overflow-hidden border border-slate-200 bg-white flex items-center justify-center p-3 cursor-zoom-in"
                        >
                          <img
                            src={att.viewUrl}
                            alt={att.fileName}
                            className="max-h-96 w-auto max-w-full rounded-lg object-contain shadow-sm transition-transform duration-200 group-hover:scale-[1.01]"
                          />
                          <div className="absolute inset-0 bg-slate-900/0 group-hover:bg-slate-900/10 transition-colors flex items-center justify-center pointer-events-none">
                            <span className="opacity-0 group-hover:opacity-100 transition-opacity px-3 py-1.5 rounded-lg bg-slate-900/80 text-white text-xs font-medium flex items-center gap-1.5 shadow">
                              <Maximize2 className="w-3.5 h-3.5" /> Click to enlarge photo
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* SPOKEN AUDIO RECORDING */}
                    {att.mediaCategory === "audio" && (
                      <div className="space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <Volume2 className="w-4 h-4 text-indigo-600" />
                            <div>
                              <span className="text-xs font-bold text-slate-800 block">
                                Spoken Audio Evidence #{att.index + 1}
                              </span>
                              <span className="text-[10px] text-slate-500 font-mono">{att.fileName}</span>
                            </div>
                          </div>
                          <a
                            href={att.downloadUrl}
                            download={att.fileName}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold transition-colors self-start sm:self-auto"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Download Recording</span>
                          </a>
                        </div>

                        <audio controls src={att.viewUrl} className="w-full mt-1" preload="metadata" />
                      </div>
                    )}

                    {/* DOCUMENT (PDF / DOCX / TXT) */}
                    {att.mediaCategory === "document" && (
                      <div className="space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                              <FileText className="w-5 h-5" />
                            </div>
                            <div>
                              <span className="text-xs font-bold text-slate-800 block">{att.fileName}</span>
                              <span className="text-[10px] text-slate-500 uppercase font-mono">
                                {att.sourceType} Document
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 self-start sm:self-auto">
                            {att.isPdf && (
                              <button
                                type="button"
                                onClick={() => togglePdfPreview(att.index)}
                                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold transition-colors"
                              >
                                <Eye className="w-3.5 h-3.5" />
                                <span>{openPdfIndexes[att.index] ? "Hide Preview" : "Preview PDF"}</span>
                              </button>
                            )}
                            <a
                              href={att.viewUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold transition-colors"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>Open</span>
                            </a>
                            <a
                              href={att.downloadUrl}
                              download={att.fileName}
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Download</span>
                            </a>
                          </div>
                        </div>

                        {att.isPdf && openPdfIndexes[att.index] && (
                          <div className="pt-2 animate-in fade-in">
                            <iframe
                              src={att.viewUrl}
                              className="w-full h-96 rounded-xl border border-slate-200 bg-white"
                              title={`PDF Document Preview - ${att.fileName}`}
                            />
                          </div>
                        )}
                      </div>
                    )}

                    {/* Per-Attachment Extracted Content */}
                    {att.extractedText && normalizedAttachments.length > 1 && (
                      <div className="pt-2 border-t border-slate-200/80 space-y-1">
                        <span className="text-[11px] font-semibold text-slate-600 block">
                          Extracted Analysis from {att.fileName}:
                        </span>
                        <div className="p-2.5 bg-white rounded-lg border border-slate-200 text-[11px] text-slate-600 font-mono whitespace-pre-wrap max-h-36 overflow-y-auto">
                          {att.extractedText}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* COMBINED EXTRACTED FILE CONTENT / TRANSCRIPTION */}
              {complaint.extracted_text && (
                <div className="pt-2 border-t border-slate-100 space-y-1.5">
                  <span className="text-xs font-semibold text-slate-700 block">
                    {normalizedAttachments.length > 1
                      ? "Combined Multimodal Extraction & Correlation Log:"
                      : "Extracted Attachment Content:"}
                  </span>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-600 font-mono whitespace-pre-wrap max-h-56 overflow-y-auto">
                    {complaint.extracted_text}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Explainable AI / Rule Match Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <span>Deterministic Rule Classification Explainability</span>
              </h3>
              <span className="text-xs font-bold text-indigo-600">
                Rule Match Score: {(complaint.rule_match_score * 100).toFixed(1)}%
              </span>
            </div>

            <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
              <div
                className="bg-indigo-600 h-full rounded-full"
                style={{ width: `${Math.min(100, Math.max(5, complaint.rule_match_score * 100))}%` }}
              />
            </div>

            <p className="text-xs text-slate-600 italic bg-indigo-50/50 p-3 rounded-xl border border-indigo-100">
              {complaint.classification_reason || "Predefined municipal dictionary rules matched."}
            </p>

            {complaint.matched_keywords && complaint.matched_keywords.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-slate-700 block">Triggered Rule Vocabulary Tokens:</span>
                <div className="flex flex-wrap gap-1.5">
                  {complaint.matched_keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {complaint.priority_reason && (
              <div className="pt-2 border-t border-slate-100">
                <span className="text-xs font-semibold text-slate-700 block mb-1">Priority Justification:</span>
                <p className="text-xs text-slate-600">{complaint.priority_reason}</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Admin Actions vs Citizen Status Tracking */}
        <div className="space-y-6">
          {isAdmin ? (
            <form onSubmit={handleUpdate} className="bg-white p-6 rounded-2xl border border-indigo-200 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-indigo-100 pb-2">
                <ShieldCheck className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">Admin Status & Routing Controls</h3>
              </div>

              {saveSuccess && (
                <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-emerald-600" />
                  <span>Record updated successfully.</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Lifecycle Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="Submitted">Submitted</option>
                  <option value="Classified">Classified</option>
                  <option value="Assigned">Assigned</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Needs Review">Needs Review</option>
                  <option value="Rejected">Rejected</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assigned Department</label>
                {isSuperAdmin ? (
                  <select
                    value={editDepartment}
                    onChange={(e) => setEditDepartment(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  >
                    <option value="Water Supply Department">Water Supply Department</option>
                    <option value="Sanitation Department">Sanitation Department</option>
                    <option value="Roads and Infrastructure Department">Roads and Infrastructure Department</option>
                    <option value="Electrical Department">Electrical Department</option>
                    <option value="Drainage Department">Drainage Department</option>
                    <option value="Public Health and Sanitation Department">Public Health and Sanitation Department</option>
                    <option value="Traffic Management Department">Traffic Management Department</option>
                    <option value="General Grievance Cell">General Grievance Cell</option>
                  </select>
                ) : (
                  <div className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-medium text-slate-700 flex items-center justify-between">
                    <span>{editDepartment}</span>
                    <span className="text-[10px] text-slate-400 font-mono">Assigned</span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Priority Level</label>
                <select
                  value={editPriority}
                  onChange={(e) => setEditPriority(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                  <option value="Review Required">Review Required</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Resolution & Inspection Notes</label>
                <textarea
                  rows={4}
                  placeholder="Log actions taken by field supervisors or resolution status..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 resize-y"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? "Saving Changes..." : "Update Complaint"}</span>
              </button>
            </form>
          ) : (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Grievance Progress Status</h3>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Current Stage
                </span>
                <span className="text-sm font-bold text-slate-900 block">{complaint.status}</span>
                <p className="text-xs text-slate-500">
                  {complaint.status === "Resolved"
                    ? "This grievance has been resolved by the assigned municipal department."
                    : "Assigned field workers are currently addressing this municipal grievance."}
                </p>
              </div>

              <div className="space-y-1 text-xs">
                <span className="text-slate-400 font-semibold block text-[10px] uppercase">Department In-Charge</span>
                <span className="font-semibold text-slate-800 block">{complaint.department}</span>
              </div>

              {complaint.resolution_notes && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs space-y-1">
                  <span className="font-bold block text-emerald-800">Official Department Notes:</span>
                  <p>{complaint.resolution_notes}</p>
                </div>
              )}

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-500 text-[11px] flex items-start gap-2">
                <Lock className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
                <span>
                  Administrative modifications and department reassignments are restricted to authorized municipal officers.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Photo Lightbox Modal */}
      {lightboxAttachment && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in"
          onClick={() => setLightboxAttachment(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] bg-slate-900 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between text-white text-xs">
              <span className="font-semibold truncate max-w-md">{lightboxAttachment.fileName}</span>
              <div className="flex items-center gap-2">
                <a
                  href={lightboxAttachment.downloadUrl}
                  download={lightboxAttachment.fileName}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white text-xs flex items-center gap-1 transition-colors"
                >
                  <Download className="w-3 h-3" />
                  <span>Download</span>
                </a>
                <button
                  type="button"
                  onClick={() => setLightboxAttachment(null)}
                  className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="p-4 flex items-center justify-center overflow-auto max-h-[calc(90vh-60px)]">
              <img
                src={lightboxAttachment.viewUrl}
                alt={lightboxAttachment.fileName}
                className="max-h-full max-w-full object-contain rounded-lg"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
