"""Phase 5 tests: the technical question generator.

Covers curriculum grounding, question-type selection, follow-up quality,
difficulty preservation, candidate personalization, skipped-topic safety, and
structured-output validation. LLM-backed generator tests use mocked chat
responses so they are deterministic and offline.
"""

import json
from types import SimpleNamespace

import pytest

from app.agents.question_agent import (
    DeterministicQuestionGenerator,
    LLMQuestionGenerator,
    select_question_type,
)
from app.core.exceptions import InterviewEngineError
from app.prompts.question_prompts import build_question_prompt
from app.schemas.question import Question
from app.schemas.question_context import QuestionContext

DAY = 10
TOPIC = "The Retrieval & Matching Engine"


class _FakeChat:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.response)


def _context(knowledge_service, **overrides) -> QuestionContext:
    node = knowledge_service.node(DAY)
    defaults = {
        "candidate_id": "CAND-001",
        "role": "Backend Engineer",
        "experience": 5,
        "day": node.day,
        "topic": node.title,
        "module": node.module_title,
        "objectives": list(node.objectives),
        "tools": list(node.tools),
        "difficulty": "intermediate",
        "follow_up_index": 0,
        "previous_question": None,
        "previous_answer": None,
        "previous_quality": None,
        "previous_evaluation": None,
        "probe_focus": None,
        "covered_days": [7, 8],
        "question_number": 1,
        "min_questions": 8,
        "min_covered_days": 4,
        "interview_objective": "Assess applied understanding.",
        "completion_evidence": True,
    }
    defaults.update(overrides)
    return QuestionContext(**defaults)


# --- curriculum grounding ----------------------------------------------------


def test_deterministic_question_is_grounded_in_curriculum(knowledge_service) -> None:
    context = _context(knowledge_service)
    question = DeterministicQuestionGenerator().generate(context)
    assert question.curriculum_day == DAY
    assert question.topic == TOPIC
    assert question.question.startswith("[dev-template]")
    assert context.objectives[0] in question.question
    assert TOPIC in question.question


def test_avoids_generic_one_liner(knowledge_service) -> None:
    question = DeterministicQuestionGenerator().generate(_context(knowledge_service))
    assert not question.question.rstrip().endswith("?") or "What is" not in question.question
    assert question.question_type != "conceptual"  # intermediate level never asks a definition


# --- question type selection --------------------------------------------------


def test_question_type_follows_difficulty(knowledge_service) -> None:
    generator = DeterministicQuestionGenerator()
    foundational = generator.generate(_context(knowledge_service, difficulty="foundational"))
    assert foundational.question_type == "conceptual"

    advanced_first = generator.generate(_context(knowledge_service, difficulty="advanced", question_number=1))
    assert advanced_first.question_type == "architecture"

    advanced_second = generator.generate(_context(knowledge_service, difficulty="advanced", question_number=2))
    assert advanced_second.question_type == "production"

    advanced_third = generator.generate(_context(knowledge_service, difficulty="advanced", question_number=3))
    assert advanced_third.question_type == "trade-off"

    intermediate_even = generator.generate(_context(knowledge_service, question_number=2))
    assert intermediate_even.question_type == "scenario"

    intermediate_odd = generator.generate(_context(knowledge_service, question_number=3))
    assert intermediate_odd.question_type == "implementation"


def test_select_question_type_returns_follow_up_for_follow_up(knowledge_service) -> None:
    context = _context(knowledge_service, follow_up_index=2, probe_focus="failure_scenario")
    assert select_question_type(context) == "follow-up"


# --- follow-up generation -----------------------------------------------------


def test_follow_up_connects_to_previous_answer(knowledge_service) -> None:
    previous = "I would combine SQL for claims and vector search for symptoms."
    context = _context(
        knowledge_service,
        follow_up_index=1,
        probe_focus="trade-off",
        previous_question="How would you build the retrieval engine?",
        previous_answer=previous,
        previous_quality="adequate",
        previous_evaluation="Answer covered part of the topic.",
    )
    question = DeterministicQuestionGenerator().generate(context)
    assert question.question_type == "follow-up"
    assert "previous answer" in question.question
    assert question.purpose == "Deepen or clarify the previous answer."


# --- difficulty ---------------------------------------------------------------


def test_difficulty_is_preserved_in_output(knowledge_service) -> None:
    generator = DeterministicQuestionGenerator()
    for level in ("foundational", "intermediate", "advanced"):
        question = generator.generate(_context(knowledge_service, difficulty=level))
        assert question.difficulty == level


# --- candidate personalization ------------------------------------------------


def test_prompt_includes_candidate_personalization(knowledge_service) -> None:
    context = _context(knowledge_service, experience=9, role="Senior Data Engineer")
    prompt = build_question_prompt(context)
    assert "Senior Data Engineer" in prompt
    assert "9 years" in prompt
    assert "evidence the candidate completed this curriculum topic: present" in prompt
    assert context.objectives[0] in prompt
    assert context.tools[0] in prompt


def test_llm_prompt_receives_previous_answer(knowledge_service) -> None:
    previous = "Hybrid retrieval fuses dense and sparse signals."
    context = _context(
        knowledge_service,
        follow_up_index=1,
        probe_focus="missing_concept",
        previous_answer=previous,
    )
    chat = _FakeChat(
        json.dumps(
            {
                "question": "Which curriculum concept did you leave out?",
                "question_type": "follow-up",
                "curriculum_day": DAY,
                "topic": TOPIC,
                "difficulty": "intermediate",
                "purpose": "Follow up on a missing concept.",
            }
        )
    )
    generator = LLMQuestionGenerator(chat)
    generator.generate(context)
    assert previous in chat.calls[0][0][1]


# --- skipped-topic safety -----------------------------------------------------


def test_skipped_topic_safety_phrasing(knowledge_service) -> None:
    context = _context(knowledge_service, completion_evidence=False, question_number=2)
    question = DeterministicQuestionGenerator().generate(context)
    assert "you built" not in question.question.lower()
    assert "your project" not in question.question.lower()


def test_prompt_blocks_completion_claims_when_evidence_absent(knowledge_service) -> None:
    context = _context(knowledge_service, completion_evidence=False)
    prompt = build_question_prompt(context)
    assert "never say \"you built\", \"your project\", or \"you have\"" in prompt
    assert "evidence the candidate completed this curriculum topic: absent" in prompt


# --- structured output validation (mocked LLM) --------------------------------


def test_llm_generator_returns_validated_question(knowledge_service) -> None:
    payload = {
        "question": "A user asks about a specific claim amount. How do you decide between SQL lookup, vector search, or hybrid retrieval?",
        "question_type": "scenario",
        "curriculum_day": DAY,
        "topic": TOPIC,
        "difficulty": "intermediate",
        "purpose": "Ground retrieval strategy in a query-routing scenario.",
    }
    generator = LLMQuestionGenerator(_FakeChat(json.dumps(payload)))
    question = generator.generate(_context(knowledge_service))
    assert isinstance(question, Question)
    assert question.curriculum_day == DAY
    assert question.question_type == "scenario"


def test_llm_generator_rejects_ungrounded_topic(knowledge_service) -> None:
    payload = {
        "question": "Describe Hibernate ORM mapping strategies.",
        "question_type": "conceptual",
        "curriculum_day": DAY,
        "topic": "Hibernate ORM",
        "difficulty": "intermediate",
        "purpose": "test",
    }
    generator = LLMQuestionGenerator(_FakeChat(json.dumps(payload)))
    with pytest.raises(InterviewEngineError):
        generator.generate(_context(knowledge_service))


def test_llm_generator_rejects_mismatched_day(knowledge_service) -> None:
    payload = {
        "question": "Question about a different day.",
        "question_type": "conceptual",
        "curriculum_day": 23,
        "topic": TOPIC,
        "difficulty": "intermediate",
        "purpose": "test",
    }
    generator = LLMQuestionGenerator(_FakeChat(json.dumps(payload)))
    with pytest.raises(InterviewEngineError):
        generator.generate(_context(knowledge_service))


def test_llm_generator_rejects_invalid_json(knowledge_service) -> None:
    generator = LLMQuestionGenerator(_FakeChat("sure, here is the question: ..."))
    with pytest.raises(InterviewEngineError):
        generator.generate(_context(knowledge_service))


def test_llm_generator_rejects_invalid_structure(knowledge_service) -> None:
    generator = LLMQuestionGenerator(_FakeChat('{"question": "only a question"}'))
    with pytest.raises(InterviewEngineError):
        generator.generate(_context(knowledge_service))
