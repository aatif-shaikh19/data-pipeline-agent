import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

VALID_TOKEN = settings.API_BEARER_TOKEN or "pipeline-guardian-secure-test-token-2026"
INVALID_TOKEN = "unauthorized-fake-token-999"


def test_invoke_no_token_returns_401():
    """Verify missing Authorization header returns HTTP 401 Unauthorized."""
    response = client.post("/agent/invoke", json={"message": "test health"})
    assert response.status_code == 401
    assert "Missing Authorization" in response.json()["detail"]


def test_invoke_invalid_token_returns_401():
    """Verify invalid Bearer token returns HTTP 401 Unauthorized."""
    response = client.post(
        "/agent/invoke",
        headers={"Authorization": f"Bearer {INVALID_TOKEN}"},
        json={"message": "test health"}
    )
    assert response.status_code == 401
    assert "Invalid or expired Bearer token" in response.json()["detail"]


@patch("app.api.routes.run_guardian_agent")
def test_invoke_valid_token_returns_200(mock_run_agent):
    """Verify valid token returns HTTP 200 with response and tool trace shape."""
    mock_run_agent.return_value = {
        "final_reply": "Checked customer_events_etl logs: found 1 deserialization error.",
        "tool_traces": [
            {
                "tool": "query_pipeline_logs_tool",
                "args": {"pipeline_name": "customer_events_etl", "limit": 10},
                "id": "call_12345"
            }
        ],
        "message_count": 3
    }

    response = client.post(
        "/agent/invoke",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        json={"message": "Why did customer_events_etl fail?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "tool_traces" in data
    assert "token_hash" in data
    assert "timestamp" in data
    assert len(data["tool_traces"]) == 1
    assert data["tool_traces"][0]["tool"] == "query_pipeline_logs_tool"


def test_invoke_rate_limiting():
    """Verify slowapi rate limiter rejects rapid repeated requests with HTTP 429."""
    hit_429 = False
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    payload = {"message": "ping"}

    # Fire 30 rapid requests to trigger default 20/minute rate limit
    with patch("app.api.routes.run_guardian_agent") as mock_run:
        mock_run.return_value = {"final_reply": "ok", "tool_traces": []}
        for _ in range(35):
            res = client.post("/agent/invoke", headers=headers, json=payload)
            if res.status_code == 429:
                hit_429 = True
                break

    assert hit_429, "Rate limiter did not return HTTP 429 on excessive rapid requests."
