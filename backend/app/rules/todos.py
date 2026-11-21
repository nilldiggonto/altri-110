from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.rules.rounding import percent

TARGET_NUM, TARGET_DEN = 9, 10  # 90%


@dataclass(frozen=True)
class TodoFacts:
    id: str
    due_date: date
    done_at: datetime | None


@dataclass(frozen=True)
class Completion:
    due: int
    done: int
    rate_percent: int
    meets_target: bool


def is_overdue(t: TodoFacts, today: date) -> bool:
    """Not done and due before today. Due today is not overdue."""
    return t.done_at is None and t.due_date < today


def completion(todos: Iterable[TodoFacts], week: date, week_end_utc: datetime) -> Completion | None:
    """Done by the end of the week / due that week. Done after the due week counts as not done.

    week_end_utc is the exclusive end of the company week (next Monday 00:00 local, in UTC).
    """
    week_last = week + timedelta(days=6)
    due = [t for t in todos if week <= t.due_date <= week_last]
    if not due:
        return None
    done = sum(1 for t in due if t.done_at is not None and t.done_at < week_end_utc)
    n = len(due)
    return Completion(n, done, percent(done, n), done * TARGET_DEN >= n * TARGET_NUM)
