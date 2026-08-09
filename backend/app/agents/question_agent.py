from abc import ABC, abstractmethod

from app.agents.llm_utils import invoke_json
from app.core.exceptions import InterviewEngineError
from app.prompts.question_prompts import build_question_prompt
from app.schemas.question import Question, QuestionType
from app.schemas.question_context import QuestionContext

_ADVANCED_TYPES: tuple[QuestionType, QuestionType, QuestionType] = (
    "architecture",
    "production",
    "trade-off",
)

_PURPOSES: dict[QuestionType, str] = {
    "conceptual": "Verify the candidate can explain the core concept accurately.",
    "implementation": "Check the candidate can apply the concept in practice.",
    "architecture": "Assess system-design thinking across components.",
    "debugging": "Evaluate diagnostic reasoning in a failing scenario.",
    "scenario": "Ground the concept in a realistic role-based scenario.",
    "trade-off": "Probe awareness of alternatives and their costs.",
    "production": "Assess production readiness and operational concerns.",
    "follow-up": "Deepen or clarify the previous answer.",
}


class QuestionGenerator(ABC):
    """Produces the next validated interview ``Question`` from a grounded context."""

    @abstractmethod
    def generate(self, context: QuestionContext) -> Question:
        raise NotImplementedError


def select_question_type(context: QuestionContext) -> QuestionType:
    """Pick the question type from the interview objective / difficulty (Phase 5).

    A follow-up stays a follow-up; foundational checks are conceptual; deeper
    levels rotate through applied question types so consecutive questions vary.
    """
    if context.follow_up_index > 0:
        return "follow-up"
    if context.difficulty == "foundational":
        return "conceptual"
    if context.difficulty == "advanced":
        return _ADVANCED_TYPES[(context.question_number - 1) % 3]
    return "scenario" if context.question_number % 2 == 0 else "implementation"


class DeterministicQuestionGenerator(QuestionGenerator):
    """Template-based generator used until an LLM generator is wired in.

    The output is a validated ``Question`` grounded in the curriculum objectives
    and tools from the context. Output text is marked ``[dev-template]`` so
    callers can never mistake it for LLM output.
    """

    def generate(self, context: QuestionContext) -> Question:
        question_type = select_question_type(context)
        if question_type == "follow-up":
            text = self._follow_up_text(context)
        else:
            text = self._stem_text(context, question_type)
        return Question(
            question=f"[dev-template] {text}",
            question_type=question_type,
            curriculum_day=context.day,
            topic=context.topic,
            difficulty=context.difficulty,
            purpose=_PURPOSES[question_type],
        )

    @staticmethod
    def _objective(context: QuestionContext) -> str:
        return context.objectives[0] if context.objectives else context.topic

    def _stem_text(self, context: QuestionContext, question_type: QuestionType) -> str:
        objective = self._objective(context)
        tools = ", ".join(context.tools[:3]) or "the curriculum tooling"
        if question_type == "conceptual":
            return (
                f"Explain the core idea of {context.topic} in your own words, addressing: "
                f"{objective}. Give a concrete example."
            )
        if question_type == "implementation":
            return f"Walk through how you would implement '{objective}' for {context.topic}."
        if question_type == "architecture":
            return (
                f"Design a production-grade solution for '{objective}' in {context.topic}. "
                "Cover components, trade-offs, failure modes, and how you would validate it."
            )
        if question_type == "debugging":
            return (
                f"A system built on {tools} is producing wrong results for '{objective}'. "
                "How would you debug it?"
            )
        if question_type == "scenario":
            return (
                f"As a {context.role}, you must deliver '{objective}' for {context.topic}. "
                "How would you approach it in practice, and what would you measure?"
            )
        if question_type == "trade-off":
            return (
                f"What are the main trade-offs for '{objective}' in {context.topic}, "
                "and what would make you choose one approach over another?"
            )
        return (
            f"Your team is running '{objective}' for {context.topic} in production. "
            "What scaling, monitoring, and failure concerns would you address first?"
        )

    def _follow_up_text(self, context: QuestionContext) -> str:
        objective = self._objective(context)
        focus = context.probe_focus
        if focus == "missing_concept":
            return (
                f"Your previous answer left '{objective}' unclear. What concept is missing, "
                "and how would you apply it here?"
            )
        if focus == "fundamental_understanding":
            return (
                f"Your previous answer missed the fundamentals of {context.topic}. "
                "Restate the core concept and give a concrete example."
            )
        if focus in ("production_depth", "architecture"):
            return (
                f"Your previous answer was conceptually sound. Now design it for "
                f"{focus.replace('_', ' ')}: components, trade-offs, and failure handling "
                f"for '{objective}'."
            )
        if focus == "trade-off":
            return (
                f"Your previous answer was conceptually sound. When would '{objective}' be "
                "the wrong choice, and what would you reject?"
            )
        if focus == "failure_scenario":
            return (
                "Your previous answer was conceptually sound. Where could it fail in "
                "practice, and how would you diagnose it?"
            )
        if context.follow_up_index == 1:
            return (
                f"Build on your previous answer: what trade-offs did you weigh, and what "
                f"did you reject, regarding '{objective}'?"
            )
        return (
            f"Reconsider your previous answer: where could it fail, and how would you "
            f"validate it, regarding '{objective}'?"
        )


class LLMQuestionGenerator(QuestionGenerator):
    """LLM-backed generator: HOW to phrase a question the controller decided on.

    The deterministic controller builds the grounded ``QuestionContext``; the LLM
    turns it into one specific question. The result is validated as a ``Question``
    and cross-checked against the context (topic, day, difficulty) so an LLM
    mistake can never inject ungrounded or fabricated content into the interview.
    """

    def __init__(
        self,
        chat_model: object,
        prompt_builder=build_question_prompt,
        call_kwargs: dict | None = None,
    ) -> None:
        self._chat = chat_model
        self._prompt_builder = prompt_builder
        #: Per-call generation caps (max output length / thinking budget) so the
        #: shared chat client never burns unbounded tokens on a short question.
        self._call_kwargs = call_kwargs

    def generate(self, context: QuestionContext) -> Question:
        payload = invoke_json(self._chat, self._prompt_builder(context), call_kwargs=self._call_kwargs)
        try:
            question = Question.model_validate(payload)
        except Exception as exc:
            raise InterviewEngineError(
                "LLM question generator returned an invalid structure."
            ) from exc
        if (
            question.curriculum_day != context.day
            or question.topic != context.topic
            or question.difficulty != context.difficulty
        ):
            raise InterviewEngineError(
                "LLM question generator produced a question not grounded in the curriculum."
            )
        return question
