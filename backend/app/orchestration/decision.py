"""Deterministic, inspectable probe-decision rules for the adaptive interview engine.

The engine never picks the next step randomly. Every decision is derived from the
evaluation of the last answer, the question history, the current topic, curriculum
coverage, and the question count:

- a ``weak`` answer is a signal to diagnose, so difficulty drops (or stays at the
  floor) and a focused follow-up is asked;
- an ``adequate`` answer gets a focused follow-up on the same topic;
- a ``strong`` answer deepens the topic once, then moves on to a new curriculum
  day so a strong candidate cannot stay on one topic indefinitely;
- completion requires the minimum question count AND minimum covered days, so the
  engine continues (rotating topics) until both requirements are met.
"""

from app.orchestration.difficulty import base_level, decrease, increase
from app.orchestration.state import ProbeDecision
from app.schemas.evaluation import Evaluation, ProbeFocus
from app.schemas.session import AnswerQuality, InterviewSession
from app.schemas.topic_plan import InterviewTopicPlan, PlannedTopic

# Number of strong answers on one topic before the engine forces a transition.
STRONG_ANSWERS_BEFORE_TRANSITION = 2


def quality_from_evaluation(evaluation: Evaluation) -> AnswerQuality:
    """Map the Phase 6 structured evaluation to the engine's coarse quality.

    Misconceptions and low scores are weak signals; a strong score with deep or
    excellent depth is a strong signal; everything else is adequate. This keeps
    the existing ``decide`` controller unchanged while consuming richer input.
    """
    if evaluation.misconceptions or evaluation.score < 55:
        return "weak"
    if evaluation.score >= 80 and evaluation.depth_level in ("deep", "excellent"):
        return "strong"
    return "adequate"


def recommended_probe(evaluation: Evaluation) -> ProbeFocus:
    """Phase 6 probe rules: WHAT the next question should probe.

    Deterministic and inspectable -- this is the ``WHAT to probe`` half of the
    controller. The LLM (when enabled) only decides HOW to phrase that probe.
    """
    if evaluation.misconceptions:
        return "fundamental_understanding"
    if evaluation.depth_level == "excellent":
        return "production_depth"
    if evaluation.depth_level == "deep":
        return "architecture"
    if evaluation.missing_concepts:
        return "missing_concept"
    return "evidence_clarification"


def count_questions_on_topic(session: InterviewSession, topic_title: str) -> int:
    """Number of questions already asked on ``topic_title``."""
    return sum(1 for question in session.questions_asked if question.topic == topic_title)


def next_topic_index(
    session: InterviewSession,
    plan: InterviewTopicPlan,
    max_questions_per_topic: int,
) -> int:
    """Next topic index: prefer a topic below its question cap, else keep cycling."""
    topics = plan.topics
    current = session.topic_index
    if not topics:
        return current
    for offset in range(1, len(topics) + 1):
        index = (current + offset) % len(topics)
        if count_questions_on_topic(session, topics[index].title) < max_questions_per_topic:
            return index
    return (current + 1) % len(topics)


def decide(
    session: InterviewSession,
    quality: AnswerQuality,
    *,
    min_questions: int,
    min_covered_days: int,
    max_questions_per_topic: int,
    hard_max_questions: int,
) -> ProbeDecision:
    """Return the probe decision for the just-evaluated answer.

    Completion gates are checked first: the interview may only complete normally
    once the minimum question count and minimum covered days are both satisfied,
    and a weak answer never triggers completion. ``hard_max_questions`` is a
    safety valve that terminates an interview that could never satisfy coverage.
    """
    question_count = session.question_count
    covered_days = len(session.covered_curriculum_days)
    requirements_met = question_count >= min_questions and covered_days >= min_covered_days
    if requirements_met and quality != "weak":
        return "COMPLETE"
    if question_count >= hard_max_questions:
        return "COMPLETE"

    topic_questions = count_questions_on_topic(session, session.current_topic or "")
    if topic_questions >= max_questions_per_topic:
        return "NEW_TOPIC"

    if quality == "weak":
        if session.difficulty != "foundational":
            return "DECREASE_DIFFICULTY"
        return "FOLLOW_UP"
    if quality == "adequate":
        return "FOLLOW_UP"

    # Strong answer: deepen once, then move to another curriculum day.
    if session.difficulty != "advanced" and topic_questions < STRONG_ANSWERS_BEFORE_TRANSITION:
        return "INCREASE_DIFFICULTY"
    return "NEW_TOPIC"


def apply_decision(
    session: InterviewSession,
    decision: ProbeDecision,
    *,
    max_questions_per_topic: int,
) -> InterviewSession:
    """Advance the session cursor according to ``decision``.

    Called with a fresh deep copy of the session so the previous committed state is
    never mutated in place. Difficulty and topic transitions are applied here and
    are consumed by the next ``generate_question`` execution.
    """
    if decision == "COMPLETE":
        return session

    if decision == "NEW_TOPIC":
        session.topic_index = next_topic_index(session, session.topic_plan, max_questions_per_topic)
        session.follow_up_index = 0
        if session.topic_plan.topics:
            session.difficulty = base_level(session.topic_plan.topics[session.topic_index].depth)
        return session

    session.follow_up_index += 1
    if decision == "INCREASE_DIFFICULTY":
        session.difficulty = increase(session.difficulty)
    elif decision == "DECREASE_DIFFICULTY":
        session.difficulty = decrease(session.difficulty)
    return session


def planned_topic(session: InterviewSession) -> PlannedTopic:
    """The planned topic the engine should ask about next."""
    return session.topic_plan.topics[session.topic_index]
