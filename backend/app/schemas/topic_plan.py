from typing import Literal

from pydantic import BaseModel

Depth = Literal["standard", "high", "diagnostic"]


class PlannedTopic(BaseModel):
    """A curriculum topic with an initial questioning budget and depth."""

    day: int
    title: str
    outcome: str
    module: int
    module_title: str
    depth: Depth
    probe: bool
    question_slots: int
    reason: str


class InterviewTopicPlan(BaseModel):
    """Deterministic initial topic plan for an interview."""

    topics: list[PlannedTopic]
    min_days: int
    target_questions: int
    allocated_questions: int
