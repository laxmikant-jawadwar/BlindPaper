"""Question paper schemas: the faculty's configuration, the generated questions and the stored paper."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

QuestionType = Literal["MCQ", "Descriptive", "Numerical"]
ExamType = Literal["MSE", "ESE"]
Difficulty = Literal["Easy", "Balanced", "Difficult"]
PaperStatus = Literal["Draft", "Pending Approval", "Approved", "Rejected"]
Year = Literal["First Year", "Second Year", "Third Year", "Final Year"]
Semester = Literal[
    "Semester 1", "Semester 2", "Semester 3", "Semester 4",
    "Semester 5", "Semester 6", "Semester 7", "Semester 8",
]


class SubQuestionSpec(BaseModel):
    """One sub-question slot of the template: a), b), c)..."""

    id: str = Field(..., min_length=1, max_length=64)
    description: str = Field(default="", max_length=300, description="Optional hint for the question")
    co: str = Field(..., min_length=1, max_length=10)
    marks: float = Field(..., gt=0, le=100)
    unit_number: int = Field(..., ge=1)

    @field_validator("description")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class QuestionGroupSpec(BaseModel):
    """A question group (Q1, Q2...) with its instruction and sub-questions."""

    id: str = Field(..., min_length=1, max_length=64)
    instruction: str = Field(..., min_length=1, max_length=120, description="e.g. 'Attempt any two'")
    sub_questions: List[SubQuestionSpec] = Field(..., min_length=1, max_length=12)

    @field_validator("instruction")
    @classmethod
    def _clean_instruction(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("The attempt instruction cannot be empty.")
        return cleaned


class PaperConfig(BaseModel):
    """Everything the faculty configured on the Configure Question Paper screen."""

    syllabus_id: str = Field(..., min_length=1)
    course_name: str = Field(..., max_length=150)
    course_code: str = Field(..., max_length=30)
    year: Year
    semester: Semester
    exam_type: ExamType
    difficulty: Difficulty
    question_types: List[QuestionType] = Field(..., min_length=1)
    selected_units: List[int] = Field(..., min_length=1)
    groups: List[QuestionGroupSpec] = Field(..., min_length=1, max_length=10)

    @field_validator("course_name", "course_code")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned

    @model_validator(mode="after")
    def _unique_ids(self) -> "PaperConfig":
        slot_ids = [sq.id for group in self.groups for sq in group.sub_questions]
        group_ids = [group.id for group in self.groups]
        if len(set(slot_ids)) != len(slot_ids) or len(set(group_ids)) != len(group_ids):
            raise ValueError("Question groups and sub-questions need unique ids.")
        self.question_types = list(dict.fromkeys(self.question_types))
        self.selected_units = sorted(set(self.selected_units))
        return self


class QuestionEdit(BaseModel):
    """A faculty edit of one generated question."""

    sub_question_id: str
    question_text: str = Field(..., min_length=3, max_length=3000)
    options: List[str] = Field(default_factory=list, max_length=8)
    answer: str = Field(default="", max_length=2)


class PaperUpdateRequest(BaseModel):
    """Permitted corrections while a paper is a Draft (or was rejected)."""

    questions: List[QuestionEdit] = Field(..., min_length=1)


class RejectRequest(BaseModel):
    reason: str = Field(..., max_length=1000)

    @field_validator("reason")
    @classmethod
    def _reason_required(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("A rejection reason is required so the faculty knows what to correct.")
        return cleaned


class PaperSummary(BaseModel):
    """A row of the papers tables."""

    id: str
    course_name: str
    course_code: str
    department: Optional[str] = None
    faculty_name: str
    exam_type: ExamType
    year: str
    semester: str
    total_marks: float
    status: PaperStatus
    created_at: str
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    rejection_reason: Optional[str] = None


class PaperDetail(PaperSummary):
    """A whole paper: configuration, template, questions and checks."""

    faculty_id: str
    syllabus_id: str
    difficulty: Difficulty
    question_types: List[QuestionType]
    selected_units: List[int]
    groups: List[QuestionGroupSpec]
    questions: List[Dict[str, Any]]
    syllabus_snapshot: Dict[str, Any]
    analysis: Dict[str, Any]
    review_history: List[Dict[str, Any]] = Field(default_factory=list)
    generation: Dict[str, Any] = Field(default_factory=dict)
