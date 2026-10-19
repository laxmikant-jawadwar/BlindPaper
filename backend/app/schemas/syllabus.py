from typing import Optional
from pydantic import BaseModel, Field


class SyllabusExtractResponse(BaseModel):
    """Schema for syllabus PDF text extraction response."""

    filename: str = Field(..., description="Original name of the uploaded syllabus file")
    page_count: int = Field(..., description="Total number of pages processed in the PDF")
    extracted_text: str = Field(..., description="Full text extracted from all pages of the syllabus")
    message: Optional[str] = Field(
        default=None,
        description="Optional status or informational note about the extraction",
    )
