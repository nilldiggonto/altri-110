"""Issue order and meeting rating."""
from datetime import UTC, datetime

from app.rules.issues import IssueFacts as I, issue_order
from app.rules.meeting import meeting_rating


def at(h: int) -> datetime:
    return datetime(2026, 11, 1, h, tzinfo=UTC)


def test_issue_order_priority_then_oldest_then_no_priority():
    issues = [
        I("none_old", None, at(1)), I("p1", 1, at(1)), I("p5_new", 5, at(9)),
        I("p5_old", 5, at(2)), I("p3", 3, at(1)), I("none_new", None, at(8)),
    ]
    assert [i.id for i in issue_order(issues)] == ["p5_old", "p5_new", "p3", "p1", "none_old", "none_new"]


def test_issue_order_same_time_is_stable_by_id():
    assert [i.id for i in issue_order([I("b", 2, at(1)), I("a", 2, at(1))])] == ["a", "b"]


def test_rating_average_one_decimal_half_up():
    assert meeting_rating([8, 8, 8, 9]) == 8.3  # 8.25 -> 8.3
    assert meeting_rating([7, 8]) == 7.5
    assert meeting_rating([9]) == 9.0


def test_rating_excludes_non_raters_and_none_means_no_score():
    # Callers pass only submitted ratings; attendees who did not rate add nothing.
    assert meeting_rating([10, 6]) == 8.0
    assert meeting_rating([]) is None
