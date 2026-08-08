from typing import Literal

from pydantic import BaseModel

from app.schemas.candidate import Candidate, Mission, Outcome

Strength = Literal["strong", "moderate", "weak", "not_assessed"]


class MissionEvidence(BaseModel):
    day: int
    title: str
    outcome: Outcome
    attempts: int | None
    strength: Strength
    probe: bool
    note: str


class CandidateAnalysis(BaseModel):
    candidate: Candidate
    evidence: list[MissionEvidence]
    strong_days: list[int]
    probe_days: list[int]
    weak_days: list[int]
    not_assessed_days: list[int]


def assess_mission(mission: Mission) -> MissionEvidence:
    """Deterministic, inspectable evidence rule for a single mission."""
    if mission.skipped is True:
        return MissionEvidence(
            day=mission.day,
            title=mission.title,
            outcome="skipped",
            attempts=None,
            strength="not_assessed",
            probe=False,
            note="Skipped: not assessed / not completed.",
        )
    attempts = mission.attempts or 0
    if mission.passed is False:
        return MissionEvidence(
            day=mission.day,
            title=mission.title,
            outcome="failed",
            attempts=attempts,
            strength="weak",
            probe=False,
            note="Attempted but not passed: demonstrated difficulty.",
        )
    if attempts == 1:
        return MissionEvidence(
            day=mission.day,
            title=mission.title,
            outcome="passed",
            attempts=attempts,
            strength="strong",
            probe=False,
            note="Passed on first attempt: stronger positive signal.",
        )
    if attempts <= 3:
        return MissionEvidence(
            day=mission.day,
            title=mission.title,
            outcome="passed",
            attempts=attempts,
            strength="moderate",
            probe=False,
            note=f"Completed in {attempts} attempts.",
        )
    return MissionEvidence(
        day=mission.day,
        title=mission.title,
        outcome="passed",
        attempts=attempts,
        strength="moderate",
        probe=True,
        note=f"Completed after {attempts} attempts: completed but potentially worth probing.",
    )


class CandidateAnalysisService:
    """Transforms raw candidate data into interview evidence."""

    def analyze(self, candidate: Candidate) -> CandidateAnalysis:
        evidence = [assess_mission(mission) for mission in candidate.missions]
        return CandidateAnalysis(
            candidate=candidate,
            evidence=evidence,
            strong_days=[item.day for item in evidence if item.strength == "strong"],
            probe_days=[item.day for item in evidence if item.probe],
            weak_days=[item.day for item in evidence if item.strength == "weak"],
            not_assessed_days=[item.day for item in evidence if item.strength == "not_assessed"],
        )
