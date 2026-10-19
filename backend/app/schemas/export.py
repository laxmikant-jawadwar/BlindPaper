from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.question import QuestionItem


class PaperExportRequest(BaseModel):
    """Request schema for exporting an approved question paper to PDF."""

    subject_name: str = Field(..., description="Course/Subject title", min_length=1)
    questions: List[QuestionItem] = Field(..., description="Ordered list of questions to render", min_length=1)
    total_marks: int = Field(..., description="Total marks allocated to the paper", gt=0)
    question_count: int = Field(..., description="Total number of questions in the paper", gt=0)

    # Optional examination header metadata
    college_name: Optional[str] = Field(default=None, description="Name of the university, college, or institute")
    exam_name: Optional[str] = Field(default=None, description="Name/session of the examination (e.g., Final Semester Exam)")
    semester: Optional[str] = Field(default=None, description="Academic year or semester (e.g., Semester V)")
    paper_code: Optional[str] = Field(default=None, description="Course / Subject / Paper Code (e.g., CS-401)")
    duration: Optional[str] = Field(default=None, description="Examination duration (e.g., 3 Hours)")
    instructions: Optional[List[str]] = Field(
        default=None,
        description="General instructions for candidates (e.g., 'Attempt all questions.')",
    )

    @field_validator("subject_name")
    @classmethod
    def validate_subject_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("subject_name cannot be empty or whitespace only.")
        return trimmed
