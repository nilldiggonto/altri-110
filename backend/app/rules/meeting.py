from collections.abc import Iterable
from fractions import Fraction

from app.rules.rounding import one_decimal


def meeting_rating(ratings: Iterable[int]) -> float | None:
    """Average of submitted ratings, one decimal half up. No ratings: None."""
    rs = list(ratings)
    return one_decimal(Fraction(sum(rs), len(rs))) if rs else None
