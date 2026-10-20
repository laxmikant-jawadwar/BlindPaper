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


class SyllabusExtractResponse(BaseModel):
    """Schema for syllabus PDF text extraction response."""

    filename: str = Field(..., description="Original name of the uploaded syllabus file")
    page_count: int = Field(..., description="Total number of pages processed in the PDF")
    extracted_text: str = Field(..., description="Full text extracted from all pages of the syllabus")
    message: Optional[str] = Field(
        default=None,
        description="Optional status or informational note about the extraction",
    )


class SyllabusStructureRequest(BaseModel):
    """Request payload to parse and structure raw syllabus text."""

    subject_name: Optional[str] = Field(default=None, description="Course/subject name if known")
    filename: Optional[str] = Field(default="syllabus.pdf", description="Original filename")
    page_count: Optional[int] = Field(default=1, description="Page count of the document")
    extracted_text: str = Field(..., description="Raw extracted text from syllabus PDF", min_length=5)


class SyllabusStructureResponse(BaseModel):
    """The structured syllabus: course name, description, outcomes and unit-wise contents."""

    subject_name: str = Field(..., description="Identified or provided course name")
    course_code: Optional[str] = Field(default=None, description="Course code found in the document, if any")
    course_description: Optional[str] = Field(default=None, description="Course description, if the syllabus has one")
    course_outcomes: List[CourseOutcome] = Field(default_factory=list, description="Course outcomes (COs)")
    course_content: List[CourseUnit] = Field(default_factory=list, description="Units with their topics")
    filename: str = Field(..., description="Original filename")
    page_count: int = Field(..., description="Total pages processed")
    extracted_text: str = Field(..., description="Extracted raw text")
    processing_status: Literal["extracted", "structured", "reviewed"] = Field(
        default="structured",
        description="'structured' if unit headings were found, 'extracted' if the text could not be split into units",
    )
    message: Optional[str] = Field(default=None, description="Note on structuring results")


class SyllabusCreateRequest(BaseModel):
    """Request payload to save a structured syllabus to MongoDB."""

    subject_name: str = Field(..., description="Course name", min_length=1)
    course_code: Optional[str] = Field(default=None, description="Course code, if known")
    course_description: Optional[str] = Field(default=None, description="Course description")
    course_outcomes: List[CourseOutcome] = Field(default_factory=list, description="Course outcomes (COs)")
    course_content: List[CourseUnit] = Field(default_factory=list, description="Units with their topics")
    filename: str = Field(..., description="Filename of original syllabus", min_length=1)
    page_count: int = Field(..., description="Page count", ge=1)
    file_size_bytes: Optional[int] = Field(default=None, description="Size of the uploaded PDF in bytes", ge=0)
    extracted_text: str = Field(..., description="Raw extracted text", min_length=5)
    processing_status: Literal["extracted", "structured", "reviewed"] = Field(
        default="reviewed",
        description="Review and processing status of this syllabus",
    )


class SyllabusUpdateRequest(BaseModel):
    """Request payload to update an existing syllabus in MongoDB."""

    subject_name: Optional[str] = Field(default=None, description="Updated course name")
    course_code: Optional[str] = Field(default=None, description="Updated course code")
    course_description: Optional[str] = Field(default=None, description="Updated course description")
    course_outcomes: Optional[List[CourseOutcome]] = Field(default=None, description="Updated course outcomes")
    course_content: Optional[List[CourseUnit]] = Field(default=None, description="Updated units and topics")
    processing_status: Optional[Literal["extracted", "structured", "reviewed"]] = Field(
        default=None,
        description="Updated processing status",
    )


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
