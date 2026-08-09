import os
import tempfile
from pathlib import Path

import pytest

# The offline suite must stay deterministic regardless of the developer's
# backend/.env: force the LLM off unless the opt-in live LLM test run
# (PROBEIQ_LIVE_LLM_TEST=true) explicitly requests the real model.
# The env var is set before any app import so the Settings singleton in
# app.core.config (and the API's module-level LLM construction) sees it.
if os.getenv("PROBEIQ_LIVE_LLM_TEST") != "true":
    os.environ["PROBEIQ_LLM_ENABLED"] = "false"

# Isolate the auth database: point the app at a throwaway SQLite file so tests
# never touch (or require) a developer's real app/data/probeiq.db.
if os.getenv("PROBEIQ_DATABASE_URL") is None:
    _tmp_dir = Path(tempfile.mkdtemp(prefix="probeiq-test-auth-"))
    os.environ["PROBEIQ_DATABASE_URL"] = f"sqlite:///{_tmp_dir.as_posix()}/test.db"

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
