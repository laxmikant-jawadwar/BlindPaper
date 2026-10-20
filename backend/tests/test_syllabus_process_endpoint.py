"""
Uploading a syllabus PDF (application workflow, step 2): the PDF is extracted, structured and
stored in MongoDB under the faculty member who uploaded it. Faculty only ever see their own.
"""

from pathlib import Path

import pymupdf
import pytest
from bson import ObjectId

from app.repositories.errors import DatabaseConnectionError
from app.repositories.syllabus_repository import syllabus_repository

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


def post_pdf(client, pdf_bytes: bytes, headers=None, filename: str = "ds.pdf", **form):
    return client.post(
        "/api/syllabus/process",
        files={"file": (filename, pdf_bytes, "application/pdf")},
        data=form,
        headers=headers or {},
    )


def test_only_a_signed_in_faculty_member_can_upload_a_syllabus(client, admin):
    pdf = make_pdf(SYLLABUS_LINES)

    assert post_pdf(client, pdf).status_code == 401
    assert post_pdf(client, pdf, headers=admin["headers"]).status_code == 403


def test_process_stores_raw_text_and_the_structured_syllabus_for_the_uploader(client, faculty, fake_mongo):
    pdf_bytes = make_pdf(SYLLABUS_LINES, OUTCOME_TABLE)

    response = post_pdf(client, pdf_bytes, headers=faculty["headers"])

    assert response.status_code == 201
    body = response.json()
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

    stored = fake_mongo["blindpaper"]["syllabi"].find_one({"_id": ObjectId(body["id"])})
    assert stored["owner_id"] == faculty["user"]["id"]
    assert "Unit 1: Stacks and Queues" in stored["extracted_text"]  # the raw text is kept
    assert stored["filename"] == "ds.pdf" and stored["page_count"] == 1 and stored["file_size_bytes"] == len(pdf_bytes)
    # Only the wanted parts of the syllabus are stored
    assert not {"structured_syllabus", "objectives", "co_po_mapping", "prerequisites", "tables"} & set(stored)


def test_process_lets_the_faculty_override_the_subject_name(client, faculty):
    response = post_pdf(client, make_pdf(SYLLABUS_LINES), headers=faculty["headers"], subject_name="Advanced Data Structures")

    assert response.status_code == 201
    assert response.json()["subject_name"] == "Advanced Data Structures"


def test_process_marks_a_pdf_without_unit_headings_as_extracted(client, faculty):
    pdf_bytes = make_pdf(["Some free text about nothing in particular.", "It has no units at all."])

    response = post_pdf(client, pdf_bytes, headers=faculty["headers"], filename="free_text.pdf")

    assert response.status_code == 201
    assert response.json()["processing_status"] == "extracted"
    assert response.json()["course_content"] == []


def test_process_rejects_non_pdf_files_and_stores_nothing(client, faculty, fake_mongo):
    response = client.post(
        "/api/syllabus/process",
        files={"file": ("syllabus.txt", b"Plain text syllabus", "text/plain")},
        headers=faculty["headers"],
    )

    assert response.status_code == 400
    assert "Only PDF files (.pdf) are accepted" in response.json()["detail"]
    assert fake_mongo["blindpaper"]["syllabi"].count_documents({}) == 0


def test_process_asks_for_ocr_on_scanned_pdfs_and_stores_nothing(client, faculty, fake_mongo):
    doc = pymupdf.open()
    doc.new_page()
    blank_pdf = doc.tobytes()
    doc.close()

    response = post_pdf(client, blank_pdf, headers=faculty["headers"], filename="scan.pdf")

    assert response.status_code == 400
    assert "ocr" in response.json()["detail"].lower()
    assert fake_mongo["blindpaper"]["syllabi"].count_documents({}) == 0


def test_process_reports_503_when_mongodb_is_unavailable(client, faculty, monkeypatch):
    def refuse(_document):
        raise DatabaseConnectionError("connection refused")

    monkeypatch.setattr(syllabus_repository, "create", refuse)

    response = post_pdf(client, make_pdf(SYLLABUS_LINES), headers=faculty["headers"])

    assert response.status_code == 503
    assert "MongoDB" in response.json()["detail"]


def test_faculty_only_see_their_own_syllabi(client, faculty, other_faculty):
    mine = post_pdf(client, make_pdf(SYLLABUS_LINES), headers=faculty["headers"]).json()
    theirs = post_pdf(client, make_pdf(SYLLABUS_LINES), headers=other_faculty["headers"], subject_name="Not Mine").json()

    listed = client.get("/api/syllabus", headers=faculty["headers"]).json()
    assert [item["id"] for item in listed] == [mine["id"]]
    assert listed[0]["unit_count"] == 2

    assert client.get(f"/api/syllabus/{mine['id']}", headers=faculty["headers"]).status_code == 200
    # someone else's syllabus looks exactly like one that does not exist
    assert client.get(f"/api/syllabus/{theirs['id']}", headers=faculty["headers"]).status_code == 404
    assert client.delete(f"/api/syllabus/{theirs['id']}", headers=faculty["headers"]).status_code == 404


def test_syllabus_endpoints_need_a_login(client):
    assert client.get("/api/syllabus").status_code == 401
    assert client.get("/api/syllabus/507f1f77bcf86cd799439011").status_code == 401
    assert client.delete("/api/syllabus/507f1f77bcf86cd799439011").status_code == 401


def test_a_syllabus_can_be_deleted_by_its_owner(client, faculty):
    created = post_pdf(client, make_pdf(SYLLABUS_LINES), headers=faculty["headers"]).json()

    assert client.delete(f"/api/syllabus/{created['id']}", headers=faculty["headers"]).status_code == 200
    assert client.get(f"/api/syllabus/{created['id']}", headers=faculty["headers"]).status_code == 404


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="sample OR syllabus PDF is not present in sample/")
def test_process_stores_the_real_operations_research_syllabus(client, faculty):
    response = post_pdf(client, SAMPLE_PDF.read_bytes(), headers=faculty["headers"], filename="OR Syllabus.pdf")

    assert response.status_code == 201
    body = response.json()
    assert body["subject_name"] == "Operations Research"
    assert body["course_code"] == "UCBEM0404"
    assert [o["code"] for o in body["course_outcomes"]] == ["CO1", "CO2", "CO3", "CO4"]
    assert [(u["unit_number"], u["unit_name"]) for u in body["course_content"]] == [
        (1, "Linear Programming Problems"),
        (2, "Inventory Control"),
        (3, "Network Models"),
        (4, "Transportation and Assignment Model"),
        (5, "Queuing Theory"),
        (6, "Game Theory"),
    ]
