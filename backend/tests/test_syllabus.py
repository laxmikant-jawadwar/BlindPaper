"""Text and table extraction from uploaded syllabus PDFs, and the upload validation around it."""

import pymupdf

from app.services.syllabus_service import syllabus_service


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


def upload(client, headers, filename: str, content: bytes, content_type: str = "application/pdf"):
    return client.post("/api/syllabus/process", files={"file": (filename, content, content_type)}, headers=headers)


def test_valid_pdf_upload(client, faculty):
    """A valid PDF returns its extracted text and an accurate page count."""
    pages = [
        "Unit 1: Data Structures and Algorithms\nArrays, Linked Lists, Stacks",
        "Unit 2: Sorting and Searching\nQuickSort, MergeSort, Binary Search",
    ]

    response = upload(client, faculty["headers"], "syllabus.pdf", generate_pdf_bytes(pages))

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "syllabus.pdf"
    assert data["page_count"] == 2
    assert "Unit 1: Data Structures and Algorithms" in data["extracted_text"]
    assert "Unit 2: Sorting and Searching" in data["extracted_text"]


def test_text_is_extracted_in_visual_reading_order(client, faculty):
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

    response = upload(client, faculty["headers"], "scrambled.pdf", pdf_bytes)

    assert response.status_code == 201
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
    result = syllabus_service.extract_text_from_pdf_bytes(make_pdf_with_ruled_table(), "grid.pdf")

    assert result["tables"] == [
        [["CO", "Outcome"], ["CO1", "Explain stacks and queues"], ["CO2", "Apply tree traversals"]]
    ]
    assert "Explain stacks and queues" in result["extracted_text"]


def test_table_extraction_failure_does_not_lose_the_text():
    from unittest.mock import patch

    with patch("app.services.syllabus_service.pdfplumber.open", side_effect=RuntimeError("boom")):
        result = syllabus_service.extract_text_from_pdf_bytes(make_pdf_with_ruled_table(), "grid.pdf")

    assert result["tables"] == []
    assert "Explain stacks and queues" in result["extracted_text"]


def test_non_pdf_upload_rejected(client, faculty):
    """Uploading a non-PDF file (e.g., .txt) is rejected with 400."""
    response = upload(client, faculty["headers"], "syllabus.txt", b"Plain text syllabus", "text/plain")

    assert response.status_code == 400
    assert "Only PDF files (.pdf) are accepted" in response.json()["detail"]


def test_empty_file_rejected(client, faculty):
    """Uploading an empty 0-byte file is rejected with 400."""
    response = upload(client, faculty["headers"], "empty_syllabus.pdf", b"")

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_malformed_pdf_rejected(client, faculty):
    """A corrupted or malformed PDF is rejected with 400."""
    malformed_bytes = b"%PDF-1.4\nMalicious or corrupted random payload that fails parsing"

    response = upload(client, faculty["headers"], "corrupted.pdf", malformed_bytes)

    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "corrupted" in detail or "not a readable pdf" in detail


def test_scanned_pdf_no_text_response(client, faculty):
    """A PDF containing no extractable text returns a clear OCR message."""
    response = upload(client, faculty["headers"], "scanned_syllabus.pdf", generate_empty_text_pdf_bytes(page_count=2))

    assert response.status_code == 400
    assert "ocr" in response.json()["detail"].lower()


def test_oversized_file_rejected(client, faculty):
    """A file exceeding 10 MB is rejected with 413 Payload Too Large."""
    oversized_bytes = b"%PDF-" + b"0" * (10 * 1024 * 1024 + 1024)  # 10 MB + 1 KB

    response = upload(client, faculty["headers"], "huge_syllabus.pdf", oversized_bytes)

    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()
