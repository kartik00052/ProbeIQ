from app.agents.question_agent import QuestionGenerator
from app.core.exceptions import InterviewEngineError
from app.orchestration.decision import planned_topic
from app.orchestration.state import InterviewGraphState
from app.schemas.evaluation import ProbeFocus
from app.schemas.question import Question
from app.schemas.question_context import QuestionContext
from app.schemas.session import AskedQuestion
from app.services.curriculum_knowledge import CurriculumKnowledgeService


def _interview_objective(session, topic, probe_focus: str | None) -> str:
    if session.follow_up_index > 0:
        focus = f" ({probe_focus})" if probe_focus else ""
        return f"Probe the previous answer on {topic.title} more deeply{focus}."
    if session.difficulty == "foundational":
        return f"Establish foundational understanding of {topic.title}."
    if session.difficulty == "advanced":
        return f"Assess production and system-design depth on {topic.title}."
    return f"Assess applied understanding of {topic.title}."


def build_generate_question(
    knowledge_service: CurriculumKnowledgeService,
    question_generator: QuestionGenerator,
    min_questions: int,
    min_covered_days: int,
):
    """Ask the next question on the current planned topic.

    The question is grounded in the compact ``QuestionContext`` (candidate role,
    experience, current curriculum day/topic, objectives, tools, adaptive
    difficulty, and only the immediately relevant history) -- never the raw
    transcript. Generated output is validated as a structured ``Question`` and
    cross-checked against the curriculum context before it is committed, so a
    failing or ungrounded generator cannot corrupt state or fabricate a question.
    """

    def generate_question(state: InterviewGraphState) -> dict:
        session = state.get("session")
        if session is None:
            raise InterviewEngineError("interview session missing")
        if not session.topic_plan.topics:
            raise InterviewEngineError("topic plan is empty; cannot generate a question")

        topic = planned_topic(session)
        node = knowledge_service.node(topic.day)

        probe_focus: ProbeFocus | None = None
        previous_evaluation: str | None = None
        if session.evaluations:
            last = session.evaluations[-1]
            previous_evaluation = last.note
            if last.details is not None:
                probe_focus = last.details.recommended_probe

        context = QuestionContext(
            candidate_id=session.candidate_profile.candidate_id,
            role=session.candidate_profile.role,
            experience=session.candidate_profile.experience,
            day=topic.day,
            topic=topic.title,
            module=node.module_title if node else topic.module_title,
            objectives=list(node.objectives) if node else [],
            tools=list(node.tools) if node else [],
            difficulty=session.difficulty,
            follow_up_index=session.follow_up_index,
            previous_question=session.questions_asked[-1].text if session.questions_asked else None,
            previous_answer=session.candidate_responses[-1] if session.candidate_responses else None,
            previous_quality=session.evaluations[-1].quality if session.evaluations else None,
            previous_evaluation=previous_evaluation,
            probe_focus=probe_focus,
            covered_days=list(session.covered_curriculum_days),
            question_number=session.question_count + 1,
            min_questions=min_questions,
            min_covered_days=min_covered_days,
            interview_objective=_interview_objective(session, topic, probe_focus),
            completion_evidence=topic.outcome != "not_assessed",
        )

        question: Question = question_generator.generate(context)
        if not question.question.strip():
            raise InterviewEngineError("question generator returned an empty question")
        if (
            question.curriculum_day != topic.day
            or question.topic != topic.title
            or question.difficulty != session.difficulty
        ):
            raise InterviewEngineError(
                "question generator produced a question not grounded in the current curriculum context"
            )

        session = session.model_copy(deep=True)
        asked = AskedQuestion(
            question_number=context.question_number,
            day=topic.day,
            topic=topic.title,
            text=question.question.strip(),
            depth=topic.depth,
            difficulty=session.difficulty,
            follow_up_index=session.follow_up_index,
            question_type=question.question_type,
        )
        session.questions_asked.append(asked)
        session.question_count = asked.question_number
        session.follow_up_count = sum(1 for item in session.questions_asked if item.follow_up_index > 0)
        session.current_question = asked.text
        session.current_topic = asked.topic
        session.current_day = asked.day
        session.status = "ACTIVE"
        session.last_reply = asked.text
        if asked.day not in session.covered_curriculum_days:
            session.covered_curriculum_days.append(asked.day)
        if asked.topic not in session.covered_topics:
            session.covered_topics.append(asked.topic)
        return {"session": session}

    return generate_question
