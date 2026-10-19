"""
Syllabus extraction service using PyMuPDF.
Responsible for reading, validating, and extracting text from uploaded syllabus PDFs.
"""

from typing import Any, Dict
import pymupdf


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


class SyllabusServiceError(Exception):
    """Base exception for syllabus processing errors."""
    pass


class EmptyFileError(SyllabusServiceError):
    """Raised when the uploaded file contains 0 bytes."""
    pass


class FileSizeLimitExceededError(SyllabusServiceError):
    """Raised when the uploaded file exceeds the 10 MB limit."""
    pass


class InvalidPDFError(SyllabusServiceError):
    """Raised when the file is not a valid or readable PDF."""
    pass


class OCRRequiredError(SyllabusServiceError):
    """Raised when the PDF has pages but contains no extractable text (e.g. scanned image)."""
    pass


class SyllabusService:
    """Service handling syllabus PDF inspection and text extraction."""

    def __init__(self, max_file_size: int = MAX_FILE_SIZE_BYTES) -> None:
        self.max_file_size = max_file_size

    def extract_text_from_pdf_bytes(
        self, file_bytes: bytes, filename: str
    ) -> Dict[str, Any]:
        """
        Validate and extract textual content from PDF byte stream.

        Args:
            file_bytes: Raw binary bytes of the PDF file.
            filename: Original filename of the uploaded PDF.

        Returns:
            Dictionary with keys: filename, page_count, extracted_text.

        Raises:
            EmptyFileError: If file_bytes is empty.
            FileSizeLimitExceededError: If file exceeds the allowed size limit.
            InvalidPDFError: If content is not a valid readable PDF.
            OCRRequiredError: If document contains no readable text.
        """
        # 1. Validate file is not empty
        if not file_bytes or len(file_bytes) == 0:
            raise EmptyFileError("The uploaded file is empty.")

        # 2. Validate file size does not exceed limit
        if len(file_bytes) > self.max_file_size:
            max_mb = self.max_file_size // (1024 * 1024)
            raise FileSizeLimitExceededError(
                f"File size exceeds the maximum allowed limit of {max_mb} MB."
            )

        # 3. Check PDF magic header (%PDF-)
        if not file_bytes.startswith(b"%PDF-"):
            raise InvalidPDFError("The file does not start with a valid PDF header.")

        # 4. Attempt opening and reading with PyMuPDF
        doc = None
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception:
            raise InvalidPDFError("The uploaded file is corrupted or not a readable PDF.")

        try:
            page_count = len(doc)
            if page_count == 0:
                raise InvalidPDFError("The PDF document contains no pages.")

            extracted_chunks = []
            for page_index in range(page_count):
                page = doc.load_page(page_index)
                page_text = page.get_text("text")
                if page_text and page_text.strip():
                    extracted_chunks.append(page_text.strip())

            full_text = "\n\n".join(extracted_chunks).strip()

            # 5. Check if document has readable text or requires OCR
            if not full_text:
                raise OCRRequiredError(
                    "No extractable text found in this PDF. It appears to be a scanned "
                    "document or image-only PDF, which requires OCR (Optical Character "
                    "Recognition) to extract text."
                )

            return {
                "filename": filename,
                "page_count": page_count,
                "extracted_text": full_text,
            }
        finally:
            if doc is not None:
                doc.close()


# Default singleton service instance
syllabus_service = SyllabusService()
