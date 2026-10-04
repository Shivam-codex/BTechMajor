"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  FileUp, 
  LayoutDashboard, 
  Bot, 
  BookOpen, 
  ArrowRight, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Droplet, 
  Trash2, 
  Construction, 
  Lightbulb, 
  Waves, 
  Bath, 
  Zap, 
  Car, 
  SearchCheck, 
  ShieldCheck, 
  Cpu,
  LogIn,
  UserPlus,
  FolderOpen,
  Check,
  Building2,
  Sparkles
} from "lucide-react";
import { fetchApi } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import AuthModal from "../components/AuthModal";

export default function HomePage() {
  const { isAuthenticated, user, isCitizen, isAdmin, isSuperAdmin, loading: authLoading } = useAuth();
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Auth Popup Modal State
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalTab, setAuthModalTab] = useState("login"); // "login" | "register"

  // Automatically trigger the Login/Register popup when visiting the site unauthenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      setShowAuthModal(true);
    }
  }, [authLoading, isAuthenticated]);

  // Fetch admin dashboard stats only if authenticated as administrator
  useEffect(() => {
    async function loadStats() {
      if (!isAdmin) return;
      setLoadingStats(true);
      try {
        const data = await fetchApi("/dashboard/stats");
        setStats(data);
      } catch (err) {
        console.warn("Dashboard stats restricted to administrators.");
      } finally {
        setLoadingStats(false);
      }
    }
    loadStats();
  }, [isAdmin]);

  const openLoginModal = () => {
    setAuthModalTab("login");
    setShowAuthModal(true);
  };

  const openRegisterModal = () => {
    setAuthModalTab("register");
    setShowAuthModal(true);
  };

  const categories = [
    { name: "Water Supply", icon: Droplet, color: "text-blue-500 bg-blue-50" },
    { name: "Garbage/Waste", icon: Trash2, color: "text-emerald-500 bg-emerald-50" },
    { name: "Road/Pothole", icon: Construction, color: "text-amber-500 bg-amber-50" },
    { name: "Street Light", icon: Lightbulb, color: "text-yellow-500 bg-yellow-50" },
    { name: "Drainage/Sewerage", icon: Waves, color: "text-cyan-500 bg-cyan-50" },
    { name: "Public Toilet", icon: Bath, color: "text-teal-500 bg-teal-50" },
    { name: "Electricity", icon: Zap, color: "text-purple-500 bg-purple-50" },
    { name: "Traffic", icon: Car, color: "text-rose-500 bg-rose-50" },
  ];

  const steps = [
    {
      num: "01",
      title: "Citizen & Official Access",
      desc: "Secure 100% local cryptographic authentication segregates citizen grievance portfolios from municipal departmental dashboards.",
    },
    {
      num: "02",
      title: "Multi-Format Grievance Intake",
      desc: "Citizens lodge civic issues via direct text or official documents (PDF, DOCX, TXT) in English and Marathi.",
    },
    {
      num: "03",
      title: "Deterministic NLP Routing",
      desc: "Automated lexical tokenization and explainable rule matching compute match scores and route complaints to the responsible department.",
    },
    {
      num: "04",
      title: "Auditable Redressal & Resolution",
      desc: "Track real-time status updates, priority escalations, and official resolution notes until final grievance closure.",
    },
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 text-white p-8 sm:p-12 lg:p-16 shadow-2xl">
        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-semibold">
            <Cpu className="w-3.5 h-3.5 text-blue-400" />
            <span>Deterministic Natural Language Processing • Non-ML Retrieval Engine</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
            AI-Based Smart City <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-200">
              Complaint Management System
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl">
            A transparent, locally executed civic grievance management platform. Built strictly with 
            classical natural language processing, rule-based classification, and lexical information retrieval 
            without external cloud or black-box dependencies.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center gap-4 pt-4">
            {!isAuthenticated ? (
              <>
                <button
                  type="button"
                  onClick={openLoginModal}
                  className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg hover:shadow-blue-500/30 transition-all"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Sign In to Portal</span>
                </button>

                <button
                  type="button"
                  onClick={openRegisterModal}
                  className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-sm border border-white/20 transition-all backdrop-blur"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Create Citizen Account</span>
                </button>
              </>
            ) : isCitizen ? (
              <>
                <Link
                  href="/complaints/my"
                  className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg hover:shadow-blue-500/30 transition-all"
                >
                  <FolderOpen className="w-4 h-4" />
                  <span>My Complaints</span>
                </Link>

                <Link
                  href="/complaints"
                  className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-sm border border-white/20 transition-all backdrop-blur"
                >
                  <FileUp className="w-4 h-4" />
                  <span>Submit Grievance</span>
                </Link>

                <Link
                  href="/assistant"
                  className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-emerald-600/30 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40 font-semibold text-sm transition-all"
                >
                  <Bot className="w-4 h-4 text-emerald-400" />
                  <span>Ask Municipal Assistant</span>
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg hover:shadow-blue-500/30 transition-all"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span>Admin Operations Dashboard</span>
                </Link>

                <Link
                  href="/complaints"
                  className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-sm border border-white/20 transition-all backdrop-blur"
                >
                  <FileUp className="w-4 h-4" />
                  <span>Lodge Intake</span>
                </Link>

                {isSuperAdmin && (
                  <Link
                    href="/knowledge-base"
                    className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-indigo-600/40 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 font-semibold text-sm transition-all"
                  >
                    <BookOpen className="w-4 h-4 text-indigo-300" />
                    <span>Knowledge Base</span>
                  </Link>
                )}
              </>
            )}
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute right-0 top-0 -mt-16 -mr-16 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* Live Operational Metrics Counters (Only for Administrators) */}
      {isAdmin && (
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
              <FileUp className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Complaints</p>
              <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loadingStats ? "..." : stats?.total_complaints || 0}</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-lg">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Resolved</p>
              <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loadingStats ? "..." : stats?.resolved || 0}</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-lg">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Progress</p>
              <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loadingStats ? "..." : stats?.in_progress || 0}</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-lg">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">High / Critical</p>
              <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loadingStats ? "..." : stats?.high_critical_count || 0}</p>
            </div>
          </div>
        </section>
      )}

      {/* How It Works - Platform Overview */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto">
          <span className="text-xs font-bold text-blue-600 uppercase tracking-wider block mb-1">System Overview</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">How Municipal Redressal Works</h2>
          <p className="text-sm text-slate-500 mt-1">An automated, auditable civic pipeline designed for fast and transparent complaint resolution.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step) => (
            <div key={step.num} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 relative hover:border-blue-300 transition-colors">
              <span className="text-3xl font-black text-slate-200 block font-mono">{step.num}</span>
              <h3 className="text-base font-bold text-slate-900">{step.title}</h3>
              <p className="text-xs text-slate-600 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 3 Architectural Pillars */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto">
          <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider block mb-1">Technical Architecture</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">System Architectural Pillars</h2>
          <p className="text-sm text-slate-500 mt-1">Engineered strictly without black-box machine learning or external cloud dependencies.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
              <SearchCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Deterministic NLP Engine</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Regex tokenization, Unicode NFC canonical normalization, and bilingual vocabulary dictionaries 
              supporting English and Marathi (Devanagari) grievances with exact keyword matching.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Explainable Rule Scoring</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Weighted rule points (Phrases: 5pts, Keywords: 3pts, Synonyms: 2pts, Negative penalties: -4pts) 
              producing a transparent <strong>Rule Match Score</strong> with an auditable explanation chain.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <Bot className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">Non-ML Municipal Assistant</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Classical TF-IDF and Okapi BM25 information retrieval over 14 structured academic documents (74 chunks). 
              Grounded, hallucination-free answers with full source transparency.
            </p>
          </div>
        </div>
      </section>

      {/* Supported Civic Categories */}
      <section className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-slate-900">Municipal Grievance Categories</h3>
            <p className="text-xs text-slate-500 mt-0.5">Automated rule classification and department routing across 9 civic domains.</p>
          </div>
          {isSuperAdmin ? (
            <Link href="/knowledge-base" className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700">
              <span>View All Procedures</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          ) : isAuthenticated ? (
            <Link href="/assistant" className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700">
              <span>Ask Municipal Assistant</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          ) : null}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {categories.map((cat) => {
            const Icon = cat.icon;
            return (
              <div key={cat.name} className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${cat.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-900">{cat.name}</h4>
                  <span className="text-[10px] text-slate-400">Automated Routing</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Bottom CTA Banner for Visitors */}
      {!isAuthenticated && (
        <section className="bg-slate-900 text-white p-8 sm:p-10 rounded-3xl text-center space-y-5 border border-slate-800 shadow-xl">
          <div className="max-w-xl mx-auto space-y-2">
            <h3 className="text-2xl font-extrabold tracking-tight">Ready to Lodge a Civic Complaint?</h3>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Sign in or create a free citizen account to register grievances, track resolution timelines, and receive municipal updates.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={openLoginModal}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-md shadow-blue-500/20 transition-all flex items-center gap-2"
            >
              <LogIn className="w-4 h-4" />
              <span>Sign In to Access Portal</span>
            </button>

            <button
              type="button"
              onClick={openRegisterModal}
              className="px-6 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs border border-white/20 transition-all flex items-center gap-2"
            >
              <UserPlus className="w-4 h-4" />
              <span>Register New Citizen</span>
            </button>
          </div>
        </section>
      )}

      {/* Login & Register Popup Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialTab={authModalTab}
      />
    </div>
  );
}
