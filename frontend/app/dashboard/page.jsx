"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  LayoutDashboard, 
  Search, 
  Filter, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  FileText, 
  ArrowRight, 
  RefreshCw,
  Eye,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  LogIn,
  ShieldCheck,
  Building2
} from "lucide-react";
import { fetchApi } from "../../utils/api";
import { useAuth } from "../../context/AuthContext";

export default function AdminDashboardPage() {
  const { user, isAdmin, isSuperAdmin, loading: authLoading } = useAuth();

  const [stats, setStats] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const loadData = async () => {
    if (!isAdmin) return;
    setLoading(true);
    try {
      // 1. Fetch dashboard statistics (scoped to department if departmental admin)
      const statsParams = new URLSearchParams();
      if (isSuperAdmin && departmentFilter) {
        statsParams.append("department", departmentFilter);
      }
      const statsUrl = `/dashboard/stats${statsParams.toString() ? `?${statsParams.toString()}` : ""}`;
      const statsData = await fetchApi(statsUrl);
      setStats(statsData);

      // 2. Build complaints query params
      const queryParams = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });
      if (searchTerm.trim()) queryParams.append("search", searchTerm.trim());
      if (categoryFilter) queryParams.append("category", categoryFilter);
      if (isSuperAdmin) {
        if (departmentFilter) queryParams.append("department", departmentFilter);
      } else if (user?.department) {
        queryParams.append("department", user.department);
      }
      if (priorityFilter) queryParams.append("priority", priorityFilter);
      if (statusFilter) queryParams.append("status", statusFilter);

      const listData = await fetchApi(`/complaints?${queryParams.toString()}`);
      setComplaints(listData.items || []);
      setTotalCount(listData.total || 0);
    } catch (err) {
      console.error("Dashboard data fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && isAdmin) {
      loadData();
    }
  }, [authLoading, isAdmin, page, categoryFilter, departmentFilter, priorityFilter, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadData();
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
    "Needs Review": "bg-rose-100 text-rose-700 font-bold",
  };

  const totalPages = Math.ceil(totalCount / limit) || 1;

  if (authLoading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Verifying Administrator Permissions...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-6">
        <div className="w-16 h-16 rounded-3xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto shadow-sm">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-slate-900">Administrative Access Required</h2>
          <p className="text-xs text-slate-600 leading-relaxed max-w-sm mx-auto">
            The Municipal Command Center is strictly segregated and protected from unauthorized citizen access.
            Please sign in with a verified Municipal Official account.
          </p>
        </div>
        <div className="flex items-center justify-center gap-3">
          <Link
            href="/login?error=admin_required"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-sm shadow-indigo-500/20 transition-all"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In as Municipal Official</span>
          </Link>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-all"
          >
            <span>Return Home</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
              isSuperAdmin 
                ? "bg-purple-100 text-purple-800 border-purple-200" 
                : "bg-blue-100 text-blue-800 border-blue-200"
            }`}>
              {isSuperAdmin ? "Super Admin: All Municipal Departments" : `Department Admin: ${user?.department || "General"}`}
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5 mt-1">
            <LayoutDashboard className="w-6 h-6 text-indigo-600" />
            <span>
              {isSuperAdmin ? "City-Wide Grievance Command Center" : `${user?.department} Command Center`}
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Logged in as <strong className="text-slate-800">{user?.full_name}</strong>.{" "}
            {isSuperAdmin 
              ? "Comprehensive municipal overview across all civic departments."
              : `Strict departmental segregation active: You have administrative authority exclusively over ${user?.department} grievances.`}
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-sm transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Total Grievances</span>
          <span className="text-2xl font-black text-slate-900">{stats?.total_complaints ?? 0}</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Submitted</span>
          <span className="text-2xl font-black text-slate-700">{stats?.submitted ?? 0}</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 block mb-1">In Progress</span>
          <span className="text-2xl font-black text-amber-600">{stats?.in_progress ?? 0}</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 block mb-1">Resolved</span>
          <span className="text-2xl font-black text-emerald-600">{stats?.resolved ?? 0}</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600 block mb-1">Needs Review</span>
          <span className="text-2xl font-black text-rose-600">{stats?.needs_review ?? 0}</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-red-600 block mb-1">High / Critical</span>
          <span className="text-2xl font-black text-red-600">{stats?.high_critical_count ?? 0}</span>
        </div>
      </div>

      {/* Visual Distributions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Complaints by Category</h3>
          <div className="space-y-2">
            {stats?.by_category && stats.by_category.slice(0, 5).map((cat) => (
              <div key={cat.category} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-700 font-medium">{cat.category}</span>
                  <span className="text-slate-400 font-mono">{cat.count} ({cat.percentage}%)</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-600 h-full rounded-full" style={{ width: `${cat.percentage}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Breakdown */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Complaints by Priority</h3>
          <div className="grid grid-cols-2 gap-3 pt-2">
            {stats?.by_priority && stats.by_priority.map((p) => (
              <div key={p.priority} className="p-3 rounded-xl border border-slate-100 bg-slate-50 flex items-center justify-between">
                <div>
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${priorityColors[p.priority]}`}>
                    {p.priority}
                  </span>
                </div>
                <span className="text-base font-bold text-slate-900">{p.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-grow">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by Complaint ID, citizen name, location, or grievance text..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow transition-all"
          >
            Search
          </button>
        </form>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
          <select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-slate-50 text-slate-700 font-medium"
          >
            <option value="">All Categories</option>
            <option value="Water Supply">Water Supply</option>
            <option value="Garbage/Waste Management">Garbage/Waste Management</option>
            <option value="Road/Pothole">Road/Pothole</option>
            <option value="Street Light">Street Light</option>
            <option value="Drainage/Sewerage">Drainage/Sewerage</option>
            <option value="Public Toilet">Public Toilet</option>
            <option value="Electricity">Electricity</option>
            <option value="Traffic">Traffic</option>
            <option value="Other">Other</option>
          </select>

          {isSuperAdmin ? (
            <select
              value={departmentFilter}
              onChange={(e) => { setDepartmentFilter(e.target.value); setPage(1); }}
              className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-slate-50 text-slate-700 font-medium"
            >
              <option value="">All Departments</option>
              <option value="Water Supply Department">Water Supply Department</option>
              <option value="Sanitation Department">Sanitation Department</option>
              <option value="Roads and Infrastructure Department">Roads & Infrastructure</option>
              <option value="Electrical Department">Electrical Department</option>
              <option value="Drainage Department">Drainage Department</option>
              <option value="Public Health and Sanitation Department">Public Health</option>
              <option value="Traffic Management Department">Traffic Department</option>
              <option value="General Grievance Cell">General Grievance Cell</option>
            </select>
          ) : (
            <div className="px-3 py-1.5 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-900 text-xs font-semibold flex items-center justify-between">
              <span className="truncate">{user?.department}</span>
              <span className="text-[10px] text-indigo-600 uppercase font-mono ml-1.5">Locked</span>
            </div>
          )}

          <select
            value={priorityFilter}
            onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-slate-50 text-slate-700 font-medium"
          >
            <option value="">All Priorities</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-slate-50 text-slate-700 font-medium"
          >
            <option value="">All Statuses</option>
            <option value="Submitted">Submitted</option>
            <option value="Assigned">Assigned</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Needs Review">Needs Review</option>
            <option value="Rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Complaints Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3.5 px-4">Complaint ID</th>
                <th className="py-3.5 px-4">Category</th>
                <th className="py-3.5 px-4">Grievance Preview</th>
                <th className="py-3.5 px-4">Priority</th>
                <th className="py-3.5 px-4">Rule Score</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {complaints.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-slate-400">
                    No complaints found matching the specified criteria.
                  </td>
                </tr>
              ) : (
                complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-blue-700">{c.id}</td>
                    <td className="py-3 px-4 font-medium text-slate-900">{c.category}</td>
                    <td className="py-3 px-4 max-w-xs truncate text-slate-600">{c.complaint_text}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${priorityColors[c.priority]}`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-indigo-600">
                      {(c.rule_match_score * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${statusColors[c.status] || "bg-slate-100 text-slate-700"}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/complaints/${c.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-blue-50 text-slate-600 hover:text-blue-700 font-semibold transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Showing page {page} of {totalPages} ({totalCount} total records)</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-slate-700 px-2">{page}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
