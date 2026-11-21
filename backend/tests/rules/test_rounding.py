from fractions import Fraction

from app.rules.rounding import one_decimal, percent


def test_percent_half_up():
    assert percent(1, 8) == 13  # 12.5 -> 13
    assert percent(1, 3) == 33
    assert percent(2, 3) == 67


def test_one_decimal_half_up():
    assert one_decimal(Fraction(33, 4)) == 8.3  # 8.25 -> 8.3, float would give 8.2
    assert one_decimal(Fraction(8, 1)) == 8.0
