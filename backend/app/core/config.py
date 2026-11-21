"""Settings from env: DATABASE_URL, APP_NOW, APP_CLOCK, SEED_PATH, SECRET_KEY, CORS_ORIGINS."""
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://altri:altri@localhost:5432/altri"
    app_now: str = "2026-11-11T15:00:00Z"
    # running: starts at APP_NOW and advances in real time (meeting timers work).
    # frozen: always exactly APP_NOW (rules report, tests).
    app_clock: Literal["running", "frozen"] = "running"
    seed_path: Path = ROOT / "data" / "seed.json"
    company_tz: str = "America/Chicago"
    secret_key: str = "dev-only-change-me"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
