from pydantic import BaseModel

from app.schemas.candidate import Outcome


class TopicEvidence(BaseModel):
    """Evidence for a single curriculum topic, expressed as a signal rather than a verdict."""

    day: int
    title: str
    outcome: Outcome
    attempts: int | None
    category: str
    note: str


class CandidateInterviewProfile(BaseModel):
    """Application-level representation of what is useful for interviewing.

    Contains only derived evidence and role context -- never the raw candidate
    payload. ``recommended_topics`` is the deterministic, interview-oriented
    ordering of topics produced from candidate evidence.
    """

    candidate_id: str
    role: str
    experience: int
    role_is_technical: bool
    completed_days: list[int]
    failed_days: list[int]
    skipped_days: list[int]
    high_attempt_days: list[int]
    strong_evidence_topics: list[TopicEvidence]
    uncertain_topics: list[TopicEvidence]
    recommended_topics: list[TopicEvidence]
