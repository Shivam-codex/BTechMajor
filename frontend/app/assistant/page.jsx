"use client";

import { useState } from "react";
import Link from "next/link";
import { 
  Bot, 
  Send, 
  Sparkles, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  Building2, 
  HelpCircle, 
  ShieldCheck, 
  Tag, 
  AlertCircle,
  Lock
} from "lucide-react";
import { fetchApi } from "../../utils/api";
import { useAuth } from "../../context/AuthContext";

export default function AssistantPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: 
        "Welcome to the Non-ML Retrieval-Augmented Municipal Assistant. " +
        "I provide deterministic civic information retrieved directly from the official " +
        "Sample Municipal Knowledge Base using Classical TF-IDF Lexical Similarity.\n\n" +
        "How may I assist you with municipal procedures today?",
      sources: [],
      retrieved_chunks: [],
      confidence: 1.0,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedChunkId, setExpandedChunkId] = useState(null);

  const sampleQueries = [
    "How do I report a pothole on my street?",
    "What is the turnaround time for a major water pipeline burst?",
    "What should I do if an electrical wire is sparking?",
    "How often does the garbage truck visit our neighborhood?",
    "Can I file a complaint in Marathi or mixed script?",
  ];

  const handleSend = async (queryText = inputQuery) => {
    const q = (queryText || "").trim();
    if (!q || loading) return;

    const userMsg = {
      role: "user",
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const response = await fetchApi("/assistant/query", {
        method: "POST",
        body: JSON.stringify({ question: q }),
      });

      const assistantMsg = {
        role: "assistant",
        content: response.answer,
        sources: response.sources || [],
        retrieved_chunks: response.retrieved_chunks || [],
        confidence: response.confidence || 0.0,
        has_answer: response.has_answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Assistant Error: ${err.message || "Failed to retrieve knowledge base information."}`,
          sources: [],
          retrieved_chunks: [],
          confidence: 0.0,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-slate-500 font-medium">Verifying account authentication...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-xl mx-auto my-12 p-8 bg-white border border-slate-200 rounded-3xl shadow-sm text-center space-y-6">
        <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto">
          <Bot className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Sign In to Use Municipal Assistant</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            The retrieval-augmented civic assistant is available to verified citizens and municipal officials. 
            Please sign in or create an account to query procedures and timelines.
          </p>
        </div>
        <div className="pt-2 flex items-center justify-center gap-3">
          <Link
            href="/login"
            className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors shadow-sm"
          >
            Sign In to Portal
          </Link>
          <Link
            href="/register"
            className="px-6 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
          >
            Create Citizen Account
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="space-y-1 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center shadow">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Non-ML Municipal Assistant</h1>
            <p className="text-xs text-slate-500">
              Classical Information Retrieval Engine (TF-IDF & Cosine Similarity). Grounded exclusively in local municipal procedures.
            </p>
          </div>
        </div>
      </div>

      {/* Suggested Quick Question Chips */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
          Frequent Municipal Inquiries:
        </span>
        <div className="flex flex-wrap gap-2">
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              onClick={() => handleSend(sq)}
              className="px-3 py-1 rounded-full bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-slate-700 hover:text-blue-700 text-xs font-medium transition-all shadow-sm"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-6 min-h-[460px] max-h-[600px] overflow-y-auto space-y-6">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-2xl rounded-2xl p-4 sm:p-5 text-sm leading-relaxed shadow-sm ${
                msg.role === "user"
                  ? "bg-blue-600 text-white rounded-br-sm"
                  : "bg-slate-50 text-slate-800 border border-slate-200 rounded-bl-sm space-y-4"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Source Transparency Section for Assistant responses */}
              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div className="pt-3 border-t border-slate-200/80 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                      Audited Grounding Sources ({msg.sources.length})
                    </span>
                    <span className="text-[11px] font-mono text-blue-700 font-semibold bg-blue-100/60 px-2 py-0.5 rounded">
                      Top Similarity: {(msg.confidence * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    {msg.sources.map((src, sIdx) => (
                      <div
                        key={sIdx}
                        className="p-2.5 rounded-xl bg-white border border-slate-200 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                          <div>
                            <span className="font-semibold text-slate-900 block">{src.title}</span>
                            <span className="text-[10px] text-slate-500">{src.department} • {src.category}</span>
                          </div>
                        </div>

                        <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[10px] font-semibold text-slate-600">
                          TF-IDF: {src.score}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Expandable Retrieved Chunk Inspector */}
                  {msg.retrieved_chunks && msg.retrieved_chunks.length > 0 && (
                    <div className="pt-1">
                      <button
                        onClick={() => setExpandedChunkId(expandedChunkId === idx ? null : idx)}
                        className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                      >
                        <span>{expandedChunkId === idx ? "Hide" : "Inspect"} Exact Retrieved Knowledge Chunk</span>
                        {expandedChunkId === idx ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>

                      {expandedChunkId === idx && (
                        <div className="mt-2 p-3 rounded-xl bg-slate-900 text-slate-300 font-mono text-xs whitespace-pre-wrap border border-slate-800">
                          {msg.retrieved_chunks[0]?.text}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <span className="text-[10px] text-slate-400 mt-1 px-1">
              {msg.role === "user" ? "Citizen" : "Municipal Assistant"} • {msg.timestamp}
            </span>
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-2 text-xs text-slate-500 font-medium">
            <div className="w-4 h-4 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin mt-0.5" />
            <span>Executing Classical TF-IDF Retrieval over Municipal Index...</span>
          </div>
        )}
      </div>

      {/* Query Input Bar */}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        className="flex items-center gap-3 bg-white p-2 rounded-2xl border border-slate-200 shadow-md"
      >
        <input
          type="text"
          placeholder="Ask any question about municipal procedures, SLAs, or complaint escalation..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={loading}
          className="flex-grow px-4 py-2.5 text-sm focus:outline-none"
        />

        <button
          type="submit"
          disabled={loading || !inputQuery.trim()}
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs shadow flex items-center gap-1.5 transition-all"
        >
          <span>Ask</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
