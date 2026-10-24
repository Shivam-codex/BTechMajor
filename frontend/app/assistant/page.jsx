"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { 
  Bot, 
  Send, 
  Sparkles, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  Building2, 
  ShieldCheck, 
  Lock,
  ArrowRight,
  PhoneCall,
  Zap,
  ListFilter,
  Copy,
  Check,
  RotateCcw,
  ExternalLink,
  MessageSquareQuote,
  HelpCircle
} from "lucide-react";
import { fetchApi } from "../../utils/api";
import { useAuth } from "../../context/AuthContext";

export default function AssistantPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const messagesEndRef = useRef(null);
  const [copiedIdx, setCopiedIdx] = useState(null);

  const initialGreeting = {
    role: "assistant",
    content: 
      "Hello! 👋 Welcome to the **Smart City Civic Support & Grievance Assistant**.\n\n" +
      "I am your dedicated 24/7 Municipal Support Assistant (powered by **Google Gemini** & Grounded RAG). " +
      "I can help you lodge grievances, check live resolution timelines (SLAs), and connect directly with municipal departments.\n\n" +
      "What civic issue or municipal procedure would you like help with today?",
    sources: [],
    retrieved_chunks: [],
    confidence: 1.0,
    detected_category: null,
    suggested_actions: [
      {
        label: "⚡ Report Electricity Issue",
        action_type: "link",
        url: "/complaints?category=Electricity&text=Electricity+power+supply+issue",
        icon: "zap"
      },
      {
        label: "💧 Report Water Leakage",
        action_type: "link",
        url: "/complaints?category=Water+Supply&text=Water+pipeline+leakage+issue",
        icon: "droplet"
      },
      {
        label: "🛣️ Report Road Pothole",
        action_type: "link",
        url: "/complaints?category=Road/Pothole&text=Pothole+on+road",
        icon: "road"
      },
      {
        label: "📋 Track My Existing Grievances",
        action_type: "link",
        url: "/complaints/my",
        icon: "list"
      }
    ],
    quick_replies: [
      "I want to raise a complaint related to electricity",
      "How do I report a pothole on my street?",
      "What is the turnaround time for a water pipeline burst?",
      "How can I track my complaint status?"
    ],
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };

  const [messages, setMessages] = useState([initialGreeting]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedChunkId, setExpandedChunkId] = useState(null);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleCopy = (text, idx) => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    }
  };

  const handleResetChat = () => {
    setMessages([{
      ...initialGreeting,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
  };

  const handleSend = async (queryText = inputQuery) => {
    const q = (queryText || "").trim();
    if (!q || loading) return;

    const userMsg = {
      role: "user",
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInputQuery("");
    setLoading(true);

    try {
      // Build conversation history for multi-turn conversational context
      const history = newMessages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await fetchApi("/assistant/query", {
        method: "POST",
        body: JSON.stringify({ 
          question: q,
          conversation_history: history,
        }),
      });

      const assistantMsg = {
        role: "assistant",
        content: response.answer,
        sources: response.sources || [],
        retrieved_chunks: response.retrieved_chunks || [],
        confidence: response.confidence || 0.0,
        has_answer: response.has_answer,
        detected_category: response.detected_category,
        detected_department: response.detected_department,
        suggested_actions: response.suggested_actions || [],
        quick_replies: response.quick_replies || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Assistant Error: ${err.message || "Failed to process municipal inquiry."}`,
          sources: [],
          retrieved_chunks: [],
          confidence: 0.0,
          suggested_actions: [
            {
              label: "📝 Go to Complaint Portal",
              action_type: "link",
              url: "/complaints",
            },
            {
              label: "📞 Call Helpline (1800-233-0001)",
              action_type: "tel",
              url: "tel:18002330001",
            }
          ],
          quick_replies: [],
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
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-slate-500 font-medium">Verifying portal authentication...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-xl mx-auto my-12 p-8 bg-white border border-slate-200 rounded-3xl shadow-sm text-center space-y-6">
        <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto">
          <Bot className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Sign In to Use Municipal Assistant</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            The Conversational Civic Assistant is available to verified citizens and municipal staff.
            Please sign in to lodge complaints, track resolutions, and get personalized support.
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

  // Get quick replies from the latest assistant message
  const lastAssistantMsg = [...messages].reverse().find(m => m.role === "assistant");
  const activeQuickReplies = lastAssistantMsg?.quick_replies || [];

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">Smart City Civic Assistant</h1>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live 24/7 Support
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Interactive Grievance Redressal • Resolution SLAs • Direct Portal Actions
            </p>
          </div>
        </div>

        <button
          onClick={handleResetChat}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors border border-slate-200 shadow-sm"
          title="Reset conversation"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Main Chat Stream Container */}
      <div className="bg-slate-50/50 rounded-2xl border border-slate-200/80 shadow-sm p-4 sm:p-6 min-h-[480px] max-h-[620px] overflow-y-auto space-y-6">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-2xl rounded-2xl p-4 sm:p-5 text-sm leading-relaxed shadow-sm ${
                msg.role === "user"
                  ? "bg-blue-600 text-white rounded-br-sm"
                  : "bg-white text-slate-800 border border-slate-200/90 rounded-bl-sm space-y-4"
              }`}
            >
              {msg.role === "user" ? (
                <div className="whitespace-pre-wrap font-medium">{msg.content}</div>
              ) : (
                <div className="space-y-3">
                  {/* Category Pill Badge if detected */}
                  {msg.detected_category && (
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200/80 text-blue-700 text-[11px] font-semibold flex items-center gap-1">
                        <Zap className="w-3 h-3 text-blue-600" />
                        {msg.detected_category} Issue
                      </span>
                      {msg.detected_department && (
                        <span className="text-[11px] text-slate-500 font-medium">
                          Routed to {msg.detected_department}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Markdown Answer Content */}
                  <div className="text-slate-800 space-y-2 leading-relaxed text-sm">
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
                        ul: ({ children }) => <ul className="list-disc pl-5 space-y-1.5 my-2.5">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1.5 my-2.5">{children}</ol>,
                        li: ({ children }) => <li className="pl-1 text-slate-800">{children}</li>,
                        h1: ({ children }) => <h1 className="font-bold text-slate-900 text-lg mt-3 mb-1.5">{children}</h1>,
                        h2: ({ children }) => <h2 className="font-bold text-slate-900 text-base mt-3 mb-1.5">{children}</h2>,
                        h3: ({ children }) => <h3 className="font-semibold text-slate-900 text-sm mt-3 mb-1">{children}</h3>,
                        h4: ({ children }) => <h4 className="font-semibold text-slate-900 text-xs mt-2 mb-1">{children}</h4>,
                        code: ({ children }) => (
                          <code className="bg-slate-100 text-blue-800 px-1.5 py-0.5 rounded font-mono text-xs border border-slate-200">
                            {children}
                          </code>
                        ),
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-blue-500 bg-blue-50/60 p-2.5 rounded-r-xl italic text-slate-700 my-2">
                            {children}
                          </blockquote>
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  {/* Flipkart / Amazon Style Interactive Action Cards */}
                  {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 space-y-2">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                        Quick Support Actions:
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {msg.suggested_actions.map((act, actIdx) => (
                          act.action_type === "tel" ? (
                            <a
                              key={actIdx}
                              href={act.url}
                              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 font-semibold text-xs shadow-sm transition-all"
                            >
                              <PhoneCall className="w-3.5 h-3.5 text-amber-700" />
                              <span>{act.label}</span>
                            </a>
                          ) : (
                            <Link
                              key={actIdx}
                              href={act.url}
                              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-sm hover:shadow transition-all"
                            >
                              <span>{act.label}</span>
                              <ArrowRight className="w-3.5 h-3.5" />
                            </Link>
                          )
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Copy Answer Button */}
                  <div className="flex items-center justify-end pt-1">
                    <button
                      onClick={() => handleCopy(msg.content, idx)}
                      className="text-[11px] text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors"
                      title="Copy response"
                    >
                      {copiedIdx === idx ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-600" />
                          <span className="text-emerald-600 font-medium">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Audited Grounding Sources & Transparency Accordion */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                          <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                          Knowledge Base Sources ({msg.sources.length})
                        </span>
                        <span className="text-[10px] font-mono text-blue-700 font-semibold bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                          Match Score: {(msg.confidence * 100).toFixed(1)}%
                        </span>
                      </div>

                      <div className="space-y-1">
                        {msg.sources.map((src, sIdx) => (
                          <div
                            key={sIdx}
                            className="p-2 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs"
                          >
                            <div className="flex items-center gap-2">
                              <FileText className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
                              <div>
                                <span className="font-semibold text-slate-900 block text-xs">{src.title}</span>
                                <span className="text-[10px] text-slate-500">{src.department} • {src.category}</span>
                              </div>
                            </div>
                            <span className="px-1.5 py-0.5 rounded bg-white border border-slate-200 font-mono text-[10px] text-slate-600">
                              Score: {src.score}
                            </span>
                          </div>
                        ))}
                      </div>

                      {/* Expandable Chunk Inspector */}
                      {msg.retrieved_chunks && msg.retrieved_chunks.length > 0 && (
                        <div>
                          <button
                            onClick={() => setExpandedChunkId(expandedChunkId === idx ? null : idx)}
                            className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                          >
                            <span>{expandedChunkId === idx ? "Hide" : "Inspect"} Retrieved Knowledge Chunk</span>
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
              )}
            </div>

            <span className="text-[10px] text-slate-400 mt-1 px-1">
              {msg.role === "user" ? "Citizen" : "Municipal Support Bot"} • {msg.timestamp}
            </span>
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-2.5 text-xs text-slate-500 font-medium p-3.5 bg-white rounded-2xl border border-slate-200 shadow-sm w-fit animate-pulse">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mt-0.5" />
            <span>Finding relevant municipal procedures and preparing actions...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Follow-up Quick Reply Chips (Flipkart / Amazon style) */}
      {activeQuickReplies.length > 0 && !loading && (
        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block px-1">
            Suggested Follow-up Questions:
          </span>
          <div className="flex flex-wrap gap-2">
            {activeQuickReplies.map((reply, rIdx) => (
              <button
                key={rIdx}
                onClick={() => handleSend(reply)}
                className="px-3.5 py-1.5 rounded-full bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-slate-700 hover:text-blue-700 text-xs font-medium transition-all shadow-sm flex items-center gap-1.5"
              >
                <span>{reply}</span>
                <ArrowRight className="w-3 h-3 text-slate-400" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Query Input Bar */}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        className="flex items-center gap-2 bg-white p-2 rounded-2xl border border-slate-200 shadow-md focus-within:border-blue-400 transition-all"
      >
        <input
          type="text"
          placeholder="e.g., I want to raise a complaint related to electricity..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={loading}
          className="flex-grow px-4 py-2.5 text-sm focus:outline-none bg-transparent"
        />

        <button
          type="submit"
          disabled={loading || !inputQuery.trim()}
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs shadow flex items-center gap-1.5 transition-all"
        >
          <span>Send</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
