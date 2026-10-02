"""
Pydantic schemas for the Admin Dashboard statistics and analytics.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict


class CategoryDistribution(BaseModel):
    category: str
    count: int
    percentage: float


class DepartmentDistribution(BaseModel):
    department: str
    count: int


class PriorityDistribution(BaseModel):
    priority: str
    count: int


class StatusDistribution(BaseModel):
    status: str
    count: int


class DashboardStatsResponse(BaseModel):
    total_complaints: int
    submitted: int
    in_progress: int
    resolved: int
    needs_review: int
    high_critical_count: int
    by_category: List[CategoryDistribution]
    by_department: List[DepartmentDistribution]
    by_priority: List[PriorityDistribution]
    by_status: List[StatusDistribution]

    model_config = ConfigDict(from_attributes=True)
