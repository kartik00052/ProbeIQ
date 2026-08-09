from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

STRONG_ANSWER = (
    "I would design this in three layers: an ingestion pipeline that normalizes "
    "documents into retrieval-friendly chunks with metadata, a vector index with "
    "hybrid retrieval that fuses dense and sparse signals, and a generation step "
    "that is grounded strictly in the retrieved context. The main trade-off is "
    "recall versus latency, so I would benchmark chunk size and index layout "
    "before locking the design."
)

TEST_PASSWORD = "S3cure!Pass123"


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register(client: TestClient, prefix: str = "interview") -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": _unique_email(prefix), "password": TEST_PASSWORD},
    )
    assert response.status_code == 201


@pytest.fixture(scope="module")
def client() -> TestClient:
    test_client = TestClient(app)
    _register(test_client)
    return test_client


class _Ids:
    counter = 0

    @classmethod
    def next(cls) -> str:
        cls.counter += 1
        return f"api-sess-{cls.counter}"


def _start(client: TestClient, candidate_repository) -> str:
    session_id = _Ids.next()
    candidate = candidate_repository.get("CAND-001").model_dump(mode="json")
    response = client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})
    assert response.status_code == 200
    return session_id


def _answer_until_done(client: TestClient, session_id: str, cap: int = 20) -> dict:
    last: dict | None = None
    for _ in range(cap):
        last = client.post("/api/interview", json={"sessionId": session_id, "message": STRONG_ANSWER}).json()
        if last["done"]:
            return last
    assert last is not None
    return last


def test_start_interview_asks_first_question(client: TestClient, candidate_repository) -> None:
    session_id = _start(client, candidate_repository)
    body = client.post("/api/interview", json={"sessionId": session_id, "message": "Yes"}).json()
    assert body["done"] is False
    assert "[dev-template]" in body["reply"]


def test_message_turn_advances_session(client: TestClient, candidate_repository) -> None:
    session_id = _start(client, candidate_repository)
    first = client.post("/api/interview", json={"sessionId": session_id, "message": "Yes"}).json()
    second = client.post("/api/interview", json={"sessionId": session_id, "message": "Yes"}).json()
    assert first["done"] is False
    assert second["done"] is False
    assert first["reply"] != second["reply"]


def test_full_interview_completes_with_feedback(client: TestClient, candidate_repository) -> None:
    session_id = _start(client, candidate_repository)
    last = _answer_until_done(client, session_id)
    assert last["done"] is True
    assert last["reply"] == "Interview completed."
    assert last["feedback"] is not None
    assert last["feedback"]["summary"].startswith("Interview complete:")


def test_unknown_session_turn_rejected(client: TestClient) -> None:
    response = client.post("/api/interview", json={"sessionId": "does-not-exist", "message": "Hello"})
    assert response.status_code == 404
    assert response.json()["error"] == "session_not_found"


def test_duplicate_start_rejected(client: TestClient, candidate_repository) -> None:
    session_id = _Ids.next()
    candidate = candidate_repository.get("CAND-001").model_dump(mode="json")
    first = client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})
    assert first.status_code == 200
    duplicate = client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "session_already_exists"


def test_completed_session_rejects_answer(client: TestClient, candidate_repository) -> None:
    session_id = _start(client, candidate_repository)
    _answer_until_done(client, session_id)
    response = client.post("/api/interview", json={"sessionId": session_id, "message": "one more"})
    assert response.status_code == 400
    assert response.json()["error"] == "session_completed"


def test_empty_message_rejected(client: TestClient, candidate_repository) -> None:
    session_id = _start(client, candidate_repository)
    empty = client.post("/api/interview", json={"sessionId": session_id, "message": ""})
    assert empty.status_code == 400
    assert empty.json()["error"] == "invalid_request"
    whitespace = client.post("/api/interview", json={"sessionId": session_id, "message": "   "})
    assert whitespace.status_code == 400
    assert whitespace.json()["error"] == "invalid_request"


def test_rejects_payload_without_candidate_or_message(client: TestClient) -> None:
    response = client.post("/api/interview", json={"sessionId": "sess-x"})
    assert response.status_code == 422


def test_rejects_payload_with_both_candidate_and_message(client: TestClient, candidate_repository) -> None:
    candidate = candidate_repository.get("CAND-001").model_dump(mode="json")
    response = client.post(
        "/api/interview",
        json={"sessionId": "sess-y", "candidate": candidate, "message": "Hello"},
    )
    assert response.status_code == 422


def test_rejects_empty_session_id(client: TestClient) -> None:
    response = client.post("/api/interview", json={"sessionId": "", "message": "Hello"})
    assert response.status_code == 422


def test_health_check_endpoint_exists(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/interview" in response.json()["paths"]


def test_cors_allows_configured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/interview",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_denies_unlisted_origin(client: TestClient) -> None:
    response = client.options(
        "/api/interview",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None


def test_register_response_never_exposes_password_or_hash(client: TestClient) -> None:
    email = _unique_email("no-leak")
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"id", "email"}
    assert "password" not in body
    assert "password_hash" not in body
    assert "hash" not in body
    assert body["email"] == email


def test_unauthenticated_start_rejected() -> None:
    anonymous = TestClient(app)
    response = anonymous.post(
        "/api/interview",
        json={
            "sessionId": "unauth-start",
            "candidate": {
                "member": {
                    "id": "UNAUTH-1",
                    "name": "No Auth",
                    "jobRole": "ML Engineer",
                    "yearsExperience": 1,
                    "education": "BSc",
                    "status": "ACTIVE",
                },
                "missions": [],
                "signals": {"commitDays": 1, "missionsCompleted": 0, "missionsFirstTry": 0},
            },
        },
    )
    assert response.status_code == 401
    assert response.json()["error"] == "not_authenticated"


def test_unauthenticated_turn_rejected(client: TestClient) -> None:
    anonymous = TestClient(app)
    response = anonymous.post(
        "/api/interview",
        json={"sessionId": "unauth-turn", "message": "Hello"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "not_authenticated"


def test_interview_ownership_enforced(client: TestClient, candidate_repository) -> None:
    session_id = _start(client, candidate_repository)

    intruder = TestClient(app)
    _register(intruder, prefix="intruder")
    response = intruder.post(
        "/api/interview",
        json={"sessionId": session_id, "message": STRONG_ANSWER},
    )
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"

    owner_turn = client.post(
        "/api/interview",
        json={"sessionId": session_id, "message": "Yes"},
    )
    assert owner_turn.status_code == 200


def test_unknown_session_still_404_authenticated(client: TestClient) -> None:
    response = client.post("/api/interview", json={"sessionId": "does-not-exist", "message": "Hello"})
    assert response.status_code == 404
    assert response.json()["error"] == "session_not_found"


def test_logout_revokes_session_and_blocks_protected_requests() -> None:
    user_client = TestClient(app)
    _register(user_client, prefix="logout")

    me_before = user_client.get("/api/auth/me")
    assert me_before.status_code == 200
    assert me_before.json()["user"] is not None

    logout = user_client.post("/api/auth/logout")
    assert logout.status_code == 200

    me_after = user_client.get("/api/auth/me")
    assert me_after.status_code == 200
    assert me_after.json()["user"] is None

    blocked = user_client.post("/api/interview", json={"sessionId": "after-logout", "message": "Hello"})
    assert blocked.status_code == 401
