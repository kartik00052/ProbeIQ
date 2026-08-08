from pydantic import BaseModel, Field

from app.schemas.evaluation import ProbeFocus
from app.schemas.session import AnswerQuality, Level


class QuestionContext(BaseModel):
    """Everything a question generator should see for the next question.

    Deliberately compact: candidate identity, current topic grounding, adaptive
    difficulty, and only the immediately relevant conversation history.
    """

    candidate_id: str
    role: str
    experience: int
    day: int
    topic: str
    module: str
    objectives: list[str]
    tools: list[str]
    difficulty: Level
    follow_up_index: int
    previous_question: str | None
    previous_answer: str | None
    previous_quality: AnswerQuality | None
    previous_evaluation: str | None = None
    probe_focus: ProbeFocus | None = None
    covered_days: list[int]
    question_number: int
    min_questions: int
    min_covered_days: int
    interview_objective: str
    completion_evidence: bool


class EvaluationContext(BaseModel):
    """Input for answer evaluation: the question asked, the candidate's answer,
    and the curriculum + candidate evidence needed to judge depth.

    ``topic_evidence`` carries the candidate's learning signal for this topic
    (for example "Passed on the first attempt." or "Skipped: not assessed.").
    It is evidence for where to probe -- never a verdict on the answer.
    """

    question_number: int
    day: int
    topic: str
    question: str
    answer: str
    objectives: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    role: str = ""
    experience: int = 0
    topic_evidence: str | None = None
    prior_quality: AnswerQuality | None = None
