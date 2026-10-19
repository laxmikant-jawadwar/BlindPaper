from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)

SAMPLE_SYLLABUS = """
Unit 1: Stacks, Queues, and Linked Lists
Implementation, Array Representation, Applications of Stacks.

Unit 2: Trees and Binary Search Trees
Binary Tree Traversal, AVL Trees, B-Trees.

Unit 3: Sorting and Searching Algorithms
QuickSort, MergeSort, HeapSort, Binary Search.
"""


def test_valid_generation_request_demo_mode():
    """Verify that a valid generation request succeeds in demo mode."""
    # Ensure no API key is set for demo mode test
    with patch.object(settings, "llm_api_key", None), \
         patch.object(settings, "gemini_api_key", None), \
         patch.object(settings, "openai_api_key", None):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Unit 1: Stacks, Queues, and Linked Lists", "Unit 2: Trees and Binary Search Trees"],
            "total_marks": 25,
            "question_count": 5,
            "question_types": ["Short Answer", "Long Answer"],
            "difficulty": "medium",
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["subject_name"] == "Data Structures"
        assert data["generation_mode"] == "demo"
        assert data["question_count"] == 5
        assert data["total_marks"] == 25
        assert len(data["questions"]) == 5


def test_missing_or_empty_syllabus_content():
    """Verify that missing or whitespace syllabus content is rejected with 422."""
    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": "   ",
        "selected_units": ["Unit 1"],
        "total_marks": 20,
        "question_count": 4,
    }
    response = client.post("/api/questions/generate", json=payload)
    assert response.status_code == 422


def test_invalid_question_count_or_marks():
    """Verify validation for non-positive or conflicting marks/counts."""
    # Case 1: question_count = 0
    payload_zero_count = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks"],
        "total_marks": 20,
        "question_count": 0,
    }
    resp1 = client.post("/api/questions/generate", json=payload_zero_count)
    assert resp1.status_code == 422

    # Case 2: total_marks = 0
    payload_zero_marks = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks"],
        "total_marks": 0,
        "question_count": 5,
    }
    resp2 = client.post("/api/questions/generate", json=payload_zero_marks)
    assert resp2.status_code == 422

    # Case 3: total_marks < question_count (impossible to assign >= 1 mark per question)
    payload_less_marks = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks"],
        "total_marks": 3,
        "question_count": 5,
    }
    resp3 = client.post("/api/questions/generate", json=payload_less_marks)
    assert resp3.status_code == 422


def test_valid_structured_response():
    """Verify that each question returned adheres to the structured schema."""
    with patch.object(settings, "llm_api_key", None), \
         patch.object(settings, "gemini_api_key", None), \
         patch.object(settings, "openai_api_key", None):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Unit 1: Stacks", "Unit 2: Trees"],
            "total_marks": 10,
            "question_count": 2,
            "question_types": ["MCQ", "Short Answer"],
            "difficulty": "easy",
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        for q in data["questions"]:
            assert "question_id" in q and isinstance(q["question_id"], int)
            assert "question_text" in q and len(q["question_text"]) > 5
            assert "question_type" in q and q["question_type"] in ["MCQ", "Short Answer"]
            assert "unit_or_topic" in q and len(q["unit_or_topic"]) > 0
            assert "marks" in q and q["marks"] >= 1
            assert "difficulty" in q and q["difficulty"] == "easy"


def test_total_marks_consistency():
    """Verify that question marks sum up exactly to total_marks even with uneven division."""
    with patch.object(settings, "llm_api_key", None), \
         patch.object(settings, "gemini_api_key", None), \
         patch.object(settings, "openai_api_key", None):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Unit 1: Stacks", "Unit 2: Trees"],
            "total_marks": 17,
            "question_count": 4,
            "question_types": ["Short Answer"],
            "difficulty": "medium",
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        marks_sum = sum(q["marks"] for q in data["questions"])
        assert marks_sum == 17
        assert data["total_marks"] == 17
        assert len(data["questions"]) == 4


def test_demo_fallback_when_no_api_key():
    """Verify that demo fallback mode is explicitly indicated when no API key is configured."""
    with patch.object(settings, "llm_api_key", None), \
         patch.object(settings, "gemini_api_key", None), \
         patch.object(settings, "openai_api_key", None):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Unit 3: Sorting and Searching Algorithms"],
            "total_marks": 10,
            "question_count": 2,
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["generation_mode"] == "demo"
        assert "demo mode" in data["message"].lower()


def test_syllabus_mismatch_rejected():
    """Verify rejection when selected units are absent from the syllabus text."""
    with patch.object(settings, "llm_api_key", None), \
         patch.object(settings, "gemini_api_key", None), \
         patch.object(settings, "openai_api_key", None):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Quantum Electrodynamics", "Fluid Mechanics"],
            "total_marks": 10,
            "question_count": 2,
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 400
        assert "syllabus" in response.json()["detail"].lower()


def test_llm_generation_with_mocked_provider():
    """Verify that when an API key is set, LLM provider output is parsed and returned."""
    mock_gemini_output = """
    {
      "questions": [
        {
          "question_id": 1,
          "question_text": "Explain how Stacks operate using LIFO principle.",
          "question_type": "Short Answer",
          "unit_or_topic": "Unit 1: Stacks",
          "marks": 5,
          "difficulty": "medium"
        },
        {
          "question_id": 2,
          "question_text": "Describe AVL tree rotations with examples.",
          "question_type": "Long Answer",
          "unit_or_topic": "Unit 2: Trees",
          "marks": 10,
          "difficulty": "medium"
        }
      ]
    }
    """

    with patch.object(settings, "gemini_api_key", "mock_gemini_key"), \
         patch.object(settings, "llm_provider", "gemini"), \
         patch("app.services.question_service.LLMQuestionGenerator._call_gemini", return_value=mock_gemini_output):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Unit 1: Stacks", "Unit 2: Trees"],
            "total_marks": 15,
            "question_count": 2,
            "question_types": ["Short Answer", "Long Answer"],
            "difficulty": "medium",
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["generation_mode"] == "llm"
        assert len(data["questions"]) == 2
        assert data["total_marks"] == 15
        assert data["questions"][0]["question_text"] == "Explain how Stacks operate using LIFO principle."


def test_malformed_llm_response_handled():
    """Verify that malformed or broken JSON from LLM raises 502 Bad Gateway gracefully."""
    with patch.object(settings, "gemini_api_key", "mock_gemini_key"), \
         patch.object(settings, "llm_provider", "gemini"), \
         patch("app.services.question_service.LLMQuestionGenerator._call_gemini", return_value="This is plain text and not valid JSON"):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Unit 1: Stacks"],
            "total_marks": 10,
            "question_count": 2,
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 502
        assert "invalid json" in response.json()["detail"].lower()


def test_llm_provider_network_failure_handled():
    """Verify that an upstream API failure from LLM provider returns 502 Bad Gateway."""
    from app.services.question_service import LLMGenerationError

    with patch.object(settings, "gemini_api_key", "mock_gemini_key"), \
         patch.object(settings, "llm_provider", "gemini"), \
         patch("app.services.question_service.LLMQuestionGenerator._call_gemini", side_effect=LLMGenerationError("Upstream connection timeout")):

        payload = {
            "subject_name": "Data Structures",
            "syllabus_text": SAMPLE_SYLLABUS,
            "selected_units": ["Unit 1: Stacks"],
            "total_marks": 10,
            "question_count": 2,
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 502
        assert "upstream connection timeout" in response.json()["detail"].lower()
