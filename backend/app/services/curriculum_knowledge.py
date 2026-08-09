from pydantic import BaseModel

from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.curriculum import Curriculum, Module


class TopicNode(BaseModel):
    """One curriculum topic: a day connected to its module, objectives, and tools."""

    day: int
    title: str
    module: int
    module_title: str
    objectives: list[str]
    tools: list[str]


class CurriculumKnowledge(BaseModel):
    """Structured module -> day -> topic -> objectives -> tools representation."""

    cohort: str
    nodes: list[TopicNode]
    topics_by_day: dict[int, TopicNode]


class CurriculumKnowledgeService:
    """Exposes the curriculum as a knowledge graph for the question generator."""

    def __init__(self, curriculum_repository: CurriculumRepository) -> None:
        self._curriculum = curriculum_repository
        self._knowledge_cache: CurriculumKnowledge | None = None

    def knowledge(self) -> CurriculumKnowledge:
        """Return the built knowledge graph, constructed once and reused.

        The curriculum is static at runtime, so the node graph is memoized on the
        service instead of being rebuilt on every question/evaluation turn.
        """
        if self._knowledge_cache is None:
            self._knowledge_cache = self._build_knowledge()
        return self._knowledge_cache

    def _build_knowledge(self) -> CurriculumKnowledge:
        curriculum: Curriculum = self._curriculum.load()
        module_by_day: dict[int, Module] = {}
        for module in curriculum.modules:
            start, end = module.days
            for day_number in range(start, end + 1):
                module_by_day[day_number] = module

        nodes: list[TopicNode] = []
        for day in curriculum.days:
            day_module = module_by_day.get(day.day)
            nodes.append(
                TopicNode(
                    day=day.day,
                    title=day.title,
                    module=day_module.n if day_module else 0,
                    module_title=day_module.title if day_module else "Unknown",
                    objectives=list(day.objectives),
                    tools=list(day.tools),
                )
            )
        return CurriculumKnowledge(
            cohort=curriculum.cohort,
            nodes=nodes,
            topics_by_day={node.day: node for node in nodes},
        )

    def node(self, day_number: int) -> TopicNode | None:
        return self.knowledge().topics_by_day.get(day_number)

    def module_title(self, day_number: int) -> str | None:
        node = self.node(day_number)
        return node.module_title if node is not None else None
