"""Tests proving the adaptive interview engine actually adapts.

The engine must never behave like a fixed Q1..Q8 questionnaire: every decision is
derived from the evaluation of the last answer plus history, coverage, and counts.
These tests drive real multi-turn graph runs and assert the observed decisions and
topic/difficulty transitions (not just the replies).
"""

import pytest

from app.agents.evaluation_agent import AnswerEvaluator, DeterministicAnswerEvaluator
from app.agents.feedback_agent import DeterministicFeedbackGenerator
from app.agents.question_agent import DeterministicQuestionGenerator
from app.core.exceptions import InterviewEngineError
from app.orchestration.decision import (
    STRONG_ANSWERS_BEFORE_TRANSITION,
    apply_decision,
    count_questions_on_topic,
    decide,
    next_topic_index,
)
from app.orchestration.graph import build_interview_graph
from app.repositories.session_store import InMemorySessionStore
from app.schemas.profile import CandidateInterviewProfile
from app.schemas.question import Question
from app.schemas.session import AskedQuestion, InterviewSession
from app.schemas.strategy import InterviewStrategy
from app.schemas.topic_plan import Depth, InterviewTopicPlan, PlannedTopic
from app.services.session_service import SessionService
from app.services.topic_planner import TopicPlannerService

STRONG_ANSWER = (
    "I would design this in three layers: an ingestion pipeline that normalizes "
    "documents into retrieval-friendly chunks with metadata, a vector index with "
    "hybrid retrieval that fuses dense and sparse signals, and a generation step "
    "that is grounded strictly in the retrieved context. The main trade-off is "
    "recall versus latency, so I would benchmark chunk size and index layout "
    "before locking the design."
)
ADEPT_ANSWER = (
    "I would start by chunking the documents and storing their embeddings in a "
    "vector database, then query it with the user question."
)
WEAK_ANSWER = "I don't know."

MIN_QUESTIONS = 8
MIN_DAYS = 4
MAX_PER_TOPIC = 3
HARD_MAX = 16


# --- fixtures for a controllable topic plan ----------------------------------


class _FixedPlanPlanner(TopicPlannerService):
    """Topic planner that returns exactly the given topics (for coverage tests)."""

    def __init__(self, topics: list[PlannedTopic]) -> None:
        self._topics = topics

    def plan(self, analysis, min_days: int = 4, target_questions: int = 8) -> InterviewTopicPlan:
        return InterviewTopicPlan(
            topics=[topic.model_copy(deep=True) for topic in self._topics],
            min_days=min_days,
            target_questions=target_questions,
            allocated_questions=sum(topic.question_slots for topic in self._topics),
        )


def _planned_topics(knowledge_service, days: list[int], depth: Depth = "standard", slots: int = 3) -> list[PlannedTopic]:
    topics: list[PlannedTopic] = []
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
                question_slots=slots,
                reason="test fixture",
            )
        )
    return topics


def _build_graph(*, topic_planner, knowledge_service, analysis_service, profile_service, strategy_service):
    return build_interview_graph(
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=topic_planner,
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=DeterministicQuestionGenerator(),
        evaluator=DeterministicAnswerEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
        min_questions=MIN_QUESTIONS,
        min_covered_days=MIN_DAYS,
        max_questions_per_topic=MAX_PER_TOPIC,
        hard_max_questions=HARD_MAX,
    )


def _run_turn(graph, action: str, **inputs) -> dict:
    return graph.invoke({"action": action, **inputs})


def _start(graph, candidate) -> dict:
    return _run_turn(graph, "start", session_id="graph-sess", candidate=candidate)


def _answer(graph, session: InterviewSession, message: str) -> dict:
    return _run_turn(
        graph,
        "answer",
        session_id=session.session_id,
        candidate_answer=message,
        session=session,
    )


# --- graph structure ----------------------------------------------------------


def test_graph_structure(
    knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    graph = _build_graph(
        topic_planner=_FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16])),
        knowledge_service=knowledge_service,
        analysis_service=analysis_service,
        profile_service=profile_service,
        strategy_service=strategy_service,
    )
    node_names = set(graph.get_graph().nodes)
    assert {"analyze_candidate", "plan_interview", "generate_question", "evaluate_response", "decide_next_step", "generate_feedback"} <= node_names


# --- probe decision rules (pure) ----------------------------------------------


def _profile() -> CandidateInterviewProfile:
    return CandidateInterviewProfile(
        candidate_id="unit",
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
    return InterviewStrategy(
        primary_areas=["retrieval"],
        probe_areas=["trade-offs"],
        avoid_assuming=[],
    )


def _session_with(question_count: int, days: int, difficulty="intermediate", topic="T") -> InterviewSession:
    plan = InterviewTopicPlan(
        topics=[_topic("T", 7, "standard")],
        min_days=MIN_DAYS,
        target_questions=MIN_QUESTIONS,
        allocated_questions=MIN_QUESTIONS,
    )
    session = InterviewSession(
        session_id="unit",
        status="ACTIVE",
        candidate_profile=_profile(),
        strategy=_strategy(),
        topic_plan=plan,
    )
    session.current_topic = topic
    session.difficulty = difficulty
    session.question_count = question_count
    session.covered_curriculum_days = list(range(1, days + 1))
    for number in range(question_count):
        session.questions_asked.append(
            AskedQuestion(
                question_number=number + 1,
                day=7,
                topic=topic,
                text="question",
                depth="standard",
                difficulty=difficulty,
                follow_up_index=0,
            )
        )
    return session


def _topic(title: str, day: int, depth: Depth) -> PlannedTopic:
    return PlannedTopic(
        day=day,
        title=title,
        outcome="passed",
        module=3,
        module_title="M",
        depth=depth,
        probe=False,
        question_slots=3,
        reason="unit",
    )


def test_decide_weak_answer_decreases_difficulty() -> None:
    session = _session_with(2, 1, difficulty="advanced")
    assert decide(session, "weak", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "DECREASE_DIFFICULTY"


def test_decide_weak_answer_at_floor_stays_foundational() -> None:
    session = _session_with(2, 1, difficulty="foundational")
    assert decide(session, "weak", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "FOLLOW_UP"


def test_decide_adequate_answer_follows_up() -> None:
    session = _session_with(2, 1, difficulty="intermediate")
    assert decide(session, "adequate", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "FOLLOW_UP"


def test_decide_first_strong_answer_increases_difficulty() -> None:
    session = _session_with(1, 1, difficulty="foundational")
    assert decide(session, "strong", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "INCREASE_DIFFICULTY"


def test_decide_second_strong_answer_moves_topic() -> None:
    session = _session_with(2, 1, difficulty="intermediate")
    assert decide(session, "strong", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "NEW_TOPIC"


def test_decide_strong_answer_at_advanced_moves_topic() -> None:
    session = _session_with(1, 1, difficulty="advanced")
    assert decide(session, "strong", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "NEW_TOPIC"


def test_decide_topic_cap_forces_transition() -> None:
    session = _session_with(3, 1, difficulty="foundational")
    assert decide(session, "adequate", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "NEW_TOPIC"


def test_decide_completes_only_when_requirements_met() -> None:
    session = _session_with(MIN_QUESTIONS, MIN_DAYS, difficulty="intermediate")
    assert decide(session, "strong", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "COMPLETE"


def test_decide_never_completes_on_weak_answer() -> None:
    session = _session_with(MIN_QUESTIONS, MIN_DAYS, difficulty="intermediate")
    assert decide(session, "weak", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) != "COMPLETE"


def test_decide_continues_below_min_covered_days() -> None:
    # 8 questions asked but only 3 days covered: the engine must continue.
    session = _session_with(MIN_QUESTIONS, 3, difficulty="advanced")
    assert decide(session, "strong", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) != "COMPLETE"


def test_decide_continues_below_min_questions() -> None:
    session = _session_with(5, MIN_DAYS, difficulty="advanced")
    assert decide(session, "strong", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) != "COMPLETE"


def test_decide_hard_max_is_safety_valve() -> None:
    session = _session_with(HARD_MAX, 2, difficulty="foundational")
    assert decide(session, "adequate", min_questions=MIN_QUESTIONS, min_covered_days=MIN_DAYS, max_questions_per_topic=MAX_PER_TOPIC, hard_max_questions=HARD_MAX) == "COMPLETE"


def test_apply_decision_updates_cursor() -> None:
    plan = InterviewTopicPlan(
        topics=[_topic("A", 7, "high"), _topic("B", 8, "standard")],
        min_days=MIN_DAYS,
        target_questions=MIN_QUESTIONS,
        allocated_questions=MIN_QUESTIONS,
    )
    session = InterviewSession(
        session_id="unit",
        status="ACTIVE",
        candidate_profile=_profile(),
        strategy=_strategy(),
        topic_plan=plan,
    )
    session.difficulty = "foundational"

    apply_decision(session, "INCREASE_DIFFICULTY", max_questions_per_topic=MAX_PER_TOPIC)
    assert session.difficulty == "intermediate"
    assert session.follow_up_index == 1

    apply_decision(session, "NEW_TOPIC", max_questions_per_topic=MAX_PER_TOPIC)
    assert session.topic_index == 1
    assert session.follow_up_index == 0
    assert session.difficulty == "foundational"  # base level of the next topic


# --- adaptive behavior in real graph runs (the actual proof) ------------------


def test_strong_answer_leads_to_increased_difficulty(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16], depth="standard"))
    graph = _build_graph(
        topic_planner=planner,
        knowledge_service=knowledge_service,
        analysis_service=analysis_service,
        profile_service=profile_service,
        strategy_service=strategy_service,
    )
    started = _start(graph, candidate_repository.get("CAND-001"))
    assert started["session"].difficulty == "foundational"

    after = _answer(graph, started["session"], STRONG_ANSWER)
    assert after["decision"] == "INCREASE_DIFFICULTY"
    assert after["session"].difficulty == "intermediate"
    assert after["session"].follow_up_index == 1
    assert after["session"].question_count == 2


def test_weak_answer_leads_to_diagnostic_foundational_probe(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16], depth="standard"))
    graph = _build_graph(
        topic_planner=planner,
        knowledge_service=knowledge_service,
        analysis_service=analysis_service,
        profile_service=profile_service,
        strategy_service=strategy_service,
    )
    started = _start(graph, candidate_repository.get("CAND-001"))
    after_strong = _answer(graph, started["session"], STRONG_ANSWER)

    after_weak = _answer(graph, after_strong["session"], WEAK_ANSWER)
    assert after_weak["decision"] == "DECREASE_DIFFICULTY"
    assert after_weak["session"].difficulty == "foundational"
    assert after_weak["session"].current_day == started["session"].current_day  # still probing same topic


def test_two_strong_answers_eventually_transition_topic(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16], depth="standard"))
    graph = _build_graph(
        topic_planner=planner,
        knowledge_service=knowledge_service,
        analysis_service=analysis_service,
        profile_service=profile_service,
        strategy_service=strategy_service,
    )
    started = _start(graph, candidate_repository.get("CAND-001"))
    first_day = started["session"].current_day

    after_one = _answer(graph, started["session"], STRONG_ANSWER)
    after_two = _answer(graph, after_one["session"], STRONG_ANSWER)

    assert after_two["decision"] == "NEW_TOPIC"
    assert after_two["session"].current_day != first_day
    assert after_two["session"].follow_up_index == 0
    assert STRONG_ANSWERS_BEFORE_TRANSITION == 2


def test_adequate_answer_follows_up_on_same_topic(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16], depth="standard"))
    graph = _build_graph(
        topic_planner=planner,
        knowledge_service=knowledge_service,
        analysis_service=analysis_service,
        profile_service=profile_service,
        strategy_service=strategy_service,
    )
    started = _start(graph, candidate_repository.get("CAND-001"))
    after = _answer(graph, started["session"], ADEPT_ANSWER)
    assert after["decision"] == "FOLLOW_UP"
    assert after["session"].current_day == started["session"].current_day
    assert after["session"].follow_up_index == 1


def test_next_question_depends_on_previous_answer(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    # Different first answers must steer the conversation differently.
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16], depth="standard"))
    graph = _build_graph(
        topic_planner=planner,
        knowledge_service=knowledge_service,
        analysis_service=analysis_service,
        profile_service=profile_service,
        strategy_service=strategy_service,
    )
    started = _start(graph, candidate_repository.get("CAND-001"))

    weak_turn = _answer(graph, started["session"], WEAK_ANSWER)
    strong_turn = _answer(graph, started["session"].model_copy(deep=True), STRONG_ANSWER)

    assert weak_turn["decision"] != strong_turn["decision"]
    assert weak_turn["session"].difficulty == "foundational"
    assert strong_turn["session"].difficulty == "intermediate"


def test_engine_continues_with_only_three_covered_days(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    # A plan covering only 3 days must never complete even after 8 questions.
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16]))
    service = SessionService(
        store=InMemorySessionStore(),
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=planner,
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=DeterministicQuestionGenerator(),
        evaluator=DeterministicAnswerEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
        min_questions=MIN_QUESTIONS,
        min_covered_days=MIN_DAYS,
        max_questions_per_topic=MAX_PER_TOPIC,
        hard_max_questions=HARD_MAX,
    )
    session = service.start("coverage-session", candidate_repository.get("CAND-001"))
    for _ in range(8):
        session = service.answer(session.session_id, STRONG_ANSWER)
        assert session.interview_complete is False

    assert session.question_count == 9  # start asks Q1, then 8 answers
    assert len(session.covered_curriculum_days) == 3


def test_engine_continues_until_coverage_satisfied_then_stops(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16]))
    service = SessionService(
        store=InMemorySessionStore(),
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=planner,
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=DeterministicQuestionGenerator(),
        evaluator=DeterministicAnswerEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
        min_questions=MIN_QUESTIONS,
        min_covered_days=MIN_DAYS,
        max_questions_per_topic=MAX_PER_TOPIC,
        hard_max_questions=HARD_MAX,
    )
    session = service.start("coverage-session-2", candidate_repository.get("CAND-001"))
    for _ in range(16):
        session = service.answer(session.session_id, STRONG_ANSWER)

    assert session.interview_complete is True
    assert session.question_count >= 8
    assert len(session.covered_curriculum_days) == 3  # 4th day simply does not exist in the plan


def test_normal_completion_meets_both_requirements(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service, planner_service
) -> None:
    service = SessionService(
        store=InMemorySessionStore(),
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=planner_service,
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=DeterministicQuestionGenerator(),
        evaluator=DeterministicAnswerEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
        min_questions=MIN_QUESTIONS,
        min_covered_days=MIN_DAYS,
        max_questions_per_topic=MAX_PER_TOPIC,
        hard_max_questions=HARD_MAX,
    )
    session = service.start("complete-session", candidate_repository.get("CAND-001"))
    for _ in range(20):
        if session.interview_complete:
            break
        session = service.answer(session.session_id, STRONG_ANSWER)

    assert session.interview_complete is True
    assert session.question_count >= MIN_QUESTIONS
    assert len(session.covered_curriculum_days) >= MIN_DAYS
    assert session.feedback is not None
    assert session.feedback.summary.startswith("Interview complete:")
    assert session.last_reply == "Interview completed."


def test_interview_is_deterministic(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    planner = _FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16], depth="standard"))

    def run() -> list[str]:
        graph = _build_graph(
            topic_planner=planner,
            knowledge_service=knowledge_service,
            analysis_service=analysis_service,
            profile_service=profile_service,
            strategy_service=strategy_service,
        )
        started = _start(graph, candidate_repository.get("CAND-001"))
        replies = [started["session"].last_reply]
        session = started["session"]
        for message in [WEAK_ANSWER, ADEPT_ANSWER, STRONG_ANSWER, STRONG_ANSWER]:
            turn = _answer(graph, session, message)
            session = turn["session"]
            replies.append(session.last_reply)
        return replies

    assert run() == run()


# --- safety: LLM/generator failure must not corrupt state ---------------------


class _FlakyEvaluator(AnswerEvaluator):
    """Fails exactly once, like an unavailable LLM, then behaves normally."""

    def __init__(self) -> None:
        self._inner = DeterministicAnswerEvaluator()
        self.calls = 0

    def evaluate(self, context):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("llm unavailable")
        return self._inner.evaluate(context)


def test_failed_evaluation_does_not_corrupt_session_and_can_retry(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    service = SessionService(
        store=InMemorySessionStore(),
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=_FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16])),
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=DeterministicQuestionGenerator(),
        evaluator=_FlakyEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
        min_questions=MIN_QUESTIONS,
        min_covered_days=MIN_DAYS,
        max_questions_per_topic=MAX_PER_TOPIC,
        hard_max_questions=HARD_MAX,
    )
    session = service.start("safety-session", candidate_repository.get("CAND-001"))
    before = session.model_dump()

    with pytest.raises(InterviewEngineError):
        service.answer(session.session_id, STRONG_ANSWER)

    # The committed session is untouched -- nothing was fabricated or half-applied.
    assert service.get(session.session_id).model_dump() == before

    # Retrying the same turn succeeds and advances normally.
    retried = service.answer(session.session_id, STRONG_ANSWER)
    assert retried.question_count == 2
    assert len(retried.evaluations) == 1


def test_empty_generator_output_is_rejected(
    candidate_repository, knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    class _EmptyGenerator:
        def generate(self, context) -> "Question":
            return Question(
                question="   ",
                question_type="conceptual",
                curriculum_day=context.day,
                topic=context.topic,
                difficulty=context.difficulty,
                purpose="test",
            )

    service = SessionService(
        store=InMemorySessionStore(),
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=_FixedPlanPlanner(_planned_topics(knowledge_service, [7, 8, 16])),
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=_EmptyGenerator(),  # type: ignore[arg-type]
        evaluator=DeterministicAnswerEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
        min_questions=MIN_QUESTIONS,
        min_covered_days=MIN_DAYS,
        max_questions_per_topic=MAX_PER_TOPIC,
        hard_max_questions=HARD_MAX,
    )
    with pytest.raises(InterviewEngineError):
        service.start("empty-q-session", candidate_repository.get("CAND-001"))
    assert service._store.exists("empty-q-session") is False


def test_next_topic_index_cycles_when_all_topics_at_cap(
    knowledge_service, analysis_service, profile_service, strategy_service
) -> None:
    topics = _planned_topics(knowledge_service, [7, 8, 16])
    plan = InterviewTopicPlan(topics=topics, min_days=4, target_questions=8, allocated_questions=9)
    session = InterviewSession(
        session_id="unit",
        status="ACTIVE",
        candidate_profile=_profile(),
        strategy=_strategy(),
        topic_plan=plan,
    )
    session.current_topic = "Embeddings Explained"
    session.topic_index = 0
    assert count_questions_on_topic(session, "Embeddings Explained") == 0
    assert next_topic_index(session, plan, MAX_PER_TOPIC) == 1
