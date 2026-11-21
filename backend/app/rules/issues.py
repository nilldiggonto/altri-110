from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar


@dataclass(frozen=True)
class IssueFacts:
    id: str
    priority: int | None
    created_at: datetime


T = TypeVar("T", bound=IssueFacts)


def issue_sort_key(i: IssueFacts) -> tuple:
    """Priority 5 first down to 1, no priority last; oldest first; id as final tie break."""
    return (-(i.priority or 0), i.created_at, i.id)


def issue_order(issues: Iterable[T]) -> list[T]:
    return sorted(issues, key=issue_sort_key)
