from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.session import Level

QuestionType = Literal[
    "conceptual",
    "implementation",
    "architecture",
    "debugging",
    "scenario",
    "trade-off",
    "production",
    "follow-up",
]


class Question(BaseModel):
    """Validated output of the question generator (Phase 5).

    Only what the application needs; no internal chain-of-thought is exposed.
    """

    question: str = Field(min_length=1)
    question_type: QuestionType
    curriculum_day: int = Field(ge=1)
    topic: str = Field(min_length=1)
    difficulty: Level
    purpose: str = Field(min_length=1)
