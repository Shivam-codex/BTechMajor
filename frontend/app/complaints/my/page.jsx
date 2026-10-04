"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  FileText, 
  PlusCircle, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldCheck, 
  ArrowRight, 
  RefreshCw,
  Search,
  Filter,
  Eye,
  Inbox
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { fetchApi } from "../../../utils/api";

export default function MyComplaintsPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const loadMyComplaints = async () => {
    setLoading(true);
    try {
      const data = await fetchApi("/complaints?page=1&limit=50&my_only=true");
      setComplaints(data.items || []);
    } catch (err) {
      console.error("Failed to load user complaints:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated) {
        router.push("/login");
      } else {
        loadMyComplaints();
      }
    }
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || (loading && complaints.length === 0)) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Loading your grievance portfolio...</p>
      </div>
    );
  }

  const filteredComplaints = complaints.filter((c) => {
    const matchesSearch = 
      !searchTerm.trim() || 
      c.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
      c.complaint_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const submittedCount = complaints.filter(c => c.status === "Submitted").length;
  const inProgressCount = complaints.filter(c => c.status === "In Progress" || c.status === "Assigned").length;
  const resolvedCount = complaints.filter(c => c.status === "Resolved").length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <span className="text-[11px] font-bold text-blue-600 tracking-wider uppercase">
            Citizen Grievance Portfolio
          </span>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            My Submitted Complaints
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Logged in as <span className="font-semibold text-slate-800">{user?.full_name}</span> ({user?.email})
          </p>
        </div>

        <Link
          href="/complaints"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-sm shadow-blue-500/20 transition-all self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Lodge New Grievance</span>
        </Link>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Filed</span>
          <span className="text-2xl font-bold text-slate-900 mt-1 block">{complaints.length}</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider block">Submitted</span>
          <span className="text-2xl font-bold text-amber-700 mt-1 block">{submittedCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">Under Action</span>
          <span className="text-2xl font-bold text-blue-700 mt-1 block">{inProgressCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">Resolved</span>
          <span className="text-2xl font-bold text-emerald-700 mt-1 block">{resolvedCount}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-grow w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by ID, keyword, or category..."
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-full sm:w-44 px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700"
        >
          <option value="">All Statuses</option>
          <option value="Submitted">Submitted</option>
          <option value="Assigned">Assigned</option>
          <option value="In Progress">In Progress</option>
          <option value="Resolved">Resolved</option>
          <option value="Needs Review">Needs Review</option>
        </select>

        <button
          onClick={loadMyComplaints}
          className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 self-stretch sm:self-auto flex items-center justify-center"
          title="Refresh List"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Grievances List */}
      {filteredComplaints.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <Inbox className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">No Grievances Found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {complaints.length === 0 
                ? "You haven't filed any municipal complaints yet. Submit a grievance to track civic resolution." 
                : "No complaints match your current search and filter criteria."}
            </p>
          </div>
          {complaints.length === 0 && (
            <Link
              href="/complaints"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-sm transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Submit First Grievance</span>
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredComplaints.map((cmp) => {
            const isCritical = cmp.priority === "Critical";
            const isHigh = cmp.priority === "High";
            const isResolved = cmp.status === "Resolved";
            const isInProgress = cmp.status === "In Progress" || cmp.status === "Assigned";

            return (
              <div
                key={cmp.id}
                className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-blue-200 transition-all space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-lg border border-blue-100">
                      {cmp.id}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Filed on {cmp.created_at ? new Date(cmp.created_at).toLocaleDateString() : "Recent"}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Status Badge */}
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold flex items-center gap-1 ${
                        isResolved
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : isInProgress
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {isResolved && <CheckCircle2 className="w-3 h-3" />}
                      {isInProgress && <Clock className="w-3 h-3" />}
                      <span>{cmp.status}</span>
                    </span>

                    {/* Priority Badge */}
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        isCritical
                          ? "bg-rose-100 text-rose-800"
                          : isHigh
                          ? "bg-orange-100 text-orange-800"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {cmp.priority} Priority
                    </span>
                  </div>
                </div>

                {/* Complaint Body */}
                <p className="text-xs text-slate-700 line-clamp-2 leading-relaxed">
                  {cmp.complaint_text}
                </p>

                {/* Details Footer */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 text-[11px] text-slate-500 border-t border-slate-50">
                  <div className="flex flex-wrap items-center gap-3">
                    <span>
                      <strong className="text-slate-700">Category:</strong> {cmp.category}
                    </span>
                    <span>•</span>
                    <span>
                      <strong className="text-slate-700">Department:</strong> {cmp.department}
                    </span>
                    <span>•</span>
                    <span className="text-blue-600 font-medium">
                      Rule Match Score: {cmp.rule_match_score}
                    </span>
                  </div>

                  <Link
                    href={`/complaints/${cmp.id}`}
                    className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-700 text-xs self-end sm:self-auto"
                  >
                    <span>View Timeline & Explainability</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
