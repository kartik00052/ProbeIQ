"""Phase 6 tests: answer evaluation and the probe engine.

Verifies that strong, partial, incorrect, excellent, vague, and unsupported
answers produce different probe decisions, that the structured evaluation maps to
the engine's coarse quality, that the probe rules are explicit and deterministic,
and that LLM evaluator output is validated. LLM evaluator tests use mocked chat
responses.
"""

import json
from types import SimpleNamespace

import pytest

from app.agents.evaluation_agent import DeterministicAnswerEvaluator, LLMAnswerEvaluator
from app.core.exceptions import InterviewEngineError
from app.orchestration.decision import quality_from_evaluation, recommended_probe
from app.schemas.evaluation import DepthLevel, Evaluation
from app.schemas.question_context import EvaluationContext
from app.schemas.topic_plan import Depth
from app.services.topic_planner import TopicPlannerService

DAY = 10
TOPIC = "The Retrieval & Matching Engine"
OBJECTIVES = [
    "Build a query router that decides between SQL, vector search, or hybrid retrieval",
    "Implement structured data lookup for plans and claims",
    "Implement semantic retrieval from the vector database",
    "Merge and deduplicate results from multiple retrieval sources",
    "Evaluate retrieval accuracy using a diverse set of healthcare questions",
]
TOOLS = ["SQLite", "ChromaDB", "Python"]


class _FakeChat:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.response)


def _ctx(answer: str, *, evidence="Passed on the first attempt.", role="Backend Engineer", experience=3) -> EvaluationContext:
    return EvaluationContext(
        question_number=1,
        day=DAY,
        topic=TOPIC,
        question="How would you build the retrieval engine for this curriculum project?",
        answer=answer,
        objectives=list(OBJECTIVES),
        tools=list(TOOLS),
        role=role,
        experience=experience,
        topic_evidence=evidence,
        prior_quality=None,
    )


STRONG_CONCEPTUAL = (
    "Hybrid retrieval fuses dense semantic vectors with sparse lexical matching. "
    "It helps when synonym variation matters, because pure semantic search can miss "
    "exact identifiers. The trade-off is added latency and index complexity."
)

EXCELLENT = (
    "Hybrid retrieval fuses dense and sparse signals to maximize recall. In production "
    "I would benchmark precision-recall on a held-out query set, monitor latency "
    "percentiles and index freshness, add a fallback to exact-match for identifiers, "
    "and A/B test chunking. The trade-off is complexity versus accuracy, and I would "
    "validate the design by measuring p95 latency and NDCG before scaling index shards."
)

PARTIAL = "Hybrid retrieval fuses dense and sparse signals."

INCORRECT = "You just use a cache and retry on failure; that is all you need."

VAGUE = "I think it has something to do with retrieval, not sure though."

UNSUPPORTED = "I built a production hybrid retrieval system at my last job and scaled it to a million users."


def _evaluate(answer: str, **overrides) -> Evaluation:
    return DeterministicAnswerEvaluator().evaluate(_ctx(answer, **overrides))


# --- probe decisions per answer type -----------------------------------------


def test_strong_conceptual_answer_probes_architecture() -> None:
    evaluation = _evaluate(STRONG_CONCEPTUAL)
    assert evaluation.depth_level == "deep"
    assert evaluation.recommended_probe == "architecture"
    assert quality_from_evaluation(evaluation) == "strong"


def test_partial_answer_probes_missing_concept() -> None:
    evaluation = _evaluate(PARTIAL)
    assert evaluation.missing_concepts
    assert evaluation.recommended_probe == "missing_concept"
    assert quality_from_evaluation(evaluation) == "adequate"


def test_incorrect_answer_probes_fundamental_understanding() -> None:
    evaluation = _evaluate(INCORRECT)
    assert evaluation.misconceptions
    assert evaluation.recommended_probe == "fundamental_understanding"
    assert quality_from_evaluation(evaluation) == "weak"


def test_excellent_answer_probes_production_depth() -> None:
    evaluation = _evaluate(EXCELLENT)
    assert evaluation.depth_level == "excellent"
    assert evaluation.recommended_probe == "production_depth"
    assert quality_from_evaluation(evaluation) == "strong"


def test_vague_answer_probes_evidence_clarification() -> None:
    evaluation = _evaluate(VAGUE)
    assert evaluation.recommended_probe == "evidence_clarification"
    assert evaluation.follow_up_needed is True
    assert quality_from_evaluation(evaluation) == "weak"


def test_unsupported_claims_probe_evidence() -> None:
    evaluation = _evaluate(UNSUPPORTED, evidence="Skipped: not assessed / not completed.")
    assert evaluation.recommended_probe == "evidence_clarification"
    assert evaluation.follow_up_reason is not None
    assert "evidence" in evaluation.follow_up_reason
    assert quality_from_evaluation(evaluation) == "weak"


def test_different_answer_types_produce_different_probe_decisions() -> None:
    evaluations = [
        _evaluate(STRONG_CONCEPTUAL),
        _evaluate(PARTIAL),
        _evaluate(INCORRECT),
        _evaluate(EXCELLENT),
        _evaluate(VAGUE),
        _evaluate(UNSUPPORTED, evidence="Skipped: not assessed / not completed."),
    ]
    decisions = {(item.recommended_probe, item.follow_up_reason) for item in evaluations}
    assert len(decisions) == 6


def test_concise_grounded_answer_is_not_penalized() -> None:
    evaluation = _evaluate("Hybrid retrieval, because pure semantic search misses exact identifiers.")
    assert quality_from_evaluation(evaluation) != "weak"


# --- quality mapping ----------------------------------------------------------


def _mocked(score: int, depth: DepthLevel, *, misconceptions=None, missing=None) -> Evaluation:
    return Evaluation(
        score=score,
        assessment="mocked",
        misconceptions=list(misconceptions or []),
        missing_concepts=list(missing or []),
        depth_level=depth,
        follow_up_needed=True,
    )


def test_quality_from_evaluation_mapping() -> None:
    assert quality_from_evaluation(_mocked(90, "deep")) == "strong"
    assert quality_from_evaluation(_mocked(90, "excellent")) == "strong"
    assert quality_from_evaluation(_mocked(65, "moderate")) == "adequate"
    assert quality_from_evaluation(_mocked(40, "shallow")) == "weak"
    assert quality_from_evaluation(_mocked(90, "deep", misconceptions=["wrong"])) == "weak"


# --- explicit probe rules -----------------------------------------------------


def test_recommended_probe_rules_are_explicit() -> None:
    assert recommended_probe(_mocked(45, "shallow", misconceptions=["wrong"])) == "fundamental_understanding"
    assert recommended_probe(_mocked(90, "excellent")) == "production_depth"
    assert recommended_probe(_mocked(80, "deep")) == "architecture"
    assert recommended_probe(_mocked(65, "moderate", missing=["some concept"])) == "missing_concept"
    assert recommended_probe(_mocked(40, "shallow")) == "evidence_clarification"


# --- structured output validation (mocked LLM) --------------------------------


def test_llm_evaluator_returns_validated_evaluation() -> None:
    payload = {
        "score": 88,
        "assessment": "Sound answer with clear trade-off reasoning.",
        "strengths": ["Trade-off awareness", "Technical correctness"],
        "missing_concepts": [],
        "misconceptions": [],
        "depth_level": "deep",
        "follow_up_needed": True,
        "follow_up_reason": "Probe production behavior.",
        "recommended_probe": "architecture",
    }
    evaluator = LLMAnswerEvaluator(_FakeChat(json.dumps(payload)))
    evaluation = evaluator.evaluate(_ctx(STRONG_CONCEPTUAL))
    assert evaluation.score == 88
    assert evaluation.depth_level == "deep"
    assert evaluation.recommended_probe == "architecture"


def test_llm_evaluator_rejects_invalid_json() -> None:
    evaluator = LLMAnswerEvaluator(_FakeChat("definitely a strong answer!"))
    with pytest.raises(InterviewEngineError):
        evaluator.evaluate(_ctx(STRONG_CONCEPTUAL))


def test_llm_evaluator_rejects_invalid_depth_level() -> None:
    payload = {
        "score": 88,
        "assessment": "a",
        "strengths": [],
        "missing_concepts": [],
        "misconceptions": [],
        "depth_level": "ultra",
        "follow_up_needed": True,
        "follow_up_reason": None,
        "recommended_probe": None,
    }
    evaluator = LLMAnswerEvaluator(_FakeChat(json.dumps(payload)))
    with pytest.raises(InterviewEngineError):
        evaluator.evaluate(_ctx(STRONG_CONCEPTUAL))


# --- engine integration -------------------------------------------------------


class _FixedPlanPlanner(TopicPlannerService):
    def __init__(self, topics) -> None:
        self._topics = topics

    def plan(self, analysis, min_days: int = 4, target_questions: int = 8):
        from app.schemas.topic_plan import InterviewTopicPlan

        return InterviewTopicPlan(
            topics=[topic.model_copy(deep=True) for topic in self._topics],
            min_days=min_days,
            target_questions=target_questions,
            allocated_questions=sum(topic.question_slots for topic in self._topics),
        )


def _planned_topics(knowledge_service, days, depth: Depth = "standard") -> list:
    from app.schemas.topic_plan import PlannedTopic

    topics = []
    for day in days:
        node = knowledge_service.node(day)
        topics.append(
            PlannedTopic(
                day=day,
                title=node.title,
                outcome="passed",
                module=node.module,
                module_title=node.module_title,
                depth=depth,
                probe=False,
                question_slots=3,
                reason="test fixture",
            )
        )
    return topics


def test_engine_records_structured_evaluation(
    candidate_repository,
    knowledge_service,
    analysis_service,
    profile_service,
    strategy_service,
) -> None:
    from app.agents.evaluation_agent import DeterministicAnswerEvaluator
    from app.agents.feedback_agent import DeterministicFeedbackGenerator
    from app.agents.question_agent import DeterministicQuestionGenerator
    from app.orchestration.graph import build_interview_graph

    graph = build_interview_graph(
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=_FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16])),
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=DeterministicQuestionGenerator(),
        evaluator=DeterministicAnswerEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
        min_questions=8,
        min_covered_days=4,
        max_questions_per_topic=3,
        hard_max_questions=16,
    )
    started = graph.invoke({"action": "start", "session_id": "graph", "candidate": candidate_repository.get("CAND-001")})
    session = started["session"]

    turn = graph.invoke({"action": "answer", "session_id": "graph", "session": session, "candidate_answer": PARTIAL})
    recorded = turn["session"].evaluations[-1]
    assert recorded.quality == "adequate"
    assert recorded.details is not None
    assert recorded.details.recommended_probe == "missing_concept"
    assert turn["session"].last_reply is not None
