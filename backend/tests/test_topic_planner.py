def _plan_for(candidate_id, candidate_repository, analysis_service, planner_service):
    analysis = analysis_service.analyze(candidate_repository.get(candidate_id))
    return planner_service.plan(analysis)


def test_plan_includes_at_least_four_different_days(
    candidate_repository, analysis_service, planner_service
) -> None:
    for candidate_id in ["CAND-001", "CAND-003", "CAND-004", "CAND-010", "CAND-011"]:
        plan = _plan_for(candidate_id, candidate_repository, analysis_service, planner_service)
        days = [topic.day for topic in plan.topics]
        assert len(days) == len(set(days)) >= 4


def test_plan_allocates_all_target_questions(
    candidate_repository, analysis_service, planner_service
) -> None:
    plan = _plan_for("CAND-001", candidate_repository, analysis_service, planner_service)
    assert plan.allocated_questions == 8
    assert sum(topic.question_slots for topic in plan.topics) == 8


def test_plan_supports_follow_ups(candidate_repository, analysis_service, planner_service) -> None:
    plan = _plan_for("CAND-001", candidate_repository, analysis_service, planner_service)
    assert all(topic.question_slots >= 2 for topic in plan.topics)


def test_candidate_a_receives_higher_depth_questioning(
    candidate_repository, analysis_service, planner_service
) -> None:
    plan = _plan_for("CAND-003", candidate_repository, analysis_service, planner_service)
    assert all(topic.depth == "high" for topic in plan.topics)
    assert all(not topic.probe for topic in plan.topics)


def test_candidate_b_receives_diagnostic_probing(
    candidate_repository, analysis_service, planner_service
) -> None:
    plan = _plan_for("CAND-004", candidate_repository, analysis_service, planner_service)
    assert any(topic.depth == "diagnostic" for topic in plan.topics)
    assert any(topic.probe for topic in plan.topics)


def test_candidate_c_skipped_topics_not_selected_as_strength(
    candidate_repository, analysis_service, planner_service
) -> None:
    plan = _plan_for("CAND-011", candidate_repository, analysis_service, planner_service)
    selected = {topic.day for topic in plan.topics}
    assert {7, 8, 12, 16, 22}.isdisjoint(selected)


def test_candidate_d_failed_topics_get_diagnostic_planning(
    candidate_repository, analysis_service, planner_service
) -> None:
    plan = _plan_for("CAND-010", candidate_repository, analysis_service, planner_service)
    probe_days = [topic.day for topic in plan.topics if topic.probe]
    assert probe_days == [7, 16, 12]
    assert all(topic.depth == "diagnostic" for topic in plan.topics if topic.probe)


def test_plan_is_deterministic(candidate_repository, analysis_service, planner_service) -> None:
    first = _plan_for("CAND-005", candidate_repository, analysis_service, planner_service)
    second = _plan_for("CAND-005", candidate_repository, analysis_service, planner_service)
    assert first.model_dump() == second.model_dump()
