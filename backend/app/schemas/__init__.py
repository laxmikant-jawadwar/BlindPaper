"""Pydantic schemas for request and response data validation."""
from app.schemas.health import HealthResponse, WelcomeResponse
from app.schemas.syllabus import SyllabusExtractResponse

__all__ = ["HealthResponse", "WelcomeResponse", "SyllabusExtractResponse"]
