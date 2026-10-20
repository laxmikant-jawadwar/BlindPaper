"""
POST /api/syllabus/process: upload a PDF, extract its text and tables, structure it and store
both representations in MongoDB (application flow, steps 1-4).
"""

from pathlib import Path
from unittest.mock import patch

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.syllabus_repository import DatabaseConnectionError

client = TestClient(app)

FAKE_ID = "507f1f77bcf86cd799439011"
SAMPLE_PDF = Path(__file__).resolve().parents[2] / "sample" / "OR Syllabus.pdf"

SYLLABUS_LINES = [
    "Title of the Course: Data Structures",
    "Course Code: CS201",
    "Course Description: Stacks, queues and trees for beginners",
    "Course Contents:",
    "Unit 1: Stacks and Queues 6 Hours",
    "Introduction to stacks, Queue operations",
    "Unit 2: Trees 8 Hours",
    "Binary trees, Tree traversals",
]

# header row + one outcome, drawn as a ruled table under the text
OUTCOME_TABLE = [
    ["CO", "Outcome", "Level", "Descriptor"],
    ["CO1", "Explain stack operations", "II", "Understand"],
]


def make_pdf(lines: list[str], table: list[list[str]] | None = None) -> bytes:
    """Page layout like a real syllabus: the outcome table first, the text sections below it."""
    doc = pymupdf.open()
    page = doc.new_page()

    widths = [40, 180, 50, 80]
    top = 60
    for row, cells in enumerate(table or []):
        x = 50
        for width, text in zip(widths, cells):
            page.draw_rect(pymupdf.Rect(x, top + row * 24, x + width, top + (row + 1) * 24), color=(0, 0, 0), width=1)
            page.insert_text((x + 3, top + row * 24 + 16), text, fontsize=8)
            x += width

    y = top + 24 * len(table or []) + 40
    for line in lines:
        page.insert_text((50, y), line)
        y += 18

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def stored_like_mongo(document: dict) -> dict:
    """What SyllabusRepository.create returns: the document plus id and timestamps."""
    return {
        **document,
        "id": FAKE_ID,
        "created_at": "2026-10-20T10:00:00+00:00",
        "updated_at": "2026-10-20T10:00:00+00:00",
    }


def post_pdf(pdf_bytes: bytes, filename: str = "ds.pdf", **form):
    return client.post(
        "/api/syllabus/process",
        files={"file": (filename, pdf_bytes, "application/pdf")},
        data=form,
    )


def test_process_stores_raw_text_and_the_structured_syllabus_and_returns_the_id():
    pdf_bytes = make_pdf(SYLLABUS_LINES, OUTCOME_TABLE)

    with patch("app.api.routes.syllabus.syllabus_repository") as repo:
        repo.create.side_effect = stored_like_mongo
        response = post_pdf(pdf_bytes)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == FAKE_ID
    assert body["subject_name"] == "Data Structures"
    assert body["course_code"] == "CS201"
    assert body["course_description"] == "Stacks, queues and trees for beginners"
    assert body["course_outcomes"] == [
        {"code": "CO1", "description": "Explain stack operations", "blooms_level": 2, "blooms_descriptor": "Understand"}
    ]
    assert body["course_content"] == [
        {"unit_number": 1, "unit_name": "Stacks and Queues", "topics": ["Introduction to stacks", "Queue operations"]},
        {"unit_number": 2, "unit_name": "Trees", "topics": ["Binary trees", "Tree traversals"]},
    ]
    assert body["processing_status"] == "structured"

    stored = repo.create.call_args.args[0]
    assert "Unit 1: Stacks and Queues" in stored["extracted_text"]  # raw text is kept
    assert stored["course_content"][0]["topics"] == ["Introduction to stacks", "Queue operations"]  # plain dicts
    assert stored["course_outcomes"][0]["code"] == "CO1"
    assert stored["filename"] == "ds.pdf"
    assert stored["page_count"] == 1
    assert stored["file_size_bytes"] == len(pdf_bytes)
    assert stored["processing_status"] == "structured"
    # Only the wanted parts of the syllabus are stored
    assert not {"structured_syllabus", "objectives", "co_po_mapping", "prerequisites", "tables"} & set(stored)


def test_process_lets_the_faculty_override_the_subject_name():
    with patch("app.api.routes.syllabus.syllabus_repository") as repo:
        repo.create.side_effect = stored_like_mongo
        response = post_pdf(make_pdf(SYLLABUS_LINES), subject_name="Advanced Data Structures")

    assert response.status_code == 201
    assert response.json()["subject_name"] == "Advanced Data Structures"
    assert repo.create.call_args.args[0]["subject_name"] == "Advanced Data Structures"


def test_process_marks_a_pdf_without_unit_headings_as_extracted():
    pdf_bytes = make_pdf(["Some free text about nothing in particular.", "It has no units at all."])

    with patch("app.api.routes.syllabus.syllabus_repository") as repo:
        repo.create.side_effect = stored_like_mongo
        response = post_pdf(pdf_bytes, filename="free_text.pdf")

    assert response.status_code == 201
    assert response.json()["processing_status"] == "extracted"
    assert response.json()["course_content"] == []
    assert repo.create.call_args.args[0]["processing_status"] == "extracted"


def test_process_rejects_non_pdf_files_without_touching_the_database():
    with patch("app.api.routes.syllabus.syllabus_repository") as repo:
        response = client.post(
            "/api/syllabus/process",
            files={"file": ("syllabus.txt", b"Plain text syllabus", "text/plain")},
        )

    assert response.status_code == 400
    assert "Only PDF files (.pdf) are accepted" in response.json()["detail"]
    repo.create.assert_not_called()


def test_process_asks_for_ocr_on_scanned_pdfs_and_stores_nothing():
    doc = pymupdf.open()
    doc.new_page()
    blank_pdf = doc.tobytes()
    doc.close()

    with patch("app.api.routes.syllabus.syllabus_repository") as repo:
        response = post_pdf(blank_pdf, filename="scan.pdf")

    assert response.status_code == 400
    assert "ocr" in response.json()["detail"].lower()
    repo.create.assert_not_called()


def test_process_reports_503_when_mongodb_is_unavailable():
    with patch("app.api.routes.syllabus.syllabus_repository") as repo:
        repo.create.side_effect = DatabaseConnectionError("connection refused")
        response = post_pdf(make_pdf(SYLLABUS_LINES))

    assert response.status_code == 503
    assert "MongoDB" in response.json()["detail"]


def test_structure_endpoint_returns_the_same_shape():
    response = client.post(
        "/api/syllabus/structure",
        json={"extracted_text": "\n".join(SYLLABUS_LINES), "filename": "ds.pdf", "page_count": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["subject_name"] == "Data Structures"
    assert body["course_code"] == "CS201"
    assert body["course_description"] == "Stacks, queues and trees for beginners"
    assert [(u["unit_number"], u["unit_name"]) for u in body["course_content"]] == [(1, "Stacks and Queues"), (2, "Trees")]
    assert body["processing_status"] == "structured"


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="sample OR syllabus PDF is not present in sample/")
def test_process_stores_the_real_operations_research_syllabus():
    with patch("app.api.routes.syllabus.syllabus_repository") as repo:
        repo.create.side_effect = stored_like_mongo
        response = post_pdf(SAMPLE_PDF.read_bytes(), filename="OR Syllabus.pdf")

    assert response.status_code == 201
    stored = repo.create.call_args.args[0]
    assert stored["subject_name"] == "Operations Research"
    assert stored["course_code"] == "UCBEM0404"
    assert [o["code"] for o in stored["course_outcomes"]] == ["CO1", "CO2", "CO3", "CO4"]
    assert [(u["unit_number"], u["unit_name"]) for u in stored["course_content"]] == [
        (1, "Linear Programming Problems"),
        (2, "Inventory Control"),
        (3, "Network Models"),
        (4, "Transportation and Assignment Model"),
        (5, "Queuing Theory"),
        (6, "Game Theory"),
    ]
