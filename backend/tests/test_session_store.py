import pytest

from app.core.exceptions import SessionConflictError, SessionNotFoundError
from app.repositories.session_store import InMemorySessionStore
from app.schemas.profile import CandidateInterviewProfile
from app.schemas.session import InterviewSession
from app.schemas.strategy import InterviewStrategy
from app.schemas.topic_plan import InterviewTopicPlan


def _session(session_id: str = "sess-store") -> InterviewSession:
    return InterviewSession(
        session_id=session_id,
        status="NEW",
        candidate_profile=CandidateInterviewProfile(
            candidate_id="CAND-001",
            role="Engineer",
            experience=5,
            role_is_technical=True,
            completed_days=[],
            failed_days=[],
            skipped_days=[],
            high_attempt_days=[],
            strong_evidence_topics=[],
            uncertain_topics=[],
            recommended_topics=[],
        ),
        strategy=InterviewStrategy(primary_areas=[], probe_areas=[], avoid_assuming=[]),
        topic_plan=InterviewTopicPlan(
            topics=[],
            min_days=4,
            target_questions=8,
            allocated_questions=0,
        ),
    )


def test_create_and_retrieve() -> None:
    store = InMemorySessionStore()
    store.create(_session())
    assert store.get("sess-store").session_id == "sess-store"


def test_update_persists_changes() -> None:
    store = InMemorySessionStore()
    store.create(_session())
    stored = store.get("sess-store")
    stored.status = "ACTIVE"
    stored.question_count = 3
    store.update(stored)
    assert store.get("sess-store").status == "ACTIVE"
    assert store.get("sess-store").question_count == 3


def test_unknown_session_get_raises() -> None:
    store = InMemorySessionStore()
    with pytest.raises(SessionNotFoundError):
        store.get("does-not-exist")


def test_duplicate_create_raises() -> None:
    store = InMemorySessionStore()
    store.create(_session())
    with pytest.raises(SessionConflictError):
        store.create(_session())


def test_update_unknown_session_raises() -> None:
    store = InMemorySessionStore()
    with pytest.raises(SessionNotFoundError):
        store.update(_session())


def test_get_returns_copy_not_reference() -> None:
    store = InMemorySessionStore()
    store.create(_session())
    first = store.get("sess-store")
    first.question_count = 99
    assert store.get("sess-store").question_count == 0
