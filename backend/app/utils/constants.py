"""
Application constants for the Smart City Complaint Management System.
All categories, departments, priorities, and statuses are defined deterministically here.
"""

from enum import Enum


class ComplaintCategory(str, Enum):
    WATER_SUPPLY = "Water Supply"
    GARBAGE_WASTE = "Garbage/Waste Management"
    ROAD_POTHOLE = "Road/Pothole"
    STREET_LIGHT = "Street Light"
    DRAINAGE_SEWERAGE = "Drainage/Sewerage"
    PUBLIC_TOILET = "Public Toilet"
    ELECTRICITY = "Electricity"
    TRAFFIC = "Traffic"
    OTHER = "Other"


class DepartmentName(str, Enum):
    WATER_SUPPLY = "Water Supply Department"
    SANITATION = "Sanitation Department"
    ROADS_INFRASTRUCTURE = "Roads and Infrastructure Department"
    ELECTRICAL = "Electrical Department"
    DRAINAGE = "Drainage Department"
    PUBLIC_HEALTH = "Public Health and Sanitation Department"
    TRAFFIC = "Traffic Management Department"
    GENERAL_GRIEVANCE = "General Grievance Cell"


class ComplaintPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ComplaintStatus(str, Enum):
    SUBMITTED = "Submitted"
    CLASSIFIED = "Classified"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"
    NEEDS_REVIEW = "Needs Review"


class SourceType(str, Enum):
    MANUAL = "MANUAL"
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"


# Category to Department deterministic mapping
CATEGORY_DEPARTMENT_MAPPING = {
    ComplaintCategory.WATER_SUPPLY.value: DepartmentName.WATER_SUPPLY.value,
    ComplaintCategory.GARBAGE_WASTE.value: DepartmentName.SANITATION.value,
    ComplaintCategory.ROAD_POTHOLE.value: DepartmentName.ROADS_INFRASTRUCTURE.value,
    ComplaintCategory.STREET_LIGHT.value: DepartmentName.ELECTRICAL.value,
    ComplaintCategory.DRAINAGE_SEWERAGE.value: DepartmentName.DRAINAGE.value,
    ComplaintCategory.PUBLIC_TOILET.value: DepartmentName.PUBLIC_HEALTH.value,
    ComplaintCategory.ELECTRICITY.value: DepartmentName.ELECTRICAL.value,
    ComplaintCategory.TRAFFIC.value: DepartmentName.TRAFFIC.value,
    ComplaintCategory.OTHER.value: DepartmentName.GENERAL_GRIEVANCE.value,
}

# File Upload Configuration
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
