"""Phase 7 tests: the final feedback engine.

Covers the required public schema, concise arrays, actionable next steps,
evidence grounding, empty/partial evaluation handling, and mocked-LLM validation
of the structured feedback output. All LLM tests are deterministic and offline.
"""

import json
from types import SimpleNamespace
from typing import Literal

import pytest

from app.agents.feedback_agent import (
    DeterministicFeedbackGenerator,
    LLMFeedbackGenerator,
)
from app.core.exceptions import InterviewEngineError
from app.prompts.feedback_prompts import build_feedback_prompt
from app.schemas.evaluation import Evaluation
from app.schemas.interview import InterviewFeedback
from app.schemas.profile import CandidateInterviewProfile
from app.schemas.session import AnswerEvaluation, InterviewSession
from app.schemas.strategy import InterviewStrategy
from app.schemas.topic_plan import InterviewTopicPlan, PlannedTopic

EMBEDDINGS = "Embeddings Explained"
VECTOR_DB = "Vector Databases Overview"
BACKEND = "Chatbot Backend & API Integration"

MISSING_CONCEPT = "Understand how text is converted into vector embeddings"
MISCONCEPTION = "Vector search and SQL are the same thing."


class _FakeChat:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.response)


# --- session fixtures ---------------------------------------------------------


def _profile() -> CandidateInterviewProfile:
    return CandidateInterviewProfile(
        candidate_id="CAND-T",
        role="Backend Engineer",
        experience=3,
        role_is_technical=True,
        completed_days=[],
        failed_days=[],
        skipped_days=[],
        high_attempt_days=[],
        strong_evidence_topics=[],
        uncertain_topics=[],
        recommended_topics=[],
    )


def _strategy() -> InterviewStrategy:
    return InterviewStrategy(primary_areas=["retrieval"], probe_areas=["trade-offs"], avoid_assuming=[])


def _topic(day: int, title: str) -> PlannedTopic:
    return PlannedTopic(
        day=day,
        title=title,
        outcome="passed",
        module=3,
        module_title="Embeddings & Vector Search",
        depth="standard",
        probe=False,
        question_slots=3,
        reason="test fixture",
    )


def _evaluation(
    question_number: int,
    topic: str,
    quality: Literal["strong", "adequate", "weak"],
    *,
    missing: list[str] | None = None,
    wrong: list[str] | None = None,
    score: int = 70,
) -> AnswerEvaluation:
    return AnswerEvaluation(
        question_number=question_number,
        day=7,
        topic=topic,
        quality=quality,
        note="assessment",
        details=Evaluation(
            score=score,
            assessment="assessment",
            strengths=["Technical correctness"],
            missing_concepts=list(missing or []),
            misconceptions=list(wrong or []),
            depth_level="moderate",
            follow_up_needed=True,
            follow_up_reason="reason",
            recommended_probe="missing_concept",
        ),
    )


def _session(
    *,
    evaluations: list[AnswerEvaluation] | None = None,
    covered: list[str] | None = None,
    question_count: int = 8,
) -> InterviewSession:
    topics = [_topic(7, EMBEDDINGS), _topic(8, VECTOR_DB), _topic(16, BACKEND)]
    plan = InterviewTopicPlan(
        topics=topics,
        min_days=4,
        target_questions=8,
        allocated_questions=8,
    )
    session = InterviewSession(
        session_id="sess",
        status="COMPLETED",
        candidate_profile=_profile(),
        strategy=_strategy(),
        topic_plan=plan,
    )
    session.evaluations = list(evaluations or [])
    session.covered_topics = list(covered or [topic.title for topic in topics])
    session.covered_curriculum_days = [7, 8, 16]
    session.question_count = question_count
    return session


# --- required public schema ---------------------------------------------------


def test_feedback_schema_is_exactly_the_public_contract() -> None:
    assert set(InterviewFeedback.model_fields) == {"summary", "strengths", "gaps", "next"}


def test_deterministic_generator_returns_valid_feedback() -> None:
    evaluations = [
        _evaluation(1, EMBEDDINGS, "strong", score=92),
        _evaluation(2, VECTOR_DB, "weak", missing=[MISSING_CONCEPT], score=40),
    ]
    feedback = DeterministicFeedbackGenerator().generate(_session(evaluations=evaluations))
    assert isinstance(feedback, InterviewFeedback)
    assert feedback.summary.startswith("Interview complete:")
    assert isinstance(feedback.strengths, list)
    assert isinstance(feedback.gaps, list)
    assert isinstance(feedback.next, list)


# --- concise arrays -----------------------------------------------------------


def test_arrays_are_concise() -> None:
    evaluations = [
        _evaluation(1, EMBEDDINGS, "strong", score=95),
        _evaluation(2, VECTOR_DB, "weak", missing=["one"], score=40),
        _evaluation(3, VECTOR_DB, "weak", missing=["two"], score=35),
        _evaluation(4, BACKEND, "adequate", missing=["three"], score=65),
        _evaluation(5, BACKEND, "weak", wrong=["four"], score=30),
    ]
    feedback = DeterministicFeedbackGenerator().generate(_session(evaluations=evaluations))
    assert len(feedback.strengths) <= 3
    assert len(feedback.gaps) <= 3
    assert len(feedback.next) <= 3
    for item in [*feedback.strengths, *feedback.gaps, *feedback.next]:
        assert isinstance(item, str) and item.strip()
        assert len(item) < 250


# --- actionable next steps ----------------------------------------------------


def test_next_steps_are_actionable_and_grounded() -> None:
    evaluations = [
        _evaluation(1, EMBEDDINGS, "weak", missing=[MISSING_CONCEPT], score=40),
        _evaluation(2, EMBEDDINGS, "weak", wrong=[MISCONCEPTION], score=30),
    ]
    feedback = DeterministicFeedbackGenerator().generate(_session(evaluations=evaluations))
    assert feedback.next
    assert any(item.startswith("Review: ") and MISSING_CONCEPT in item for item in feedback.next)
    assert any(
        item.startswith("Correct the misunderstanding: ") and MISCONCEPTION in item
        for item in feedback.next
    )
    # No generic filler advice.
    assert not any("Study AI more" in item or "Practice more" in item for item in feedback.next)


def test_next_steps_reference_curriculum_not_generic_goals() -> None:
    evaluations = [_evaluation(1, VECTOR_DB, "weak", missing=[MISSING_CONCEPT], score=40)]
    feedback = DeterministicFeedbackGenerator().generate(_session(evaluations=evaluations))
    assert all(item.lower().find("study ai") == -1 for item in feedback.next)
    assert all(" " in item for item in feedback.next)


# --- evidence grounding -------------------------------------------------------


def test_strengths_and_gaps_trace_to_evaluations() -> None:
    evaluations = [
        _evaluation(1, EMBEDDINGS, "strong", score=92),
        _evaluation(2, VECTOR_DB, "weak", missing=[MISSING_CONCEPT], score=40),
    ]
    feedback = DeterministicFeedbackGenerator().generate(_session(evaluations=evaluations))
    assert any(EMBEDDINGS in item for item in feedback.strengths)
    assert not any(VECTOR_DB in item for item in feedback.strengths)
    assert any(VECTOR_DB in item for item in feedback.gaps)
    assert not any(EMBEDDINGS in item for item in feedback.gaps)
    assert MISSING_CONCEPT in " ".join(feedback.next)


def test_no_evaluation_is_invented() -> None:
    # A planned topic with zero questions must never appear in strengths or gaps.
    session = _session(
        evaluations=[_evaluation(1, EMBEDDINGS, "strong", score=90)],
        covered=[EMBEDDINGS],
    )
    feedback = DeterministicFeedbackGenerator().generate(session)
    for item in [*feedback.strengths, *feedback.gaps]:
        assert BACKEND not in item
        assert VECTOR_DB not in item


# --- empty / partial evaluation handling --------------------------------------


def test_empty_evaluation_handling() -> None:
    feedback = DeterministicFeedbackGenerator().generate(_session(evaluations=[], covered=[]))
    assert isinstance(feedback, InterviewFeedback)
    assert feedback.summary
    assert feedback.strengths == []
    assert feedback.gaps == []
    assert feedback.next  # honest, actionable fallback
    assert "no answers were evaluated" in feedback.summary


def test_partial_evaluation_handling() -> None:
    evaluations = [_evaluation(1, EMBEDDINGS, "strong", score=95)]
    feedback = DeterministicFeedbackGenerator().generate(_session(evaluations=evaluations))
    assert feedback.summary
    assert any(EMBEDDINGS in item for item in feedback.strengths)
    assert "1/1 answers strong" in feedback.summary


# --- mocked LLM structured output validation ----------------------------------


def test_llm_feedback_returns_validated_feedback() -> None:
    payload = {
        "summary": "Solid understanding with a clear gap in retrieval accuracy.",
        "strengths": ["Explained hybrid retrieval trade-offs"],
        "gaps": ["Retrieval accuracy measurement"],
        "next": ["Review: how to evaluate retrieval accuracy"],
    }
    generator = LLMFeedbackGenerator(_FakeChat(json.dumps(payload)))
    feedback = generator.generate(_session())
    assert isinstance(feedback, InterviewFeedback)
    assert feedback.summary == payload["summary"]
    assert feedback.gaps == ["Retrieval accuracy measurement"]


def test_llm_feedback_prompt_is_grounded() -> None:
    session = _session(
        evaluations=[
            _evaluation(1, EMBEDDINGS, "strong", score=92),
            _evaluation(2, VECTOR_DB, "weak", missing=[MISSING_CONCEPT], score=40),
        ],
        covered=[EMBEDDINGS, VECTOR_DB, BACKEND],
    )
    prompt = build_feedback_prompt(session)
    assert EMBEDDINGS in prompt
    assert VECTOR_DB in prompt
    assert "[strong]" in prompt
    assert "[weak]" in prompt
    assert MISSING_CONCEPT in prompt
    assert '"summary": str, "strengths": [str], "gaps": [str], "next": [str]' in prompt


def test_llm_feedback_rejects_invalid_json() -> None:
    generator = LLMFeedbackGenerator(_FakeChat("great interview, here is the feedback: ..."))
    with pytest.raises(InterviewEngineError):
        generator.generate(_session())


def test_llm_feedback_rejects_missing_fields() -> None:
    generator = LLMFeedbackGenerator(_FakeChat('{"summary": "only a summary"}'))
    with pytest.raises(InterviewEngineError):
        generator.generate(_session())


def test_llm_feedback_rejects_empty_summary() -> None:
    payload = {"summary": "", "strengths": [], "gaps": [], "next": []}
    generator = LLMFeedbackGenerator(_FakeChat(json.dumps(payload)))
    with pytest.raises(InterviewEngineError):
        generator.generate(_session())


def test_llm_feedback_rejects_uncovered_topic() -> None:
    payload = {
        "summary": "Good interview.",
        "strengths": ["Solid work on Vector Databases Overview"],
        "gaps": [],
        "next": ["Review: retrieval accuracy"],
    }
    # The interview only covered Embeddings; Vector DB was planned but skipped.
    session = _session(
        evaluations=[_evaluation(1, EMBEDDINGS, "strong", score=92)],
        covered=[EMBEDDINGS],
    )
    generator = LLMFeedbackGenerator(_FakeChat(json.dumps(payload)))
    with pytest.raises(InterviewEngineError):
        generator.generate(session)
