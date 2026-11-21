"""The rules on the seed records that sit next to a boundary on purpose, through the report service."""
import pytest

from app.services.report import team_report
from tests.conftest import APP_NOW


@pytest.fixture
def lead(db):
    return team_report(db, "team_lead", APP_NOW)


def test_done_minutes_around_week_end(lead):
    # t28 done Mon 2026-11-09 05:59Z (Sun 23:59 Chicago) counts; t29 at 06:01Z (Mon 00:01) does not.
    assert lead["todo_completion"]["2026-11-02"] == {"due": 10, "done": 9, "rate_percent": 90, "meets_target": True}


def test_done_in_dst_end_hour_counts(lead):
    # t11 due Oct 30, done 2026-11-02T05:30Z = Sun Nov 1 23:30 CST, inside the week of Oct 26.
    assert lead["todo_completion"]["2026-10-26"]["done"] == 2


def test_current_week_and_empty_weeks(lead):
    assert lead["todo_completion"]["2026-11-09"]["meets_target"] is False
    assert lead["todo_completion"]["2026-08-17"] is None


def test_rating_excludes_non_rater_and_rounds_half_up(lead):
    # mt2: u5 attended without rating; 8, 9, 8, 8 -> 8.25 -> 8.3.
    mt2 = lead["meetings"]["mt2"]
    assert "u5" in mt2["attendee_ids"] and mt2["rating"] == 8.3


def test_issue_order_on_seed(lead):
    assert lead["issue_order"] == ["i2", "i1", "i5", "i3", "i4"]
