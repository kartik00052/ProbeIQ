"""Prompt builder for the LLM-backed final feedback generator (Phase 7).

The prompt is strictly grounded in evidence collected during the interview
(questions, answers, evaluations, curriculum topics, candidate context). The LLM
only maps that evidence to the required public schema; a post-hoc grounding
cross-check keeps claims about uncovered topics out of the feedback.
"""

from app.schemas.session import AnswerEvaluation, InterviewSession

MAX_ITEMS = 3


def build_feedback_prompt(session: InterviewSession) -> str:
    """Build the feedback prompt from a completed interview session.

    Every line is derived from the session's stored evidence, never the raw
    transcript and never anything the interview did not observe.
    """
    topics = ", ".join(session.covered_topics) or "none"
    evaluation_lines = "\n".join(
        f"- Q{evaluation.question_number} {evaluation.topic} "
        f"[{evaluation.quality}]{_evaluation_extra(evaluation)}"
        for evaluation in session.evaluations
    ) or "- (no evaluations recorded)"

    return f"""You are the final feedback writer for ProbeIQ. Produce the end-of-interview feedback.

Evidence collected during the interview (use ONLY this):
- candidate role: {session.candidate_profile.role}
- candidate experience: {session.candidate_profile.experience} years
- questions asked: {session.question_count}
- curriculum topics covered: {topics}
- per-question evaluations:
{evaluation_lines}

Rules:
1. Base every statement ONLY on the evidence above. Never invent projects,
   experience, weaknesses, or communication problems the interview did not show.
2. summary: one short paragraph describing the candidate's demonstrated level.
3. strengths: evidence-backed strengths only (max {MAX_ITEMS}).
4. gaps: concepts where the interview exposed incomplete understanding
   (max {MAX_ITEMS}).
5. next: concrete, actionable revision steps grounded in the curriculum concepts
   above (max {MAX_ITEMS}). Avoid generic advice such as "Study AI more".
6. Return ONLY a JSON object with exactly these fields:
{{"summary": str, "strengths": [str], "gaps": [str], "next": [str]}}
Do not include any text outside the JSON object.
"""


def _evaluation_extra(evaluation: AnswerEvaluation) -> str:
    """Compact per-evaluation concept detail (missing / wrong concepts only)."""
    details = evaluation.details
    if details is None:
        return ""
    parts: list[str] = []
    if details.missing_concepts:
        parts.append("missing: " + "; ".join(details.missing_concepts[:2]))
    if details.misconceptions:
        parts.append("wrong: " + "; ".join(details.misconceptions[:2]))
    return f" ({'; '.join(parts)})" if parts else ""
