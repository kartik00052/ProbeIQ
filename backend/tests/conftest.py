import pytest

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.services.candidate_service import CandidateAnalysisService
from app.services.curriculum_service import CurriculumSelectionService


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
