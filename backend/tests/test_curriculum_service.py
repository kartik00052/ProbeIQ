from app.schemas.candidate import Candidate, CandidateMember, CandidateSignals, Mission


def _candidate_with_missions(day_titles: list[tuple[int, str, int]]) -> Candidate:
    return Candidate(
        member=CandidateMember(
            id="CAND-TEST",
            name="Test Candidate",
            jobRole="AI Engineer",
            yearsExperience=3,
            education="BS CS",
            status="COMPLETED",
        ),
        missions=[
            Mission(day=day, title=title, passed=True, attempts=attempts)
            for day, title, attempts in day_titles
        ],
        signals=CandidateSignals(commitDays=20, missionsCompleted=30, missionsFirstTry=10),
    )


def test_selection_covers_at_least_four_days(selection_service, candidate_repository, analysis_service) -> None:
    analysis = analysis_service.analyze(candidate_repository.get("CAND-001"))
    plan = selection_service.select(analysis)
    assert len(plan.selected_days) >= 4
    assert plan.min_days == 4
    assert plan.target_questions == 8


def test_selection_only_uses_completed_days(selection_service, candidate_repository, analysis_service) -> None:
    analysis = analysis_service.analyze(candidate_repository.get("CAND-001"))
    plan = selection_service.select(analysis)
    assert all(item.outcome == "completed" for item in plan.selected_days)


def test_selection_prefers_ai_core_over_setup(selection_service, analysis_service) -> None:
    candidate = _candidate_with_missions(
        [
            (1, "VS Code & Python Environment Setup", 1),
            (7, "Embeddings Explained", 1),
            (8, "Vector Databases Overview", 1),
            (12, "Prompt Engineering Fundamentals", 1),
            (16, "Chatbot Backend & API Integration", 1),
        ]
    )
    plan = selection_service.select(analysis_service.analyze(candidate))
    assert len(plan.selected_days) >= 4
    assert plan.selected_days[0].day.type == "AI_CORE"


def test_selection_is_deterministic(selection_service, candidate_repository, analysis_service) -> None:
    analysis = analysis_service.analyze(candidate_repository.get("CAND-005"))
    first = selection_service.select(analysis)
    second = selection_service.select(analysis)
    assert [item.day.day for item in first.selected_days] == [item.day.day for item in second.selected_days]


def test_selection_orders_by_ai_relevance_then_attempts(selection_service, analysis_service) -> None:
    candidate = _candidate_with_missions(
        [
            (7, "Embeddings Explained", 1),
            (8, "Vector Databases Overview", 5),
            (12, "Prompt Engineering Fundamentals", 4),
            (16, "Chatbot Backend & API Integration", 2),
        ]
    )
    plan = selection_service.select(analysis_service.analyze(candidate))
    days = [item.day.day for item in plan.selected_days]
    # Tier first (AI_CORE 7 > BUILD 8/16 > LEARN 12), then attempts descending.
    assert days == [7, 8, 16, 12]
