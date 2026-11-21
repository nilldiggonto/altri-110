"""Rock status and progress."""
from datetime import date

from app.rules.rocks import MilestoneFacts as M, rock_progress, rock_status

TODAY = date(2026, 11, 11)


def test_seeded_complete_wins():
    assert rock_status("complete", [M(date(2026, 10, 1), False)], TODAY) == "complete"


def test_seeded_off_track_stays_off_track():
    assert rock_status("off_track", [M(date(2026, 12, 1), False)], TODAY) == "off_track"


def test_unfinished_past_due_milestone_is_off_track():
    assert rock_status("on_track", [M(date(2026, 11, 10), False)], TODAY) == "off_track"


def test_milestone_due_today_is_not_past_due():
    assert rock_status("on_track", [M(TODAY, False)], TODAY) == "on_track"


def test_done_past_milestone_keeps_on_track():
    assert rock_status("on_track", [M(date(2026, 10, 1), True)], TODAY) == "on_track"


def test_no_milestones_uses_seeded_status():
    assert rock_status("on_track", [], TODAY) == "on_track"
    assert rock_status("off_track", [], TODAY) == "off_track"


def test_progress_whole_percent_half_up():
    ms = [M(TODAY, True)] + [M(TODAY, False)] * 7
    assert rock_progress("on_track", ms) == 13  # 12.5 -> 13
    assert rock_progress("on_track", [M(TODAY, True)] * 2 + [M(TODAY, False)]) == 67


def test_progress_no_milestones():
    assert rock_progress("on_track", []) == 0
    assert rock_progress("off_track", []) == 0
    assert rock_progress("complete", []) == 100
