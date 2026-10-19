"""
API endpoints for examination question paper validation and quality assurance.
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.validation import ValidationRequest, ValidationResponse
from app.services.validation_service import validation_service

router = APIRouter(prefix="/api/questions", tags=["Validation"])


@router.post(
    "/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate question paper against syllabus and examination rules",
    description="Analyzes questions for syllabus relevance, duplicate content, marks/count consistency, and unit coverage.",
)
def validate_questions(
    request: ValidationRequest,
) -> ValidationResponse:
    """
    Handle validation of an examination paper.
    Evaluates:
    - Syllabus relevance score for each question.
    - Exact and near-duplicate question detection.
    - Total marks and question count constraints.
    - Syllabus unit coverage percentage.
    """
    try:
        response = validation_service.validate_paper(request)
        return response
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while validating the question paper.",
        )
