"""
API endpoints for syllabus file uploads, text extraction, structuring,
and MongoDB persistence.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.repositories.syllabus_repository import (
    DatabaseConnectionError,
    syllabus_repository,
)
from app.schemas.syllabus import (
    SyllabusCreateRequest,
    SyllabusDocumentResponse,
    SyllabusExtractResponse,
    SyllabusStructureRequest,
    SyllabusStructureResponse,
    SyllabusSummaryResponse,
    SyllabusUpdateRequest,
)
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

MAX_ALLOWED_SIZE = 10 * 1024 * 1024  # 10 MB


async def _read_and_extract(file: UploadFile) -> Tuple[bytes, Dict[str, Any]]:
    """
    Validate an uploaded syllabus PDF and extract its text.
    Returns the raw bytes and the extraction result; service errors become HTTP errors.
    """
    # 1. Validate filename exists and has .pdf extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files (.pdf) are accepted.",
        )

    # 2. Read file contents safely
    try:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the syllabus PDF.",
        )

    return contents, result


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
    _, result = await _read_and_extract(file)
    return SyllabusExtractResponse(
        filename=result["filename"],
        page_count=result["page_count"],
        extracted_text=result["extracted_text"],
    )


def _structure_and_store(
    contents: bytes, extracted: Dict[str, Any], subject_name: Optional[str]
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
        "Runs the first part of the BlindPaper flow in one call: extracts the PDF text, "
        "structures it into units and topics, and stores the raw text, the structured "
        "syllabus and the file metadata under a new syllabus ID."
    ),
)
async def process_syllabus(
    file: UploadFile = File(..., description="Syllabus PDF file"),
    subject_name: Optional[str] = Form(
        default=None, description="Optional subject name that overrides the one detected in the PDF"
    ),
) -> SyllabusDocumentResponse:
    """Extract, structure and persist an uploaded syllabus PDF."""
    contents, extracted = await _read_and_extract(file)

    try:
        # pymongo is blocking; keep it off the event loop
        created = await run_in_threadpool(_structure_and_store, contents, extracted, subject_name)
        return SyllabusDocumentResponse(**created)
    except DatabaseConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MongoDB service is unavailable: {err}",
        )
    except Exception:
        logger.exception("Failed to structure and store syllabus '%s'", extracted["filename"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while structuring and storing the syllabus.",
        )


@router.post(
    "/structure",
    response_model=SyllabusStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse extracted syllabus into structured units and Bloom's levels",
    description="Analyzes extracted syllabus text to identify units, topics, and recommended Bloom's cognitive levels.",
)
def structure_syllabus(request: SyllabusStructureRequest) -> SyllabusStructureResponse:
    """Parse syllabus text and recommend Bloom's Taxonomy levels for topics."""
    try:
        result = syllabus_structuring_service.structure_syllabus_text(
            extracted_text=request.extracted_text,
            subject_name=request.subject_name,
            filename=request.filename or "syllabus.pdf",
            page_count=request.page_count or 1,
        )
        return SyllabusStructureResponse(**result)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to structure syllabus: {err}",
        )


@router.post(
    "",
    response_model=SyllabusDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save confirmed syllabus to MongoDB",
    description="Persists faculty-confirmed structured syllabus and raw text in the MongoDB syllabi collection.",
)
def save_syllabus(request: SyllabusCreateRequest) -> SyllabusDocumentResponse:
    """Persist confirmed syllabus document in local MongoDB."""
    try:
        doc_data = request.model_dump()
        created_doc = syllabus_repository.create(doc_data)
        return SyllabusDocumentResponse(**created_doc)
    except DatabaseConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MongoDB service is unavailable: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist syllabus document: {err}",
        )


@router.get(
    "",
    response_model=List[SyllabusSummaryResponse],
    summary="List all saved syllabi from MongoDB",
    description="Returns a list of saved syllabus summaries for the faculty dashboard.",
)
def list_syllabi(limit: int = 50, skip: int = 0) -> List[SyllabusSummaryResponse]:
    """Retrieve all saved syllabi from MongoDB."""
    try:
        docs = syllabus_repository.list_all(limit=limit, skip=skip)
        summaries: List[SyllabusSummaryResponse] = []
        for doc in docs:
            units = doc.get("course_content", [])
            summaries.append(
                SyllabusSummaryResponse(
                    id=doc.get("id", ""),
                    subject_name=doc.get("subject_name", "Untitled Subject"),
                    course_code=doc.get("course_code"),
                    filename=doc.get("filename", "unknown.pdf"),
                    page_count=doc.get("page_count", 1),
                    unit_count=len(units),
                    processing_status=doc.get("processing_status", "reviewed"),
                    created_at=doc.get("created_at", ""),
                    updated_at=doc.get("updated_at", ""),
                )
            )
        return summaries
    except DatabaseConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MongoDB service is unavailable: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch syllabi from database: {err}",
        )


@router.get(
    "/{syllabus_id}",
    response_model=SyllabusDocumentResponse,
    summary="Retrieve a saved syllabus by ID",
    description="Fetches full syllabus details including structured units and extracted text.",
)
def get_syllabus(syllabus_id: str) -> SyllabusDocumentResponse:
    """Retrieve single syllabus by MongoDB ObjectId string."""
    try:
        doc = syllabus_repository.get_by_id(syllabus_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Syllabus with ID '{syllabus_id}' not found.",
            )
        return SyllabusDocumentResponse(**doc)
    except HTTPException:
        raise
    except DatabaseConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MongoDB service is unavailable: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve syllabus '{syllabus_id}': {err}",
        )


@router.put(
    "/{syllabus_id}",
    response_model=SyllabusDocumentResponse,
    summary="Update an existing syllabus structure in MongoDB",
    description="Updates subject name or structured syllabus data for a saved syllabus document.",
)
def update_syllabus(syllabus_id: str, request: SyllabusUpdateRequest) -> SyllabusDocumentResponse:
    """Update syllabus details in MongoDB."""
    try:
        update_data = request.model_dump(exclude_unset=True)
        updated_doc = syllabus_repository.update(syllabus_id, update_data)
        if updated_doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Syllabus with ID '{syllabus_id}' not found.",
            )
        return SyllabusDocumentResponse(**updated_doc)
    except HTTPException:
        raise
    except DatabaseConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MongoDB service is unavailable: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update syllabus '{syllabus_id}': {err}",
        )


@router.delete(
    "/{syllabus_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a saved syllabus from MongoDB",
    description="Removes a saved syllabus document by ID.",
)
def delete_syllabus(syllabus_id: str) -> dict:
    """Delete syllabus by ID."""
    try:
        success = syllabus_repository.delete(syllabus_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Syllabus with ID '{syllabus_id}' not found.",
            )
        return {"success": True, "message": f"Syllabus '{syllabus_id}' deleted successfully."}
    except HTTPException:
        raise
    except DatabaseConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MongoDB service is unavailable: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete syllabus '{syllabus_id}': {err}",
        )
