"""
A paper's life on the faculty side (application workflow, steps 3-7):
generate -> correct -> (regenerate) -> submit for approval. Admin decisions live in admin_service.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.core.constants import STATUS_APPROVED, STATUS_DRAFT, STATUS_PENDING, STATUS_REJECTED
from app.models.mongo import get_utc_now_iso
from app.repositories.paper_repository import paper_repository
from app.repositories.syllabus_repository import syllabus_repository
from app.schemas.paper import PaperConfig, PaperUpdateRequest
from app.services import paper_rules
from app.services.paper_analysis import analyze
from app.services.paper_generation_service import GenerationResult, paper_generation_service

EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_REJECTED)


class PaperError(Exception):
    """Base for problems the API turns into an HTTP error."""


class PaperNotFound(PaperError):
    pass


class InvalidTransition(PaperError):
    """The paper is in a status where this action is not allowed (409)."""


class ConfigurationInvalid(PaperError):
    """The request is inconsistent; `problems` lists what to fix (422)."""

    def __init__(self, problems: List[str], message: Optional[str] = None):
        super().__init__(message or "Please fix the following: " + " ".join(problems))
        self.problems = problems


class PaperNotReady(PaperError):
    """The paper still fails its checks, so it cannot be submitted (422)."""


def to_summary(paper: Dict[str, Any]) -> Dict[str, Any]:
    keys = (
        "id course_name course_code department faculty_name exam_type year semester total_marks status "
        "created_at submitted_at reviewed_at rejection_reason"
    ).split()
    return {key: paper.get(key) for key in keys}


def to_detail(paper: Dict[str, Any]) -> Dict[str, Any]:
    """A paper as the API returns it, with its checks computed from what is stored right now."""
    return {
        **to_summary(paper),
        "faculty_id": paper["faculty_id"],
        "syllabus_id": paper["syllabus_id"],
        "difficulty": paper["difficulty"],
        "question_types": paper["question_types"],
        "selected_units": paper["selected_units"],
        "groups": paper["groups"],
        "questions": paper["questions"],
        "syllabus_snapshot": paper["syllabus_snapshot"],
        "review_history": paper.get("review_history", []),
        "generation": paper.get("generation", {}),
        "analysis": analyze(paper),
    }


def _generation_info(result: GenerationResult) -> Dict[str, Any]:
    return {"provider": "groq", "model": result.model, "generated_at": get_utc_now_iso(), "usage": result.usage}


def _snapshot(syllabus: Dict[str, Any], selected_units: List[int]) -> Dict[str, Any]:
    """The part of the syllabus this paper was written from, so the paper stands on its own."""
    return {
        "units": [
            {"unit_number": u["unit_number"], "unit_name": u["unit_name"], "topics": u.get("topics", [])}
            for u in syllabus.get("course_content", [])
            if u["unit_number"] in selected_units
        ],
        "outcomes": syllabus.get("course_outcomes", []),
    }


class PaperService:
    def _owned(self, faculty: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
        paper = paper_repository.get(paper_id, faculty_id=faculty["id"])
        if paper is None:
            raise PaperNotFound("Paper not found.")
        return paper

    def _editable(self, faculty: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
        paper = self._owned(faculty, paper_id)
        if paper["status"] not in EDITABLE_STATUSES:
            raise InvalidTransition(f"A paper that is {paper['status']} can't be changed.")
        return paper

    # ---- generate ------------------------------------------------------------------------
    def generate(self, faculty: Dict[str, Any], config: PaperConfig) -> Dict[str, Any]:
        syllabus = syllabus_repository.get_by_id(config.syllabus_id, owner_id=faculty["id"])
        if syllabus is None:
            raise PaperNotFound("Syllabus not found.")
        problems = paper_rules.validate_config(config, syllabus)
        if problems:
            raise ConfigurationInvalid(problems)

        result = paper_generation_service.generate(config, syllabus)
        stored = paper_repository.create(
            {
                "faculty_id": faculty["id"],
                "faculty_name": faculty["name"],
                "department": faculty.get("department"),
                "syllabus_id": config.syllabus_id,
                "course_name": config.course_name,
                "course_code": config.course_code,
                "year": config.year,
                "semester": config.semester,
                "exam_type": config.exam_type,
                "difficulty": config.difficulty,
                "question_types": config.question_types,
                "selected_units": config.selected_units,
                "groups": [group.model_dump() for group in config.groups],
                "questions": result.questions,
                "total_marks": paper_rules.total_marks(config),
                "syllabus_snapshot": _snapshot(syllabus, config.selected_units),
                "status": STATUS_DRAFT,
                "rejection_reason": None,
                "review_history": [],
                "submitted_at": None,
                "reviewed_at": None,
                "reviewed_by": None,
                "generation": _generation_info(result),
            }
        )
        return to_detail(stored)

    @staticmethod
    def _config_and_syllabus(paper: Dict[str, Any]) -> Tuple[PaperConfig, Dict[str, Any]]:
        """The configuration a stored paper was made from, and the syllabus snapshot saved with it."""
        config = PaperConfig(
            **{key: paper[key] for key in (
                "syllabus_id course_name course_code year semester exam_type difficulty question_types selected_units groups"
            ).split()}
        )
        snapshot = paper["syllabus_snapshot"]
        return config, {"course_content": snapshot["units"], "course_outcomes": snapshot["outcomes"]}

    def regenerate(self, faculty: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
        """Write every question of the paper again."""
        paper = self._editable(faculty, paper_id)
        config, syllabus = self._config_and_syllabus(paper)

        result = paper_generation_service.generate(config, syllabus)
        updated = paper_repository.update(paper_id, {"questions": result.questions, "generation": _generation_info(result)})
        return to_detail(updated)

    def regenerate_question(self, faculty: Dict[str, Any], paper_id: str, sub_question_id: str) -> Dict[str, Any]:
        """Write one question again, leaving every other question exactly as it is."""
        paper = self._editable(faculty, paper_id)
        current = next((q for q in paper["questions"] if q["sub_question_id"] == sub_question_id), None)
        if current is None:
            raise PaperNotFound("That question is not in this paper.")
        config, syllabus = self._config_and_syllabus(paper)

        result = paper_generation_service.generate_question(
            config,
            syllabus,
            sub_question_id,
            current["question_type"],
            avoid=[q["question_text"] for q in paper["questions"]],
        )
        replacement = result.questions[0]
        questions = [replacement if q["sub_question_id"] == sub_question_id else q for q in paper["questions"]]
        return to_detail(paper_repository.update(paper_id, {"questions": questions}))

    # ---- read ----------------------------------------------------------------------------
    def list_for_faculty(self, faculty: Dict[str, Any], status: Optional[str] = None) -> List[Dict[str, Any]]:
        return [to_summary(p) for p in paper_repository.list_for_faculty(faculty["id"], status)]

    def get_for_faculty(self, faculty: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
        return to_detail(self._owned(faculty, paper_id))

    def notifications(self, faculty: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "paper_id": p["id"],
                "course_name": p["course_name"],
                "status": p["status"],
                "reason": p.get("rejection_reason"),
                "reviewed_at": p["reviewed_at"],
            }
            for p in paper_repository.list_reviewed_for_faculty(faculty["id"])
        ]

    # ---- correct -------------------------------------------------------------------------
    def update_questions(self, faculty: Dict[str, Any], paper_id: str, request: PaperUpdateRequest) -> Dict[str, Any]:
        paper = self._editable(faculty, paper_id)
        by_id = {q["sub_question_id"]: dict(q) for q in paper["questions"]}

        unknown = [edit.sub_question_id for edit in request.questions if edit.sub_question_id not in by_id]
        if unknown:
            raise ConfigurationInvalid([f"There is no question '{u}' in this paper." for u in unknown])

        for edit in request.questions:
            question = by_id[edit.sub_question_id]
            question["question_text"] = edit.question_text.strip()
            if question["question_type"] == "MCQ":  # only an MCQ has options and a correct answer
                question["options"] = [option.strip() for option in edit.options]
                question["answer"] = edit.answer.strip().upper()

        updated = paper_repository.update(paper_id, {"questions": [by_id[q["sub_question_id"]] for q in paper["questions"]]})
        return to_detail(updated)

    # ---- submit and delete ---------------------------------------------------------------
    def submit(self, faculty: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
        paper = self._editable(faculty, paper_id)
        report = analyze(paper)
        if report["status"] == "fail":
            failing = " ".join(c["message"] for c in report["checks"] if c["status"] == "fail")
            raise PaperNotReady(f"This paper can't be submitted yet. {failing}")

        updated = paper_repository.update(
            paper_id,
            {
                "status": STATUS_PENDING,
                "submitted_at": get_utc_now_iso(),
                "faculty_name": faculty["name"],
                "department": faculty.get("department"),
                "rejection_reason": None,
            },
        )
        return to_detail(updated)

    def delete(self, faculty: Dict[str, Any], paper_id: str) -> None:
        self._editable(faculty, paper_id)
        paper_repository.delete(paper_id)


paper_service = PaperService()

__all__ = [
    "ConfigurationInvalid", "InvalidTransition", "PaperError", "PaperNotFound", "PaperNotReady",
    "STATUS_APPROVED", "paper_service", "to_detail", "to_summary",
]
