from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuthSession(Base):
    """Server-side opaque session token, stored until logout or expiry.

    The token is delivered to the browser as an HTTP-only cookie; revoking the
    row (logout) invalidates it immediately. Expired rows are pruned lazily.
    """

    __tablename__ = "auth_sessions"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship()

    @property
    def is_expired(self) -> bool:
        now = datetime.now(UTC)
        expires_at = self.expires_at
        # SQLite round-trips aware UTC datetimes as naive; normalize before comparing.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return now >= expires_at

    @staticmethod
    def expires_after(ttl_seconds: int) -> datetime:
        return datetime.now(UTC) + timedelta(seconds=ttl_seconds)
