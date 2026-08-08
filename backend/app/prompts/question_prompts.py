"""Prompt builder for the LLM-backed question generator (Phase 5).

The deterministic ProbeIQ controller decides WHAT to probe (topic, difficulty,
probe focus); the LLM only decides HOW to phrase the question. The prompt is
strictly grounded in the supplied ``QuestionContext`` so the model cannot
fabricate candidate experience, projects, tools, or curriculum content.
"""

from app.schemas.question_context import QuestionContext


def build_question_prompt(context: QuestionContext) -> str:
    evidence = "present" if context.completion_evidence else "absent (the topic was skipped or not assessed)"
    objectives = "\n".join(f"- {objective}" for objective in context.objectives) or "- (none provided)"
    tools = ", ".join(context.tools) or "none listed"
    previous_question = context.previous_question or "none (this is the first question)"
    previous_answer = context.previous_answer or "none (this is the first question)"
    previous_evaluation = context.previous_evaluation or "none"

    return f"""You are the technical interviewer for ProbeIQ. Ask one interview question.

Candidate context:
- role: {context.role}
- experience: {context.experience} years
- evidence the candidate completed this curriculum topic: {evidence}
- curriculum day {context.day} topic: {context.topic}
- curriculum objectives:
{objectives}
- tools in the curriculum for this day: {tools}

Conversation context:
- previous question: {previous_question}
- previous answer: {previous_answer}
- previous evaluation: {previous_evaluation}
- probe focus for this next step: {context.probe_focus or "none (ask a fresh question)"}
- target difficulty: {context.difficulty}
- interview objective: {context.interview_objective}

Rules:
1. Ground the question ONLY in the curriculum objectives and tools listed above.
2. Never claim the candidate built, used, or completed anything. If completion
   evidence is absent, phrase the question hypothetically ("How would you ..." /
   "Explain ...") and never say "you built", "your project", or "you have".
3. Avoid generic one-word-definition questions ("What is X?") unless the
   difficulty is foundational and a foundational check is required.
4. Ask one specific, scenario-oriented question; prefer practical scenarios.
5. If this is a follow-up (follow_up_index > 0), build on the candidate's
   previous answer and target the given probe focus.
6. Return ONLY a JSON object with exactly these fields:
{{"question": str, "question_type": "conceptual"|"implementation"|"architecture"|"debugging"|"scenario"|"trade-off"|"production"|"follow-up", "curriculum_day": {context.day}, "topic": "{context.topic}", "difficulty": "{context.difficulty}", "purpose": str}}
Do not include any text outside the JSON object.
"""
