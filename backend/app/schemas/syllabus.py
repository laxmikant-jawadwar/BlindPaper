from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class CourseOutcome(BaseModel):
    """A course outcome (CO) with its Bloom's Taxonomy level, as listed in the syllabus."""

    code: str = Field(..., description="Outcome code, e.g. 'CO1'", min_length=1)
    description: str = Field(..., description="What the student should be able to do")
    blooms_level: Optional[int] = Field(
        default=None,
        description="Bloom's level as a number: 1 Remember, 2 Understand, 3 Apply, 4 Analyze, 5 Evaluate, 6 Create",
        ge=1,
        le=6,
    )
    blooms_descriptor: Optional[str] = Field(default=None, description="Bloom's level name, e.g. 'Understand'")


class CourseUnit(BaseModel):
    """A unit of the course contents with its list of topics."""

    unit_number: int = Field(..., description="Unit number as printed in the syllabus", ge=1)
    unit_name: str = Field(..., description="Unit title, e.g. 'Accounting Concept'", min_length=1)
    topics: List[str] = Field(default_factory=list, description="Topics covered in this unit")


class SyllabusDocumentResponse(BaseModel):
    """Full syllabus document returned from MongoDB."""

    id: str = Field(..., description="Unique MongoDB string ID")
    subject_name: str = Field(..., description="Course name")
    course_code: Optional[str] = Field(default=None, description="Course code, if known")
    course_description: Optional[str] = Field(default=None, description="Course description")
    course_outcomes: List[CourseOutcome] = Field(default_factory=list, description="Course outcomes (COs)")
    course_content: List[CourseUnit] = Field(default_factory=list, description="Units with their topics")
    filename: str = Field(..., description="Original PDF filename")
    page_count: int = Field(..., description="Total pages in the PDF")
    file_size_bytes: Optional[int] = Field(default=None, description="Size of the uploaded PDF in bytes")
    extracted_text: str = Field(..., description="Raw extracted text")
    processing_status: str = Field(..., description="Status (e.g., 'structured')")
    created_at: str = Field(..., description="ISO UTC timestamp of creation")
    updated_at: str = Field(..., description="ISO UTC timestamp of last update")


class SyllabusSummaryResponse(BaseModel):
    """Summary item for listing saved syllabi on the faculty dashboard."""

    id: str = Field(..., description="Unique MongoDB string ID")
    subject_name: str = Field(..., description="Course name")
    course_code: Optional[str] = Field(default=None, description="Course code, if known")
    filename: str = Field(..., description="Original PDF filename")
    page_count: int = Field(..., description="Total pages in PDF")
    unit_count: int = Field(..., description="Number of units in this syllabus")
    processing_status: str = Field(..., description="Status")
    created_at: str = Field(..., description="Creation date/time")
    updated_at: str = Field(..., description="Last updated date/time")
