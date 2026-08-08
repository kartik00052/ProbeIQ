from app.schemas.profile import CandidateInterviewProfile, TopicEvidence
from app.services.candidate_service import CandidateAnalysis, MissionEvidence

HIGH_ATTEMPT_THRESHOLD = 4

_TECHNICAL_ROLE_KEYWORDS = (
    "AI",
    "data",
    "machine learning",
    "ML",
    "software",
    "backend",
    "engineer",
    "engineering",
    "developer",
    "devops",
    "architect",
    "platform",
    "cloud",
    "technical",
)


def _role_is_technical(role: str) -> bool:
    lowered = role.lower()
    return any(keyword in lowered for keyword in _TECHNICAL_ROLE_KEYWORDS)


def _evidence_note(evidence: MissionEvidence) -> str:
    if evidence.outcome == "skipped":
        return "Skipped: not assessed / no evidence of mastery."
    if evidence.outcome == "failed":
        return f"Attempted but not passed after {evidence.attempts} attempt(s): demonstrated difficulty."
    if evidence.attempts == 1:
        return "Passed on the first attempt."
    if evidence.probe:
        return f"Passed after {evidence.attempts} attempt(s): completed, but worth probing."
    return f"Passed after {evidence.attempts} attempt(s)."


def _topic_evidence(evidence: MissionEvidence, category: str, role_context: str | None) -> TopicEvidence:
    note = _evidence_note(evidence)
    if role_context is not None:
        note = f"{note} Role context ({role_context}) -- useful for scenario questions."
    return TopicEvidence(
        day=evidence.day,
        title=evidence.title,
        outcome=evidence.outcome,
        attempts=evidence.attempts,
        category=category,
        note=note,
    )


class ProfileService:
    """Builds the interview-facing candidate profile from deterministic evidence."""

    def build(self, analysis: CandidateAnalysis) -> CandidateInterviewProfile:
        member = analysis.candidate.member
        technical = _role_is_technical(member.jobRole)
        role_context = member.jobRole if technical else None

        strong: list[TopicEvidence] = []
        uncertain: list[TopicEvidence] = []
        recommended_strong: list[TopicEvidence] = []
        recommended_uncertain: list[TopicEvidence] = []

        for evidence in analysis.evidence:
            if evidence.outcome == "passed" and evidence.attempts == 1:
                item = _topic_evidence(evidence, "strong", role_context)
                strong.append(item)
                recommended_strong.append(item)
            elif evidence.outcome == "passed" and evidence.probe:
                item = _topic_evidence(evidence, "uncertain", role_context)
                uncertain.append(item)
                recommended_uncertain.append(item)
            elif evidence.outcome == "failed":
                item = _topic_evidence(evidence, "uncertain", None)
                uncertain.append(item)
                recommended_uncertain.append(item)
            elif evidence.outcome == "passed":
                item = _topic_evidence(evidence, "moderate", role_context)
                uncertain.append(item)
            else:
                item = _topic_evidence(evidence, "not_assessed", None)
                uncertain.append(item)

        recommended = [*recommended_strong, *recommended_uncertain]

        return CandidateInterviewProfile(
            candidate_id=member.id,
            role=member.jobRole,
            experience=member.yearsExperience,
            role_is_technical=technical,
            completed_days=[item.day for item in analysis.evidence if item.outcome == "passed"],
            failed_days=[item.day for item in analysis.evidence if item.outcome == "failed"],
            skipped_days=[item.day for item in analysis.evidence if item.outcome == "skipped"],
            high_attempt_days=[
                item.day
                for item in analysis.evidence
                if item.attempts is not None and item.attempts >= HIGH_ATTEMPT_THRESHOLD
            ],
            strong_evidence_topics=strong,
            uncertain_topics=uncertain,
            recommended_topics=recommended,
        )
