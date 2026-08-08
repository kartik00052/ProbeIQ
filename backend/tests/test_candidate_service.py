from app.schemas.candidate import Mission
from app.services.candidate_service import assess_mission


def test_first_attempt_is_strong() -> None:
    evidence = assess_mission(Mission(day=7, title="Embeddings Explained", passed=True, attempts=1))
    assert evidence.outcome == "passed"
    assert evidence.strength == "strong"
    assert evidence.probe is False


def test_two_attempts_is_moderate() -> None:
    evidence = assess_mission(Mission(day=10, title="Retrieval", passed=True, attempts=2))
    assert evidence.outcome == "passed"
    assert evidence.strength == "moderate"
    assert evidence.probe is False


def test_four_or_more_attempts_flags_probe() -> None:
    evidence = assess_mission(Mission(day=12, title="Prompting", passed=True, attempts=4))
    assert evidence.strength == "moderate"
    assert evidence.probe is True


def test_failed_mission_is_weak() -> None:
    evidence = assess_mission(Mission(day=8, title="Vector DBs", passed=False, attempts=4))
    assert evidence.outcome == "failed"
    assert evidence.strength == "weak"


def test_skipped_mission_is_not_assessed_not_weak() -> None:
    evidence = assess_mission(Mission(day=29, title="Monitoring", skipped=True))
    assert evidence.outcome == "skipped"
    assert evidence.strength == "not_assessed"
    assert evidence.probe is False


def test_analysis_rollup_for_sarah(candidate_repository, analysis_service) -> None:
    analysis = analysis_service.analyze(candidate_repository.get("CAND-001"))
    assert analysis.strong_days == [7, 8, 16, 31]
    assert analysis.probe_days == [12]
    assert analysis.not_assessed_days == [29]
    assert analysis.weak_days == []


def test_analysis_rollup_for_gerald_includes_failures(candidate_repository, analysis_service) -> None:
    analysis = analysis_service.analyze(candidate_repository.get("CAND-010"))
    assert analysis.weak_days == [8, 10, 22]
    assert analysis.not_assessed_days == [27, 28]
