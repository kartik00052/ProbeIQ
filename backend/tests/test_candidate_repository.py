import pytest

from app.core.exceptions import CandidateNotFoundError


def test_loads_all_candidates(candidate_repository) -> None:
    candidates = candidate_repository.all()
    assert len(candidates) == 20


def test_find_candidate_by_id(candidate_repository) -> None:
    candidate = candidate_repository.get("CAND-003")
    assert candidate.member.name == "Emily Chen"
    assert candidate.member.jobRole == "AI Engineer"


def test_candidate_shapes_are_typed(candidate_repository) -> None:
    for candidate in candidate_repository.all():
        assert candidate.member.id.startswith("CAND-")
        assert isinstance(candidate.missions, list)
        assert candidate.signals.missionsCompleted >= 0


def test_unknown_candidate_raises(candidate_repository) -> None:
    with pytest.raises(CandidateNotFoundError):
        candidate_repository.get("CAND-999")
