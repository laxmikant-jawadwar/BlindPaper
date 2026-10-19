"""
API endpoints for syllabus-centric examination question generation.
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.question import (
    QuestionGenerateRequest,
    QuestionGenerateResponse,
)
from app.services.question_service import (
    InvalidRequirementError,
    LLMGenerationError,
    SyllabusMismatchError,
    question_service,
)

router = APIRouter(prefix="/api/questions", tags=["Questions"])


@router.post(
    "/generate",
    response_model=QuestionGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate examination questions from syllabus",
    description="Generates structured questions grounded in the supplied syllabus text and exam requirements.",
)
def generate_questions(
    request: QuestionGenerateRequest,
) -> QuestionGenerateResponse:
    """
    Handle question generation requests using LLM provider or deterministic demo fallback.
    """
    try:
        response = question_service.generate_questions(request)
        return response
    except (SyllabusMismatchError, InvalidRequirementError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except LLMGenerationError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(err),
        )
    except Exception:
        # Prevent leaking internal stack traces
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating examination questions.",
        )
