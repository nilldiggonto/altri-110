"""To-Do completion rate (target 90%) and overdue."""
from datetime import UTC, date, datetime, timedelta

from app.core import time as ct
from app.rules.todos import TodoFacts, completion, is_overdue

WEEK = date(2026, 11, 2)
END = ct.week_bounds_utc(WEEK)[1]  # Mon 2026-11-09 06:00Z
DUE = date(2026, 11, 6)


def todos(done: int, total: int, done_at: datetime = datetime(2026, 11, 5, tzinfo=UTC)) -> list[TodoFacts]:
    return [TodoFacts(f"t{i}", DUE, done_at if i < done else None) for i in range(total)]


def rate(ts):
    return completion(ts, WEEK, END)


def test_exactly_90_meets_target():
    c = rate(todos(9, 10))
    assert (c.due, c.done, c.rate_percent, c.meets_target) == (10, 9, 90, True)


def test_just_under_90_misses_even_if_rounded_to_90():
    c = rate(todos(179, 200))  # 89.5% rounds to 90, exact ratio is under target
    assert c.rate_percent == 90 and c.meets_target is False


def test_rate_rounds_half_up():
    assert rate(todos(1, 8)).rate_percent == 13


def test_zero_due_is_no_rate():
    assert rate([]) is None
    assert rate([TodoFacts("t1", WEEK + timedelta(days=7), None)]) is None


def test_due_week_is_monday_to_sunday():
    ts = [TodoFacts("mon", WEEK, None), TodoFacts("sun", WEEK + timedelta(days=6), None),
          TodoFacts("next", WEEK + timedelta(days=7), None), TodoFacts("prev", WEEK - timedelta(days=1), None)]
    assert rate(ts).due == 2


def test_done_after_due_week_counts_as_not_done():
    one_s = timedelta(seconds=1)
    assert rate([TodoFacts("a", DUE, END - one_s)]).done == 1  # Sun 23:59:59 Chicago
    assert rate([TodoFacts("a", DUE, END)]).done == 0  # Mon 00:00 Chicago


def test_dst_week_end_uses_company_time():
    week = date(2026, 10, 26)
    end = ct.week_bounds_utc(week)[1]  # 2026-11-02T06:00Z, after DST ends
    late_cdt = datetime(2026, 11, 2, 5, 30, tzinfo=UTC)  # Sun 23:30 CST, still inside the week
    assert completion([TodoFacts("a", date(2026, 10, 30), late_cdt)], week, end).done == 1


def test_overdue_is_strictly_before_today():
    today = date(2026, 11, 11)
    assert is_overdue(TodoFacts("a", date(2026, 11, 10), None), today)
    assert not is_overdue(TodoFacts("a", today, None), today)  # due today is not overdue
    assert not is_overdue(TodoFacts("a", date(2026, 11, 10), datetime(2026, 11, 11, tzinfo=UTC)), today)
