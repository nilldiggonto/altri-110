from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.rules.rounding import percent

RockStatus = Literal["on_track", "off_track", "complete"]


@dataclass(frozen=True)
class MilestoneFacts:
    due_date: date
    done: bool


def rock_status(seeded: str, milestones: Sequence[MilestoneFacts], today: date) -> RockStatus:
    """Complete wins. Off track if seeded so, or an unfinished Milestone is past due (due today is not)."""
    if seeded == "complete":
        return "complete"
    if seeded == "off_track" or any(not m.done and m.due_date < today for m in milestones):
        return "off_track"
    return "on_track"


def rock_progress(seeded: str, milestones: Sequence[MilestoneFacts]) -> int:
    """Done / total as a whole percent. No Milestones: 0, or 100 once Complete."""
    if not milestones:
        return 100 if seeded == "complete" else 0
    return percent(sum(m.done for m in milestones), len(milestones))
