from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import In, Out

Section = Literal["scorecard", "ids", "conclude"]


class AgendaItemOut(Out):
    section: Section
    minutes: int


class AttendeeOut(Out):
    user_id: str
    joined_at: datetime | None


class RatingOut(Out):
    user_id: str
    rating: int


class MeetingOut(Out):
    """Live state. Clients show elapsed = server_now - section_started_at, offset by their own clock skew."""
    id: str
    team_id: str
    facilitator_id: str
    started_at: datetime
    ended_at: datetime | None
    current_section: Section
    section_started_at: datetime
    version: int
    server_now: datetime
    agenda: list[AgendaItemOut]
    attendees: list[AttendeeOut]
    ratings: list[RatingOut]
    rating: float | None
    issues_solved: list[str]
    todos_created: list[str]


class AdvanceIn(In):
    to: Section  # must be the next section; equal to the current one is a no-op (double click)


class RatingIn(In):
    rating: Annotated[int, Field(ge=1, le=10)]


class MeetingSummaryOut(Out):
    meeting_id: str
    started_at: datetime
    ended_at: datetime
    scorecard_week: str
    measurable_status: dict[str, str]
    issues_solved: list[str]
    todos_created: list[str]
    attendee_ids: list[str]
    rating: float | None
