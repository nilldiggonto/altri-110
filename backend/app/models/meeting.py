from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.ids import new_id

SECTIONS = ("scorecard", "ids", "conclude")


class Meeting(Base):
    """Level 10 Meeting. The row is the source of truth for live state (section + timer)."""
    __tablename__ = "meetings"
    __table_args__ = (
        CheckConstraint(f"current_section IN {SECTIONS}", name="section"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ended_after_start"),
        # One active meeting per team.
        Index("uq_meetings_active_team", "team_id", unique=True, postgresql_where=text("ended_at IS NULL")),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id("mt"))
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    facilitator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_section: Mapped[str] = mapped_column(String(16), default="scorecard")
    section_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(default=0)


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MeetingRating(Base):
    __tablename__ = "meeting_ratings"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 10", name="rating_range"),)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
