from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateAccountError, InvalidCredentialsError
from app.core.security import generate_session_token, hash_password, verify_password
from app.models.auth_session import AuthSession
from app.models.user import User
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    """Registration, credential verification, and server-side session lifecycle."""

    def __init__(
        self,
        users: UserRepository,
        sessions: AuthSessionRepository,
        *,
        session_ttl_seconds: int,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._session_ttl_seconds = session_ttl_seconds

    def register(self, db: Session, *, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if self._users.get_by_email(db, normalized_email) is not None:
            raise DuplicateAccountError("an account with this email already exists")
        user = self._users.create(
            db, email=normalized_email, password_hash=hash_password(password)
        )
        return user

    def authenticate(self, db: Session, *, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        user = self._users.get_by_email(db, normalized_email)
        if user is None or not verify_password(password, user.password_hash):
            # Single generic message: do not reveal whether the account exists.
            raise InvalidCredentialsError("email or password is incorrect")
        return user

    def create_session(self, db: Session, user: User) -> AuthSession:
        return self._sessions.create(
            db,
            token=generate_session_token(),
            user_id=user.id,
            expires_at=AuthSession.expires_after(self._session_ttl_seconds),
        )

    def resolve_session_user(self, db: Session, token: str | None) -> User | None:
        """Return the user for a valid, unexpired session token, else None."""
        if not token:
            return None
        session = self._sessions.get(db, token)
        if session is None or session.is_expired:
            return None
        return self._users.get_by_id(db, session.user_id)

    def revoke(self, db: Session, token: str) -> None:
        self._sessions.delete(db, token)

    def prune_expired(self, db: Session) -> int:
        return self._sessions.delete_expired(db, datetime.now(UTC))
