"""Opt-in live NVIDIA GLM 5.2 integration test.

Runs a real request against the configured endpoint ONLY when both:

    PROBEIQ_LIVE_LLM_TEST=true

is set and the LLM is configured in ``backend/.env`` (key never read from code).
Skipped by default so the normal suite stays offline and deterministic.

The test exercises the actual ProbeIQ agents end-to-end: the LLM generates a
grounded question, then evaluates an answer -- while the deterministic
controller (``app.orchestration.decision``) is untouched. The API key is never
printed.
"""

import os

import pytest

from app.agents.evaluation_agent import LLMAnswerEvaluator
from app.agents.question_agent import LLMQuestionGenerator
from app.core.config import settings
from app.llm.factory import get_llm
from app.schemas.question_context import EvaluationContext, QuestionContext

pytestmark = pytest.mark.skipif(
    os.getenv("PROBEIQ_LIVE_LLM_TEST") != "true",
    reason="Live LLM test disabled (set PROBEIQ_LIVE_LLM_TEST=true to run).",
)


def _require_llm():
    llm = get_llm()
    if llm is None:
        pytest.skip("LLM not enabled; configure PROBEIQ_LLM_* in backend/.env.")
    return llm


def _model_name(llm) -> str:
    return (
        getattr(llm, "model", None)
        or getattr(llm, "model_name", None)
        or settings.llm_model
        or "unknown"
    )


def _question_context(knowledge_service) -> QuestionContext:
    node = knowledge_service.node(10)
    return QuestionContext(
        candidate_id="LIVE-1",
        role="Backend Engineer",
        experience=5,
        day=node.day,
        topic=node.title,
        module=node.module_title,
        objectives=list(node.objectives),
        tools=list(node.tools),
        difficulty="intermediate",
        follow_up_index=0,
        previous_question=None,
        previous_answer=None,
        previous_quality=None,
        previous_evaluation=None,
        probe_focus=None,
        covered_days=[7, 8],
        question_number=1,
        min_questions=8,
        min_covered_days=4,
        interview_objective="Assess applied understanding.",
        completion_evidence=True,
    )


def _evaluation_context(knowledge_service) -> EvaluationContext:
    node = knowledge_service.node(10)
    return EvaluationContext(
        question_number=1,
        day=node.day,
        topic=node.title,
        question="How would you build the retrieval engine for this curriculum project?",
        answer=(
            "Hybrid retrieval fuses dense semantic vectors with sparse lexical "
            "matching; the trade-off is added latency and index complexity."
        ),
        objectives=list(node.objectives),
        tools=list(node.tools),
        role="Backend Engineer",
        experience=5,
        topic_evidence="Passed on the first attempt.",
        prior_quality=None,
    )


def test_live_model_responds() -> None:
    llm = _require_llm()
    response = llm.invoke(
        [
            ("system", "You are a terse assistant."),
            ("user", "Reply with exactly the single word: ready"),
        ]
    )
    text = getattr(response, "content", "")
    assert isinstance(text, str) and text.strip()
    print(f"[live] model={_model_name(llm)} provider={settings.llm_provider} responded")


def test_live_question_generation(knowledge_service) -> None:
    llm = _require_llm()
    context = _question_context(knowledge_service)
    question = LLMQuestionGenerator(llm).generate(context)
    assert question.curriculum_day == context.day
    assert question.topic == context.topic
    assert question.difficulty == context.difficulty
    print(f"[live] generated question ({question.question_type}): {question.question[:100]}")


def test_live_answer_evaluation(knowledge_service) -> None:
    llm = _require_llm()
    context = _evaluation_context(knowledge_service)
    evaluation = LLMAnswerEvaluator(llm).evaluate(context)
    assert 0 <= evaluation.score <= 100
    assert evaluation.assessment
    print(f"[live] score={evaluation.score} depth={evaluation.depth_level}")
