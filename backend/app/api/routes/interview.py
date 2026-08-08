from fastapi import APIRouter

from app.schemas.interview import InterviewRequest, InterviewResponse

router = APIRouter(prefix="/api", tags=["interview"])

DEV_START_REPLY = (
    "[dev] Session {session} initialized. The ProbeIQ interview engine is not "
    "implemented in this foundation build yet."
)
DEV_TURN_REPLY = (
    "[dev] Message received for session {session}. The ProbeIQ interview engine is not "
    "implemented in this foundation build yet."
)


@router.post("/interview", response_model=InterviewResponse)
def interview(payload: InterviewRequest) -> InterviewResponse:
    """Single endpoint per technical-spec.md: start with candidate, then message turns."""
    if payload.candidate is not None:
        return InterviewResponse(reply=DEV_START_REPLY.format(session=payload.sessionId), done=False)
    return InterviewResponse(reply=DEV_TURN_REPLY.format(session=payload.sessionId), done=False)
