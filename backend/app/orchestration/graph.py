"""LangGraph orchestration for the ProbeIQ adaptive interview engine.

Graph structure (one HTTP request = one graph invocation):

    START
      │  route(action)
      ├── "start"  ──▶ analyze_candidate ──▶ plan_interview ──▶ generate_question ──▶ END (WAIT at API boundary)
      │
      └── "answer" ──▶ evaluate_response ──▶ decide_next_step ──┬── COMPLETE ──▶ generate_feedback ──▶ END
                                                                └── other ──▶ generate_question ──▶ END (WAIT)

The WAIT box in the conceptual state machine is the API boundary: after
``generate_question`` the graph ends and the client holds the stored session until
it sends the next answer, at which point ``evaluate_response`` resumes the flow.

The graph is intentionally compiled without a checkpointer. State is explicit and
typed (``InterviewGraphState``): the start turn receives the raw candidate and the
answer turn receives the committed ``session`` as input, and every invocation
returns the full updated state. This makes each turn retry-safe -- a failed
invocation mutates nothing, and the caller simply retries with the same committed
session -- and keeps critical state out of hidden globals.
"""

from collections.abc import Hashable

from langgraph.graph import END, START, StateGraph

from app.agents.evaluation_agent import AnswerEvaluator
from app.agents.feedback_agent import FeedbackGenerator
from app.agents.question_agent import QuestionGenerator
from app.orchestration.nodes.analyze_candidate import build_analyze_candidate
from app.orchestration.nodes.decide_next_step import build_decide_next_step
from app.orchestration.nodes.evaluate_response import build_evaluate_response
from app.orchestration.nodes.generate_feedback import build_generate_feedback
from app.orchestration.nodes.generate_question import build_generate_question
from app.orchestration.nodes.plan_interview import build_plan_interview
from app.orchestration.state import InterviewGraphState
from app.services.candidate_service import CandidateAnalysisService
from app.services.curriculum_knowledge import CurriculumKnowledgeService
from app.services.profile_service import ProfileService
from app.services.strategy_service import StrategyService
from app.services.topic_planner import TopicPlannerService

_COMPLETION_ROUTES: dict[Hashable, str] = {
    "COMPLETE": "generate_feedback",
    "FOLLOW_UP": "generate_question",
    "NEW_TOPIC": "generate_question",
    "INCREASE_DIFFICULTY": "generate_question",
    "DECREASE_DIFFICULTY": "generate_question",
}

_START_ROUTES: dict[Hashable, str] = {
    "start": "analyze_candidate",
    "answer": "evaluate_response",
}


def build_interview_graph(
    *,
    analysis_service: CandidateAnalysisService,
    profile_service: ProfileService,
    topic_planner: TopicPlannerService,
    strategy_service: StrategyService,
    knowledge_service: CurriculumKnowledgeService,
    question_generator: QuestionGenerator,
    evaluator: AnswerEvaluator,
    feedback_generator: FeedbackGenerator,
    min_questions: int,
    min_covered_days: int,
    max_questions_per_topic: int,
    hard_max_questions: int,
):
    """Assemble and compile the interview StateGraph with the injected services."""
    graph = StateGraph(InterviewGraphState)

    graph.add_node("analyze_candidate", build_analyze_candidate(analysis_service, profile_service))
    graph.add_node("plan_interview", build_plan_interview(topic_planner, strategy_service, min_questions, min_covered_days))
    graph.add_node("generate_question", build_generate_question(knowledge_service, question_generator, min_questions, min_covered_days))
    graph.add_node("evaluate_response", build_evaluate_response(evaluator, knowledge_service))
    graph.add_node("decide_next_step", build_decide_next_step(min_questions, min_covered_days, max_questions_per_topic, hard_max_questions))
    graph.add_node("generate_feedback", build_generate_feedback(feedback_generator))

    graph.add_conditional_edges(
        START,
        lambda state: state.get("action", "start"),
        _START_ROUTES,
    )
    graph.add_edge("analyze_candidate", "plan_interview")
    graph.add_edge("plan_interview", "generate_question")
    graph.add_edge("generate_question", END)
    graph.add_edge("evaluate_response", "decide_next_step")
    graph.add_conditional_edges("decide_next_step", lambda state: state.get("decision"), _COMPLETION_ROUTES)
    graph.add_edge("generate_feedback", END)

    return graph.compile()
