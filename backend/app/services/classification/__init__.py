"""
Rule-Based Classification and Routing Engine.
Deterministic, non-ML grievance categorization, priority detection, and department routing.
"""

from backend.app.services.classification.classifier import classify_complaint, ClassificationResult
from backend.app.services.classification.department_router import assign_department
from backend.app.services.classification.priority_detector import detect_priority, PriorityResult

__all__ = [
    "classify_complaint",
    "ClassificationResult",
    "assign_department",
    "detect_priority",
    "PriorityResult",
]
