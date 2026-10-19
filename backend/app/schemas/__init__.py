"""Pydantic schemas for request and response data validation."""
from app.schemas.health import HealthResponse, WelcomeResponse
from app.schemas.question import (
    QuestionGenerateRequest,
    QuestionGenerateResponse,
    QuestionItem,
)
from app.schemas.syllabus import SyllabusExtractResponse
from app.schemas.validation import (
    DuplicatePair,
    MarksValidationResult,
    QuestionRelevance,
    UnitCoverageResult,
    ValidationRequest,
    ValidationResponse,
)

__all__ = [
    "HealthResponse",
    "WelcomeResponse",
    "SyllabusExtractResponse",
    "QuestionItem",
    "QuestionGenerateRequest",
    "QuestionGenerateResponse",
    "QuestionRelevance",
    "DuplicatePair",
    "MarksValidationResult",
    "UnitCoverageResult",
    "ValidationRequest",
    "ValidationResponse",
]
