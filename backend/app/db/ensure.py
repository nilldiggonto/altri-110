"""Create the configured database if it does not exist (tests and e2e use their own database).

Run: python -m app.db.ensure
"""
import psycopg
from sqlalchemy.engine import make_url

from app.core.config import settings


def ensure_database(url: str) -> None:
    u = make_url(url)
    admin = u.set(database="postgres", drivername="postgresql")
    with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (u.database,)).fetchone():
            conn.execute(f'CREATE DATABASE "{u.database}"')


if __name__ == "__main__":
    ensure_database(settings.database_url)
