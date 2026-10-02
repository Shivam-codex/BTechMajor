import { Shield, Sparkles, Code2 } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 text-sm mt-20 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 text-white font-bold text-base mb-2">
              <Shield className="w-5 h-5 text-blue-400" />
              <span>Smart City Complaint Management System</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              A comprehensive final-year engineering major project demonstrating local, 
              explainable civic governance automation through deterministic Natural Language Processing 
              and classical Information Retrieval.
            </p>
          </div>

          <div>
            <h4 className="text-white text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Zero-ML Architecture
            </h4>
            <ul className="text-xs space-y-1.5 text-slate-400">
              <li>• Rule-based weighted complaint classification (9 Categories)</li>
              <li>• Automatic department routing & priority triage</li>
              <li>• Classical TF-IDF & BM25 municipal retrieval assistant</li>
              <li>• Zero external APIs, zero paid services, 100% locally hosted</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Code2 className="w-4 h-4 text-emerald-400" />
              Tech Stack
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              FastAPI • SQLAlchemy 2.0 • SQLite • Next.js • React • Tailwind CSS • Python-docx • Pdfplumber • Scikit-learn (TF-IDF & Cosine Similarity utilities only).
            </p>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <p>© 2026 Academic Final-Year Major Project. All civic procedures based on Sample Municipal Knowledge Base.</p>
          <p className="mt-2 sm:mt-0 font-mono text-[11px] text-blue-400">Status: Operational & Validated</p>
        </div>
      </div>
    </footer>
  );
}
