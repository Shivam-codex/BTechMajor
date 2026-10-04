"""
Dashboard Analytics API.
Aggregates municipal complaints by status, category, department, and priority for admin visualization.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.complaint import Complaint
from backend.app.models.user import User
from backend.app.api.deps import get_current_admin
from backend.app.schemas.dashboard_schema import (
    DashboardStatsResponse,
    CategoryDistribution,
    DepartmentDistribution,
    PriorityDistribution,
    StatusDistribution,
)
from backend.app.utils.constants import ComplaintStatus, ComplaintPriority

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get aggregated statistics and chart distributions for Admin Dashboard (Admin Only)",
)
def get_dashboard_stats(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Computes key performance indicators (KPIs) and distributions.
    STRICTLY RESTRICTED TO MUNICIPAL ADMINISTRATORS.
    """
    total = db.query(func.count(Complaint.id)).scalar() or 0

    submitted = db.query(func.count(Complaint.id)).filter(Complaint.status == ComplaintStatus.SUBMITTED.value).scalar() or 0
    in_progress = db.query(func.count(Complaint.id)).filter(Complaint.status == ComplaintStatus.IN_PROGRESS.value).scalar() or 0
    resolved = db.query(func.count(Complaint.id)).filter(Complaint.status == ComplaintStatus.RESOLVED.value).scalar() or 0
    needs_review = db.query(func.count(Complaint.id)).filter(Complaint.status == ComplaintStatus.NEEDS_REVIEW.value).scalar() or 0

    high_critical = db.query(func.count(Complaint.id)).filter(
        Complaint.priority.in_([ComplaintPriority.HIGH.value, ComplaintPriority.CRITICAL.value])
    ).scalar() or 0

    # Group by category
    cat_rows = (
        db.query(Complaint.category, func.count(Complaint.id))
        .group_by(Complaint.category)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    by_category = [
        CategoryDistribution(
            category=row[0],
            count=row[1],
            percentage=round((row[1] / total * 100), 1) if total > 0 else 0.0,
        )
        for row in cat_rows
    ]

    # Group by department
    dept_rows = (
        db.query(Complaint.department, func.count(Complaint.id))
        .group_by(Complaint.department)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    by_department = [DepartmentDistribution(department=row[0], count=row[1]) for row in dept_rows]

    # Group by priority
    priority_rows = (
        db.query(Complaint.priority, func.count(Complaint.id))
        .group_by(Complaint.priority)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    by_priority = [PriorityDistribution(priority=row[0], count=row[1]) for row in priority_rows]

    # Group by status
    status_rows = (
        db.query(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    by_status = [StatusDistribution(status=row[0], count=row[1]) for row in status_rows]

    return DashboardStatsResponse(
        total_complaints=total,
        submitted=submitted,
        in_progress=in_progress,
        resolved=resolved,
        needs_review=needs_review,
        high_critical_count=high_critical,
        by_category=by_category,
        by_department=by_department,
        by_priority=by_priority,
        by_status=by_status,
    )
