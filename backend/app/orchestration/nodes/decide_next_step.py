from app.core.exceptions import InterviewEngineError
from app.orchestration.decision import apply_decision, decide
from app.orchestration.state import InterviewGraphState


def build_decide_next_step(
    min_questions: int,
    min_covered_days: int,
    max_questions_per_topic: int,
    hard_max_questions: int,
):
    """Choose the next step and advance the session cursor.

    The decision is deterministic (see ``app.orchestration.decision``) and is
    applied to a deep copy of the session; the previous committed state is never
    mutated in place.
    """

    def decide_next_step(state: InterviewGraphState) -> dict:
        session = state.get("session")
        quality = state.get("quality")
        if session is None or quality is None:
            raise InterviewEngineError("cannot decide the next step without an evaluation")
        decision = decide(
            session,
            quality,
            min_questions=min_questions,
            min_covered_days=min_covered_days,
            max_questions_per_topic=max_questions_per_topic,
            hard_max_questions=hard_max_questions,
        )
        session = apply_decision(session.model_copy(deep=True), decision, max_questions_per_topic=max_questions_per_topic)
        return {"session": session, "decision": decision}

    return decide_next_step
