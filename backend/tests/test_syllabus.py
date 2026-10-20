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


def test_text_is_extracted_in_visual_reading_order():
    """Table-based syllabus PDFs draw cells out of order; text must still read top to bottom."""
    doc = pymupdf.open()
    page = doc.new_page()
    # Deliberately drawn in scrambled order: contents first, headings last.
    page.insert_text((51, 300), "Beta topics are listed here")
    page.insert_text((51, 200), "Alpha topics are listed here")
    page.insert_text((83, 280), "Beta Title")
    page.insert_text((51, 280), "Unit 2")
    page.insert_text((83, 180), "Alpha Title")
    page.insert_text((51, 180), "Unit 1")
    page.insert_text((400, 180), "8 Hours")
    pdf_bytes = doc.tobytes()
    doc.close()

    response = client.post(
        "/api/syllabus/upload",
        files={"file": ("scrambled.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    text = response.json()["extracted_text"]
    positions = [
        text.index(marker)
        for marker in ("Unit 1", "Alpha Title", "Alpha topics", "Unit 2", "Beta Title", "Beta topics")
    ]
    assert positions == sorted(positions)
    # The hours cell sits on the same row as its unit heading
    heading_row = next(line for line in text.splitlines() if "Unit 1" in line)
    assert "Alpha Title" in heading_row and "8 Hours" in heading_row


def make_pdf_with_ruled_table() -> bytes:
    """A PDF whose 3x2 grid is drawn with ruling lines, like the CO tables in real syllabi."""
    doc = pymupdf.open()
    page = doc.new_page()
    cells = [["CO", "Outcome"], ["CO1", "Explain stacks and queues"], ["CO2", "Apply tree traversals"]]
    for row, texts in enumerate(cells):
        for col, text in enumerate(texts):
            x0, y0 = (50 if col == 0 else 110), 100 + row * 30  # columns share an edge
            page.draw_rect(pymupdf.Rect(x0, y0, x0 + (60 if col == 0 else 200), y0 + 30), color=(0, 0, 0), width=1)
            page.insert_text((x0 + 4, y0 + 19), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_ruled_tables_are_returned_as_rows_of_cell_text():
    from app.services.syllabus_service import syllabus_service

    result = syllabus_service.extract_text_from_pdf_bytes(make_pdf_with_ruled_table(), "grid.pdf")

    assert result["tables"] == [
        [["CO", "Outcome"], ["CO1", "Explain stacks and queues"], ["CO2", "Apply tree traversals"]]
    ]
    assert "Explain stacks and queues" in result["extracted_text"]


def test_table_extraction_failure_does_not_lose_the_text():
    from unittest.mock import patch

    from app.services.syllabus_service import syllabus_service

    with patch("app.services.syllabus_service.pdfplumber.open", side_effect=RuntimeError("boom")):
        result = syllabus_service.extract_text_from_pdf_bytes(make_pdf_with_ruled_table(), "grid.pdf")

    assert result["tables"] == []
    assert "Explain stacks and queues" in result["extracted_text"]


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
