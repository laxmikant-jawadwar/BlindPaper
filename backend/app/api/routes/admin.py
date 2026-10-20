"""The admin panel's API: dashboard, review queue, decisions, faculty and departments."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import require_admin
from app.api.responses import pdf_response
from app.api.routes.papers import as_http_error
from app.core.constants import DEPARTMENTS
from app.repositories.errors import DatabaseConnectionError
from app.schemas.paper import PaperDetail, PaperSummary, RejectRequest
from app.services.admin_service import admin_service
from app.services.paper_service import PaperError

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


def valid_department(department: Optional[str] = Query(default=None)) -> Optional[str]:
    if department and department not in DEPARTMENTS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unknown department '{department}'.")
    return department


@router.get("/stats", summary="Dashboard numbers, optionally for one department")
def stats(department: Optional[str] = Depends(valid_department)) -> Dict[str, Any]:
    try:
        return admin_service.stats(department)
    except DatabaseConnectionError as err:
        raise as_http_error(err)


@router.get("/papers", response_model=List[PaperSummary], summary="Submitted papers, newest first")
def list_papers(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    department: Optional[str] = Depends(valid_department),
    q: Optional[str] = None,
):
    try:
        return admin_service.list_papers(status_filter, department, q)
    except DatabaseConnectionError as err:
        raise as_http_error(err)


@router.get("/papers/{paper_id}", response_model=PaperDetail, summary="A submitted paper with its review analysis")
def get_paper(paper_id: str) -> Dict[str, Any]:
    try:
        return admin_service.get_paper(paper_id)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.get("/papers/{paper_id}/pdf", summary="Download a submitted paper as a PDF")
def download_paper(paper_id: str) -> Response:
    try:
        return pdf_response(admin_service.get_paper(paper_id))
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.post("/papers/{paper_id}/approve", response_model=PaperDetail, summary="Approve a pending paper")
def approve_paper(paper_id: str, admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    try:
        return admin_service.approve(admin, paper_id)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.post("/papers/{paper_id}/reject", response_model=PaperDetail, summary="Reject a pending paper, with a reason")
def reject_paper(paper_id: str, request: RejectRequest, admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    try:
        return admin_service.reject(admin, paper_id, request.reason)
    except (PaperError, DatabaseConnectionError) as err:
        raise as_http_error(err)


@router.get("/faculty", summary="Faculty members with their paper counts")
def faculty() -> List[Dict[str, Any]]:
    try:
        return admin_service.faculty()
    except DatabaseConnectionError as err:
        raise as_http_error(err)


@router.get("/departments", summary="Every department with its faculty and paper counts")
def departments() -> List[Dict[str, Any]]:
    try:
        return admin_service.departments()
    except DatabaseConnectionError as err:
        raise as_http_error(err)
