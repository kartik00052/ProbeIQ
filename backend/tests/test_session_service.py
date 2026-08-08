import pytest

from app.core.exceptions import (
    InvalidRequestError,
    SessionCompletedError,
    SessionConflictError,
    SessionNotFoundError,
)

STRONG_ANSWER = (
    "I would design this in three layers: an ingestion pipeline that normalizes "
    "documents into retrieval-friendly chunks with metadata, a vector index with "
    "hybrid retrieval that fuses dense and sparse signals, and a generation step "
    "that is grounded strictly in the retrieved context. The main trade-off is "
    "recall versus latency, so I would benchmark chunk size and index layout "
    "before locking the design."
)


class _Ids:
    counter = 0

    @classmethod
    def next(cls) -> str:
        cls.counter += 1
        return f"svc-{cls.counter}"


def _start(session_service, candidate_repository, candidate_id: str = "CAND-001"):
    candidate = candidate_repository.get(candidate_id)
    return session_service.start(_Ids.next(), candidate)


def _run_until_done(session_service, session_id: str, message: str = STRONG_ANSWER, cap: int = 20):
    session = session_service.get(session_id)
    for _ in range(cap):
        if session.interview_complete:
            return session
        session = session_service.answer(session_id, message)
    return session


def test_start_activates_session_with_first_question(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    assert session.status == "ACTIVE"
    assert session.question_count == 1
    assert session.interview_complete is False
    assert session.last_reply is not None
    assert session.questions_asked[0].question_number == 1


def test_multiple_turns_preserve_full_state(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    for _ in range(3):
        session = session_service.answer(session.session_id, "A candidate answer.")
    assert session.question_count == 4
    assert len(session.questions_asked) == 4
    assert len(session.candidate_responses) == 3
    assert len(session.covered_topics) >= 1
    assert len(session.covered_curriculum_days) >= 1


def test_question_sequence_then_answer_sequence_available(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    q1 = session.questions_asked[0]
    session = session_service.answer(session.session_id, "answer 1")
    q2 = session.questions_asked[1]
    assert q1.question_number == 1 and q2.question_number == 2
    assert session.candidate_responses == ["answer 1"]
    assert q2.topic == q1.topic or len(session.covered_curriculum_days) >= 1


def test_unknown_session_answer_does_not_create_session(session_service) -> None:
    with pytest.raises(SessionNotFoundError):
        session_service.answer("missing-session", "hello")


def test_completed_session_rejects_another_answer(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    session = _run_until_done(session_service, session.session_id)
    assert session.interview_complete is True
    assert session.status == "COMPLETED"
    with pytest.raises(SessionCompletedError):
        session_service.answer(session.session_id, "too late")


def test_empty_message_rejected(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    with pytest.raises(InvalidRequestError):
        session_service.answer(session.session_id, "")
    with pytest.raises(InvalidRequestError):
        session_service.answer(session.session_id, "   ")


def test_full_interview_reaches_completion_with_feedback(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    session = _run_until_done(session_service, session.session_id)
    assert session.interview_complete is True
    assert session.last_reply == "Interview completed."
    assert session.feedback is not None
    assert session.feedback.summary.startswith("Interview complete:")
    assert isinstance(session.feedback.strengths, list)
    assert isinstance(session.feedback.gaps, list)
    assert isinstance(session.feedback.next, list)
    assert session.question_count >= 8
    assert len(session.covered_curriculum_days) >= 4


def test_conversation_context_is_compact(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    for _ in range(6):
        session = session_service.answer(session.session_id, "an answer")
    context = session.to_conversation_context()
    assert context.question_count == 7
    assert len(context.questions_asked) == 7
    assert len(context.recent_responses) <= 3


def test_duplicate_start_rejected(session_service, candidate_repository) -> None:
    candidate = candidate_repository.get("CAND-001")
    session_id = _Ids.next()
    session_service.start(session_id, candidate)
    with pytest.raises(SessionConflictError):
        session_service.start(session_id, candidate)


def test_retrieve_session_after_turns(session_service, candidate_repository) -> None:
    session = _start(session_service, candidate_repository)
    session_service.answer(session.session_id, "answer 1")
    session_service.answer(session.session_id, "answer 2")
    retrieved = session_service.get(session.session_id)
    assert len(retrieved.questions_asked) == 3
    assert retrieved.candidate_responses == ["answer 1", "answer 2"]
