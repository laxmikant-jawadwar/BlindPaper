from typing import List, Literal, Optional
from pydantic import BaseModel, Field


BLOOMS_LEVELS = [
    "Remember",
    "Understand",
    "Apply",
    "Analyze",
    "Evaluate",
    "Create",
]


class TopicStructure(BaseModel):
    """Structured topic inside a syllabus unit."""

    topic_name: str = Field(..., description="Name or title of the topic", min_length=1)
    subtopics: List[str] = Field(default_factory=list, description="Subtopics or detailed sub-points")
    blooms_levels: List[str] = Field(
        default=["Understand"],
        description="Suggested or confirmed Bloom's Taxonomy cognitive levels",
    )
    blooms_confidence: Literal["inferred", "confirmed", "needs_review"] = Field(
        default="inferred",
        description="Confidence status of the assigned Bloom's Taxonomy classification",
    )


class UnitStructure(BaseModel):
    """Structured unit or module inside the syllabus."""

    unit_name: str = Field(..., description="Title or label of the unit (e.g., 'Unit 1: Stacks')")
    topics: List[TopicStructure] = Field(default_factory=list, description="List of topics in this unit")


class StructuredSyllabus(BaseModel):
    """Container for the structured units and topics of a syllabus."""

    units: List[UnitStructure] = Field(default_factory=list, description="Units or modules in the syllabus")


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
    """Response containing parsed units, topics, and suggested Bloom's levels."""

    subject_name: str = Field(..., description="Identified or provided subject name")
    filename: str = Field(..., description="Original filename")
    page_count: int = Field(..., description="Total pages processed")
    extracted_text: str = Field(..., description="Extracted raw text")
    structured_syllabus: StructuredSyllabus = Field(..., description="Structured syllabus breakdown")
    message: Optional[str] = Field(default=None, description="Note on structuring results")


class SyllabusCreateRequest(BaseModel):
    """Request payload to save confirmed structured syllabus to MongoDB."""

    subject_name: str = Field(..., description="Confirmed subject name", min_length=1)
    filename: str = Field(..., description="Filename of original syllabus", min_length=1)
    page_count: int = Field(..., description="Page count", ge=1)
    extracted_text: str = Field(..., description="Raw extracted text", min_length=5)
    structured_syllabus: StructuredSyllabus = Field(..., description="Confirmed structured units and topics")
    processing_status: Literal["extracted", "structured", "reviewed"] = Field(
        default="reviewed",
        description="Review and processing status of this syllabus",
    )


class SyllabusUpdateRequest(BaseModel):
    """Request payload to update an existing syllabus in MongoDB."""

    subject_name: Optional[str] = Field(default=None, description="Updated subject name")
    structured_syllabus: Optional[StructuredSyllabus] = Field(default=None, description="Updated structured syllabus")
    processing_status: Optional[Literal["extracted", "structured", "reviewed"]] = Field(
        default=None,
        description="Updated processing status",
    )


class SyllabusDocumentResponse(BaseModel):
    """Full syllabus document returned from MongoDB."""

    id: str = Field(..., description="Unique MongoDB string ID")
    subject_name: str = Field(..., description="Course/subject name")
    filename: str = Field(..., description="Original PDF filename")
    page_count: int = Field(..., description="Total pages in the PDF")
    extracted_text: str = Field(..., description="Raw extracted text")
    structured_syllabus: StructuredSyllabus = Field(..., description="Structured syllabus hierarchy")
    processing_status: str = Field(..., description="Status (e.g., 'reviewed')")
    created_at: str = Field(..., description="ISO UTC timestamp of creation")
    updated_at: str = Field(..., description="ISO UTC timestamp of last update")


class SyllabusSummaryResponse(BaseModel):
    """Summary item for listing saved syllabi on the faculty dashboard."""

    id: str = Field(..., description="Unique MongoDB string ID")
    subject_name: str = Field(..., description="Course/subject name")
    filename: str = Field(..., description="Original PDF filename")
    page_count: int = Field(..., description="Total pages in PDF")
    unit_count: int = Field(..., description="Number of units in this syllabus")
    processing_status: str = Field(..., description="Status")
    created_at: str = Field(..., description="Creation date/time")
    updated_at: str = Field(..., description="Last updated date/time")
