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
  Info
} from "lucide-react";
import { fetchApi } from "../../../utils/api";
import { useAuth } from "../../../context/AuthContext";

export default function ComplaintDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAdmin } = useAuth();
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

  const priorityColors = {
    Critical: "bg-red-100 text-red-800 border-red-200",
    High: "bg-amber-100 text-amber-800 border-amber-200",
    Medium: "bg-blue-100 text-blue-800 border-blue-200",
    Low: "bg-slate-100 text-slate-700 border-slate-200",
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
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600">
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Back Button & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="space-y-1">
          <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors mb-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 font-mono">{complaint.id}</h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${statusColors[complaint.status] || "bg-slate-100 text-slate-700"}`}>
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
                <span className={`text-[11px] font-medium block ${isCurrent ? "text-blue-700 font-bold" : "text-slate-500"}`}>
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
              <span>Grievance Description</span>
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap bg-slate-50 p-4 rounded-xl border border-slate-100">
              {complaint.complaint_text}
            </p>

            <div className="grid grid-cols-2 gap-4 pt-2 text-xs text-slate-500">
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Citizen: <strong className="text-slate-700">{complaint.citizen_name || "Anonymous"}</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>Location: <strong className="text-slate-700">{complaint.location || "Central Ward"}</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Submitted: <strong className="text-slate-700">{complaint.created_at ? new Date(complaint.created_at).toLocaleString() : "Recent"}</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                <span>Intake: <strong className="text-slate-700">{complaint.source_type} {complaint.source_file_name ? `(${complaint.source_file_name})` : ""}</strong></span>
              </div>
            </div>
          </div>

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
                    <span key={i} className="px-2.5 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono">
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
                <h3 className="text-sm font-bold text-slate-900">
                  Admin Status & Routing Controls
                </h3>
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
                <h3 className="text-sm font-bold text-slate-900">
                  Grievance Progress Status
                </h3>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Current Stage
                </span>
                <span className="text-sm font-bold text-slate-900 block">
                  {complaint.status}
                </span>
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
    </div>
  );
}
