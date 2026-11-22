"""Test fixtures: a separate Postgres database, migrated and reseeded, and a frozen clock.

Env is set before any app import, because settings are read at import time.
TEST_DATABASE_URL overrides the default altri_test database on the dev Postgres.
"""
import os

DEFAULT_TEST_DB = "postgresql+psycopg://altri:altri@localhost:5432/altri_test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB)
os.environ["APP_NOW"] = "2026-11-11T15:00:00Z"
os.environ["APP_CLOCK"] = "frozen"
os.environ.setdefault("SECRET_KEY", "test-secret")

import json  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app.core.clock import clock, parse_utc  # noqa: E402
from app.core.config import ROOT, settings  # noqa: E402
from app.db.ensure import ensure_database  # noqa: E402

APP_NOW = parse_utc(settings.app_now)


@pytest.fixture(scope="session")
def migrated() -> None:
    ensure_database(settings.database_url)
    cfg = Config(str(ROOT / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "backend" / "alembic"))
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def seed_data() -> dict:
    return json.loads(settings.seed_path.read_text())


@pytest.fixture
def seeded(migrated, seed_data) -> None:
    """A freshly seeded database for each test that asks for it."""
    from app.db.session import SessionLocal
    from app.seed.load import load, reset

    with SessionLocal.begin() as db:
        reset(db)
        load(db, seed_data)


@pytest.fixture(autouse=True)
def frozen_clock():
    """Every test starts at APP_NOW with the clock frozen; tests may advance it."""
    clock.set(APP_NOW, running=False)
    yield clock
    clock.set(APP_NOW, running=False)


@pytest.fixture
def db(seeded):
    from app.db.session import SessionLocal

    with SessionLocal() as s:
        yield s


@pytest.fixture
def client(seeded):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


def auth(user_id: str) -> dict[str, str]:
    from app.core.security import issue_token

    return {"Authorization": f"Bearer {issue_token(user_id)}"}
