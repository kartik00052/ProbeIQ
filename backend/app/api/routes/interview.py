from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, session_service
from app.models.user import User
from app.schemas.interview import InterviewRequest, InterviewResponse

router = APIRouter(prefix="/api", tags=["interview"])


@router.post("/interview", response_model=InterviewResponse)
def interview(
    payload: InterviewRequest, current_user: User = Depends(get_current_user)  # noqa: B008
) -> InterviewResponse:
    """Single endpoint per technical-spec.md: start with candidate, then message turns.

    Authentication is enforced server-side; every started session is bound to the
    authenticated user and can only be driven by that user.
    """
    owner_user_id = current_user.id
    if payload.candidate is not None:
        session = session_service.start(payload.sessionId, payload.candidate, owner_user_id=owner_user_id)
    else:
        assert payload.message is not None
        session = session_service.answer(payload.sessionId, payload.message, owner_user_id=owner_user_id)
    return InterviewResponse(
        reply=session.last_reply or "",
        done=session.interview_complete,
        feedback=session.feedback,
    )
