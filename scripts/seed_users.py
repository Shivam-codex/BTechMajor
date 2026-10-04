"""
Database Seeder for Municipal Administrators and Sample Citizens.
Creates default accounts with securely hashed passwords for local authentication.
"""

import sys
from pathlib import Path

# Add project root to sys.path
_current = Path(__file__).resolve().parent.parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

from backend.app.core.database import SessionLocal, init_db
from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.models.complaint import Complaint


def seed_default_users():
    """Initializes standard administrative and citizen test accounts."""
    init_db()
    db = SessionLocal()

    default_users = [
        {
            "full_name": "Municipal System Administrator",
            "email": "admin@smartcity.gov",
            "password": "Admin@12345",
            "phone": "+91 20 2550 1000",
            "role": "ADMIN",
            "department": "General Grievance Cell",
        },
        {
            "full_name": "Water Department Officer",
            "email": "water.admin@smartcity.gov",
            "password": "Admin@12345",
            "phone": "+91 20 2550 1100",
            "role": "ADMIN",
            "department": "Water Supply Department",
        },
        {
            "full_name": "Ramesh Sharma",
            "email": "citizen@example.com",
            "password": "Citizen@12345",
            "phone": "+91 98765 43210",
            "role": "CITIZEN",
            "department": None,
        },
    ]

    print("--- Seeding Users into Smart City Database ---")
    created_count = 0
    citizen_user = None

    for udata in default_users:
        existing = db.query(User).filter(User.email == udata["email"]).first()
        if not existing:
            user = User(
                full_name=udata["full_name"],
                email=udata["email"],
                phone=udata["phone"],
                hashed_password=hash_password(udata["password"]),
                role=udata["role"],
                department=udata["department"],
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[+] Created user: {user.email} (Role: {user.role}, Dept: {user.department or 'N/A'})")
            created_count += 1
            if user.role == "CITIZEN":
                citizen_user = user
        else:
            print(f"[*] User already exists: {existing.email} (Role: {existing.role})")
            if existing.role == "CITIZEN":
                citizen_user = existing

    # Assign a subset of existing complaints to the sample citizen for demonstration
    if citizen_user:
        unassigned_complaints = db.query(Complaint).filter(Complaint.user_id == None).limit(8).all()
        for cmp in unassigned_complaints:
            cmp.user_id = citizen_user.id
            cmp.citizen_name = citizen_user.full_name
        if unassigned_complaints:
            db.commit()
            print(f"[+] Assigned {len(unassigned_complaints)} complaints to citizen {citizen_user.email}")

    db.close()
    print("--- User Seeding Completed Successfully ---")


if __name__ == "__main__":
    seed_default_users()
