from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import auth_service
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    MeResponse,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/")


@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> User:  # noqa: B008
    """Create an account and start an authenticated session (HTTP-only cookie)."""
    user = auth_service.register(db, email=payload.email, password=payload.password)
    session = auth_service.create_session(db, user)
    _set_session_cookie(response, session.token)
    return user


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:  # noqa: B008
    """Verify credentials and start an authenticated session (HTTP-only cookie)."""
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    session = auth_service.create_session(db, user)
    _set_session_cookie(response, session.token)
    return user


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request, response: Response, db: Session = Depends(get_db)  # noqa: B008
) -> LogoutResponse:
    """Revoke the current session server-side and clear the cookie."""
    token = request.cookies.get(settings.auth_cookie_name)
    if token:
        auth_service.revoke(db, token)
    _clear_session_cookie(response)
    return LogoutResponse(detail="logged out")


@router.get("/me", response_model=MeResponse)
def me(request: Request, db: Session = Depends(get_db)) -> MeResponse:  # noqa: B008
    """Return the current user, or ``{user: null}`` when there is no valid session.

    Always 200 so the frontend can safely probe session validity on boot without
    triggering a noisy 401. The protected endpoints themselves still enforce
    authentication via ``get_current_user``.
    """
    user = auth_service.resolve_session_user(db, request.cookies.get(settings.auth_cookie_name))
    return MeResponse(user=UserResponse(id=user.id, email=user.email) if user else None)
