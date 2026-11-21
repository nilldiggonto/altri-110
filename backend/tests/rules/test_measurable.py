"""Measurable status: boundaries on track, closed week without score off track, current week pending."""
from datetime import date
from decimal import Decimal as D

import pytest

from app.rules.measurable import Goal, score_status

CUR = date(2026, 11, 9)
CLOSED = date(2026, 11, 2)


@pytest.mark.parametrize(
    "goal, value, expected",
    [
        (Goal("at_least", D(10)), D(10), "on_track"),
        (Goal("at_least", D(10)), D("9.99"), "off_track"),
        (Goal("at_most", D(5)), D(5), "on_track"),
        (Goal("at_most", D(5)), D("5.01"), "off_track"),
        (Goal("between", min=D(90), max=D(95)), D(90), "on_track"),
        (Goal("between", min=D(90), max=D(95)), D(95), "on_track"),
        (Goal("between", min=D(90), max=D(95)), D("89.9"), "off_track"),
        (Goal("between", min=D(90), max=D(95)), D("95.1"), "off_track"),
        (Goal("exactly", D(100)), D(100), "on_track"),
        (Goal("exactly", D(100)), D("100.5"), "off_track"),
    ],
)
def test_goal_types_and_boundaries(goal, value, expected):
    assert score_status(goal, value, CLOSED, CUR) == expected


def test_scored_current_week_has_a_status():
    assert score_status(Goal("at_least", D(10)), D(3), CUR, CUR) == "off_track"


def test_no_score_closed_week_is_off_track():
    assert score_status(Goal("at_least", D(10)), None, CLOSED, CUR) == "off_track"


def test_no_score_current_week_is_pending():
    assert score_status(Goal("at_least", D(10)), None, CUR, CUR) == "pending"
