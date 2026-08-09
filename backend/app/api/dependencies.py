from fastapi import Depends, Request
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.agents.evaluation_agent import (
    AnswerEvaluator,
    DeterministicAnswerEvaluator,
    LLMAnswerEvaluator,
)
from app.agents.feedback_agent import (
    DeterministicFeedbackGenerator,
    FeedbackGenerator,
    LLMFeedbackGenerator,
)
from app.agents.question_agent import (
    DeterministicQuestionGenerator,
    LLMQuestionGenerator,
    QuestionGenerator,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.llm.factory import generation_caps, get_llm
from app.llm.fallback import FallbackChatModel
from app.models.user import User
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.repositories.session_store import InMemorySessionStore
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.candidate_service import CandidateAnalysisService
from app.services.curriculum_knowledge import CurriculumKnowledgeService
from app.services.curriculum_service import CurriculumSelectionService
from app.services.profile_service import ProfileService
from app.services.session_service import SessionService
from app.services.strategy_service import StrategyService
from app.services.topic_planner import TopicPlannerService

candidate_repository = CandidateRepository()
curriculum_repository = CurriculumRepository()
candidate_analysis_service = CandidateAnalysisService()
curriculum_selection_service = CurriculumSelectionService(curriculum_repository)
curriculum_knowledge_service = CurriculumKnowledgeService(curriculum_repository)
profile_service = ProfileService()
topic_planner_service = TopicPlannerService(curriculum_selection_service, curriculum_knowledge_service)
strategy_service = StrategyService(curriculum_knowledge_service)
session_store = InMemorySessionStore()

user_repository = UserRepository()
auth_session_repository = AuthSessionRepository()
auth_service = AuthService(
    user_repository,
    auth_session_repository,
    session_ttl_seconds=settings.auth_session_ttl_seconds,
)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:  # noqa: B008
    """FastAPI dependency: resolve the authenticated user from the session cookie.

    Raises 401 ``not_authenticated`` when no valid session is present. This is
    the single authorization gate for protected endpoints — frontend route
    guards are UX only.
    """
    token = request.cookies.get(settings.auth_cookie_name)
    user = auth_service.resolve_session_user(db, token)
    if user is None:
        raise AuthenticationError("authentication required")
    return user


def _build_llm() -> ChatOpenAI | ChatNVIDIA | FallbackChatModel | None:
    """Configured LangChain chat model via the central factory; ``None`` = offline.

    The factory validates provider/settings and never returns a model when the
    LLM is disabled, so the deterministic template generator and heuristic
    evaluator remain the offline default. When a roster is configured the
    returned ``FallbackChatModel`` retries across models automatically.
    """
    return get_llm()


def _question_generator(
    llm: ChatOpenAI | ChatNVIDIA | FallbackChatModel | None,
) -> QuestionGenerator:
    if llm is not None:
        return LLMQuestionGenerator(llm, call_kwargs=generation_caps(settings, max_tokens=1024))
    return DeterministicQuestionGenerator()


def _answer_evaluator(
    llm: ChatOpenAI | ChatNVIDIA | FallbackChatModel | None,
) -> AnswerEvaluator:
    if llm is not None:
        return LLMAnswerEvaluator(llm, call_kwargs=generation_caps(settings, max_tokens=2048))
    return DeterministicAnswerEvaluator()


def _feedback_generator(
    llm: ChatOpenAI | ChatNVIDIA | FallbackChatModel | None,
) -> FeedbackGenerator:
    if llm is not None:
        return LLMFeedbackGenerator(llm, call_kwargs=generation_caps(settings, max_tokens=2048))
    return DeterministicFeedbackGenerator()


# One shared LLM engine across the question generator, evaluator, and feedback
# writer, so the fallback roster's "last used model" reflects the whole turn and
# the API response can report it via ``session_service.engine_info``.
llm_engine: ChatOpenAI | ChatNVIDIA | FallbackChatModel | None = _build_llm()

session_service = SessionService(
    store=session_store,
    analysis_service=candidate_analysis_service,
    profile_service=profile_service,
    topic_planner=topic_planner_service,
    strategy_service=strategy_service,
    knowledge_service=curriculum_knowledge_service,
    question_generator=_question_generator(llm_engine),
    evaluator=_answer_evaluator(llm_engine),
    feedback_generator=_feedback_generator(llm_engine),
    llm_engine=llm_engine,
    min_questions=settings.min_questions,
    min_covered_days=settings.min_covered_days,
    max_questions_per_topic=settings.max_questions_per_topic,
    hard_max_questions=settings.hard_max_questions,
)
