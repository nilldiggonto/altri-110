from collections.abc import Iterable
from fractions import Fraction

from app.rules.rounding import one_decimal

# Agenda in order, with planned minutes. Overrun shows as over time; it never auto-advances.
AGENDA: tuple[tuple[str, int], ...] = (("scorecard", 5), ("ids", 60), ("conclude", 10))


def next_section(section: str) -> str | None:
    keys = [k for k, _ in AGENDA]
    i = keys.index(section)
    return keys[i + 1] if i + 1 < len(keys) else None


def meeting_rating(ratings: Iterable[int]) -> float | None:
    """Average of submitted ratings, one decimal half up. No ratings: None."""
    rs = list(ratings)
    return one_decimal(Fraction(sum(rs), len(rs))) if rs else None
