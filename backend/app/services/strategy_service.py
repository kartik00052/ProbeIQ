from app.schemas.profile import CandidateInterviewProfile
from app.schemas.strategy import InterviewStrategy
from app.services.curriculum_knowledge import CurriculumKnowledgeService
from app.services.topic_planner import InterviewTopicPlan


def _ordered_areas(titles: list[str]) -> list[str]:
    seen: list[str] = []
    for title in titles:
        if title and title not in seen:
            seen.append(title)
    return seen


class StrategyService:
    """Builds the internal candidate-specific interview strategy."""

    def __init__(self, knowledge_service: CurriculumKnowledgeService) -> None:
        self._knowledge = knowledge_service

    def build(
        self,
        profile: CandidateInterviewProfile,
        plan: InterviewTopicPlan,
    ) -> InterviewStrategy:
        primary_titles = [
            topic.module_title
            for topic in plan.topics
            if topic.outcome != "not_assessed" and topic.module_title
        ]
        probe_titles = [
            topic.module_title for topic in plan.topics if topic.probe and topic.module_title
        ]
        failed_modules = [
            title
            for day in profile.failed_days
            if (title := self._knowledge.module_title(day)) is not None
        ]

        avoid_assuming = [
            topic.title for topic in profile.uncertain_topics if topic.outcome == "skipped"
        ]

        return InterviewStrategy(
            primary_areas=_ordered_areas(primary_titles),
            probe_areas=_ordered_areas([*probe_titles, *failed_modules]),
            avoid_assuming=avoid_assuming,
        )
