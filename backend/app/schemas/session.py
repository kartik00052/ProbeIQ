from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.evaluation import Evaluation
from app.schemas.interview import InterviewFeedback
from app.schemas.profile import CandidateInterviewProfile
from app.schemas.strategy import InterviewStrategy
from app.schemas.topic_plan import InterviewTopicPlan

SessionStatus = Literal["NEW", "ACTIVE", "COMPLETED"]
Depth = Literal["standard", "high", "diagnostic"]
Level = Literal["foundational", "intermediate", "advanced"]
AnswerQuality = Literal["strong", "adequate", "weak"]


class AskedQuestion(BaseModel):
    question_number: int
    day: int
    topic: str
    text: str
    depth: Depth
    difficulty: Level
    follow_up_index: int
    question_type: str | None = None


class AnswerEvaluation(BaseModel):
    """Structured evaluation for one answer (deterministic in this phase)."""

    question_number: int
    day: int
    topic: str
    quality: AnswerQuality
    note: str
    details: Evaluation | None = None


class ConversationContext(BaseModel):
    """Compact structured context for future LLM calls -- never the raw transcript."""

    candidate_id: str
    role: str
    covered_topics: list[str]
    questions_asked: list[AskedQuestion]
    recent_responses: list[str]
    question_count: int
    follow_up_count: int
    difficulty: Level


class InterviewSession(BaseModel):
    """Typed state for a single interview conversation."""

    session_id: str
    status: SessionStatus
    candidate_profile: CandidateInterviewProfile
    strategy: InterviewStrategy
    topic_plan: InterviewTopicPlan

    selected_curriculum_days: list[int] = Field(default_factory=list)
    covered_curriculum_days: list[int] = Field(default_factory=list)
    covered_topics: list[str] = Field(default_factory=list)
    questions_asked: list[AskedQuestion] = Field(default_factory=list)
    candidate_responses: list[str] = Field(default_factory=list)
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)

    # Adaptive engine cursor: position inside the topic plan and follow-up depth
    # within the current topic. Read and advanced by the graph decision node.
    topic_index: int = 0
    follow_up_index: int = 0

    current_question: str | None = None
    current_topic: str | None = None
    current_day: int | None = None
    question_count: int = 0
    follow_up_count: int = 0
    difficulty: Level = "foundational"
    interview_complete: bool = False
    feedback: InterviewFeedback | None = None
    last_reply: str | None = None

    def to_conversation_context(self) -> ConversationContext:
        return ConversationContext(
            candidate_id=self.candidate_profile.candidate_id,
            role=self.candidate_profile.role,
            covered_topics=list(self.covered_topics),
            questions_asked=[question.model_copy() for question in self.questions_asked],
            recent_responses=list(self.candidate_responses[-3:]),
            question_count=self.question_count,
            follow_up_count=self.follow_up_count,
            difficulty=self.difficulty,
        )
