"""The faculty member's papers: generate, preview, correct, submit, delete and download."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import require_faculty
from app.api.errors import ProblemsHTTPException
from app.api.responses import pdf_response
from app.repositories.errors import DatabaseConnectionError
from app.schemas.paper import PaperConfig, PaperDetail, PaperSummary, PaperUpdateRequest
from app.services.paper_generation_service import (
    GenerationError,
    GenerationNotConfigured,
    GenerationRateLimited,
)
from app.services.paper_service import (
    ConfigurationInvalid,
    InvalidTransition,
    PaperError,
    PaperNotFound,
    PaperNotReady,
    paper_service,
)

router = APIRouter(prefix="/api/papers", tags=["Papers"])


def as_http_error(err: Exception) -> HTTPException:
    """Turn a paper or generation problem into the HTTP error the faculty should see."""
    if isinstance(err, PaperNotFound):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(err))
    if isinstance(err, InvalidTransition):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(err))
    if isinstance(err, (ConfigurationInvalid, PaperNotReady)):
        return ProblemsHTTPException(str(err), getattr(err, "problems", []))
    if isinstance(err, GenerationNotConfigured):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))
    if isinstance(err, GenerationRateLimited):
        headers = {"Retry-After": str(err.retry_after)} if err.retry_after else None
        return HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail=str(err), headers=headers)
    if isinstance(err, GenerationError):
        return HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(err))
    if isinstance(err, DatabaseConnectionError):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"MongoDB service is unavailable: {err}")
    raise err


@router.post(
    "/generate",
    response_model=PaperDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a question paper from the configuration (saved as a Draft)",
)
def generate_paper(config: PaperConfig, user: Dict[str, Any] = Depends(require_faculty)) -> Dict[str, Any]:
    try:
        return paper_service.generate(user, config)
    except (PaperError, GenerationError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.get("", response_model=List[PaperSummary], summary="My papers")
def list_papers(status_filter: Optional[str] = Query(default=None, alias="status"), user: Dict[str, Any] = Depends(require_faculty)):
    try:
        return paper_service.list_for_faculty(user, status_filter)
    except DatabaseConnectionError as err:
        raise as_http_error(err)


@router.get("/notifications", summary="Recent admin decisions on my papers")
def notifications(user: Dict[str, Any] = Depends(require_faculty)) -> List[Dict[str, Any]]:
    try:
        return paper_service.notifications(user)
    except DatabaseConnectionError as err:
        raise as_http_error(err)


@router.get("/{paper_id}", response_model=PaperDetail, summary="One of my papers")
def get_paper(paper_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> Dict[str, Any]:
    try:
        return paper_service.get_for_faculty(user, paper_id)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.get("/{paper_id}/pdf", summary="Download an approved paper as a PDF")
def download_paper(paper_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> Response:
    try:
        paper = paper_service.get_for_faculty(user, paper_id)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)
    if paper["status"] != "Approved":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="The paper can be downloaded once the admin has approved it.")
    return pdf_response(paper)


@router.put("/{paper_id}", response_model=PaperDetail, summary="Correct the questions of a Draft or Rejected paper")
def update_paper(paper_id: str, request: PaperUpdateRequest, user: Dict[str, Any] = Depends(require_faculty)):
    try:
        return paper_service.update_questions(user, paper_id, request)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.post(
    "/{paper_id}/questions/{sub_question_id}/regenerate",
    response_model=PaperDetail,
    summary="Write one question again, leaving the others as they are",
)
def regenerate_question(paper_id: str, sub_question_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> Dict[str, Any]:
    try:
        return paper_service.regenerate_question(user, paper_id, sub_question_id)
    except (PaperError, GenerationError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.post("/{paper_id}/regenerate", response_model=PaperDetail, summary="Write the questions again")
def regenerate_paper(paper_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> Dict[str, Any]:
    try:
        return paper_service.regenerate(user, paper_id)
    except (PaperError, GenerationError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.post("/{paper_id}/submit", response_model=PaperDetail, summary="Submit for admin approval")
def submit_paper(paper_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> Dict[str, Any]:
    try:
        return paper_service.submit(user, paper_id)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.delete("/{paper_id}", summary="Delete a Draft or Rejected paper")
def delete_paper(paper_id: str, user: Dict[str, Any] = Depends(require_faculty)) -> Dict[str, bool]:
    try:
        paper_service.delete(user, paper_id)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)
    return {"success": True}
