import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_start_interview_with_candidate(client: TestClient, candidate_repository) -> None:
    candidate = candidate_repository.get("CAND-001").model_dump(mode="json")
    response = client.post("/api/interview", json={"sessionId": "sess-1", "candidate": candidate})
    assert response.status_code == 200
    body = response.json()
    assert body["done"] is False
    assert "[dev]" in body["reply"]


def test_message_turn(client: TestClient) -> None:
    response = client.post("/api/interview", json={"sessionId": "sess-1", "message": "Hello"})
    assert response.status_code == 200
    assert response.json()["done"] is False


def test_rejects_payload_without_candidate_or_message(client: TestClient) -> None:
    response = client.post("/api/interview", json={"sessionId": "sess-1"})
    assert response.status_code == 422


def test_rejects_payload_with_both_candidate_and_message(client: TestClient, candidate_repository) -> None:
    candidate = candidate_repository.get("CAND-001").model_dump(mode="json")
    response = client.post(
        "/api/interview",
        json={"sessionId": "sess-1", "candidate": candidate, "message": "Hello"},
    )
    assert response.status_code == 422


def test_rejects_empty_session_id(client: TestClient) -> None:
    response = client.post("/api/interview", json={"sessionId": "", "message": "Hello"})
    assert response.status_code == 422


def test_health_check_endpoint_exists(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/interview" in response.json()["paths"]
