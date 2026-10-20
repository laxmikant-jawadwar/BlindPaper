"""Values shared by the API: departments, roles and paper statuses."""

DEPARTMENTS = [
    "Computer Science",
    "Mechanical",
    "Civil",
    "Electrical",
    "Electronics",
    "Information Technology",
]

ROLE_ADMIN = "admin"
ROLE_FACULTY = "faculty"

STATUS_DRAFT = "Draft"
STATUS_PENDING = "Pending Approval"
STATUS_APPROVED = "Approved"
STATUS_REJECTED = "Rejected"

# Statuses an admin can see: a Draft has not been submitted yet
SUBMITTED_STATUSES = [STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED]
