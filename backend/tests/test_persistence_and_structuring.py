"""
Tests for syllabus structuring, Bloom's Taxonomy categorization,
and MongoDB persistence layer.
"""

from unittest.mock import MagicMock, patch
from bson import ObjectId
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.repositories.syllabus_repository import (
    DatabaseConnectionError,
    SyllabusRepository,
)
from app.services.syllabus_structuring_service import (
    SyllabusStructuringService,
    syllabus_structuring_service,
)

client = TestClient(app)

SAMPLE_STRUCTURED_DATA = {
    "subject_name": "Data Structures",
    "course_code": "CS201",
    "course_description": "Stacks, queues and trees.",
    "course_outcomes": [
        {
            "code": "CO1",
            "description": "Explain stack and queue operations.",
            "blooms_level": 2,
            "blooms_descriptor": "Understand",
        }
    ],
    "course_content": [
        {
            "unit_number": 1,
            "unit_name": "Stacks and Queues",
            "topics": ["Implement stack operations", "Explain queue mechanisms"],
        },
        {"unit_number": 2, "unit_name": "Trees", "topics": ["Design binary search tree"]},
    ],
    "filename": "dsa.pdf",
    "page_count": 2,
    "extracted_text": "Unit 1: Stacks and Queues\nImplement stack operations.\nExplain queue mechanisms.\n\nUnit 2: Trees\nDesign binary search tree.",
    "processing_status": "reviewed",
}


def test_structuring_service_reads_units_and_topics():
    """Verify the structuring service splits plain 'Unit N: Title' text into units and topics."""
    raw_text = (
        "Course: Operating Systems\n\n"
        "Unit 1: Process Management\n"
        "Explain process states and life cycles.\n"
        "Implement CPU scheduling algorithms.\n\n"
        "Unit 2: Memory Management\n"
        "Evaluate page replacement policies.\n"
        "Virtual memory basics."
    )

    result = syllabus_structuring_service.structure_syllabus_text(
        extracted_text=raw_text,
        filename="os_syllabus.pdf",
        page_count=2,
    )

    assert result["subject_name"] == "Operating Systems"
    units = result["course_content"]
    assert [(u.unit_number, u.unit_name) for u in units] == [
        (1, "Process Management"),
        (2, "Memory Management"),
    ]
    assert units[0].topics == [
        "Explain process states and life cycles",
        "Implement CPU scheduling algorithms",
    ]
    assert units[1].topics == ["Evaluate page replacement policies", "Virtual memory basics"]


def test_structure_endpoint_api():
    """Verify POST /api/syllabus/structure returns parsed units and recommendations."""
    payload = {
        "subject_name": "Database Management Systems",
        "extracted_text": (
            "Unit 1: Relational Models\n"
            "Define relational algebra.\n"
            "Design entity relationship diagrams."
        ),
        "filename": "dbms.pdf",
        "page_count": 1,
    }

    response = client.post("/api/syllabus/structure", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["subject_name"] == "Database Management Systems"
    units = data["course_content"]
    assert len(units) == 1
    assert units[0]["unit_name"] == "Relational Models"
    assert units[0]["topics"] == ["Define relational algebra", "Design entity relationship diagrams"]


def test_repository_crud_operations():
    """Verify SyllabusRepository CRUD methods using a mocked MongoDB collection."""
    mock_collection = MagicMock()
    mock_id = ObjectId()

    # Mock insert_one
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = mock_id
    mock_collection.insert_one.return_value = mock_insert_result

    repo = SyllabusRepository(collection_provider=lambda: mock_collection)

    # 1. Create
    created = repo.create(SAMPLE_STRUCTURED_DATA)
    assert created["id"] == str(mock_id)
    assert created["subject_name"] == "Data Structures"
    assert "created_at" in created
    assert "updated_at" in created

    # 2. Get by ID
    doc_to_return = dict(SAMPLE_STRUCTURED_DATA)
    doc_to_return["_id"] = mock_id
    mock_collection.find_one.return_value = doc_to_return

    retrieved = repo.get_by_id(str(mock_id))
    assert retrieved is not None
    assert retrieved["id"] == str(mock_id)
    assert retrieved["subject_name"] == "Data Structures"

    # 3. Invalid ID returns None
    assert repo.get_by_id("invalid-hex-id") is None

    # 4. Update
    updated_doc = dict(doc_to_return)
    updated_doc["subject_name"] = "Advanced Data Structures"
    mock_collection.find_one_and_update.return_value = updated_doc

    result_update = repo.update(str(mock_id), {"subject_name": "Advanced Data Structures"})
    assert result_update is not None
    assert result_update["subject_name"] == "Advanced Data Structures"

    # 5. Delete
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_delete_result
    assert repo.delete(str(mock_id)) is True


def test_syllabus_persistence_endpoints_with_mocked_repo():
    """Verify POST, GET, PUT, and DELETE /api/syllabus endpoints with mocked repository."""
    fake_id = "507f1f77bcf86cd799439011"
    doc_response = dict(SAMPLE_STRUCTURED_DATA)
    doc_response["id"] = fake_id
    doc_response["created_at"] = "2026-10-20T10:00:00Z"
    doc_response["updated_at"] = "2026-10-20T10:00:00Z"

    with patch("app.api.routes.syllabus.syllabus_repository") as mock_repo:
        mock_repo.create.return_value = doc_response
        mock_repo.list_all.return_value = [doc_response]
        mock_repo.get_by_id.return_value = doc_response
        mock_repo.update.return_value = doc_response
        mock_repo.delete.return_value = True

        # 1. POST /api/syllabus (save)
        resp = client.post("/api/syllabus", json=SAMPLE_STRUCTURED_DATA)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == fake_id

        # 2. GET /api/syllabus (list)
        resp = client.get("/api/syllabus")
        assert resp.status_code == 200
        summaries = resp.json()
        assert len(summaries) == 1
        assert summaries[0]["id"] == fake_id
        assert summaries[0]["unit_count"] == 2

        # 3. GET /api/syllabus/{id}
        resp = client.get(f"/api/syllabus/{fake_id}")
        assert resp.status_code == 200
        assert resp.json()["subject_name"] == "Data Structures"

        # 4. PUT /api/syllabus/{id}
        resp = client.put(f"/api/syllabus/{fake_id}", json={"subject_name": "Updated DSA"})
        assert resp.status_code == 200

        # 5. DELETE /api/syllabus/{id}
        resp = client.delete(f"/api/syllabus/{fake_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


def test_question_generation_with_syllabus_id():
    """Verify question generation works when syllabus_id is passed and resolved from DB."""
    fake_id = "507f1f77bcf86cd799439011"
    saved_doc = {
        "id": fake_id,
        "subject_name": "Computer Networks",
        "extracted_text": (
            "Unit 1: OSI Model and TCP/IP\n"
            "Layers, Protocols, Packets, Routing.\n\n"
            "Unit 2: Data Link Layer\n"
            "Framing, Error Detection, Flow Control."
        ),
    }

    with patch("app.repositories.syllabus_repository.syllabus_repository.get_by_id", return_value=saved_doc):
        payload = {
            "subject_name": "Computer Networks",
            "syllabus_id": fake_id,
            "selected_units": ["Unit 1: OSI Model and TCP/IP"],
            "total_marks": 20,
            "question_count": 4,
            "question_types": ["Short Answer", "Long Answer"],
            "difficulty": "medium",
        }

        response = client.post("/api/questions/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["subject_name"] == "Computer Networks"
        assert len(data["questions"]) == 4
        assert data["total_marks"] == 20
        # Verify blooms_level is assigned
        for q in data["questions"]:
            assert q.get("blooms_level") is not None
