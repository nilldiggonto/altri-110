from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction


def _half_up(x: Fraction, places: int) -> Decimal:
    q = Decimal(1).scaleb(-places)
    return (Decimal(x.numerator) / Decimal(x.denominator)).quantize(q, rounding=ROUND_HALF_UP)


def percent(num: int, den: int) -> int:
    """Whole percent, half up (12.5 -> 13). Exact: no float division."""
    exact = Fraction(num * 100, den)
    return int(_half_up(exact, 0))


def one_decimal(x: Fraction) -> float:
    """One decimal, half up (8.25 -> 8.3)."""
    return float(_half_up(x, 1))
