def _strategy_for(candidate_id, candidate_repository, analysis_service, profile_service, planner_service, strategy_service):
    analysis = analysis_service.analyze(candidate_repository.get(candidate_id))
    profile = profile_service.build(analysis)
    plan = planner_service.plan(analysis)
    return strategy_service.build(profile, plan)


def test_strategy_primary_areas_from_completed_modules(
    candidate_repository, analysis_service, profile_service, planner_service, strategy_service
) -> None:
    strategy = _strategy_for(
        "CAND-003", candidate_repository, analysis_service, profile_service, planner_service, strategy_service
    )
    assert "Embeddings & Vector Search" in strategy.primary_areas
    assert "LLM Core, Prompting & Fine-Tuning" in strategy.primary_areas
    assert strategy.probe_areas == []
    assert strategy.avoid_assuming == []


def test_strategy_probe_areas_cover_failed_days(
    candidate_repository, analysis_service, profile_service, planner_service, strategy_service
) -> None:
    strategy = _strategy_for(
        "CAND-010", candidate_repository, analysis_service, profile_service, planner_service, strategy_service
    )
    assert "Embeddings & Vector Search" in strategy.probe_areas


def test_strategy_avoids_assuming_skipped_topics(
    candidate_repository, analysis_service, profile_service, planner_service, strategy_service
) -> None:
    strategy = _strategy_for(
        "CAND-011", candidate_repository, analysis_service, profile_service, planner_service, strategy_service
    )
    assert strategy.avoid_assuming == [
        "Embeddings Explained",
        "Vector Databases Overview",
        "Prompt Engineering Fundamentals",
        "Chatbot Backend & API Integration",
        "Multi-Agent Orchestration",
    ]


def test_strategy_is_deterministic(
    candidate_repository, analysis_service, profile_service, planner_service, strategy_service
) -> None:
    first = _strategy_for(
        "CAND-004", candidate_repository, analysis_service, profile_service, planner_service, strategy_service
    )
    second = _strategy_for(
        "CAND-004", candidate_repository, analysis_service, profile_service, planner_service, strategy_service
    )
    assert first.model_dump() == second.model_dump()
