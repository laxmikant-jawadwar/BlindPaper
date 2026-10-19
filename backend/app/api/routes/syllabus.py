"""
API endpoints for syllabus file uploads and text extraction.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.syllabus import SyllabusExtractResponse
from app.services.syllabus_service import (
    EmptyFileError,
    FileSizeLimitExceededError,
    InvalidPDFError,
    OCRRequiredError,
    syllabus_service,
)

router = APIRouter(prefix="/api/syllabus", tags=["Syllabus"])

MAX_ALLOWED_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/upload",
    response_model=SyllabusExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and extract text from syllabus PDF",
    description="Upload a syllabus PDF file (up to 10 MB) to extract and return its raw text.",
)
async def upload_syllabus(
    file: UploadFile = File(..., description="Syllabus PDF file"),
) -> SyllabusExtractResponse:
    """
    Handle syllabus PDF upload, validation, and PyMuPDF text extraction.
    """
    # 1. Validate filename exists and has .pdf extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files (.pdf) are accepted.",
        )

    # 2. Read file contents safely
    try:
        # Read the file content
        contents = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file stream.",
        )

    # 3. Process and extract text using the syllabus service
    try:
        result = syllabus_service.extract_text_from_pdf_bytes(
            file_bytes=contents,
            filename=file.filename,
        )
    except EmptyFileError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except FileSizeLimitExceededError as err:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(err),
        )
    except InvalidPDFError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except OCRRequiredError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception:
        # Do not expose internal server tracebacks
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the syllabus PDF.",
        )

    return SyllabusExtractResponse(
        filename=result["filename"],
        page_count=result["page_count"],
        extracted_text=result["extracted_text"],
    )
