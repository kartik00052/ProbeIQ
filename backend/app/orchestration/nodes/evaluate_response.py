from app.agents.evaluation_agent import AnswerEvaluator
from app.core.exceptions import InterviewEngineError
from app.orchestration.decision import quality_from_evaluation, recommended_probe
from app.orchestration.state import InterviewGraphState
from app.schemas.evaluation import Evaluation
from app.schemas.question_context import EvaluationContext
from app.schemas.session import AnswerEvaluation
from app.services.curriculum_knowledge import CurriculumKnowledgeService


def build_evaluate_response(
    evaluator: AnswerEvaluator,
    knowledge_service: CurriculumKnowledgeService,
):
    """Evaluate the candidate's latest answer against the question asked.

    The evaluator returns a structured Phase 6 ``Evaluation``; the deterministic
    controller maps it to the engine's coarse quality and to the recommended
    probe focus. The answer and evaluation are only recorded after the evaluator
    returns a validated result, so an evaluator failure cannot partially mutate
    the session and a retry simply re-runs this node against the stored state.
    """

    def evaluate_response(state: InterviewGraphState) -> dict:
        session = state.get("session")
        answer = state.get("candidate_answer")
        if session is None or not answer:
            raise InterviewEngineError("cannot evaluate a missing candidate answer")
        last = session.questions_asked[-1]
        node = knowledge_service.node(last.day)
        topic_evidence = next(
            (topic.reason for topic in session.topic_plan.topics if topic.day == last.day),
            None,
        )
        context = EvaluationContext(
            question_number=last.question_number,
            day=last.day,
            topic=last.topic,
            question=last.text,
            answer=answer,
            objectives=list(node.objectives) if node else [],
            tools=list(node.tools) if node else [],
            role=session.candidate_profile.role,
            experience=session.candidate_profile.experience,
            topic_evidence=topic_evidence,
            prior_quality=session.evaluations[-1].quality if session.evaluations else None,
        )
        evaluation: Evaluation = evaluator.evaluate(context)
        if not evaluation.assessment.strip():
            raise InterviewEngineError("evaluator returned an empty assessment")
        if evaluation.recommended_probe is None:
            evaluation.recommended_probe = recommended_probe(evaluation)
        quality = quality_from_evaluation(evaluation)

        session = session.model_copy(deep=True)
        session.candidate_responses.append(answer.strip())
        recorded = AnswerEvaluation(
            question_number=last.question_number,
            day=last.day,
            topic=last.topic,
            quality=quality,
            note=evaluation.assessment,
            details=evaluation,
        )
        session.evaluations.append(recorded)
        return {"session": session, "quality": quality, "evaluation": recorded}

    return evaluate_response
