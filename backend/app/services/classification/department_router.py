"""
Automatic Department Assignment Router.
Deterministically routes categorized municipal grievances to corresponding municipal bodies.
"""

from typing import Tuple
from backend.app.utils.constants import CATEGORY_DEPARTMENT_MAPPING, DepartmentName


def assign_department(category: str) -> Tuple[str, str]:
    """
    Deterministically maps a grievance category to the designated municipal department.
    Returns: (department_name, routing_reason)
    """
    department = CATEGORY_DEPARTMENT_MAPPING.get(category, DepartmentName.GENERAL_GRIEVANCE.value)
    reason = f"Automatically routed to {department} based on verified {category} category rules."
    return department, reason
