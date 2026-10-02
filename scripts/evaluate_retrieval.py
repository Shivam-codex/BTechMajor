"""
Classical Information Retrieval Evaluation Script.
Evaluates the Non-ML TF-IDF / BM25 retriever against data/rag/rag_questions.json.
Calculates standard academic Information Retrieval metrics:
- Recall@1, Recall@3, Recall@5
- Precision@1, Precision@3
- Mean Reciprocal Rank (MRR)
Generates formal academic report: reports/retrieval_evaluation.md
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.services.retrieval.ranking import retrieve_relevant_chunks

REPORTS_DIR = root_dir / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_retrieval():
    print("=" * 75)
    print("  Evaluating Classical Information Retrieval Engine (Non-ML TF-IDF)")
    print("=" * 75)

    rag_file = root_dir / "data" / "rag" / "rag_questions.json"
    if not rag_file.exists():
        print(f"ERROR: RAG evaluation questions not found at {rag_file}")
        return

    with open(rag_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total_queries = len(questions)
    print(f"Loaded {total_queries} ground-truth retrieval evaluation queries.\n")

    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    precision_at_1_sum = 0.0
    precision_at_3_sum = 0.0
    reciprocal_ranks = []

    query_details = []

    for item in questions:
        query = item["question"]
        expected_docs = [d.lower() for d in item["expected_documents"]]

        # Retrieve top 5 chunks
        results = retrieve_relevant_chunks(query, top_k=5, threshold=0.05)
        retrieved_titles = [r.title.lower() for r in results]

        # Calculate Rank of First Hit
        first_rank = 0
        for rank, title in enumerate(retrieved_titles, start=1):
            if any(exp in title or title in exp for exp in expected_docs):
                first_rank = rank
                break

        if first_rank > 0:
            reciprocal_ranks.append(1.0 / first_rank)
        else:
            reciprocal_ranks.append(0.0)

        # Hits at K
        if first_rank == 1:
            hits_at_1 += 1
        if 1 <= first_rank <= 3:
            hits_at_3 += 1
        if 1 <= first_rank <= 5:
            hits_at_5 += 1

        # Precision at K
        p1_matches = sum(1 for t in retrieved_titles[:1] if any(exp in t or t in exp for exp in expected_docs))
        precision_at_1_sum += (p1_matches / 1.0)

        p3_count = min(3, len(retrieved_titles))
        p3_matches = sum(1 for t in retrieved_titles[:3] if any(exp in t or t in exp for exp in expected_docs))
        precision_at_3_sum += (p3_matches / 3.0) if p3_count > 0 else 0.0

        query_details.append({
            "question": query,
            "expected": item["expected_documents"],
            "retrieved_top_3": [r.title for r in results[:3]],
            "first_rank": first_rank,
            "top_score": results[0].score if results else 0.0,
        })

    recall_at_1 = hits_at_1 / total_queries
    recall_at_3 = hits_at_3 / total_queries
    recall_at_5 = hits_at_5 / total_queries
    prec_at_1 = precision_at_1_sum / total_queries
    prec_at_3 = precision_at_3_sum / total_queries
    mrr = sum(reciprocal_ranks) / total_queries

    print(f"Recall@1:       {recall_at_1 * 100:.2f}%")
    print(f"Recall@3:       {recall_at_3 * 100:.2f}%")
    print(f"Recall@5:       {recall_at_5 * 100:.2f}%")
    print(f"Precision@1:    {prec_at_1 * 100:.2f}%")
    print(f"Precision@3:    {prec_at_3 * 100:.2f}%")
    print(f"MRR (Mean RR):  {mrr:.4f}\n")

    # Generate Markdown Report
    report_file = REPORTS_DIR / "retrieval_evaluation.md"
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write("# Academic Research Report: Classical Information Retrieval Evaluation\n\n")
        rf.write("**Project Title:** AI-Based Smart City Complaint Management System  \n")
        rf.write("**Retrieval Architecture:** Non-ML TF-IDF with Sublinear Term Frequency & Cosine Similarity  \n")
        rf.write(f"**Evaluation Queries:** {total_queries} citizen questions mapped to ground-truth municipal documents  \n")
        rf.write("**Document Repository:** 14 structured academic municipal procedure documents (74 indexed chunks)  \n\n")

        rf.write("## 1. Classical Information Retrieval Performance Summary\n\n")
        rf.write("| Metric | Score | Percentage |\n")
        rf.write("|:---|:---:|:---:|\n")
        rf.write(f"| **Recall@1** | {recall_at_1:.4f} | **{recall_at_1*100:.1f}%** |\n")
        rf.write(f"| **Recall@3** | {recall_at_3:.4f} | **{recall_at_3*100:.1f}%** |\n")
        rf.write(f"| **Recall@5** | {recall_at_5:.4f} | **{recall_at_5*100:.1f}%** |\n")
        rf.write(f"| **Precision@1** | {prec_at_1:.4f} | **{prec_at_1*100:.1f}%** |\n")
        rf.write(f"| **Precision@3** | {prec_at_3:.4f} | **{prec_at_3*100:.1f}%** |\n")
        rf.write(f"| **Mean Reciprocal Rank (MRR)** | **{mrr:.4f}** | — |\n\n")

        rf.write("## 2. Methodology & Scientific Justification\n\n")
        rf.write(
            "1. **Non-ML Lexical Foundation:** Avoids dense vector embeddings, vector databases (FAISS/Chroma), "
            "and generative language models. Operates entirely via deterministically computed n-gram TF-IDF matrices.\n"
            "2. **Explainability & Verification:** Every retrieved candidate preserves explicit similarity scores and source attributions.\n"
            "3. **Query Term Coverage Filtering:** Multi-word queries are verified for lexical token overlap to eliminate spurious single-token matches.\n\n"
        )

        rf.write("## 3. Query-Level Audit Log (Sample 10 Queries)\n\n")
        rf.write("| Query | Expected Ground Truth | Top-1 Retrieved Document | Top-1 Score | Rank Hit |\n")
        rf.write("|:---|:---|:---|:---:|:---:|\n")
        for q in query_details[:10]:
            top_ret = q["retrieved_top_3"][0] if q["retrieved_top_3"] else "None"
            exp_str = ", ".join(q["expected"][:1])
            rf.write(f"| {q['question']} | {exp_str} | {top_ret} | {q['top_score']:.3f} | Rank {q['first_rank']} |\n")

    print(f"Academic retrieval evaluation report written to {report_file}")
    print("=" * 75)


if __name__ == "__main__":
    evaluate_retrieval()
