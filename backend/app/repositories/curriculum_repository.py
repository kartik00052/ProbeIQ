import json
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import CurriculumDayNotFoundError, DataLoadError
from app.schemas.curriculum import Curriculum, Day, Module


class CurriculumRepository:
    """Deterministic, in-memory access to the supplied curriculum JSON."""

    def __init__(self, data_path: Path | None = None) -> None:
        self._path = data_path or (settings.data_dir / "curriculum.json")
        self._curriculum: Curriculum | None = None

    def load(self) -> Curriculum:
        if self._curriculum is not None:
            return self._curriculum
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise DataLoadError(f"failed to load curriculum data from {self._path}: {exc}") from exc
        self._curriculum = Curriculum.model_validate(payload)
        return self._curriculum

    def all_days(self) -> list[Day]:
        return list(self.load().days)

    def modules(self) -> list[Module]:
        return list(self.load().modules)

    def get_day(self, day_number: int) -> Day:
        for day in self.load().days:
            if day.day == day_number:
                return day
        raise CurriculumDayNotFoundError(f"curriculum day {day_number} not found")

    def get_day_by_title(self, title: str) -> Day | None:
        for day in self.load().days:
            if day.title == title:
                return day
        return None

    def module_for_day(self, day_number: int) -> Module | None:
        for module in self.load().modules:
            start, end = module.days
            if start <= day_number <= end:
                return module
        return None

    def days_for_module(self, module_number: int) -> list[Day]:
        module = next((m for m in self.modules() if m.n == module_number), None)
        if module is None:
            return []
        start, end = module.days
        return [day for day in self.all_days() if start <= day.day <= end]
