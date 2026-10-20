"""
Syllabus endpoints (application workflow, step 2): upload a PDF, have it extracted and
structured, and keep it in MongoDB under the faculty member who uploaded it.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.api.deps import require_faculty
from app.repositories.errors import DatabaseConnectionError
from app.repositories.syllabus_repository import syllabus_repository
from app.schemas.syllabus import SyllabusDocumentResponse, SyllabusSummaryResponse
from app.services.syllabus_service import (
    EmptyFileError,
    FileSizeLimitExceededError,
    InvalidPDFError,
    OCRRequiredError,
    syllabus_service,
)
from app.services.syllabus_structuring_service import syllabus_structuring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/syllabus", tags=["Syllabus"])


def _db_unavailable(err: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"MongoDB service is unavailable: {err}",
    )


async def _read_and_extract(file: UploadFile) -> Tuple[bytes, Dict[str, Any]]:
    """
    Validate an uploaded syllabus PDF and extract its text and tables.
    Returns the raw bytes and the extraction result; service errors become HTTP errors.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files (.pdf) are accepted.",
        )

    try:
        contents = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file stream.",
        )

    try:
        result = syllabus_service.extract_text_from_pdf_bytes(file_bytes=contents, filename=file.filename)
    except FileSizeLimitExceededError as err:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(err))
    except (EmptyFileError, InvalidPDFError, OCRRequiredError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception:
        logger.exception("Unexpected error extracting syllabus '%s'", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the syllabus PDF.",
        )

    return contents, result


def _structure_and_store(
    owner_id: str, contents: bytes, extracted: Dict[str, Any], subject_name: Optional[str]
) -> Dict[str, Any]:
    """Structure the extracted text and persist both representations in MongoDB."""
    structured = syllabus_structuring_service.structure_syllabus_text(
        extracted_text=extracted["extracted_text"],
        subject_name=subject_name,
        filename=extracted["filename"],
        page_count=extracted["page_count"],
        tables=extracted["tables"],
    )
    return syllabus_repository.create(
        {
            "owner_id": owner_id,
            # The structured syllabus: only the parts BlindPaper uses
            "subject_name": structured["subject_name"],
            "course_code": structured["course_code"],
            "course_description": structured["course_description"],
            "course_outcomes": [outcome.model_dump() for outcome in structured["course_outcomes"]],
            "course_content": [unit.model_dump() for unit in structured["course_content"]],
            "processing_status": structured["processing_status"],
            # The raw representation and the file metadata
            "extracted_text": extracted["extracted_text"],
            "filename": extracted["filename"],
            "page_count": extracted["page_count"],
            "file_size_bytes": len(contents),
        }
    )


@router.post(
    "/process",
    response_model=SyllabusDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a syllabus PDF, structure it and store it in MongoDB",
    description=(
        "Extracts the PDF text and tables, structures them into course name, description, "
        "outcomes and units with topics, and stores the raw text, the structured syllabus and "
        "the file metadata under a new syllabus ID owned by the signed-in faculty member."
    ),
)
async def process_syllabus(
    file: UploadFile = File(..., description="Syllabus PDF file"),
    subject_name: Optional[str] = Form(
        default=None, description="Optional course name that overrides the one detected in the PDF"
    ),
    user: Dict[str, Any] = Depends(require_faculty),
) -> SyllabusDocumentResponse:
    contents, extracted = await _read_and_extract(file)

    try:
        # pymongo is blocking; keep it off the event loop
        created = await run_in_threadpool(_structure_and_store, user["id"], contents, extracted, subject_name)
        return SyllabusDocumentResponse(**created)
    except DatabaseConnectionError as err:
        raise _db_unavailable(err)
    except Exception:
        logger.exception("Failed to structure and store syllabus '%s'", extracted["filename"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while structuring and storing the syllabus.",
        )


@router.get(
    "",
    response_model=List[SyllabusSummaryResponse],
    summary="List my saved syllabi",
)
def list_syllabi(limit: int = 50, skip: int = 0, user: Dict[str, Any] = Depends(require_faculty)):
    try:
        docs = syllabus_repository.list_for_owner(user["id"], limit=limit, skip=skip)
    except DatabaseConnectionError as err:
        raise _db_unavailable(err)
    return [
        SyllabusSummaryResponse(
            id=doc["id"],
            subject_name=doc.get("subject_name", "Untitled Subject"),
            course_code=doc.get("course_code"),
            filename=doc.get("filename", "unknown.pdf"),
            page_count=doc.get("page_count", 1),
            unit_count=len(doc.get("course_content", [])),
            processing_status=doc.get("processing_status", "structured"),
            created_at=doc.get("created_at", ""),
            updated_at=doc.get("updated_at", ""),
        )
        for doc in docs
    ]


@router.get("/{syllabus_id}", response_model=SyllabusDocumentResponse, summary="One of my saved syllabi")
def get_syllabus(syllabus_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> SyllabusDocumentResponse:
    try:
        doc = syllabus_repository.get_by_id(syllabus_id, owner_id=user["id"])
    except DatabaseConnectionError as err:
        raise _db_unavailable(err)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Syllabus '{syllabus_id}' not found.")
    return SyllabusDocumentResponse(**doc)


@router.delete("/{syllabus_id}", summary="Delete one of my saved syllabi")
def delete_syllabus(syllabus_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> Dict[str, Any]:
    try:
        deleted = syllabus_repository.delete(syllabus_id, owner_id=user["id"])
    except DatabaseConnectionError as err:
        raise _db_unavailable(err)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Syllabus '{syllabus_id}' not found.")
    return {"success": True, "message": f"Syllabus '{syllabus_id}' deleted successfully."}
