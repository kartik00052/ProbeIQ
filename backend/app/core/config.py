from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
APP_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = APP_DIR / "data"


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables (prefix PROBEIQ_)."""

    model_config = SettingsConfigDict(
        env_prefix="PROBEIQ_",
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = DEFAULT_DATA_DIR
    environment: str = "development"

    # Adaptive interview engine constants (see .opencode/technical-spec.md).
    min_questions: int = 8
    min_covered_days: int = 4
    max_questions_per_topic: int = 3
    # Hard cap on total questions before the engine is forced to stop (safety valve).
    hard_max_questions: int = 16

    # Optional LLM-backed question generator / answer evaluator.
    # Points at any OpenAI-compatible endpoint (e.g. NVIDIA NIM or OpenAI).
    # When disabled, the deterministic template generator and heuristic
    # evaluator are used so the service runs fully offline.
    llm_enabled: bool = False
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_temperature: float = 0.0


settings = Settings()
