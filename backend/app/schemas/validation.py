from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.question import QuestionItem


class QuestionRelevance(BaseModel):
    """Syllabus relevance analysis for a single question."""

    question_id: int = Field(..., description="ID of the question analyzed")
    question_text: str = Field(..., description="Text of the question")
    relevance_score: float = Field(..., description="Calculated relevance score from 0.0 to 1.0", ge=0.0, le=1.0)
    status: Literal["high", "review_required", "low"] = Field(
        ..., description="Relevance category based on confidence threshold"
    )
    matched_terms: List[str] = Field(default_factory=list, description="Key syllabus terms found in the question")
    explanation: str = Field(..., description="Human-readable explanation of relevance findings")


class DuplicatePair(BaseModel):
    """Details of suspected exact or near-duplicate questions."""

    question_id_1: int = Field(..., description="ID of the first question")
    question_id_2: int = Field(..., description="ID of the second question")
    question_text_1: str = Field(..., description="Text of the first question")
    question_text_2: str = Field(..., description="Text of the second question")
    similarity_score: float = Field(..., description="Similarity score between questions (0.0 to 1.0)", ge=0.0, le=1.0)
    match_type: Literal["exact", "near_duplicate"] = Field(..., description="Type of duplicate detected")
    reason: str = Field(..., description="Explanation of why questions are flagged as duplicates")


class MarksValidationResult(BaseModel):
    """Detailed results of total marks and question count checks."""

    is_valid: bool = Field(..., description="Whether both marks and counts match requirements")
    expected_marks: int = Field(..., description="Requested total marks")
    actual_marks: int = Field(..., description="Sum of marks across all questions")
    expected_count: int = Field(..., description="Requested question count")
    actual_count: int = Field(..., description="Actual number of questions supplied")
    details: str = Field(..., description="Summary explanation of the marks/count check")


class UnitCoverageResult(BaseModel):
    """Evaluation of syllabus unit and topic representation across questions."""

    total_selected_units: int = Field(..., description="Number of units selected by faculty")
    covered_units: List[str] = Field(default_factory=list, description="Units represented in questions")
    uncovered_units: List[str] = Field(default_factory=list, description="Units with no questions assigned")
    coverage_percentage: float = Field(..., description="Percentage of selected units covered", ge=0.0, le=100.0)


class ValidationRequest(BaseModel):
    """Request payload for validating a question paper."""

    subject_name: str = Field(..., description="Name of the subject/course", min_length=1)
    syllabus_text: str = Field(..., description="Extracted text from the syllabus PDF", min_length=10)
    selected_units: List[str] = Field(..., description="Units to be covered in the exam", min_length=1)
    questions: List[QuestionItem] = Field(..., description="List of generated questions to validate", min_length=1)
    total_marks: int = Field(..., description="Target total marks for the paper", gt=0)
    question_count: int = Field(..., description="Target number of questions", gt=0)

    @field_validator("subject_name", "syllabus_text")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace only.")
        return trimmed

    @field_validator("selected_units")
    @classmethod
    def validate_non_empty_units(cls, v: List[str]) -> List[str]:
        cleaned = [u.strip() for u in v if u and u.strip()]
        if not cleaned:
            raise ValueError("selected_units must contain at least one non-empty unit.")
        return cleaned


class ValidationResponse(BaseModel):
    """Overall validation report for the examination question paper."""

    overall_status: Literal["pass", "review_required", "fail"] = Field(
        ...,
        description="'pass' if clean, 'review_required' for uncertain cases/duplicates, 'fail' for rule violations",
    )
    summary: str = Field(..., description="High-level faculty-friendly summary of validation outcome")
    total_questions: int = Field(..., description="Number of questions processed")
    relevance_results: List[QuestionRelevance] = Field(..., description="Relevance analysis for each question")
    duplicate_pairs: List[DuplicatePair] = Field(default_factory=list, description="Suspected duplicate question pairs")
    marks_validation: MarksValidationResult = Field(..., description="Marks and count consistency breakdown")
    unit_coverage: UnitCoverageResult = Field(..., description="Syllabus unit coverage breakdown")
    issues: List[str] = Field(default_factory=list, description="Blocking violations causing 'fail' status")
    warnings: List[str] = Field(default_factory=list, description="Potential issues requiring faculty attention")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations for improvement")
