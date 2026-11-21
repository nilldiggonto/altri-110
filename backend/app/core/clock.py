"""Single source of "now". Anchored at APP_NOW, never the system date.

In running mode the clock advances from APP_NOW by real elapsed time (monotonic),
so timestamps keep their order and the meeting timer moves. Tests can freeze or set it.
"""
import time
from datetime import UTC, datetime, timedelta

from app.core.config import settings


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class Clock:
    def __init__(self, anchor: datetime, running: bool) -> None:
        self.set(anchor, running)

    def set(self, anchor: datetime, running: bool = False) -> None:
        self._anchor, self._running, self._t0 = anchor, running, time.monotonic()

    def advance(self, seconds: float) -> None:
        self._anchor += timedelta(seconds=seconds)

    def now(self) -> datetime:
        if not self._running:
            return self._anchor
        return self._anchor + timedelta(seconds=time.monotonic() - self._t0)


clock = Clock(parse_utc(settings.app_now), settings.app_clock == "running")


def app_now() -> datetime:
    """Exactly APP_NOW, for the rules report."""
    return parse_utc(settings.app_now)


def now() -> datetime:
    return clock.now()
