from fastapi.testclient import TestClient

from app.core.config import settings
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
    assert data["version"] == settings.app_version
    assert data["database"] == "connected"  # the in-memory test database answers the ping


def test_cors_lets_the_browser_read_the_download_name_and_the_retry_delay():
    """Without this, the browser hides Content-Disposition (PDF file name) and Retry-After (rate limit wait)."""
    response = client.get("/", headers={"Origin": "http://localhost:5173"})

    exposed = response.headers.get("access-control-expose-headers", "").lower()
    assert "content-disposition" in exposed and "retry-after" in exposed


def test_cors_headers():
    """Verify that CORS preflight/requests permit http://localhost:5173."""
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
