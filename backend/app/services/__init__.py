"""
Business logic services package.
"""

from app.services.question_service import (
    InvalidRequirementError,
    LLMGenerationError,
    QuestionService,
    QuestionServiceError,
    SyllabusMismatchError,
    distribute_marks,
    question_service,
)
from app.services.syllabus_service import (
    EmptyFileError,
    FileSizeLimitExceededError,
    InvalidPDFError,
    OCRRequiredError,
    SyllabusService,
    syllabus_service,
)

__all__ = [
    "SyllabusService",
    "syllabus_service",
    "EmptyFileError",
    "FileSizeLimitExceededError",
    "InvalidPDFError",
    "OCRRequiredError",
    "QuestionService",
    "question_service",
    "QuestionServiceError",
    "InvalidRequirementError",
    "SyllabusMismatchError",
    "LLMGenerationError",
    "distribute_marks",
]
