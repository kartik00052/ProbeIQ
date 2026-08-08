from abc import ABC, abstractmethod

from app.agents.llm_utils import invoke_json
from app.core.exceptions import InterviewEngineError
from app.prompts.feedback_prompts import build_feedback_prompt
from app.schemas.interview import InterviewFeedback
from app.schemas.session import AnswerEvaluation, InterviewSession

_STRENGTH_PREFIX = "Demonstrated strong understanding of "
_GAP_PREFIX = "Incomplete understanding of "

#: Fallback actions only used when the interview produced no specific concepts
#: to target (no evaluations, or every topic was answered strongly).
_FALLBACK_NEXT_STEP = "Apply the demonstrated strengths to advanced trade-off and system-design exercises."
_EMPTY_NEXT_STEP = "Re-run the interview and answer the questions to receive feedback."


class FeedbackGenerator(ABC):
    """Produces the structured end-of-interview feedback (Phase 7)."""

    @abstractmethod
    def generate(self, session: InterviewSession) -> InterviewFeedback:
        raise NotImplementedError


class DeterministicFeedbackGenerator(FeedbackGenerator):
    """Feedback derived from the actual transcript: evaluations per topic.

    Strengths name topics where every answer was strong; gaps name topics where
    an answer was weak or only adequate, including the concepts the interview
    exposed as incomplete; next steps are concrete revision actions grounded in
    those concepts. Nothing is invented: every statement traces back to an
    evaluation or the curriculum plan.
    """

    def generate(self, session: InterviewSession) -> InterviewFeedback:
        evaluations = session.evaluations
        total = len(evaluations)
        strong = sum(1 for evaluation in evaluations if evaluation.quality == "strong")
        adequate = sum(1 for evaluation in evaluations if evaluation.quality == "adequate")
        weak = sum(1 for evaluation in evaluations if evaluation.quality == "weak")

        strengths: list[str] = []
        gaps: list[str] = []
        next_steps: list[str] = []

        for topic in session.topic_plan.topics:
            topic_evaluations = [
                evaluation for evaluation in evaluations if evaluation.topic == topic.title
            ]
            if not topic_evaluations:
                continue
            if all(evaluation.quality == "strong" for evaluation in topic_evaluations):
                strengths.append(f"{_STRENGTH_PREFIX}{topic.title}")
            else:
                gaps.append(self._gap_for(topic.title, topic_evaluations))
                next_steps.extend(self._next_steps_for(topic_evaluations))

        if not evaluations:
            summary = (
                f"Interview complete: {session.question_count} questions across "
                f"{len(session.covered_curriculum_days)} curriculum days; "
                "no answers were evaluated."
            )
            next_steps = [_EMPTY_NEXT_STEP]
        else:
            summary = (
                f"Interview complete: {session.question_count} questions across "
                f"{len(session.covered_curriculum_days)} curriculum days; "
                f"{strong}/{total} answers strong, {adequate} adequate, {weak} weak."
            )

        if not next_steps:
            next_steps = [_FALLBACK_NEXT_STEP]

        return InterviewFeedback(
            summary=summary,
            strengths=strengths[:3],
            gaps=gaps[:3],
            next=next_steps[:3],
        )

    @staticmethod
    def _gap_for(topic: str, evaluations: list[AnswerEvaluation]) -> str:
        concepts = DeterministicFeedbackGenerator._incomplete_concepts(evaluations)
        if concepts:
            return f"{_GAP_PREFIX}{topic}: {concepts[0]}"
        return f"{_GAP_PREFIX}{topic}"

    @staticmethod
    def _incomplete_concepts(evaluations: list[AnswerEvaluation]) -> list[str]:
        concepts: list[str] = []
        for evaluation in evaluations:
            details = evaluation.details
            if details is None:
                continue
            concepts.extend(details.missing_concepts or [])
            concepts.extend(details.misconceptions or [])
        return concepts

    @staticmethod
    def _next_steps_for(evaluations: list[AnswerEvaluation]) -> list[str]:
        steps: list[str] = []
        for evaluation in evaluations:
            details = evaluation.details
            if details is None:
                continue
            for concept in (details.missing_concepts or [])[:2]:
                steps.append(f"Review: {concept}")
            for concept in (details.misconceptions or [])[:2]:
                steps.append(f"Correct the misunderstanding: {concept}")
        return steps


class LLMFeedbackGenerator(FeedbackGenerator):
    """LLM-backed feedback writer producing the Phase 7 public schema.

    The prompt is strictly grounded in the interview evidence; the result is
    validated as an ``InterviewFeedback`` and cross-checked so it can never
    reference a curriculum topic the interview did not cover.
    """

    def __init__(self, chat_model: object, prompt_builder=build_feedback_prompt) -> None:
        self._chat = chat_model
        self._prompt_builder = prompt_builder

    def generate(self, session: InterviewSession) -> InterviewFeedback:
        payload = invoke_json(self._chat, self._prompt_builder(session))
        try:
            feedback = InterviewFeedback.model_validate(payload)
        except Exception as exc:
            raise InterviewEngineError(
                "LLM feedback generator returned an invalid structure."
            ) from exc
        self._assert_grounded(feedback, session)
        return feedback

    @staticmethod
    def _assert_grounded(feedback: InterviewFeedback, session: InterviewSession) -> None:
        """Reject feedback that references a planned topic the interview skipped.

        The LLM is only allowed to talk about topics the interview actually
        covered; mentioning a planned-but-uncovered topic means it invented
        evidence.
        """
        covered = set(session.covered_topics)
        unreachable = [topic.title for topic in session.topic_plan.topics if topic.title not in covered]
        if not unreachable:
            return
        text = " ".join([feedback.summary, *feedback.strengths, *feedback.gaps, *feedback.next]).lower()
        for title in unreachable:
            if title.lower() in text:
                raise InterviewEngineError(
                    "LLM feedback referenced a curriculum topic the interview did not cover."
                )
