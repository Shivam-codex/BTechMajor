"""
Dashboard Analytics API.
Aggregates municipal complaints by status, category, department, and priority for admin visualization.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
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
    department: Optional[str] = Query(None, description="Filter stats by department (Super Admin only)"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Computes key performance indicators (KPIs) and distributions.
    STRICTLY RESTRICTED TO MUNICIPAL ADMINISTRATORS.
    Department Administrators are strictly isolated to their assigned department's data.
    """
    # Departmental Isolation Enforcement
    target_dept: Optional[str] = None
    if not current_user.is_super_admin and current_user.department:
        target_dept = current_user.department
    elif department:
        target_dept = department

    base_q = db.query(Complaint)
    if target_dept:
        base_q = base_q.filter(Complaint.department == target_dept)

    total = base_q.count()

    submitted = base_q.filter(Complaint.status == ComplaintStatus.SUBMITTED.value).count()
    in_progress = base_q.filter(Complaint.status == ComplaintStatus.IN_PROGRESS.value).count()
    resolved = base_q.filter(Complaint.status == ComplaintStatus.RESOLVED.value).count()
    needs_review = base_q.filter(Complaint.status == ComplaintStatus.NEEDS_REVIEW.value).count()

    high_critical = base_q.filter(
        Complaint.priority.in_([ComplaintPriority.HIGH.value, ComplaintPriority.CRITICAL.value])
    ).count()

    # Group by category
    cat_q = db.query(Complaint.category, func.count(Complaint.id))
    if target_dept:
        cat_q = cat_q.filter(Complaint.department == target_dept)
    cat_rows = (
        cat_q.group_by(Complaint.category)
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
    dept_q = db.query(Complaint.department, func.count(Complaint.id))
    if target_dept:
        dept_q = dept_q.filter(Complaint.department == target_dept)
    dept_rows = (
        dept_q.group_by(Complaint.department)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    by_department = [DepartmentDistribution(department=row[0], count=row[1]) for row in dept_rows]

    # Group by priority
    prio_q = db.query(Complaint.priority, func.count(Complaint.id))
    if target_dept:
        prio_q = prio_q.filter(Complaint.department == target_dept)
    priority_rows = (
        prio_q.group_by(Complaint.priority)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    by_priority = [PriorityDistribution(priority=row[0], count=row[1]) for row in priority_rows]

    # Group by status
    status_q = db.query(Complaint.status, func.count(Complaint.id))
    if target_dept:
        status_q = status_q.filter(Complaint.department == target_dept)
    status_rows = (
        status_q.group_by(Complaint.status)
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
