"""Single source of "now": reads APP_NOW, never the system clock."""
from datetime import UTC, datetime

from app.core.config import settings


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def now() -> datetime:
    return parse_utc(settings.app_now)
