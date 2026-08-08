from fastapi import APIRouter

from app.api.dependencies import session_service
from app.schemas.interview import InterviewRequest, InterviewResponse

router = APIRouter(prefix="/api", tags=["interview"])


@router.post("/interview", response_model=InterviewResponse)
def interview(payload: InterviewRequest) -> InterviewResponse:
    """Single endpoint per technical-spec.md: start with candidate, then message turns."""
    if payload.candidate is not None:
        session = session_service.start(payload.sessionId, payload.candidate)
    else:
        assert payload.message is not None
        session = session_service.answer(payload.sessionId, payload.message)
    return InterviewResponse(
        reply=session.last_reply or "",
        done=session.interview_complete,
        feedback=session.feedback,
    )
