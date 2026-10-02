"use client";

import { useEffect, useState } from "react";
import { 
  BookOpen, 
  Search, 
  Building2, 
  FileText, 
  X, 
  ExternalLink,
  Layers,
  ShieldCheck,
  Tag
} from "lucide-react";
import { fetchApi } from "../../utils/api";

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  // Modal inspection state
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [docDetail, setDocDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    async function loadDocuments() {
      try {
        const data = await fetchApi("/knowledge-base/documents");
        setDocuments(data || []);
      } catch (err) {
        console.error("Failed to load knowledge documents:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDocuments();
  }, []);

  const openDocumentModal = async (docId) => {
    setSelectedDocId(docId);
    setLoadingDetail(true);
    try {
      const detail = await fetchApi(`/knowledge-base/documents/${docId}`);
      setDocDetail(detail);
    } catch (err) {
      alert(`Failed to load document: ${err.message}`);
    } finally {
      setLoadingDetail(false);
    }
  };

  const closeModal = () => {
    setSelectedDocId(null);
    setDocDetail(null);
  };

  const filteredDocs = documents.filter((d) => {
    const matchesSearch =
      d.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter ? d.category === categoryFilter : true;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-1 border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
          <BookOpen className="w-6 h-6 text-blue-600" />
          <span>Municipal Knowledge Base Repository</span>
        </h1>
        <p className="text-xs text-slate-500">
          Official academic procedures, Service Level Agreements (SLAs), and operational guidelines 
          indexed for non-ML lexical retrieval.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
        <div className="relative flex-grow">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search procedures, categories, or department responsibilities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 rounded-xl border border-slate-300 text-xs bg-slate-50 text-slate-700 font-medium"
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
          <option value="Other">Other (General Grievance)</option>
        </select>
      </div>

      {/* Documents Grid */}
      {loading ? (
        <div className="text-center py-20">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-slate-500">Loading municipal repository documents...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocs.map((doc) => (
            <div
              key={doc.document_id}
              className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold bg-slate-100 text-slate-700">
                    {doc.document_id}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600">
                    <Layers className="w-3 h-3" />
                    <span>{doc.chunk_count} Chunks</span>
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 leading-snug">{doc.title}</h3>
                <p className="text-xs text-slate-500">{doc.department}</p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px] font-semibold">
                  {doc.category}
                </span>

                <button
                  onClick={() => openDocumentModal(doc.document_id)}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                >
                  <span>Inspect Chunks</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Document Detail Modal */}
      {selectedDocId && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-200 flex items-start justify-between bg-slate-50">
              <div>
                <span className="font-mono text-xs font-bold text-blue-600 uppercase">{selectedDocId}</span>
                <h2 className="text-lg font-bold text-slate-900 mt-0.5">
                  {docDetail ? docDetail.title : "Loading document..."}
                </h2>
                {docDetail && (
                  <p className="text-xs text-slate-500 mt-0.5">
                    {docDetail.department} • {docDetail.category} • {docDetail.chunk_count} Indexed Chunks
                  </p>
                )}
              </div>

              <button
                onClick={closeModal}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-grow">
              {loadingDetail ? (
                <div className="text-center py-10">
                  <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-xs text-slate-500">Retrieving document chunks...</p>
                </div>
              ) : (
                docDetail && (
                  <div className="space-y-4">
                    <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-100 text-xs text-slate-600">
                      <strong>Source Attribution:</strong> {docDetail.source}
                    </div>

                    <div className="space-y-3">
                      {docDetail.chunks.map((chunk, idx) => (
                        <div key={chunk.chunk_id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500">
                            <span className="font-mono text-blue-600">{chunk.chunk_id}</span>
                            <span>{chunk.word_count} words</span>
                          </div>
                          <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-wrap font-sans">
                            {chunk.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 text-right">
              <button
                onClick={closeModal}
                className="px-4 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
