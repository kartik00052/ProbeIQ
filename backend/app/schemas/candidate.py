from typing import Literal

from pydantic import BaseModel, Field, model_validator

Outcome = Literal["passed", "failed", "skipped"]


class CandidateMember(BaseModel):
    id: str
    name: str
    jobRole: str
    yearsExperience: int = Field(ge=0)
    education: str
    status: str


class Mission(BaseModel):
    day: int = Field(ge=1)
    title: str
    passed: bool | None = None
    skipped: bool | None = None
    attempts: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _validate_mission_form(self) -> "Mission":
        if self.skipped is True:
            if self.passed is not None or self.attempts is not None:
                raise ValueError("a skipped mission must not carry passed or attempts")
            return self
        if self.passed is None:
            raise ValueError("mission must declare either passed or skipped")
        if self.attempts is None:
            raise ValueError("a non-skipped mission requires attempts")
        return self


class CandidateSignals(BaseModel):
    commitDays: int = Field(ge=0)
    missionsCompleted: int = Field(ge=0)
    missionsFirstTry: int = Field(ge=0)


class Candidate(BaseModel):
    member: CandidateMember
    missions: list[Mission]
    signals: CandidateSignals
