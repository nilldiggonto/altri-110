"""Company time helpers: America/Chicago weeks (Monday start), quarters, today."""
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings

TZ = ZoneInfo(settings.company_tz)


def local_date(ts: datetime) -> date:
    return ts.astimezone(TZ).date()


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def week_of(ts: datetime) -> date:
    return week_start(local_date(ts))


def week_bounds_utc(ws: date) -> tuple[datetime, datetime]:
    """[start, end) of a company week in UTC. DST safe."""
    start = datetime.combine(ws, time.min, TZ)
    end = datetime.combine(ws + timedelta(days=7), time.min, TZ)
    return start.astimezone(UTC), end.astimezone(UTC)


def end_of_day_utc(d: date) -> datetime:
    """Exclusive end of a company calendar date in UTC."""
    return datetime.combine(d + timedelta(days=1), time.min, TZ).astimezone(UTC)


def last_weeks(current: date, n: int = 13) -> list[date]:
    return [current - timedelta(weeks=i) for i in range(n - 1, -1, -1)]


def quarter_of(d: date) -> str:
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"
