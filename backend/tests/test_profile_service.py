def test_sarah_profile_rollup(candidate_repository, analysis_service, profile_service) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-001")))
    assert profile.candidate_id == "CAND-001"
    assert profile.role == "Senior Data Engineer"
    assert profile.completed_days == [7, 8, 10, 12, 16, 22, 23, 28, 31]
    assert profile.skipped_days == [29]
    assert profile.failed_days == []
    assert profile.high_attempt_days == [12]
    assert [t.day for t in profile.strong_evidence_topics] == [7, 8, 16, 31]
    assert [t.day for t in profile.uncertain_topics if t.outcome == "skipped"] == [29]


def test_profile_does_not_embed_raw_candidate_payload(candidate_repository, analysis_service, profile_service) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-001")))
    serialized = profile.model_dump()
    assert "missions" not in serialized
    assert "signals" not in serialized
    assert "member" not in serialized


def test_evidence_notes_are_signals_not_verdicts(candidate_repository, analysis_service, profile_service) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-001")))
    text = " ".join(topic.note for topic in profile.recommended_topics)
    assert "does not understand" not in text
    assert "cannot" not in text
    assert "passed" in text.lower()


def test_strong_first_attempt_topics_are_recommended_first(
    candidate_repository, analysis_service, profile_service
) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-001")))
    categories = [topic.category for topic in profile.recommended_topics]
    strong_indexes = [i for i, category in enumerate(categories) if category == "strong"]
    uncertain_indexes = [i for i, category in enumerate(categories) if category == "uncertain"]
    if uncertain_indexes:
        assert max(strong_indexes) < min(uncertain_indexes)


def test_candidate_a_strong_first_attempts(candidate_repository, analysis_service, profile_service) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-003")))
    assert len(profile.strong_evidence_topics) == 10
    assert profile.high_attempt_days == []
    assert profile.failed_days == []
    assert profile.skipped_days == []
    assert profile.role_is_technical is True


def test_candidate_b_many_attempts(candidate_repository, analysis_service, profile_service) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-004")))
    assert len(profile.high_attempt_days) >= 4
    assert len(profile.strong_evidence_topics) == 0
    assert any(topic.outcome == "passed" for topic in profile.uncertain_topics)


def test_candidate_c_skipped_topics_not_strengths(candidate_repository, analysis_service, profile_service) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-011")))
    assert profile.skipped_days == [7, 8, 12, 16, 22]
    assert profile.role_is_technical is False
    skipped_days = {topic.day for topic in profile.uncertain_topics if topic.outcome == "skipped"}
    strong_days = {topic.day for topic in profile.strong_evidence_topics}
    assert skipped_days.isdisjoint(strong_days)
    assert all(topic.note.startswith("Skipped") for topic in profile.uncertain_topics if topic.day in skipped_days)


def test_candidate_d_failed_topics(candidate_repository, analysis_service, profile_service) -> None:
    profile = profile_service.build(analysis_service.analyze(candidate_repository.get("CAND-010")))
    assert profile.failed_days == [8, 10, 22]
    failed_recommended = [t for t in profile.recommended_topics if t.outcome == "failed"]
    assert [t.day for t in failed_recommended] == [8, 10, 22]
