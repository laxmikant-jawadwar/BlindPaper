"""
API endpoints for question paper PDF export and document download.
"""

import re
from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.export import PaperExportRequest
from app.services.pdf_service import PDFExportError, pdf_export_service

router = APIRouter(prefix="/api/questions", tags=["Export"])


@router.post(
    "/export-pdf",
    summary="Export examination question paper as a formatted PDF",
    description="Generates and streams an A4-formatted, publication-ready examination question paper PDF.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Binary PDF question paper stream.",
        },
        400: {"description": "Invalid question paper structure, marks, or counts."},
    },
)
def export_question_paper_pdf(request: PaperExportRequest) -> Response:
    """
    Validate question paper specifications and generate an in-memory PDF download stream.
    """
    actual_count = len(request.questions)
    actual_marks = sum(q.marks for q in request.questions)

    # 1. Validate question count consistency
    if actual_count != request.question_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Question count mismatch: request specifies question_count={request.question_count}, "
                f"but provided questions list contains {actual_count} items."
            ),
        )

    # 2. Validate total marks consistency
    if actual_marks != request.total_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Total marks mismatch: request specifies total_marks={request.total_marks}, "
                f"but sum of question marks equals {actual_marks}."
            ),
        )

    # 3. Validate positive marks for every question
    invalid_marks = [q.question_id for q in request.questions if q.marks <= 0]
    if invalid_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Questions with IDs {invalid_marks} have invalid non-positive marks.",
        )

    # 4. Generate the PDF bytes in memory
    try:
        pdf_bytes = pdf_export_service.generate_question_paper_pdf(request)
    except PDFExportError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the question paper PDF.",
        )

    # 5. Formulate safe download filename
    safe_subject = re.sub(r"[^\w\-]", "_", request.subject_name.strip())
    filename = f"BlindPaper_{safe_subject}_Question_Paper.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
