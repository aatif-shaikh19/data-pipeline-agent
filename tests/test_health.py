from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that GET / returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Pipeline Guardian"
    assert response.json()["status"] == "online"


def test_health_endpoint():
    """Verify that GET /health returns HTTP 200 with {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
