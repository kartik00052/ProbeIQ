from pathlib import Path
from typing import Any

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

    # CORS allowed browser origins (comma-separated). The API authenticates with an
    # HTTP-only session cookie, so credentials are enabled and origins must stay
    # explicit. Defaults to the Vite dev origin; set
    # PROBEIQ_CORS_ALLOWED_ORIGINS to the deployed frontend origin(s) in
    # production (e.g. https://app.example.com). Never use "*".
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    # Auth persistence: SQLite via SQLAlchemy. When PROBEIQ_DATABASE_URL is unset,
    # a `probeiq.db` file is created under the data dir (app/data).
    database_url: str | None = None

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(self.data_dir / 'probeiq.db').as_posix()}"

    # Authenticated-session cookie (HTTP-only).
    auth_cookie_name: str = "probeiq_session"
    auth_session_ttl_days: int = 14

    @property
    def auth_session_ttl_seconds(self) -> int:
        return self.auth_session_ttl_days * 24 * 60 * 60

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
    # Optional multi-model roster (JSON list). Each entry is a dict:
    #   {
    #     "provider": "nvidia" | "openai" | "openai-compatible",
    #     "model": "...",
    #     "api_key": "...",
    #     "base_url": "",                    # empty -> provider default
    #     "temperature": 0.0, "top_p": 1.0, "seed": 42,
    #     "max_tokens": 16384,               # completion token budget
    #     "max_retries": 2,                  # transient-retry count (OpenAI-compatible)
    #     "reasoning_budget": null,          # NVIDIA reasoning models (e.g. nemotron-3-ultra)
    #     "enable_thinking": false           # NVIDIA chat_template_kwargs.enable_thinking
    #   }
    # The first entry is the PRIMARY model; the rest are automatic fallbacks --
    # if an LLM call fails, the engine retries with the next entry (LangChain
    # ``ChatNVIDIA`` / ``ChatOpenAI`` per entry). When empty (default), the
    # single-model settings below (``llm_model`` / ``llm_api_key`` / ...) are used.
    llm_models: list[dict[str, Any]] = []
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
    # Per-request transport timeout (seconds) applied to each LLM chat client.
    # Bounds how long a slow or congested provider can stall one call before the
    # fallback roster moves to the next model (FallbackChatModel treats any
    # failure -- including a timeout -- as a model failure). 60 preserves the
    # LangChain provider default; a lower value (e.g. 30) keeps a pathological
    # model from blocking the whole interview with a long serial roster wait.
    llm_timeout_seconds: int = 60


settings = Settings()
