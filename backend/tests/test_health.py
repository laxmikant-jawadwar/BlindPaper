from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that the root GET / endpoint returns 200 and the welcome payload."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome to the BlindPaper API" in data["message"]
    assert data["status"] == "running"
    assert data["docs_url"] == "/docs"


def test_health_endpoint():
    """Verify that GET /api/health returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "BlindPaper"
    assert data["version"] == "0.1.0"


def test_cors_headers():
    """Verify that CORS preflight/requests permit http://localhost:5173."""
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
