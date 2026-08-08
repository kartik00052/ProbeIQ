import json
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import CandidateNotFoundError, DataLoadError
from app.schemas.candidate import Candidate


class CandidateRepository:
    """Loads and validates candidates from the supplied JSON file."""

    def __init__(self, data_path: Path | None = None) -> None:
        self._path = data_path or (settings.data_dir / "candidates.json")
        self._candidates: list[Candidate] | None = None

    def _load_raw(self) -> list[dict]:
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise DataLoadError(f"failed to load candidate data from {self._path}: {exc}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
            raise DataLoadError(f"candidate data file {self._path} must contain a 'candidates' list")
        return payload["candidates"]

    def all(self) -> list[Candidate]:
        if self._candidates is None:
            self._candidates = [Candidate.model_validate(item) for item in self._load_raw()]
        return list(self._candidates)

    def get(self, candidate_id: str) -> Candidate:
        for candidate in self.all():
            if candidate.member.id == candidate_id:
                return candidate
        raise CandidateNotFoundError(f"candidate '{candidate_id}' not found")
