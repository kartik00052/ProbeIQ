from abc import ABC, abstractmethod

from app.agents.llm_utils import invoke_json
from app.core.exceptions import InterviewEngineError
from app.orchestration.decision import recommended_probe
from app.prompts.evaluation_prompts import build_evaluation_prompt
from app.schemas.evaluation import DepthLevel, DimensionScores, Evaluation
from app.schemas.question_context import EvaluationContext

_WEAK_PHRASES = (
    "i don't know",
    "i dont know",
    "not sure",
    "no idea",
    "unsure",
    "no clue",
    "i don't understand",
    "i dont understand",
    "pass",
    "skip",
)

#: Phrases that signal a dismissive, definitively wrong answer (as opposed to a
#: partial answer that simply missed concepts). They drive the incorrect-vs-
#: partial split when an answer never engages the topic's curriculum concepts.
_DISMISSIVE_PHRASES = (
    "that is all you need",
    "that's all you need",
    "is all you need",
    "you just",
    "nothing more",
)

#: Phrases that assert personal hands-on experience. Claims are only treated as
#: unsupported when the candidate's learning evidence contradicts them.
_CLAIM_PHRASES = (
    "i built",
    "i implemented",
    "i developed",
    "i deployed",
    "i created",
    "i worked on",
    "i have built",
    "i have deployed",
    "i designed",
    "my project",
    "we built",
)

_STOP_WORDS = {
    "about",
    "across",
    "after",
    "against",
    "along",
    "also",
    "another",
    "based",
    "before",
    "being",
    "between",
    "both",
    "each",
    "from",
    "have",
    "into",
    "list",
    "more",
    "most",
    "must",
    "only",
    "other",
    "over",
    "such",
    "than",
    "that",
    "their",
    "them",
    "then",
    "these",
    "they",
    "this",
    "those",
    "through",
    "using",
    "very",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "will",
    "with",
    "would",
    "your",
}

_WEIGHTS = (
    ("technical_correctness", 0.25),
    ("conceptual_depth", 0.20),
    ("reasoning_quality", 0.20),
    ("practical_understanding", 0.15),
    ("tradeoff_awareness", 0.10),
    ("communication_clarity", 0.10),
)

_DEPTH_TERMS = (
    "trade-off",
    "tradeoff",
    "failure",
    "fail",
    "validate",
    "benchmark",
    "scale",
    "scalable",
    "monitor",
    "architecture",
    "measure",
)

#: Production-depth signals that separate a "strong conceptual" answer (deep)
#: from an "excellent" answer (production-ready).
_PRODUCTION_SIGNALS = (
    "validate",
    "validation",
    "benchmark",
    "scale",
    "scalable",
    "monitor",
    "failure",
    "fail",
    "measure",
    "observed",
    "test",
)

_TRADEOFF_TERMS = (
    "trade-off",
    "tradeoff",
    "versus",
    "vs.",
    "instead",
    "reject",
    "compare",
    "rather than",
)

_REASONING_CONNECTORS = ("because", "since", "therefore", "so that", "hence", "if ")

_CONCRETE_STEPS = ("first", "then", "next", "step", "start by", "finally")

_ROLE_KEYWORDS = ("engineer", "developer", "architect")

_STRENGTH_LABELS = {
    "technical_correctness": "Technically correct",
    "conceptual_depth": "Conceptually deep",
    "reasoning_quality": "Clear reasoning",
    "practical_understanding": "Practical understanding",
    "tradeoff_awareness": "Aware of trade-offs",
    "communication_clarity": "Clear communication",
}


class AnswerEvaluator(ABC):
    """Evaluates one answer and returns a structured Phase 6 ``Evaluation``."""

    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> Evaluation:
        raise NotImplementedError


def _keywords(context: EvaluationContext) -> set[str]:
    words: set[str] = set()
    for objective in context.objectives:
        for token in objective.lower().split():
            clean = token.strip(".,;:()'\"")
            if len(clean) >= 4 and clean not in _STOP_WORDS:
                words.add(clean)
    for tool in context.tools:
        words.add(tool.lower())
    return words


def _coverage(
    context: EvaluationContext, lowered: str, keywords: set[str]
) -> tuple[list[str], list[str]]:
    covered: list[str] = []
    missing: list[str] = []
    for objective in context.objectives:
        tokens = [
            token.strip(".,;:()'\"")
            for token in objective.lower().split()
            if len(token.strip(".,;:()'\"")) >= 4
            and token.strip(".,;:()'\"") not in _STOP_WORDS
        ]
        if any(token in lowered for token in tokens):
            covered.append(objective)
        else:
            missing.append(objective)
    return covered, missing


def _has_claim(answer: str) -> bool:
    lowered = " " + answer.lower() + " "
    return any(phrase in lowered for phrase in _CLAIM_PHRASES)


def _is_dismissive(lowered: str) -> bool:
    return any(phrase in lowered for phrase in _DISMISSIVE_PHRASES)


def _unsupported_claim(context: EvaluationContext) -> bool:
    if not _has_claim(context.answer):
        return False
    evidence = (context.topic_evidence or "").lower()
    return any(marker in evidence for marker in ("skipped", "not assessed", "not passed", "attempted"))


def _overall(dimensions: DimensionScores) -> int:
    raw = sum(getattr(dimensions, name) * weight for name, weight in _WEIGHTS)
    return round(raw * 20)


def _depth_from_score(score: int) -> DepthLevel:
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "deep"
    if score >= 55:
        return "moderate"
    return "shallow"


def _has_production_signals(lowered: str) -> bool:
    return any(word in lowered for word in _PRODUCTION_SIGNALS)


def _strengths(dimensions: DimensionScores) -> list[str]:
    return [label for name, label in _STRENGTH_LABELS.items() if getattr(dimensions, name) >= 4]


class DeterministicAnswerEvaluator(AnswerEvaluator):
    """Heuristic, explainable evaluator used until an LLM evaluator is wired in.

    Brevity is never penalized by itself: a short but grounded answer is scored on
    content, while hedging phrases, ungrounded answers, and claims that contradict
    the candidate's learning evidence are treated as weak signals that drive the
    deterministic controller toward diagnostic probing.
    """

    def evaluate(self, context: EvaluationContext) -> Evaluation:
        answer = context.answer.strip()
        lowered = answer.lower()
        keywords = _keywords(context)
        grounded_hits = sum(1 for keyword in keywords if keyword in lowered)
        covered, missing = _coverage(context, lowered, keywords)
        hedged = any(phrase in lowered for phrase in _WEAK_PHRASES)
        unsupported = _unsupported_claim(context)

        missing_concepts: list[str] = []
        misconceptions: list[str] = []
        dimensions: DimensionScores
        depth: DepthLevel
        reason: str

        if unsupported:
            dimensions = DimensionScores(
                technical_correctness=1,
                conceptual_depth=1,
                reasoning_quality=2,
                practical_understanding=1,
                tradeoff_awareness=1,
                communication_clarity=2,
            )
            depth = "none"
            reason = "Answer claimed experience not supported by the candidate's evidence."
        elif hedged or (grounded_hits == 0 and len(answer) < 30):
            dimensions = DimensionScores(
                technical_correctness=2,
                conceptual_depth=1,
                reasoning_quality=1,
                practical_understanding=1,
                tradeoff_awareness=1,
                communication_clarity=1,
            )
            depth = "shallow"
            reason = "Answer was vague or non-committal; concrete evidence is needed."
        else:
            dimensions = self._score_grounded(context, lowered, covered)
            if grounded_hits == 0:
                if _is_dismissive(lowered):
                    misconceptions = ["Answer did not engage with the topic's curriculum concepts."]
                    depth = "shallow"
                    reason = "Answer was off-topic or incorrect for the question asked."
                else:
                    missing_concepts = missing
                    depth = "shallow"
                    reason = "Answer did not address the topic's curriculum concepts."
            else:
                missing_concepts = missing
                depth = _depth_from_score(_overall(dimensions))
                if depth == "excellent" and not _has_production_signals(lowered):
                    depth = "deep"
                reason = self._reason_for(depth, missing)

        score = _overall(dimensions)
        follow_up_needed = not (depth == "excellent" and not misconceptions and not missing_concepts)
        evaluation = Evaluation(
            score=score,
            assessment=self._assessment(reason, depth, score),
            strengths=_strengths(dimensions),
            missing_concepts=missing_concepts,
            misconceptions=misconceptions,
            depth_level=depth,
            follow_up_needed=follow_up_needed,
            follow_up_reason=reason,
        )
        evaluation.recommended_probe = recommended_probe(evaluation)
        return evaluation

    @staticmethod
    def _score_grounded(
        context: EvaluationContext, lowered: str, covered: list[str]
    ) -> DimensionScores:
        length = len(context.answer.strip())
        multiple_points = lowered.count(". ") >= 1 or "\n" in lowered or lowered.count(";") >= 1
        confidence = not any(phrase in lowered for phrase in _WEAK_PHRASES)
        depth_terms = any(word in lowered for word in _DEPTH_TERMS)
        tradeoff_terms = any(word in lowered for word in _TRADEOFF_TERMS)
        reasoning = any(word in lowered for word in _REASONING_CONNECTORS)
        tools_mentioned = sum(1 for tool in context.tools if tool.lower() in lowered)
        concrete_steps = sum(1 for word in _CONCRETE_STEPS if word in lowered)
        role_technical = any(word in context.role.lower() for word in _ROLE_KEYWORDS)
        production = _has_production_signals(lowered)

        technical_correctness = min(5, 3 + (1 if covered else 0) + (1 if confidence else 0) + (1 if tools_mentioned else 0))
        conceptual_depth = min(5, 2 + (1 if covered else 0) + (1 if "because" in lowered else 0) + (1 if depth_terms else 0) + (1 if production else 0))
        reasoning_quality = min(5, 2 + (1 if multiple_points else 0) + (1 if reasoning else 0) + (1 if depth_terms or tradeoff_terms else 0))
        practical_understanding = min(5, 2 + (1 if tools_mentioned else 0) + (1 if concrete_steps else 0) + (1 if role_technical else 0) + (1 if production else 0))
        tradeoff_awareness = min(5, (2 if tradeoff_terms else 1) + (1 if "because" in lowered else 0))
        communication_clarity = max(0, min(5, 3 + (1 if multiple_points else 0) + (1 if confidence else 0) - (1 if length > 600 else 0)))
        return DimensionScores(
            technical_correctness=technical_correctness,
            conceptual_depth=conceptual_depth,
            reasoning_quality=reasoning_quality,
            practical_understanding=practical_understanding,
            tradeoff_awareness=tradeoff_awareness,
            communication_clarity=communication_clarity,
        )

    @staticmethod
    def _reason_for(depth: DepthLevel, missing: list[str]) -> str:
        if missing:
            return "Answer covered part of the topic; the remaining curriculum concepts are unaddressed."
        if depth in ("none", "shallow"):
            return "Answer lacked depth; further probing is needed."
        return "Answer was sound; the next step probes deeper on the same topic."

    @staticmethod
    def _assessment(reason: str, depth: DepthLevel, score: int) -> str:
        return f"{reason} Depth assessed as {depth} ({score}/100)."


class LLMAnswerEvaluator(AnswerEvaluator):
    """LLM-backed evaluator producing the structured Phase 6 ``Evaluation``.

    The deterministic probe controller (decision.py) maps the structured output
    to the engine's coarse quality and decides the next step; the LLM only judges
    the answer.
    """

    def __init__(
        self,
        chat_model: object,
        prompt_builder=build_evaluation_prompt,
        call_kwargs: dict | None = None,
    ) -> None:
        self._chat = chat_model
        self._prompt_builder = prompt_builder
        #: Per-call generation caps (max output length / thinking budget) so the
        #: shared chat client never burns unbounded tokens on a short evaluation.
        self._call_kwargs = call_kwargs

    def evaluate(self, context: EvaluationContext) -> Evaluation:
        payload = invoke_json(self._chat, self._prompt_builder(context), call_kwargs=self._call_kwargs)
        try:
            evaluation = Evaluation.model_validate(payload)
        except Exception as exc:
            raise InterviewEngineError("LLM evaluator returned an invalid structure.") from exc
        return evaluation
