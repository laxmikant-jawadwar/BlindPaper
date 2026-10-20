"""
The admin's view of the papers (application workflow, steps 8-11): dashboard numbers, the review
queue, approving and rejecting, and the faculty and department overviews.
"""

from typing import Any, Dict, List, Optional

from app.core.constants import (
    DEPARTMENTS,
    ROLE_FACULTY,
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_PENDING,
    STATUS_REJECTED,
    SUBMITTED_STATUSES,
)
from app.models.mongo import get_utc_now_iso
from app.repositories.paper_repository import paper_repository
from app.repositories.user_repository import user_repository
from app.services.paper_service import InvalidTransition, PaperNotFound, to_detail, to_summary


def _counts(papers: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "total": len(papers),
        "pending": sum(p["status"] == STATUS_PENDING for p in papers),
        "approved": sum(p["status"] == STATUS_APPROVED for p in papers),
        "rejected": sum(p["status"] == STATUS_REJECTED for p in papers),
    }


class AdminService:
    # ---- dashboard -----------------------------------------------------------------------
    def stats(self, department: Optional[str] = None) -> Dict[str, Any]:
        submitted = paper_repository.list_submitted()
        scope = [p for p in submitted if p.get("department") == department] if department else submitted
        departments = [department] if department else DEPARTMENTS
        return {
            **_counts(scope),
            "departments": [
                {"department": name, **_counts([p for p in submitted if p.get("department") == name])} for name in departments
            ],
        }

    def departments(self) -> List[Dict[str, Any]]:
        submitted = paper_repository.list_submitted()
        faculty = user_repository.list_by_role(ROLE_FACULTY)
        return [
            {
                "department": name,
                "faculty_count": sum(f.get("department") == name for f in faculty),
                **_counts([p for p in submitted if p.get("department") == name]),
            }
            for name in DEPARTMENTS
        ]

    def faculty(self) -> List[Dict[str, Any]]:
        papers = paper_repository.list_all()
        members = []
        for user in user_repository.list_by_role(ROLE_FACULTY):
            mine = [p for p in papers if p["faculty_id"] == user["id"]]
            submitted = [p for p in mine if p["status"] in SUBMITTED_STATUSES]
            members.append(
                {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "department": user.get("department"),
                    "designation": user.get("designation"),
                    "phone": user.get("phone"),
                    "created_at": user.get("created_at"),
                    "papers": {**_counts(submitted), "drafts": sum(p["status"] == STATUS_DRAFT for p in mine)},
                }
            )
        return members

    # ---- review queue --------------------------------------------------------------------
    def list_papers(self, status: Optional[str], department: Optional[str], search: Optional[str]) -> List[Dict[str, Any]]:
        return [to_summary(p) for p in paper_repository.list_submitted(status, department, search)]

    def get_paper(self, paper_id: str) -> Dict[str, Any]:
        return to_detail(self._submitted(paper_id))

    def approve(self, admin: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
        return self._decide(admin, paper_id, STATUS_APPROVED, None)

    def reject(self, admin: Dict[str, Any], paper_id: str, reason: str) -> Dict[str, Any]:
        return self._decide(admin, paper_id, STATUS_REJECTED, reason)

    # ---- internals -----------------------------------------------------------------------
    @staticmethod
    def _submitted(paper_id: str) -> Dict[str, Any]:
        """A paper the admin may see: one that has been submitted (drafts are the faculty's own business)."""
        paper = paper_repository.get(paper_id)
        if paper is None or paper["status"] not in SUBMITTED_STATUSES:
            raise PaperNotFound("Paper not found.")
        return paper

    def _decide(self, admin: Dict[str, Any], paper_id: str, status: str, reason: Optional[str]) -> Dict[str, Any]:
        paper = self._submitted(paper_id)
        if paper["status"] != STATUS_PENDING:
            raise InvalidTransition(f"Only papers that are Pending Approval can be decided (this one is {paper['status']}).")
        now = get_utc_now_iso()
        history = [*paper.get("review_history", []), {"status": status, "reason": reason, "at": now, "by": admin["name"]}]
        updated = paper_repository.update(
            paper_id,
            {
                "status": status,
                "reviewed_at": now,
                "reviewed_by": admin["id"],
                "rejection_reason": reason,
                "review_history": history,
            },
        )
        return to_detail(updated)


admin_service = AdminService()
