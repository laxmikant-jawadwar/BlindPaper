"""
Shared test setup: every test runs against an in-memory MongoDB (mongomock), so the suite
needs neither a running MongoDB nor any network access.
"""

import mongomock
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.database import mongodb
from app.main import app
from app.repositories.syllabus_repository import syllabus_repository
from app.services.paper_generation_service import paper_generation_service
from tests.groq_fake import FakeGroq, completion, valid_questions
from tests.paper_helpers import SYLLABUS

ADMIN_EMAIL = "admin@blindpaper.test"
ADMIN_PASSWORD = "Admin@12345"


@pytest.fixture(autouse=True)
def fake_mongo(monkeypatch):
    """Point the app's MongoDB client at a fresh in-memory database for each test."""
    client = mongomock.MongoClient()
    monkeypatch.setattr(mongodb, "_client", client)
    return client


@pytest.fixture(autouse=True)
def test_settings(monkeypatch):
    """Deterministic admin account and no real Groq calls unless a test opts in."""
    monkeypatch.setattr(settings, "admin_email", ADMIN_EMAIL)
    monkeypatch.setattr(settings, "admin_password", ADMIN_PASSWORD)
    monkeypatch.setattr(settings, "admin_name", "Admin")
    monkeypatch.setattr(settings, "groq_api_key", "test-key")


@pytest.fixture
def client(fake_mongo, test_settings):
    """A test client whose startup hook has run (this seeds the admin account)."""
    with TestClient(app) as test_client:
        yield test_client


def register_faculty(client, email="prof.a@college.edu", name="Prof. A", department="Computer Science", password="secret123"):
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password, "department": department},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faculty(client):
    """A registered faculty member: {'token', 'user', 'headers'}."""
    data = register_faculty(client)
    return {**data, "headers": auth_header(data["token"])}


@pytest.fixture
def other_faculty(client):
    data = register_faculty(client, email="prof.b@college.edu", name="Prof. B", department="Mechanical")
    return {**data, "headers": auth_header(data["token"])}


@pytest.fixture
def admin(client):
    response = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 200, response.text
    data = response.json()
    return {**data, "headers": auth_header(data["token"])}


@pytest.fixture
def groq(monkeypatch):
    """Groq stand-in plugged into the real generation service; by default it answers with one valid paper."""
    fake = FakeGroq(completion(valid_questions()))
    monkeypatch.setattr(paper_generation_service, "_client_factory", fake.client_factory)
    return fake


def store_syllabus(owner: dict, **overrides) -> str:
    """Put the sample Operations Research syllabus in MongoDB for this faculty member; returns its id."""
    document = {key: value for key, value in SYLLABUS.items() if key != "id"}
    document.update({"owner_id": owner["user"]["id"], "processing_status": "structured", "filename": "OR Syllabus.pdf", "page_count": 2})
    document.update(overrides)
    return syllabus_repository.create(document)["id"]
