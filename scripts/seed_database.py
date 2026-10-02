"""
Database Seeding Script.
Populates SQLite with realistic municipal complaints from sample_complaints.csv.
Distributes complaints across realistic statuses, timestamps, and citizen profiles
so the Admin Dashboard is rich and immediately demonstratable.
"""

import sys
import csv
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.core.database import SessionLocal, init_db
from backend.app.models.complaint import Complaint
from backend.app.services.nlp.preprocessing import preprocess_complaint
from backend.app.services.classification.classifier import classify_complaint
from backend.app.services.classification.department_router import assign_department
from backend.app.services.classification.priority_detector import detect_priority
from backend.app.utils.constants import ComplaintStatus, SourceType

CITIZEN_NAMES = [
    "Rajesh Patil", "Sunita Deshmukh", "Vikram Shinde", "Pooja Kulkarni",
    "Aarav Sharma", "Ananya Joshi", "Ramesh Gaikwad", "Sneha Kadam",
    "Suresh More", "Priya Nair", "Nitin Jadhav", "Meena Pawar",
    "Amitabh Sawant", "Deepika Bhosale", "Ganesh Thorat", "Kavita Chavan",
]

RESOLVED_NOTES = [
    "Site inspection conducted. Cold mix asphalt patchwork completed on the potholes.",
    "Pipeline breach isolated and joint welded. Regular water supply restored.",
    "Sanitation crew deployed. Waste accumulation cleared and disinfectant sprayed.",
    "Defective LED choke replaced on street light fixture SL-44. Illumination verified.",
    "Suction-cum-jetting vehicle cleared underground sewer choke. Drain line free flowing.",
    "Public restroom deep cleaned and plumbing hardware repaired.",
    "Transformer neutral fault rectified and overhead phase wire secured.",
    "Traffic wardens posted and illegal parking bottlenecks towed.",
]


def seed_database(limit: int = 400):
    print("=" * 70)
    print("  Smart City Complaint Management System — Database Seeder")
    print("=" * 70)

    init_db()
    db = SessionLocal()

    csv_path = root_dir / "data" / "complaints" / "sample_complaints.csv"
    if not csv_path.exists():
        print(f"ERROR: Dataset file not found at {csv_path}")
        return

    # Check if complaints table already has data
    existing_count = db.query(Complaint).count()
    if existing_count > 50:
        print(f"Database already contains {existing_count} complaints. Clearing existing records for clean seed...")
        db.query(Complaint).delete()
        db.commit()

    print(f"\n[1/3] Reading complaints from {csv_path.name}...")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    random.shuffle(rows)
    selected_rows = rows[:limit]
    print(f"      Seeding {len(selected_rows)} realistic grievances into SQLite...")

    now = datetime.now(timezone.utc)
    seeded_count = 0

    print("\n[2/3] Processing grievances through deterministic pipeline...")
    for idx, row in enumerate(selected_rows, start=1):
        raw_text = row["complaint_text"]
        lang = row.get("language", "en")

        # Run through NLP & deterministic classification
        nlp_res = preprocess_complaint(raw_text)
        classification = classify_complaint(nlp_res)
        department, _ = assign_department(classification.category)
        priority_res = detect_priority(nlp_res)

        # Distribute status: 40% Resolved, 30% In Progress, 20% Submitted, 10% Needs Review
        status_roll = random.random()
        if classification.status == ComplaintStatus.NEEDS_REVIEW.value or status_roll < 0.10:
            assigned_status = ComplaintStatus.NEEDS_REVIEW.value
        elif status_roll < 0.30:
            assigned_status = ComplaintStatus.SUBMITTED.value
        elif status_roll < 0.60:
            assigned_status = ComplaintStatus.IN_PROGRESS.value
        else:
            assigned_status = ComplaintStatus.RESOLVED.value

        # Timestamps across the past 30 days
        days_ago = random.randint(1, 30)
        created_time = now - timedelta(days=days_ago, hours=random.randint(1, 23), minutes=random.randint(1, 59))
        assigned_time = created_time + timedelta(hours=random.randint(2, 12)) if assigned_status in [ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.RESOLVED.value] else None
        resolved_time = assigned_time + timedelta(hours=random.randint(6, 48)) if assigned_status == ComplaintStatus.RESOLVED.value and assigned_time else None

        resolution_notes = random.choice(RESOLVED_NOTES) if assigned_status == ComplaintStatus.RESOLVED.value else None
        citizen_name = random.choice(CITIZEN_NAMES)

        # Vary source types: 70% MANUAL, 15% PDF, 10% DOCX, 5% TXT
        src_roll = random.random()
        if src_roll < 0.70:
            src_type = SourceType.MANUAL.value
            src_file = None
        elif src_roll < 0.85:
            src_type = SourceType.PDF.value
            src_file = f"grievance_letter_{idx}.pdf"
        elif src_roll < 0.95:
            src_type = SourceType.DOCX.value
            src_file = f"grievance_form_{idx}.docx"
        else:
            src_type = SourceType.TXT.value
            src_file = f"complaint_notice_{idx}.txt"

        complaint = Complaint(
            id=f"CMP-2026-{idx:05d}",
            complaint_text=raw_text,
            extracted_text=raw_text if src_file else None,
            source_file_name=src_file,
            source_type=src_type,
            language=nlp_res.language,
            category=classification.category,
            rule_match_score=classification.rule_match_score,
            matched_keywords=classification.matched_keywords,
            matched_phrases=classification.matched_phrases,
            classification_reason=classification.reason,
            department=department,
            priority=priority_res.priority,
            priority_reason=priority_res.priority_reason,
            status=assigned_status,
            citizen_name=citizen_name,
            location=row.get("keywords", "Central Ward"),
            resolution_notes=resolution_notes,
            created_at=created_time,
            updated_at=now,
            assigned_at=assigned_time,
            resolved_at=resolved_time,
        )
        db.add(complaint)
        seeded_count += 1

    db.commit()
    db.close()

    print(f"\n[3/3] Successfully seeded {seeded_count} complaints into SQLite.")
    print("=" * 70)
    print("  Database Seeding Completed! Admin Dashboard is now fully populated.")
    print("=" * 70)


if __name__ == "__main__":
    seed_database()
