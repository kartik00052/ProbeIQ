from pathlib import Path

from pydantic import SecretStr
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
    # The deterministic ProbeIQ controller still decides WHAT to probe; the LLM only
    # decides HOW to phrase the question and how to judge an answer.
    # When disabled (default), the template question generator and heuristic
    # evaluator are used so the service runs fully offline.
    llm_enabled: bool = False
    # Chat model provider: "nvidia" | "openai" | "openai-compatible".
    # "nvidia" reaches NVIDIA-hosted GLM 5.2 via its OpenAI-compatible endpoint
    # (default base URL applied by app.llm.factory when base_url is empty).
    llm_provider: str = "openai-compatible"
    llm_base_url: str = ""
    # Stored as SecretStr so repr/logs never expose the key.
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = ""
    llm_temperature: float = 0.0
    # Sampling / generation knobs (GLM 5.2 defaults documented in .env.example).
    llm_top_p: float = 1.0
    llm_max_tokens: int = 16384
    llm_seed: int = 42
    # Bounded retry count for transient LLM failures (handled by the chat client).
    llm_max_retries: int = 2


settings = Settings()
