"""Company time: Monday 00:00 to Sunday 23:59:59 America/Chicago, calendar quarters."""
from datetime import UTC, date, datetime

from app.core import time as ct


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def test_week_boundary_in_company_time():
    # Mon 2026-11-09 00:00 Chicago (CST) is 06:00Z.
    assert ct.week_of(utc("2026-11-09T05:59:59")) == date(2026, 11, 2)
    assert ct.week_of(utc("2026-11-09T06:00:00")) == date(2026, 11, 9)


def test_week_bounds_across_dst_end():
    # Week of Oct 26 starts in CDT (05:00Z) and ends in CST (06:00Z): 169 hours long.
    start, end = ct.week_bounds_utc(date(2026, 10, 26))
    assert start == utc("2026-10-26T05:00:00")
    assert end == utc("2026-11-02T06:00:00")


def test_today_is_company_date():
    assert ct.local_date(utc("2026-11-12T05:59:59")) == date(2026, 11, 11)
    assert ct.local_date(utc("2026-11-12T06:00:00")) == date(2026, 11, 12)


def test_last_13_weeks_end_with_current():
    weeks = ct.last_weeks(date(2026, 11, 9))
    assert len(weeks) == 13 and weeks[0] == date(2026, 8, 17) and weeks[-1] == date(2026, 11, 9)


def test_calendar_quarter():
    assert ct.quarter_of(date(2026, 9, 30)) == "2026-Q3"
    assert ct.quarter_of(date(2026, 10, 1)) == "2026-Q4"
