from app.agents.feedback_agent import FeedbackGenerator
from app.core.exceptions import InterviewEngineError
from app.orchestration.state import InterviewGraphState

COMPLETION_REPLY = "Interview completed."


def build_generate_feedback(feedback_generator: FeedbackGenerator):
    """Produce the structured final feedback and mark the session complete."""

    def generate_feedback(state: InterviewGraphState) -> dict:
        session = state.get("session")
        if session is None:
            raise InterviewEngineError("interview session missing")
        session = session.model_copy(deep=True)
        session.feedback = feedback_generator.generate(session)
        session.status = "COMPLETED"
        session.interview_complete = True
        session.last_reply = COMPLETION_REPLY
        return {"session": session}

    return generate_feedback
