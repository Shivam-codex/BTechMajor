"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  ShieldCheck, 
  User, 
  Lock, 
  Mail, 
  AlertCircle, 
  ArrowRight, 
  Building2, 
  Sparkles,
  CheckCircle2
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, isAdmin } = useAuth();

  const [activeTab, setActiveTab] = useState("citizen"); // "citizen" | "admin"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const urlError = searchParams.get("error");

  // If already authenticated, redirect appropriately
  useEffect(() => {
    if (isAuthenticated) {
      if (isAdmin) {
        router.push("/dashboard");
      } else {
        router.push("/complaints/my");
      }
    }
  }, [isAuthenticated, isAdmin, router]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await login(email, password);
      if (user.role === "ADMIN") {
        router.push("/dashboard");
      } else {
        router.push("/complaints/my");
      }
    } catch (err) {
      setError(err.message || "Invalid credentials. Please verify your email and password.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (demoEmail, demoPass, tab) => {
    setActiveTab(tab);
    setEmail(demoEmail);
    setPassword(demoPass);
    setError("");
  };

  return (
    <div className="max-w-md mx-auto py-6 sm:py-10">
      {/* Brand Header */}
      <div className="text-center space-y-2 mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-500/20">
          <Building2 className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Smart City Grievance Redressal</h1>
        <p className="text-xs text-slate-500">
          Secure, Role-Segregated Authentication for Citizens and Municipal Officials
        </p>
      </div>

      {/* URL Alert Banner */}
      {urlError === "admin_required" && (
        <div className="mb-6 p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-2.5 text-xs">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Administrative Access Required</span>
            The requested page requires Municipal Administrator privileges. Please sign in with an official admin account.
          </div>
        </div>
      )}

      {/* Tab Switcher */}
      <div className="bg-slate-100 p-1 rounded-xl grid grid-cols-2 gap-1 mb-6 text-xs font-semibold">
        <button
          type="button"
          onClick={() => {
            setActiveTab("citizen");
            setError("");
          }}
          className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
            activeTab === "citizen"
              ? "bg-white text-blue-700 shadow-sm font-bold"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          <User className="w-3.5 h-3.5" />
          <span>Citizen Portal</span>
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("admin");
            setError("");
          }}
          className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
            activeTab === "admin"
              ? "bg-white text-indigo-700 shadow-sm font-bold"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Municipal Official</span>
        </button>
      </div>

      {/* Main Login Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h2 className="text-lg font-bold text-slate-900">
            {activeTab === "citizen" ? "Sign In as Citizen" : "Municipal Administrator Access"}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {activeTab === "citizen" 
              ? "Access your submitted grievances, real-time tracking, and progress updates." 
              : "Restricted command center for triage, priority management, and department workflows."}
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={activeTab === "citizen" ? "citizen@example.com" : "admin@smartcity.gov"}
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2.5 rounded-xl font-semibold text-xs text-white shadow-sm flex items-center justify-center gap-1.5 transition-all disabled:opacity-50 ${
              activeTab === "citizen"
                ? "bg-blue-600 hover:bg-blue-500 shadow-blue-500/20"
                : "bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/20"
            }`}
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        {/* Demo Fast-Fill Chips for Academic Evaluation */}
        <div className="pt-4 border-t border-slate-100 space-y-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Academic Demo Credentials:
          </span>
          <div className="space-y-1.5">
            <button
              type="button"
              onClick={() => handleQuickFill("citizen@example.com", "Citizen@12345", "citizen")}
              className="w-full text-left p-2 rounded-lg bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 text-slate-700 text-[11px] flex items-center justify-between transition-all"
            >
              <div>
                <span className="font-semibold text-blue-700">Citizen:</span> Ramesh Sharma
                <span className="block text-[10px] text-slate-400">citizen@example.com • Citizen@12345</span>
              </div>
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            </button>

            <button
              type="button"
              onClick={() => handleQuickFill("admin@smartcity.gov", "Admin@12345", "admin")}
              className="w-full text-left p-2 rounded-lg bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-slate-700 text-[11px] flex items-center justify-between transition-all"
            >
              <div>
                <span className="font-semibold text-indigo-700">Super Admin:</span> General Grievance Cell
                <span className="block text-[10px] text-slate-400">admin@smartcity.gov • Admin@12345</span>
              </div>
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
            </button>

            <button
              type="button"
              onClick={() => handleQuickFill("water.admin@smartcity.gov", "Admin@12345", "admin")}
              className="w-full text-left p-2 rounded-lg bg-slate-50 hover:bg-cyan-50 border border-slate-200 hover:border-cyan-200 text-slate-700 text-[11px] flex items-center justify-between transition-all"
            >
              <div>
                <span className="font-semibold text-cyan-700">Dept Admin:</span> Water Supply Department
                <span className="block text-[10px] text-slate-400">water.admin@smartcity.gov • Admin@12345</span>
              </div>
              <Building2 className="w-3.5 h-3.5 text-cyan-600" />
            </button>
          </div>
        </div>

        {/* Signup Link */}
        {activeTab === "citizen" && (
          <p className="text-center text-xs text-slate-500 pt-2">
            Don't have a citizen account?{" "}
            <Link href="/register" className="font-semibold text-blue-600 hover:text-blue-700 underline underline-offset-2">
              Register now
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
