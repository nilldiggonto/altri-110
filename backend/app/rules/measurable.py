from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

Status = Literal["on_track", "off_track", "pending"]


@dataclass(frozen=True)
class Goal:
    type: Literal["at_least", "at_most", "between", "exactly"]
    value: Decimal | None = None
    min: Decimal | None = None
    max: Decimal | None = None


def meets_goal(goal: Goal, v: Decimal) -> bool:
    """Boundaries are on track."""
    match goal.type:
        case "at_least":
            return v >= goal.value
        case "at_most":
            return v <= goal.value
        case "between":
            return goal.min <= v <= goal.max
        case "exactly":
            return v == goal.value
    raise ValueError(goal.type)


def score_status(goal: Goal, value: Decimal | None, week: date, current_week: date) -> Status:
    """No score: pending in the current (or a future) week, off track once the week is closed."""
    if value is None:
        return "pending" if week >= current_week else "off_track"
    return "on_track" if meets_goal(goal, value) else "off_track"
