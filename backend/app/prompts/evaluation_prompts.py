"""Prompt builder for the LLM-backed answer evaluator (Phase 6).

The LLM produces the structured evaluation (score, depth, gaps, probe focus);
the deterministic probe controller (``app.orchestration.decision``) then decides
the next step from that structure.
"""

from app.schemas.question_context import EvaluationContext

_DIMENSIONS = (
    ("technical_correctness", "Is the technical content correct?"),
    ("conceptual_depth", "Does the candidate show understanding rather than memorization?"),
    ("reasoning_quality", "Is the reasoning coherent and justified?"),
    ("practical_understanding", "Can the candidate apply it in practice?"),
    ("tradeoff_awareness", "Does the candidate weigh alternatives and their costs?"),
    ("communication_clarity", "Is the answer clear?"),
)


def build_evaluation_prompt(context: EvaluationContext) -> str:
    dimensions = "\n".join(f"- {name}: {desc}" for name, desc in _DIMENSIONS)
    objectives = "\n".join(f"- {objective}" for objective in context.objectives) or "- (none provided)"
    tools = ", ".join(context.tools) or "none listed"
    evidence = context.topic_evidence or "no candidate evidence available"
    prior_quality = context.prior_quality or "none"

    return f"""You are an interview answer evaluator for ProbeIQ. Evaluate the candidate's answer.

Question asked (curriculum day {context.day}, topic "{context.topic}"):
{context.question}

Candidate answer:
{context.answer}

Curriculum objectives for this topic:
{objectives}

Tools in the curriculum for this topic:
{tools}

Candidate context:
- role: {context.role}
- experience: {context.experience} years
- topic evidence: {evidence}
- previous answer quality: {prior_quality}

Evaluation rules:
1. Score each dimension 0-5:
{dimensions}
2. Do not penalize brevity automatically: a concise, precise answer can be deep.
3. A correct definition is NOT deep understanding. If the candidate can define a
   concept but cannot reason about failures, trade-offs, or application, lower
   conceptual_depth and practical_understanding accordingly.
4. Score 0-100 overall, explainable from the six dimensions.
5. misconceptions = statements that are factually wrong. missing_concepts =
   curriculum concepts the answer should have covered but did not.
6. depth_level is one of: none | shallow | moderate | deep | excellent.
7. recommended_probe (what to probe next) is one of:
   architecture | trade-off | failure_scenario | missing_concept |
   fundamental_understanding | production_depth | evidence_clarification.
   - excellent answer -> production_depth
   - strong conceptual answer -> architecture or trade-off or failure_scenario
   - partial answer -> missing_concept
   - incorrect answer -> fundamental_understanding
   - unsupported claims or vague answer -> evidence_clarification
8. If the answer claims experience not supported by the candidate's topic
   evidence, note it in the assessment and use evidence_clarification.

Return ONLY a JSON object with exactly these fields:
{{"score": int, "assessment": str, "strengths": [str], "missing_concepts": [str], "misconceptions": [str], "depth_level": "none"|"shallow"|"moderate"|"deep"|"excellent", "follow_up_needed": bool, "follow_up_reason": str|null, "recommended_probe": str|null}}
Do not include any text outside the JSON object.
"""
