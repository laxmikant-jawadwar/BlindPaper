import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_sample_export_questions(count: int = 3, marks_each: int = 10) -> list[dict]:
    """Helper to generate a predictable list of question items."""
    return [
        {
            "question_id": i + 1,
            "question_text": f"Explain the fundamental algorithms and memory models for Chapter {i + 1} with practical examples.",
            "question_type": "Short Answer" if i % 2 == 0 else "Long Answer",
            "unit_or_topic": f"Unit {i + 1}: Data Architecture",
            "marks": marks_each,
            "difficulty": "medium",
        }
        for i in range(count)
    ]


# 1. Successful PDF generation
def test_successful_pdf_generation():
    questions = get_sample_export_questions(count=3, marks_each=10)
    payload = {
        "subject_name": "Data Structures",
        "questions": questions,
        "total_marks": 30,
        "question_count": 3,
        "college_name": "National Engineering College",
        "exam_name": "End Semester Examination",
        "semester": "Semester IV",
        "paper_code": "CS-402",
        "duration": "3 Hours",
        "instructions": [
            "Answer all questions carefully.",
            "Each question carries the marks indicated.",
        ],
    }

    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 200
    assert len(response.content) > 1000


# 2. Valid PDF signature and content type
def test_valid_pdf_signature_and_content_type():
    questions = get_sample_export_questions(count=2, marks_each=10)
    payload = {
        "subject_name": "Operating Systems",
        "questions": questions,
        "total_marks": 20,
        "question_count": 2,
    }

    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert response.content.startswith(b"%PDF-")


# 3. Correct download filename and response headers
def test_correct_download_headers_and_filename():
    questions = get_sample_export_questions(count=2, marks_each=5)
    payload = {
        "subject_name": "Algorithms & Complexity",
        "questions": questions,
        "total_marks": 10,
        "question_count": 2,
    }

    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 200

    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "filename=" in disposition
    assert disposition.endswith('.pdf"') or disposition.endswith(".pdf")
    assert "BlindPaper" in disposition


# 4. Missing or malformed request fields
def test_missing_or_malformed_request_fields():
    # Missing subject_name and empty questions
    payload = {
        "subject_name": "   ",
        "questions": [],
        "total_marks": 0,
        "question_count": 0,
    }
    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 422


# 5. Question-count mismatch
def test_question_count_mismatch():
    questions = get_sample_export_questions(count=3, marks_each=10)
    payload = {
        "subject_name": "Data Structures",
        "questions": questions,  # 3 questions
        "total_marks": 30,
        "question_count": 5,      # mismatch (expected 5, provided 3)
    }

    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 400
    assert "question count mismatch" in response.json()["detail"].lower()


# 6. Total-marks mismatch
def test_total_marks_mismatch():
    questions = get_sample_export_questions(count=3, marks_each=10)  # total 30 marks
    payload = {
        "subject_name": "Data Structures",
        "questions": questions,
        "total_marks": 50,       # mismatch (expected 50, provided 30)
        "question_count": 3,
    }

    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 400
    assert "total marks mismatch" in response.json()["detail"].lower()


# 7. Multiple-page PDF generation
def test_multiple_page_pdf_generation():
    # 16 detailed questions will span at least 2 pages on standard A4
    questions = [
        {
            "question_id": i + 1,
            "question_text": (
                f"Detailed examination query for Question #{i + 1}: Analyze the algorithmic complexities, "
                "worst-case time bounds, and auxiliary memory requirements when implementing modern distributed "
                "data pipelines and scalable search indices across cluster nodes."
            ),
            "question_type": "Long Answer",
            "unit_or_topic": f"Module {((i % 4) + 1)}: Distributed Architecture",
            "marks": 5,
            "difficulty": "hard",
        }
        for i in range(16)
    ]

    payload = {
        "subject_name": "Distributed Systems",
        "questions": questions,
        "total_marks": 80,
        "question_count": 16,
        "college_name": "Institute of Higher Technology",
        "exam_name": "Final Comprehensive Assessment",
    }

    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 200

    # Parse with PyMuPDF to verify multi-page pagination
    doc = pymupdf.open(stream=response.content, filetype="pdf")
    page_count = len(doc)
    doc.close()

    assert page_count >= 2


# 8. Preservation of question text, ordering, and marks
def test_preservation_of_question_content_in_pdf():
    questions = [
        {
            "question_id": 1,
            "question_text": "Verify distinct identifier Alpha for stack operations.",
            "question_type": "Short Answer",
            "unit_or_topic": "Unit 1: Stacks",
            "marks": 7,
            "difficulty": "easy",
        },
        {
            "question_id": 2,
            "question_text": "Verify distinct identifier Beta for tree traversals.",
            "question_type": "Long Answer",
            "unit_or_topic": "Unit 2: Trees",
            "marks": 13,
            "difficulty": "medium",
        },
    ]

    payload = {
        "subject_name": "Advanced Data Structures",
        "questions": questions,
        "total_marks": 20,
        "question_count": 2,
    }

    response = client.post("/api/questions/export-pdf", json=payload)
    assert response.status_code == 200

    # Extract text from the generated PDF to confirm text preservation
    doc = pymupdf.open(stream=response.content, filetype="pdf")
    full_pdf_text = "\n".join(page.get_text() for page in doc)
    doc.close()

    # Check question numbers
    assert "Q.1" in full_pdf_text
    assert "Q.2" in full_pdf_text

    # Check distinct question text
    assert "Verify distinct identifier Alpha for stack operations." in full_pdf_text
    assert "Verify distinct identifier Beta for tree traversals." in full_pdf_text

    # Check marks
    assert "[7]" in full_pdf_text
    assert "[13]" in full_pdf_text

    # Check order: Q1 appears before Q2
    idx_q1 = full_pdf_text.index("Alpha")
    idx_q2 = full_pdf_text.index("Beta")
    assert idx_q1 < idx_q2
