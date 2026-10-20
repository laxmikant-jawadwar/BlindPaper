from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class QuestionItem(BaseModel):
    """Represents an individual examination question."""

    question_id: int = Field(..., description="Unique sequence number or ID of the question", ge=1)
    question_text: str = Field(..., description="The complete text of the question", min_length=5)
    question_type: str = Field(..., description="Question format (e.g., MCQ, Short Answer, Long Answer)")
    unit_or_topic: str = Field(..., description="Syllabus unit or topic the question is derived from")
    marks: int = Field(..., description="Marks allotted to this question", ge=1)
    difficulty: str = Field(..., description="Difficulty level (e.g., easy, medium, hard)")
    blooms_level: Optional[str] = Field(
        default=None,
        description="Cognitive level according to Bloom's Taxonomy (e.g., Remember, Understand, Apply, Analyze, Evaluate, Create)",
    )


class QuestionGenerateRequest(BaseModel):
    """Schema for question generation request."""

    subject_name: str = Field(..., description="Name of the subject or course", min_length=1)
    syllabus_text: Optional[str] = Field(
        default=None,
        description="Text extracted from the syllabus PDF (optional if syllabus_id is provided)",
    )
    syllabus_id: Optional[str] = Field(
        default=None,
        description="MongoDB ID of a previously saved syllabus",
    )
    selected_units: List[str] = Field(
        ...,
        description="List of units or syllabus topics to include in the paper",
        min_length=1,
    )
    total_marks: int = Field(..., description="Total marks for the question paper", gt=0, le=500)
    question_count: int = Field(..., description="Total number of questions to generate", gt=0, le=100)
    question_types: List[str] = Field(
        default=["Short Answer", "Long Answer"],
        description="Types of questions desired (e.g., MCQ, Short Answer, Long Answer)",
        min_length=1,
    )
    difficulty: str = Field(
        default="medium",
        description="Target difficulty level (easy, medium, hard, or mixed)",
    )
    blooms_levels: Optional[List[str]] = Field(
        default=None,
        description="Optional list of target Bloom's Taxonomy levels to balance",
    )

    @field_validator("subject_name", "difficulty")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace only.")
        return trimmed

    @field_validator("selected_units", "question_types")
    @classmethod
    def validate_non_empty_lists(cls, v: List[str]) -> List[str]:
        cleaned = [item.strip() for item in v if item and item.strip()]
        if not cleaned:
            raise ValueError("List must contain at least one non-empty item.")
        return cleaned

    @model_validator(mode="after")
    def validate_marks_and_counts(self) -> "QuestionGenerateRequest":
        if self.total_marks < self.question_count:
            raise ValueError(
                f"total_marks ({self.total_marks}) cannot be less than question_count ({self.question_count}), "
                "as every question must carry at least 1 mark."
            )
        if not self.syllabus_text and not self.syllabus_id:
            raise ValueError("Either 'syllabus_text' or 'syllabus_id' must be provided.")
        if self.syllabus_text is not None and len(self.syllabus_text.strip()) < 10:
            raise ValueError("syllabus_text must be at least 10 characters long.")
        return self


class QuestionGenerateResponse(BaseModel):
    """Schema for question generation response."""

    subject_name: str = Field(..., description="Course/subject name")
    total_marks: int = Field(..., description="Total marks sum across all generated questions")
    question_count: int = Field(..., description="Total count of questions returned")
    generation_mode: Literal["llm", "demo"] = Field(
        ...,
        description="Mode used: 'llm' for real AI generation, 'demo' for deterministic fallback",
    )
    questions: List[QuestionItem] = Field(..., description="Structured list of generated questions")
    message: Optional[str] = Field(
        default=None,
        description="Informational note on generation strategy or provider status",
    )
