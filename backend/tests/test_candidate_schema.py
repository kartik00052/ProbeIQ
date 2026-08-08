import pytest
from pydantic import ValidationError

from app.schemas.candidate import Mission


def test_mission_passed_form() -> None:
    mission = Mission(day=7, title="Embeddings Explained", passed=True, attempts=1)
    assert mission.passed is True
    assert mission.attempts == 1


def test_mission_failed_form() -> None:
    mission = Mission(day=8, title="Vector Databases Overview", passed=False, attempts=4)
    assert mission.passed is False
    assert mission.attempts == 4


def test_mission_skipped_form() -> None:
    mission = Mission(day=29, title="Monitoring", skipped=True)
    assert mission.skipped is True
    assert mission.passed is None
    assert mission.attempts is None


def test_skipped_mission_must_not_have_attempts() -> None:
    with pytest.raises(ValidationError):
        Mission(day=29, title="Monitoring", skipped=True, attempts=2)


def test_mission_requires_outcome() -> None:
    with pytest.raises(ValidationError):
        Mission(day=7, title="Embeddings Explained")


def test_passed_mission_requires_attempts() -> None:
    with pytest.raises(ValidationError):
        Mission(day=7, title="Embeddings Explained", passed=True)


def test_zero_attempts_rejected() -> None:
    with pytest.raises(ValidationError):
        Mission(day=7, title="Embeddings Explained", passed=True, attempts=0)


def test_negative_years_experience_rejected() -> None:
    from app.schemas.candidate import CandidateMember

    with pytest.raises(ValidationError):
        CandidateMember(
            id="CAND-000",
            name="X",
            jobRole="Y",
            yearsExperience=-1,
            education="Z",
            status="COMPLETED",
        )
