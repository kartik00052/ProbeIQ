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


settings = Settings()
