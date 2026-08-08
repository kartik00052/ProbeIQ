import pytest

from app.core.exceptions import CurriculumDayNotFoundError


def test_day_count_and_sequence(curriculum_repository) -> None:
    days = curriculum_repository.all_days()
    assert len(days) == 31
    assert [day.day for day in days] == list(range(1, 32))


def test_module_count(curriculum_repository) -> None:
    assert len(curriculum_repository.modules()) == 8


def test_get_day(curriculum_repository) -> None:
    day = curriculum_repository.get_day(7)
    assert day.title == "Embeddings Explained"


def test_get_missing_day_raises(curriculum_repository) -> None:
    with pytest.raises(CurriculumDayNotFoundError):
        curriculum_repository.get_day(99)


def test_get_day_by_title(curriculum_repository) -> None:
    day = curriculum_repository.get_day_by_title("Embeddings Explained")
    assert day is not None
    assert day.day == 7


def test_get_day_by_unknown_title(curriculum_repository) -> None:
    assert curriculum_repository.get_day_by_title("No Such Day") is None


def test_days_for_module_uses_inclusive_range(curriculum_repository) -> None:
    days = curriculum_repository.days_for_module(3)
    assert [day.day for day in days] == [7, 8, 9, 10]


def test_module_for_day(curriculum_repository) -> None:
    module = curriculum_repository.module_for_day(12)
    assert module is not None
    assert module.n == 4
    assert module.title == "LLM Core, Prompting & Fine-Tuning"


def test_every_module_days_present_in_curriculum(curriculum_repository) -> None:
    day_numbers = {day.day for day in curriculum_repository.all_days()}
    for module in curriculum_repository.modules():
        start, end = module.days
        assert all(day_number in day_numbers for day_number in range(start, end + 1))
