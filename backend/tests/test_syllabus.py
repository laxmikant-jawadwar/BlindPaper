import io
import pymupdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def generate_pdf_bytes(pages: list[str]) -> bytes:
    """Helper to generate a valid PDF byte string with given page text contents."""
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_empty_text_pdf_bytes(page_count: int = 2) -> bytes:
    """Helper to generate a PDF with blank pages (no extractable text)."""
    doc = pymupdf.open()
    for _ in range(page_count):
        doc.new_page()  # Blank page without text
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_valid_pdf_upload():
    """Verify that a valid PDF returns extracted text and accurate page count."""
    pages = [
        "Unit 1: Data Structures and Algorithms\nArrays, Linked Lists, Stacks",
        "Unit 2: Sorting and Searching\nQuickSort, MergeSort, Binary Search",
    ]
    pdf_bytes = generate_pdf_bytes(pages)

    response = client.post(
        "/api/syllabus/upload",
        files={"file": ("syllabus.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "syllabus.pdf"
    assert data["page_count"] == 2
    assert "Unit 1: Data Structures and Algorithms" in data["extracted_text"]
    assert "Unit 2: Sorting and Searching" in data["extracted_text"]


def test_non_pdf_upload_rejected():
    """Verify that uploading a non-PDF file (e.g., .txt) is rejected with 400."""
    response = client.post(
        "/api/syllabus/upload",
        files={"file": ("syllabus.txt", b"Plain text syllabus", "text/plain")},
    )
    assert response.status_code == 400
    assert "Only PDF files (.pdf) are accepted" in response.json()["detail"]


def test_empty_file_rejected():
    """Verify that uploading an empty 0-byte file is rejected with 400."""
    response = client.post(
        "/api/syllabus/upload",
        files={"file": ("empty_syllabus.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_malformed_pdf_rejected():
    """Verify that a corrupted or malformed PDF is rejected with 400."""
    malformed_bytes = b"%PDF-1.4\nMalicious or corrupted random payload that fails parsing"
    response = client.post(
        "/api/syllabus/upload",
        files={"file": ("corrupted.pdf", malformed_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "not a readable pdf" in response.json()["detail"].lower()


def test_scanned_pdf_no_text_response():
    """Verify that a PDF containing no extractable text returns a clear OCR message."""
    pdf_bytes = generate_empty_text_pdf_bytes(page_count=2)

    response = client.post(
        "/api/syllabus/upload",
        files={"file": ("scanned_syllabus.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "ocr" in detail.lower()


def test_oversized_file_rejected():
    """Verify that a file exceeding 10 MB is rejected with 413 Payload Too Large."""
    # 10 MB + 1 KB
    oversized_bytes = b"%PDF-" + b"0" * (10 * 1024 * 1024 + 1024)
    response = client.post(
        "/api/syllabus/upload",
        files={"file": ("huge_syllabus.pdf", oversized_bytes, "application/pdf")},
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()
