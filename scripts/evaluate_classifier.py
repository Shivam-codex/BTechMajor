"""
Academic Classifier Evaluation Script.
Evaluates the deterministic rule-based complaint classifier against the held-out
test dataset (data/complaints/test_complaints.csv).
Computes exact mathematical metrics:
- Overall Accuracy
- Precision, Recall, F1-Score per category
- Macro & Weighted Averages
- Priority Detection Accuracy
- Confusion Matrix
- Analysis of Misclassifications and Edge Cases
Generates formal academic report: reports/classification_evaluation.md
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.services.nlp.preprocessing import preprocess_complaint
from backend.app.services.classification.classifier import classify_complaint
from backend.app.services.classification.priority_detector import detect_priority
from backend.app.utils.constants import ComplaintCategory

REPORTS_DIR = root_dir / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate():
    print("=" * 75)
    print("  Evaluating Deterministic Rule-Based Classifier (Non-ML)")
    print("=" * 75)

    test_csv = root_dir / "data" / "complaints" / "test_complaints.csv"
    if not test_csv.exists():
        print(f"ERROR: Test complaints file not found at {test_csv}")
        return

    with open(test_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    total_samples = len(records)
    print(f"Loaded {total_samples} held-out evaluation samples.\n")

    all_categories = [cat.value for cat in ComplaintCategory]

    # Metrics storage
    correct_category = 0
    correct_priority = 0
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    cat_tp = defaultdict(int)
    cat_fp = defaultdict(int)
    cat_fn = defaultdict(int)
    cat_support = defaultdict(int)

    misclassifications = []

    for item in records:
        text = item["complaint_text"]
        true_cat = item["category"]
        true_priority = item["priority"]

        nlp_res = preprocess_complaint(text)
        class_res = classify_complaint(nlp_res)
        priority_res = detect_priority(nlp_res)

        pred_cat = class_res.category
        pred_priority = priority_res.priority

        cat_support[true_cat] += 1
        confusion_matrix[true_cat][pred_cat] += 1

        if pred_cat == true_cat:
            correct_category += 1
            cat_tp[true_cat] += 1
        else:
            cat_fp[pred_cat] += 1
            cat_fn[true_cat] += 1
            misclassifications.append({
                "id": item["id"],
                "text": text,
                "true_category": true_cat,
                "pred_category": pred_cat,
                "rule_match_score": class_res.rule_match_score,
                "reason": class_res.reason,
            })

        if pred_priority == true_priority:
            correct_priority += 1

    overall_accuracy = correct_category / total_samples if total_samples > 0 else 0.0
    priority_accuracy = correct_priority / total_samples if total_samples > 0 else 0.0

    # Calculate per-category precision, recall, f1
    cat_metrics = {}
    macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
    active_cats = [c for c in all_categories if cat_support[c] > 0]

    for cat in all_categories:
        tp = cat_tp[cat]
        fp = cat_fp[cat]
        fn = cat_fn[cat]
        support = cat_support[cat]

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        cat_metrics[cat] = {
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "support": support,
        }

    for c in active_cats:
        macro_p += cat_metrics[c]["precision"]
        macro_r += cat_metrics[c]["recall"]
        macro_f1 += cat_metrics[c]["f1"]

    num_active = len(active_cats)
    macro_p /= num_active
    macro_r /= num_active
    macro_f1 /= num_active

    print(f"Overall Classification Accuracy: {overall_accuracy * 100:.2f}%")
    print(f"Priority Detection Accuracy:    {priority_accuracy * 100:.2f}%")
    print(f"Macro Average F1-Score:          {macro_f1 * 100:.2f}%\n")

    # Generate Markdown Report
    report_file = REPORTS_DIR / "classification_evaluation.md"
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write("# Academic Research Report: Deterministic Rule-Based Complaint Classification Evaluation\n\n")
        rf.write("**Project Title:** AI-Based Smart City Complaint Management System  \n")
        rf.write("**Evaluation Type:** Non-ML Deterministic Lexical & Rule Match Evaluation  \n")
        rf.write(f"**Test Set Size:** {total_samples} held-out municipal grievances  \n")
        rf.write("**Languages Evaluated:** English, Marathi (Devanagari), and Code-mixed Marathi-English  \n\n")

        rf.write("## 1. Executive Summary & Key Results\n\n")
        rf.write(f"- **Overall Categorization Accuracy:** **{overall_accuracy * 100:.2f}%**\n")
        rf.write(f"- **Macro Average Precision:** **{macro_p * 100:.2f}%**\n")
        rf.write(f"- **Macro Average Recall:** **{macro_r * 100:.2f}%**\n")
        rf.write(f"- **Macro Average F1-Score:** **{macro_f1 * 100:.2f}%**\n")
        rf.write(f"- **Priority Detection Accuracy:** **{priority_accuracy * 100:.2f}%**\n\n")

        rf.write("## 2. Category-Wise Performance Breakdown\n\n")
        rf.write("| Category | Precision | Recall | F1-Score | Test Support |\n")
        rf.write("|:---|:---:|:---:|:---:|:---:|\n")
        for cat in all_categories:
            m = cat_metrics[cat]
            rf.write(f"| {cat} | {m['precision']*100:.1f}% | {m['recall']*100:.1f}% | {m['f1']*100:.1f}% | {m['support']} |\n")

        rf.write(f"| **Macro Average** | **{macro_p*100:.1f}%** | **{macro_r*100:.1f}%** | **{macro_f1*100:.1f}%** | **{total_samples}** |\n\n")

        rf.write("## 3. Confusion Matrix\n\n")
        rf.write("Rows represent Ground Truth, Columns represent Deterministic Rule Predictions:\n\n")
        header_row = "| Actual \\ Predicted | " + " | ".join(all_categories) + " |"
        sep_row = "|:---|" + "|".join([":---:"] * len(all_categories)) + "|"
        rf.write(header_row + "\n" + sep_row + "\n")
        for actual in all_categories:
            cells = [str(confusion_matrix[actual][pred]) for pred in all_categories]
            rf.write(f"| **{actual}** | " + " | ".join(cells) + " |\n")

        rf.write("\n## 4. Error Analysis and Edge Cases\n\n")
        if misclassifications:
            rf.write(f"Identified {len(misclassifications)} misclassified grievances on the held-out set:\n\n")
            for idx, err in enumerate(misclassifications[:5], 1):
                rf.write(f"### Case {idx}: ID `{err['id']}`\n")
                rf.write(f"- **Grievance Text:** *\"{err['text']}\"*\n")
                rf.write(f"- **Ground Truth:** `{err['true_category']}`\n")
                rf.write(f"- **Rule Prediction:** `{err['pred_category']}` (Rule Match Score: {err['rule_match_score']})\n")
                rf.write(f"- **Rule Reason:** {err['reason']}\n\n")
        else:
            rf.write("Zero misclassifications observed on the held-out test set.\n\n")

        rf.write("## 5. Methodology & Non-ML Justification\n\n")
        rf.write(
            "1. **Deterministic Processing:** Tokenization, Unicode canonical normalization, and lemmatization without black-box neural networks.\n"
            "2. **Weighted Dictionaries:** Exact phrase matching (5.0 pts), primary keywords (3.0 pts), synonyms (2.0 pts), context (1.0 pt), negative suppressions (-4.0 pts).\n"
            "3. **Zero Probabilistic Hallucination:** Every classification outputs an exact, auditable chain of triggered phrases and vocabulary tokens.\n"
        )

    print(f"Academic evaluation report written to {report_file}")
    print("=" * 75)


if __name__ == "__main__":
    evaluate()
