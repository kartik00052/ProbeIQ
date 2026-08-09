def test_knowledge_contains_all_days(knowledge_service) -> None:
    knowledge = knowledge_service.knowledge()
    assert len(knowledge.nodes) == 31
    assert list(knowledge.topics_by_day) == list(range(1, 32))


def test_knowledge_node_grounds_question_generation(knowledge_service) -> None:
    node = knowledge_service.node(10)
    assert node is not None
    assert node.title == "The Retrieval & Matching Engine"
    assert node.module == 3
    assert node.module_title == "Embeddings & Vector Search"
    assert len(node.objectives) == 5
    assert any("retriev" in objective.lower() for objective in node.objectives)
    assert len(node.tools) == 3


def test_knowledge_connects_module_to_days(knowledge_service) -> None:
    knowledge = knowledge_service.knowledge()
    module_3_days = [node.day for node in knowledge.nodes if node.module == 3]
    assert module_3_days == [7, 8, 9, 10]


def test_unknown_day_returns_none(knowledge_service) -> None:
    assert knowledge_service.node(99) is None


def test_knowledge_is_memoized(knowledge_service) -> None:
    assert knowledge_service.knowledge() is knowledge_service.knowledge()
