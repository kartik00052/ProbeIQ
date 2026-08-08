from app.schemas.curriculum import Curriculum, Day, Module


def test_module_schema() -> None:
    module = Module(n=3, title="Embeddings & Vector Search", days=(7, 10))
    assert module.days == (7, 10)
    assert module.n == 3


def test_day_schema() -> None:
    day = Day(
        day=7,
        title="Embeddings Explained",
        type="AI_CORE",
        tools=["Sentence Transformers"],
        objectives=["Generate embeddings"],
    )
    assert day.type == "AI_CORE"
    assert len(day.tools) == 1
    assert len(day.objectives) == 1


def test_curriculum_schema() -> None:
    curriculum = Curriculum(
        cohort="AI Cohort · 31 days · 8 modules",
        modules=[Module(n=1, title="M", days=(1, 3))],
        days=[Day(day=1, title="D", type="SETUP", tools=[], objectives=[])],
    )
    assert len(curriculum.modules) == 1
    assert len(curriculum.days) == 1
