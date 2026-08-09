from typing import Any

from app.agents.evaluation_agent import AnswerEvaluator
from app.agents.feedback_agent import FeedbackGenerator
from app.agents.question_agent import QuestionGenerator
from app.core.exceptions import (
    AuthorizationError,
    InterviewEngineError,
    InvalidRequestError,
    ProbeIQError,
    SessionCompletedError,
    SessionConflictError,
)
from app.orchestration.graph import build_interview_graph
from app.repositories.session_store import InMemorySessionStore
from app.schemas.candidate import Candidate
from app.schemas.session import InterviewSession
from app.services.candidate_service import CandidateAnalysisService
from app.services.curriculum_knowledge import CurriculumKnowledgeService
from app.services.profile_service import ProfileService
from app.services.strategy_service import StrategyService
from app.services.topic_planner import TopicPlannerService


class SessionService:
    """Drives an interview session through its lifecycle (NEW -> ACTIVE -> COMPLETED).

    Each HTTP request maps to one LangGraph invocation. ``start`` seeds the graph
    with the raw candidate; every ``answer`` turn passes the committed session in
    as typed graph state. The ``InMemorySessionStore`` is the durable projection of
    the graph's final state and is only ever written after a successful run, so a
    failed invocation cannot corrupt session state and is safe to retry.
    """

    def __init__(
        self,
        *,
        store: InMemorySessionStore,
        analysis_service: CandidateAnalysisService,
        profile_service: ProfileService,
        topic_planner: TopicPlannerService,
        strategy_service: StrategyService,
        knowledge_service: CurriculumKnowledgeService,
        question_generator: QuestionGenerator,
        evaluator: AnswerEvaluator,
        feedback_generator: FeedbackGenerator,
        llm_engine: object | None = None,
        min_questions: int = 8,
        min_covered_days: int = 4,
        max_questions_per_topic: int = 3,
        hard_max_questions: int = 16,
    ) -> None:
        self._store = store
        self._llm_engine = llm_engine
        self._graph = build_interview_graph(
            analysis_service=analysis_service,
            profile_service=profile_service,
            topic_planner=topic_planner,
            strategy_service=strategy_service,
            knowledge_service=knowledge_service,
            question_generator=question_generator,
            evaluator=evaluator,
            feedback_generator=feedback_generator,
            min_questions=min_questions,
            min_covered_days=min_covered_days,
            max_questions_per_topic=max_questions_per_topic,
            hard_max_questions=hard_max_questions,
        )

    def start(
        self, session_id: str, candidate: Candidate, *, owner_user_id: str | None = None
    ) -> InterviewSession:
        if self._store.exists(session_id):
            raise SessionConflictError(f"session '{session_id}' already exists")
        result = self._invoke(
            lambda: self._graph.invoke({"action": "start", "session_id": session_id, "candidate": candidate})
        )
        session = self._session_from(result)
        if owner_user_id is not None:
            session.owner_user_id = owner_user_id
        self._store.create(session.model_copy(deep=True))
        return session

    def answer(
        self, session_id: str, message: str, *, owner_user_id: str | None = None
    ) -> InterviewSession:
        if not message or not message.strip():
            raise InvalidRequestError("message must not be empty")
        current = self._store.get(session_id)
        # Ownership enforcement: an owned session may only be driven by its owner.
        # Unowned sessions (created outside the authenticated API, e.g. unit
        # tests) keep the legacy open behavior.
        if current.owner_user_id is not None and current.owner_user_id != owner_user_id:
            raise AuthorizationError("session does not belong to the current user")
        if current.interview_complete:
            raise SessionCompletedError(f"session '{session_id}' is already complete")
        result = self._invoke(
            lambda: self._graph.invoke(
                {
                    "action": "answer",
                    "session_id": session_id,
                    "candidate_answer": message.strip(),
                    "session": current,
                }
            )
        )
        session = self._session_from(result)
        self._store.update(session.model_copy(deep=True))
        return session

    def get(self, session_id: str) -> InterviewSession:
        return self._store.get(session_id)

    @property
    def engine_info(self) -> dict[str, str | None]:
        """Which engine is driving interviews, for the frontend status badge.

        ``"offline"`` when the LLM is disabled (deterministic template/heuristic
        engine); ``"llm"`` plus the model name otherwise. The model name is the
        most recently used roster entry, or the primary model before any call.
        """
        if self._llm_engine is None:
            return {"engine": "offline", "model": None}
        model = getattr(self._llm_engine, "model", None) or getattr(
            self._llm_engine, "model_name", None
        )
        return {"engine": "llm", "model": str(model) if model else None}

    @staticmethod
    def _session_from(result: dict[str, Any]) -> InterviewSession:
        session = result.get("session")
        if session is None:
            raise InterviewEngineError("interview engine returned no session state")
        return session

    def _invoke(self, operation) -> dict[str, Any]:
        try:
            return operation()
        except ProbeIQError:
            raise
        except Exception as exc:
            raise InterviewEngineError("interview engine failed; no state was changed.") from exc
