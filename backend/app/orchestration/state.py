"""Typed LangGraph state for the ProbeIQ interview engine.

State is explicit and never hidden in globals. All critical interview
information lives in ``session``; the remaining fields are per-node inputs and
outputs for the current graph run.
"""

from typing import Literal, TypedDict

from app.schemas.candidate import Candidate
from app.schemas.profile import CandidateInterviewProfile
from app.schemas.session import AnswerEvaluation, AnswerQuality, InterviewSession
from app.schemas.strategy import InterviewStrategy
from app.schemas.topic_plan import InterviewTopicPlan
from app.services.candidate_service import CandidateAnalysis

ProbeDecision = Literal[
    "FOLLOW_UP",
    "NEW_TOPIC",
    "INCREASE_DIFFICULTY",
    "DECREASE_DIFFICULTY",
    "COMPLETE",
]

_ALLOWED_DECISIONS: tuple[ProbeDecision, ...] = (
    "FOLLOW_UP",
    "NEW_TOPIC",
    "INCREASE_DIFFICULTY",
    "DECREASE_DIFFICULTY",
    "COMPLETE",
)


class InterviewGraphState(TypedDict, total=False):
    """State shared across graph nodes.

    ``session`` is the authoritative per-turn interview state and is passed in
    (for answer turns) or produced (for start turns) on every graph invocation;
    it is never hidden in a global. The remaining fields are per-node inputs and
    outputs for the current graph run.
    """

    # Init-phase fields.
    action: str | None
    session_id: str | None
    candidate: Candidate | None
    analysis: CandidateAnalysis | None
    profile: CandidateInterviewProfile | None
    plan: InterviewTopicPlan | None
    strategy: InterviewStrategy | None

    # Turn-phase fields.
    session: InterviewSession | None
    candidate_answer: str | None
    quality: AnswerQuality | None
    evaluation: AnswerEvaluation | None
    decision: ProbeDecision | None
    error: str | None
