from app.core.exceptions import InterviewEngineError
from app.orchestration.state import InterviewGraphState
from app.schemas.candidate import Candidate
from app.services.candidate_service import CandidateAnalysisService
from app.services.profile_service import ProfileService


def build_analyze_candidate(
    analysis_service: CandidateAnalysisService,
    profile_service: ProfileService,
):
    """Analyze candidate learning evidence and build the interview profile."""

    def analyze_candidate(state: InterviewGraphState) -> dict:
        candidate: Candidate | None = state.get("candidate")
        if candidate is None:
            raise InterviewEngineError("candidate payload missing from start request")
        analysis = analysis_service.analyze(candidate)
        profile = profile_service.build(analysis)
        return {"analysis": analysis, "profile": profile}

    return analyze_candidate
