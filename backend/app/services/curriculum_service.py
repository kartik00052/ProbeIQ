from pydantic import BaseModel

from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.curriculum import Day
from app.services.candidate_service import CandidateAnalysis

DAY_TYPE_TIERS = {
    "AI_CORE": 5,
    "BUILD": 4,
    "SHIP_IT": 3,
    "LEARN": 3,
    "OPTIMIZE": 3,
    "CAPSTONE": 3,
    "SETUP": 1,
}


class SelectedDay(BaseModel):
    day: Day
    outcome: str
    rationale: str


class InterviewPlan(BaseModel):
    selected_days: list[SelectedDay]
    min_days: int
    target_questions: int


class CurriculumSelectionService:
    """Maps candidate learning evidence to relevant, completed curriculum days."""

    def __init__(self, curriculum_repository: CurriculumRepository) -> None:
        self._curriculum = curriculum_repository

    def select(
        self,
        analysis: CandidateAnalysis,
        min_days: int = 4,
        target_questions: int = 8,
    ) -> InterviewPlan:
        curriculum = self._curriculum.load()
        evidence_by_day = {item.day: item for item in analysis.evidence}

        completed = [
            day
            for day in curriculum.days
            if (evidence := evidence_by_day.get(day.day)) is not None
            and evidence.outcome == "passed"
        ]
        attempted = [
            day
            for day in curriculum.days
            if (evidence := evidence_by_day.get(day.day)) is not None
            and evidence.outcome == "failed"
        ]
        not_assessed = [
            day
            for day in curriculum.days
            if (evidence := evidence_by_day.get(day.day)) is not None
            and evidence.outcome == "skipped"
        ]

        def _priority(day: Day) -> tuple[int, int, int]:
            evidence = evidence_by_day[day.day]
            return (
                -DAY_TYPE_TIERS.get(day.type, 0),
                -(evidence.attempts or 0),
                day.day,
            )

        completed.sort(key=_priority)
        attempted.sort(key=_priority)
        not_assessed.sort(key=lambda day: day.day)

        selected: list[SelectedDay] = []
        for day in completed:
            if len(selected) >= min_days:
                break
            evidence = evidence_by_day[day.day]
            selected.append(
                SelectedDay(
                    day=day,
                    outcome="completed",
                    rationale=(
                        f"Completed with {evidence.attempts} attempt(s); "
                        f"AI relevance tier {DAY_TYPE_TIERS.get(day.type, 0)}."
                    ),
                )
            )

        for day in attempted + not_assessed:
            if len(selected) >= min_days:
                break
            evidence = evidence_by_day[day.day]
            selected.append(
                SelectedDay(
                    day=day,
                    outcome="attempted" if evidence.outcome == "failed" else "not_assessed",
                    rationale=evidence.note,
                )
            )

        return InterviewPlan(
            selected_days=selected,
            min_days=min_days,
            target_questions=target_questions,
        )
