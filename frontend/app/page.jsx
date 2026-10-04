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
  Cpu
} from "lucide-react";
import { fetchApi } from "../utils/api";
import { useAuth } from "../context/AuthContext";

export default function HomePage() {
  const { isAuthenticated, isAdmin, isSuperAdmin } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      if (!isAdmin) {
        setLoading(false);
        return;
      }
      try {
        const data = await fetchApi("/dashboard/stats");
        setStats(data);
      } catch (err) {
        console.warn("Dashboard stats restricted to administrators.");
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, [isAdmin]);

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
            A fully transparent, locally executed municipal governance platform. Citizens can submit grievances 
            via PDF, DOCX, TXT, or text in English and Marathi. Features rule-based classification, 
            automatic department routing, priority triage, and a retrieval-augmented information assistant.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <Link
              href="/complaints"
              className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg hover:shadow-blue-500/30 transition-all"
            >
              <FileUp className="w-4 h-4" />
              <span>Submit Grievance</span>
            </Link>

            {isAdmin ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-sm border border-white/20 transition-all backdrop-blur"
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Admin Dashboard</span>
              </Link>
            ) : isAuthenticated ? (
              <Link
                href="/complaints/my"
                className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-sm border border-white/20 transition-all backdrop-blur"
              >
                <FileUp className="w-4 h-4" />
                <span>My Complaints</span>
              </Link>
            ) : null}

            <Link
              href="/assistant"
              className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-emerald-600/30 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40 font-semibold text-sm transition-all"
            >
              <Bot className="w-4 h-4 text-emerald-400" />
              <span>Ask Municipal Assistant</span>
            </Link>
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute right-0 top-0 -mt-16 -mr-16 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* Live Operational Metrics Counters */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
            <FileUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Complaints</p>
            <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loading ? "..." : stats?.total_complaints || 0}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-lg">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Resolved</p>
            <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loading ? "..." : stats?.resolved || 0}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-lg">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Progress</p>
            <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loading ? "..." : stats?.in_progress || 0}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-lg">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">High / Critical</p>
            <p className="text-2xl sm:text-3xl font-bold text-slate-900">{loading ? "..." : stats?.high_critical_count || 0}</p>
          </div>
        </div>
      </section>

      {/* 4 Architectural Pillars */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">System Architectural Pillars</h2>
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
          ) : (
            <Link href="/assistant" className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700">
              <span>Ask Municipal Assistant</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
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
    </div>
  );
}
