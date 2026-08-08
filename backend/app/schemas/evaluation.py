from typing import Literal

from pydantic import BaseModel, Field

DepthLevel = Literal["none", "shallow", "moderate", "deep", "excellent"]

#: WHAT the next probe should target. The deterministic probe controller
#: (``app.orchestration.decision``) still decides whether that probe is a
#: FOLLOW_UP, a NEW_TOPIC, or a difficulty change.
ProbeFocus = Literal[
    "architecture",
    "trade-off",
    "failure_scenario",
    "missing_concept",
    "fundamental_understanding",
    "production_depth",
    "evidence_clarification",
]


class DimensionScores(BaseModel):
    """Per-dimension 0-5 scores that back the overall score (kept explainable)."""

    technical_correctness: int = Field(ge=0, le=5)
    conceptual_depth: int = Field(ge=0, le=5)
    reasoning_quality: int = Field(ge=0, le=5)
    practical_understanding: int = Field(ge=0, le=5)
    tradeoff_awareness: int = Field(ge=0, le=5)
    communication_clarity: int = Field(ge=0, le=5)


class Evaluation(BaseModel):
    """Structured evaluation for one answer (Phase 6).

    ``recommended_probe`` is a hint for the next question: WHAT to probe next.
    The deterministic probe controller (decision.py) decides whether that probe
    becomes a FOLLOW_UP, NEW_TOPIC, or a difficulty change.
    """

    score: int = Field(ge=0, le=100)
    assessment: str
    strengths: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    depth_level: DepthLevel
    follow_up_needed: bool
    follow_up_reason: str | None = None
    recommended_probe: ProbeFocus | None = None
