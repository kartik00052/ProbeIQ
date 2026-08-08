from langchain_openai import ChatOpenAI
from pydantic import SecretStr

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
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.repositories.session_store import InMemorySessionStore
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


def _build_llm() -> ChatOpenAI | None:
    """OpenAI-compatible chat model when LLM integration is enabled and configured."""
    if not (settings.llm_enabled and settings.llm_api_key and settings.llm_model):
        return None
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=SecretStr(settings.llm_api_key),
        base_url=settings.llm_base_url or None,
        temperature=settings.llm_temperature,
    )


def _question_generator() -> QuestionGenerator:
    llm = _build_llm()
    if llm is not None:
        return LLMQuestionGenerator(llm)
    return DeterministicQuestionGenerator()


def _answer_evaluator() -> AnswerEvaluator:
    llm = _build_llm()
    if llm is not None:
        return LLMAnswerEvaluator(llm)
    return DeterministicAnswerEvaluator()


def _feedback_generator() -> FeedbackGenerator:
    llm = _build_llm()
    if llm is not None:
        return LLMFeedbackGenerator(llm)
    return DeterministicFeedbackGenerator()


session_service = SessionService(
    store=session_store,
    analysis_service=candidate_analysis_service,
    profile_service=profile_service,
    topic_planner=topic_planner_service,
    strategy_service=strategy_service,
    knowledge_service=curriculum_knowledge_service,
    question_generator=_question_generator(),
    evaluator=_answer_evaluator(),
    feedback_generator=_feedback_generator(),
    min_questions=settings.min_questions,
    min_covered_days=settings.min_covered_days,
    max_questions_per_topic=settings.max_questions_per_topic,
    hard_max_questions=settings.hard_max_questions,
)
