import copy
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.question import QuestionItem
from app.services.validation_service import validation_service

client = TestClient(app)

SAMPLE_SYLLABUS = """
Unit 1: Stacks and Queues
Implementation using arrays and linked lists, LIFO principle, FIFO principle, circular queues.

Unit 2: Trees and Binary Search Trees
Binary tree traversals (inorder, preorder, postorder), AVL trees, balancing factors, binary heap.

Unit 3: Graph Algorithms
Breadth-first search (BFS), Depth-first search (DFS), Dijkstra's shortest path algorithm.
"""


def get_valid_sample_questions() -> list[dict]:
    return [
        {
            "question_id": 1,
            "question_text": "Explain the implementation of circular queues using arrays.",
            "question_type": "Short Answer",
            "unit_or_topic": "Unit 1: Stacks and Queues",
            "marks": 5,
            "difficulty": "medium",
        },
        {
            "question_id": 2,
            "question_text": "Describe binary tree traversals including inorder, preorder, and postorder methods.",
            "question_type": "Long Answer",
            "unit_or_topic": "Unit 2: Trees and Binary Search Trees",
            "marks": 10,
            "difficulty": "medium",
        },
        {
            "question_id": 3,
            "question_text": "Compare Breadth-First Search (BFS) and Depth-First Search (DFS) graph algorithms.",
            "question_type": "Short Answer",
            "unit_or_topic": "Unit 3: Graph Algorithms",
            "marks": 5,
            "difficulty": "medium",
        },
    ]


# 1. Valid paper that passes all checks
def test_valid_paper_passes_all_checks():
    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": [
            "Unit 1: Stacks and Queues",
            "Unit 2: Trees and Binary Search Trees",
            "Unit 3: Graph Algorithms",
        ],
        "questions": get_valid_sample_questions(),
        "total_marks": 20,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "pass"
    assert data["marks_validation"]["is_valid"] is True
    assert data["unit_coverage"]["coverage_percentage"] == 100.0
    assert len(data["duplicate_pairs"]) == 0
    assert len(data["issues"]) == 0
    assert len(data["warnings"]) == 0


# 2. Exact duplicate question detection
def test_exact_duplicate_detection():
    questions = get_valid_sample_questions()
    # Duplicate Q1 as Q3
    questions[2]["question_text"] = "Explain the implementation of circular queues using arrays."

    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks and Queues", "Unit 2: Trees and Binary Search Trees"],
        "questions": questions,
        "total_marks": 20,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "review_required"
    assert len(data["duplicate_pairs"]) >= 1
    dup = data["duplicate_pairs"][0]
    assert dup["match_type"] == "exact"
    assert dup["similarity_score"] == 1.0


# 3. Near-duplicate question detection
def test_near_duplicate_detection():
    questions = get_valid_sample_questions()
    # Slight rephrasing of circular queues question
    questions[2]["question_text"] = "Explain the array implementation and working of circular queues."

    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks and Queues", "Unit 2: Trees and Binary Search Trees"],
        "questions": questions,
        "total_marks": 20,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "review_required"
    near_dups = [d for d in data["duplicate_pairs"] if d["match_type"] == "near_duplicate"]
    assert len(near_dups) >= 1
    assert near_dups[0]["similarity_score"] >= 0.70


# 4. Potentially out-of-syllabus question
def test_out_of_syllabus_question():
    questions = get_valid_sample_questions()
    # Nuclear physics question in data structures exam
    questions[0]["question_text"] = "Explain how nuclear fission produces thermal energy inside pressurized water reactors."
    questions[0]["unit_or_topic"] = "Nuclear Physics"

    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": [
            "Unit 1: Stacks and Queues",
            "Unit 2: Trees and Binary Search Trees",
            "Unit 3: Graph Algorithms",
        ],
        "questions": questions,
        "total_marks": 20,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "review_required"
    q1_relevance = next(r for r in data["relevance_results"] if r["question_id"] == 1)
    assert q1_relevance["status"] == "low"
    assert q1_relevance["relevance_score"] < 0.20


# 5. Uncertain relevance case requiring faculty review
def test_uncertain_relevance_review_required():
    questions = get_valid_sample_questions()
    # Question with only a vague generic keyword overlap
    questions[0]["question_text"] = "Discuss the general historical evolution of software arrays and systems."
    questions[0]["unit_or_topic"] = "General Topics"

    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": [
            "Unit 1: Stacks and Queues",
            "Unit 2: Trees and Binary Search Trees",
            "Unit 3: Graph Algorithms",
        ],
        "questions": questions,
        "total_marks": 20,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    q1_rel = next(r for r in data["relevance_results"] if r["question_id"] == 1)
    assert q1_rel["status"] in ["review_required", "low"]
    assert any("Question #1" in w for w in data["warnings"])


# 6. Incorrect total marks
def test_incorrect_total_marks():
    questions = get_valid_sample_questions()
    # Total sum of questions is 20 (5 + 10 + 5), but request specifies 30 marks
    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks and Queues"],
        "questions": questions,
        "total_marks": 30,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "fail"
    assert data["marks_validation"]["is_valid"] is False
    assert any("marks mismatch" in issue.lower() for issue in data["issues"])


# 7. Incorrect question count
def test_incorrect_question_count():
    questions = get_valid_sample_questions()  # 3 questions
    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks and Queues"],
        "questions": questions,
        "total_marks": 20,
        "question_count": 5,  # Expected 5, provided 3
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "fail"
    assert data["marks_validation"]["is_valid"] is False
    assert any("question count mismatch" in issue.lower() for issue in data["issues"])


# 8. Selected unit with no questions
def test_selected_unit_with_no_questions():
    questions = get_valid_sample_questions()
    # Questions only cover Units 1, 2, 3. Faculty selected an extra unit:
    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS + "\nUnit 4: Dynamic Programming\nMemoization and Tabulation",
        "selected_units": [
            "Unit 1: Stacks and Queues",
            "Unit 2: Trees and Binary Search Trees",
            "Unit 3: Graph Algorithms",
            "Unit 4: Dynamic Programming",
        ],
        "questions": questions,
        "total_marks": 20,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "review_required"
    assert "Unit 4: Dynamic Programming" in data["unit_coverage"]["uncovered_units"]
    assert data["unit_coverage"]["coverage_percentage"] == 75.0
    assert any("Unit 4" in warning for warning in data["warnings"])


# 9. Missing or malformed question fields
def test_malformed_question_fields_rejected():
    questions = get_valid_sample_questions()
    # Mark is 0 (invalid)
    questions[0]["marks"] = 0

    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks and Queues"],
        "questions": questions,
        "total_marks": 20,
        "question_count": 3,
    }

    response = client.post("/api/questions/validate", json=payload)
    # Pydantic QuestionItem schema requires ge=1 for marks
    assert response.status_code == 422


# 10. Empty or invalid validation request
def test_empty_or_invalid_validation_request():
    # Empty questions list
    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1"],
        "questions": [],
        "total_marks": 20,
        "question_count": 3,
    }
    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 422


# 11. Paper containing multiple simultaneous validation issues
def test_multiple_simultaneous_issues():
    questions = get_valid_sample_questions()
    # Issue 1: Out of syllabus question
    questions[0]["question_text"] = "Explain cellular mitosis and DNA replication in genetics."
    questions[0]["unit_or_topic"] = "Genetics"

    # Issue 2 & 3: Marks and count mismatch
    payload = {
        "subject_name": "Data Structures",
        "syllabus_text": SAMPLE_SYLLABUS,
        "selected_units": ["Unit 1: Stacks and Queues", "Unit 2: Trees and Binary Search Trees"],
        "questions": questions,  # 3 questions summing to 20 marks
        "total_marks": 50,       # Mismatch
        "question_count": 8,     # Mismatch
    }

    response = client.post("/api/questions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "fail"
    assert len(data["issues"]) >= 2
    assert len(data["warnings"]) >= 1


# 12. Preservation of original questions during validation
def test_preservation_of_original_questions():
    original_questions = [
        QuestionItem(
            question_id=1,
            question_text="Explain the implementation of circular queues using arrays.",
            question_type="Short Answer",
            unit_or_topic="Unit 1: Stacks and Queues",
            marks=5,
            difficulty="medium",
        ),
        QuestionItem(
            question_id=2,
            question_text="Describe binary tree traversals including inorder, preorder, and postorder methods.",
            question_type="Long Answer",
            unit_or_topic="Unit 2: Trees and Binary Search Trees",
            marks=10,
            difficulty="medium",
        ),
    ]

    questions_copy = copy.deepcopy(original_questions)

    from app.schemas.validation import ValidationRequest
    request = ValidationRequest(
        subject_name="Data Structures",
        syllabus_text=SAMPLE_SYLLABUS,
        selected_units=["Unit 1: Stacks and Queues", "Unit 2: Trees and Binary Search Trees"],
        questions=questions_copy,
        total_marks=15,
        question_count=2,
    )

    response = validation_service.validate_paper(request)
    assert response.overall_status == "pass"

    # Verify input questions list and each object were not mutated
    assert len(questions_copy) == len(original_questions)
    for orig, current in zip(original_questions, questions_copy):
        assert orig.question_id == current.question_id
        assert orig.question_text == current.question_text
        assert orig.marks == current.marks
        assert orig.unit_or_topic == current.unit_or_topic
