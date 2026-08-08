import pytest

from app.agents.evaluation_agent import DeterministicAnswerEvaluator
from app.agents.feedback_agent import DeterministicFeedbackGenerator
from app.agents.question_agent import DeterministicQuestionGenerator
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


@pytest.fixture(scope="session")
def candidate_repository() -> CandidateRepository:
    return CandidateRepository()


@pytest.fixture(scope="session")
def curriculum_repository() -> CurriculumRepository:
    return CurriculumRepository()


@pytest.fixture(scope="session")
def analysis_service() -> CandidateAnalysisService:
    return CandidateAnalysisService()


@pytest.fixture(scope="session")
def selection_service(curriculum_repository: CurriculumRepository) -> CurriculumSelectionService:
    return CurriculumSelectionService(curriculum_repository)


@pytest.fixture(scope="session")
def knowledge_service(curriculum_repository: CurriculumRepository) -> CurriculumKnowledgeService:
    return CurriculumKnowledgeService(curriculum_repository)


@pytest.fixture(scope="session")
def profile_service() -> ProfileService:
    return ProfileService()


@pytest.fixture(scope="session")
def planner_service(
    selection_service: CurriculumSelectionService,
    knowledge_service: CurriculumKnowledgeService,
) -> TopicPlannerService:
    return TopicPlannerService(selection_service, knowledge_service)


@pytest.fixture(scope="session")
def strategy_service(knowledge_service: CurriculumKnowledgeService) -> StrategyService:
    return StrategyService(knowledge_service)


@pytest.fixture(scope="session")
def session_service(
    analysis_service: CandidateAnalysisService,
    profile_service: ProfileService,
    planner_service: TopicPlannerService,
    strategy_service: StrategyService,
    knowledge_service: CurriculumKnowledgeService,
) -> SessionService:
    return SessionService(
        store=InMemorySessionStore(),
        analysis_service=analysis_service,
        profile_service=profile_service,
        topic_planner=planner_service,
        strategy_service=strategy_service,
        knowledge_service=knowledge_service,
        question_generator=DeterministicQuestionGenerator(),
        evaluator=DeterministicAnswerEvaluator(),
        feedback_generator=DeterministicFeedbackGenerator(),
    )
