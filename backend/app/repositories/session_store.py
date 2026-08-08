import threading

from app.core.exceptions import SessionConflictError, SessionNotFoundError
from app.schemas.session import InterviewSession


class InMemorySessionStore:
    """Simplest reliable session store: process-local, mutex-protected.

    Suitable for the hackathon. Does not persist across restarts and is not
    shared between processes.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, InterviewSession] = {}
        self._lock = threading.RLock()

    def create(self, session: InterviewSession) -> InterviewSession:
        with self._lock:
            if session.session_id in self._sessions:
                raise SessionConflictError(f"session '{session.session_id}' already exists")
            self._sessions[session.session_id] = session
            return session

    def get(self, session_id: str) -> InterviewSession:
        with self._lock:
            if session_id not in self._sessions:
                raise SessionNotFoundError(f"session '{session_id}' not found")
            return self._sessions[session_id].model_copy(deep=True)

    def update(self, session: InterviewSession) -> InterviewSession:
        with self._lock:
            if session.session_id not in self._sessions:
                raise SessionNotFoundError(f"session '{session.session_id}' not found")
            self._sessions[session.session_id] = session
            return session

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions
