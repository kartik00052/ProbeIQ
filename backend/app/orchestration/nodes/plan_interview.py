from app.core.exceptions import InterviewEngineError
from app.orchestration.difficulty import base_level
from app.orchestration.state import InterviewGraphState
from app.schemas.session import InterviewSession
from app.services.strategy_service import StrategyService
from app.services.topic_planner import TopicPlannerService


def build_plan_interview(
    topic_planner: TopicPlannerService,
    strategy_service: StrategyService,
    min_questions: int,
    min_covered_days: int,
):
    """Plan the interview: topic plan + strategy, then create the session.

    The plan is seeded from the configurable completion constants so the engine can
    never be asked to complete before ``min_questions`` over ``min_covered_days``.
    """

    def plan_interview(state: InterviewGraphState) -> dict:
        analysis = state.get("analysis")
        profile = state.get("profile")
        session_id = state.get("session_id")
        if analysis is None or profile is None or not session_id:
            raise InterviewEngineError("interview cannot be planned without analysis and session id")
        plan = topic_planner.plan(analysis, min_days=min_covered_days, target_questions=min_questions)
        strategy = strategy_service.build(profile, plan)
        session = InterviewSession(
            session_id=session_id,
            status="NEW",
            candidate_profile=profile,
            strategy=strategy,
            topic_plan=plan,
        )
        session.selected_curriculum_days = [topic.day for topic in plan.topics]
        if plan.topics:
            session.difficulty = base_level(plan.topics[0].depth)
        return {"plan": plan, "strategy": strategy, "session": session}

    return plan_interview
