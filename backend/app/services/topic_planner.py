from app.schemas.topic_plan import Depth, InterviewTopicPlan, PlannedTopic
from app.services.candidate_service import CandidateAnalysis
from app.services.curriculum_knowledge import CurriculumKnowledgeService
from app.services.curriculum_service import CurriculumSelectionService


def _depth_for(evidence, outcome: str) -> tuple[Depth, bool, str]:
    if outcome == "failed":
        return "diagnostic", True, "Not passed: potential knowledge-gap probing."
    if outcome == "not_assessed":
        return "standard", False, "Skipped: no assumption of mastery; explore only if needed."
    if evidence.attempts == 1:
        return "high", False, "Passed on first attempt: support higher-depth questioning."
    if evidence.probe:
        return "diagnostic", True, "Passed after many attempts: completed but worth probing."
    return "standard", False, "Passed; standard questioning depth."


class TopicPlannerService:
    """Maps candidate evidence to a deterministic, question-budgeted topic plan.

    Reuses the Phase 1 curriculum-day selector for day selection, then allocates
    question slots across the selected days and assigns a questioning depth.
    """

    def __init__(
        self,
        curriculum_selection_service: CurriculumSelectionService,
        curriculum_knowledge_service: CurriculumKnowledgeService,
    ) -> None:
        self._selection = curriculum_selection_service
        self._knowledge = curriculum_knowledge_service

    def plan(
        self,
        analysis: CandidateAnalysis,
        min_days: int = 4,
        target_questions: int = 8,
    ) -> InterviewTopicPlan:
        plan = self._selection.select(analysis, min_days=min_days, target_questions=target_questions)
        evidence_by_day = {item.day: item for item in analysis.evidence}

        topics: list[PlannedTopic] = []
        for selected in plan.selected_days:
            evidence = evidence_by_day[selected.day.day]
            depth, probe, reason = _depth_for(evidence, selected.outcome)
            node = self._knowledge.node(selected.day.day)
            topics.append(
                PlannedTopic(
                    day=selected.day.day,
                    title=selected.day.title,
                    outcome=selected.outcome,
                    module=node.module if node else 0,
                    module_title=node.module_title if node else "",
                    depth=depth,
                    probe=probe,
                    question_slots=0,
                    reason=f"{reason} {selected.rationale}",
                )
            )

        base, remainder = divmod(target_questions, len(topics))
        for index, topic in enumerate(topics):
            topic.question_slots = base + (1 if index < remainder else 0)

        allocated = sum(topic.question_slots for topic in topics)
        return InterviewTopicPlan(
            topics=topics,
            min_days=min_days,
            target_questions=target_questions,
            allocated_questions=allocated,
        )
