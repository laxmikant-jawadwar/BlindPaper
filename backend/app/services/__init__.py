"""
Business logic services package.
"""

from app.services.syllabus_service import (
    SyllabusService,
    syllabus_service,
    EmptyFileError,
    FileSizeLimitExceededError,
    InvalidPDFError,
    OCRRequiredError,
)

__all__ = [
    "SyllabusService",
    "syllabus_service",
    "EmptyFileError",
    "FileSizeLimitExceededError",
    "InvalidPDFError",
    "OCRRequiredError",
]
