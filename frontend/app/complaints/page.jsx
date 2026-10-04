"use client";

import { useState, useEffect } from "react";
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
  UserCheck
} from "lucide-react";
import API_BASE_URL, { fetchApi } from "../../utils/api";
import { useAuth } from "../../context/AuthContext";

export default function CitizenComplaintPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("manual"); // "manual" or "upload"
  const [complaintText, setComplaintText] = useState("");
  const [citizenName, setCitizenName] = useState("");
  const [location, setLocation] = useState("");

  useEffect(() => {
    if (user?.full_name && !citizenName) {
      setCitizenName(user.full_name);
    }
  }, [user]);
  
  // File upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [extractedPreview, setExtractedPreview] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);

  // Submission result state
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState(null);

  // Handle Drag & Drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file) => {
    const validExts = [".pdf", ".docx", ".txt"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!validExts.includes(ext)) {
      setErrorMsg(`Invalid file type '${ext}'. Please upload PDF, DOCX, or TXT.`);
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("File size exceeds maximum allowed limit of 10 MB.");
      return;
    }
    setErrorMsg("");
    setSelectedFile(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSubmitting(true);
    setResult(null);

    try {
      let responseData;
      if (activeTab === "upload") {
        if (!selectedFile) {
          throw new Error("Please select a PDF, DOCX, or TXT file to upload.");
        }
        const formData = new FormData();
        formData.append("file", selectedFile);
        if (citizenName.trim()) formData.append("citizen_name", citizenName.trim());
        if (location.trim()) formData.append("location", location.trim());

        responseData = await fetchApi("/complaints/upload", {
          method: "POST",
          body: formData,
        });
      } else {
        if (!complaintText.trim() || complaintText.trim().length < 5) {
          throw new Error("Complaint description must be at least 5 characters long.");
        }
        const payload = {
          complaint_text: complaintText.trim(),
          citizen_name: citizenName.trim() || null,
          location: location.trim() || null,
        };
        responseData = await fetchApi("/complaints", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }

      setResult(responseData);
    } catch (err) {
      setErrorMsg(err.message || "Failed to submit grievance. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const priorityColors = {
    Critical: "bg-red-100 text-red-800 border-red-200",
    High: "bg-amber-100 text-amber-800 border-amber-200",
    Medium: "bg-blue-100 text-blue-800 border-blue-200",
    Low: "bg-slate-100 text-slate-700 border-slate-200",
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Citizen Grievance Submission Portal</h1>
        <p className="text-sm text-slate-500">
          Lodge your civic complaint via direct text or official document upload. The system automatically categorizes 
          the grievance, computes rule match scores, and routes it to the designated municipal department.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-4">
        <button
          type="button"
          onClick={() => { setActiveTab("manual"); setErrorMsg(""); }}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "manual"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Manual Text Input</span>
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab("upload"); setErrorMsg(""); }}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "upload"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          <span>Document Upload (PDF, DOCX, TXT)</span>
        </button>
      </div>

      {/* Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Submission Error</p>
            <p className="text-xs mt-0.5">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Submission Result Card */}
      {result && (
        <div className="p-6 rounded-2xl bg-white border border-emerald-200 shadow-lg space-y-6">
          <div className="flex items-start justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">Complaint Registered Successfully</h3>
                <p className="text-xs text-slate-500 font-mono">Tracking ID: <span className="font-bold text-blue-600">{result.id}</span></p>
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
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Detected Category</span>
              <span className="text-sm font-bold text-slate-900">{result.category}</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Assigned Department</span>
              <span className="text-sm font-bold text-blue-700">{result.department}</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Priority Triage</span>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border ${priorityColors[result.priority] || "bg-slate-100 text-slate-700"}`}>
                {result.priority}
              </span>
            </div>
          </div>

          {/* Rule Match Score Bar */}
          <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                Rule Match Score (Deterministic Non-ML Metric)
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
          </div>

          {/* Matched Keywords */}
          {result.matched_keywords && result.matched_keywords.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-slate-700 block">Matched Rule Vocabulary Tokens:</span>
              <div className="flex flex-wrap gap-1.5">
                {result.matched_keywords.map((kw, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Form */}
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">Location / Ward (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Kothrud, Ward 12"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
          </div>
        </div>

        {activeTab === "manual" ? (
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">Complaint Description *</label>
              <span className="text-[11px] text-slate-400">English or Marathi (मराठी)</span>
            </div>
            <textarea
              rows={6}
              required
              placeholder="Describe your civic issue in detail (e.g. Deep pothole on Karve road causing accidents, or आमच्या कॉलनीत गेल्या ४ दिवसांपासून पाणी येत नाही...)"
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-y"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
                dragActive
                  ? "border-blue-500 bg-blue-50/50"
                  : "border-slate-300 hover:border-slate-400 bg-slate-50/50"
              }`}
            >
              <UploadCloud className="w-10 h-10 mx-auto text-blue-600 mb-2" />
              <p className="text-sm font-semibold text-slate-700">
                Drag and drop your complaint document here, or{" "}
                <label className="text-blue-600 cursor-pointer hover:underline">
                  browse files
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
              </p>
              <p className="text-xs text-slate-400 mt-1">Supports PDF, DOCX, or TXT up to 10 MB</p>

              {selectedFile && (
                <div className="mt-4 p-3 bg-white rounded-xl border border-slate-200 inline-flex items-center gap-3 text-xs text-slate-700 font-medium">
                  <FileCode className="w-4 h-4 text-blue-600" />
                  <span>{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                </div>
              )}
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-md hover:shadow-blue-500/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Analyzing Grievance via Deterministic NLP...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4" />
              <span>Submit Grievance to Municipal Authority</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
