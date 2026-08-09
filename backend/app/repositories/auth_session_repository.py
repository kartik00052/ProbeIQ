from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession


class AuthSessionRepository:
    """Data access for the persisted ``auth_sessions`` table."""

    def create(
        self, db: Session, *, token: str, user_id: str, expires_at: datetime
    ) -> AuthSession:
        session = AuthSession(token=token, user_id=user_id, expires_at=expires_at)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get(self, db: Session, token: str) -> AuthSession | None:
        return db.scalar(select(AuthSession).where(AuthSession.token == token))

    def delete(self, db: Session, token: str) -> None:
        db.execute(delete(AuthSession).where(AuthSession.token == token))
        db.commit()

    def delete_expired(self, db: Session, now: datetime) -> int:
        expired_tokens = db.scalars(select(AuthSession.token).where(AuthSession.expires_at < now)).all()
        if expired_tokens:
            db.execute(delete(AuthSession).where(AuthSession.token.in_(expired_tokens)))
            db.commit()
        return len(expired_tokens)
