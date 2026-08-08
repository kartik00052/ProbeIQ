from pydantic import BaseModel, Field, model_validator

from app.schemas.candidate import Candidate


class InterviewStartRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    candidate: Candidate


class InterviewMessageRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    message: str


class InterviewFeedback(BaseModel):
    summary: str
    strengths: list[str]
    gaps: list[str]
    next: list[str]


class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: InterviewFeedback | None = None


class InterviewRequest(BaseModel):
    """Single endpoint payload: exactly one of ``candidate`` (start) or ``message`` (turn)."""

    sessionId: str = Field(min_length=1)
    candidate: Candidate | None = None
    message: str | None = None

    @model_validator(mode="after")
    def _exactly_one_of_candidate_or_message(self) -> "InterviewRequest":
        has_candidate = self.candidate is not None
        has_message = self.message is not None
        if has_candidate == has_message:
            raise ValueError(
                "request must provide exactly one of 'candidate' (start) or 'message' (conversation turn)"
            )
        return self
