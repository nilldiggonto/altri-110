"""Settings from env: DATABASE_URL, APP_NOW, SEED_PATH."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://altri:altri@localhost:5432/altri"
    app_now: str = "2026-11-11T15:00:00Z"
    seed_path: Path = ROOT / "data" / "seed.json"
    company_tz: str = "America/Chicago"


settings = Settings()
