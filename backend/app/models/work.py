from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Text, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.ids import new_id

GOAL_TYPES = ("at_least", "at_most", "between", "exactly")
ROCK_STATUSES = ("on_track", "off_track", "complete")


class Measurable(Base):
    __tablename__ = "measurables"
    __table_args__ = (
        CheckConstraint(f"goal_type IN {GOAL_TYPES}", name="goal_type"),
        CheckConstraint(
            "(goal_type = 'between' AND goal_min IS NOT NULL AND goal_max IS NOT NULL"
            " AND goal_min <= goal_max AND goal_value IS NULL)"
            " OR (goal_type <> 'between' AND goal_value IS NOT NULL"
            " AND goal_min IS NULL AND goal_max IS NULL)",
            name="goal_shape",
        ),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    unit: Mapped[str] = mapped_column(String(32))
    goal_type: Mapped[str] = mapped_column(String(16))
    goal_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    goal_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    goal_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))


class Score(Base):
    """One value per Measurable per company week (keyed by its Monday)."""
    __tablename__ = "scores"
    __table_args__ = (CheckConstraint("EXTRACT(ISODOW FROM week_start) = 1", name="week_is_monday"),)
    measurable_id: Mapped[str] = mapped_column(ForeignKey("measurables.id", ondelete="CASCADE"), primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class Rock(Base):
    __tablename__ = "rocks"
    __table_args__ = (
        CheckConstraint(f"status IN {ROCK_STATUSES}", name="status"),
        CheckConstraint("quarter ~ '^[0-9]{4}-Q[1-4]$'", name="quarter_format"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    quarter: Mapped[str] = mapped_column(String(7))
    status: Mapped[str] = mapped_column(String(16))


class Milestone(Base):
    __tablename__ = "milestones"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rock_id: Mapped[str] = mapped_column(ForeignKey("rocks.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    due_date: Mapped[date] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, default=False)


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        CheckConstraint("char_length(btrim(title)) > 0", name="title_not_blank"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
        CheckConstraint(
            "(source_measurable_id IS NULL) = (source_week_start IS NULL)", name="source_pair"
        ),
        CheckConstraint(
            "(solved_at IS NULL AND resolution_note IS NULL)"
            " OR (solved_at IS NOT NULL AND char_length(btrim(resolution_note)) > 0)",
            name="solved_has_note",
        ),
        # Make it an Issue dedupe: at most one unsolved Issue per Measurable and week.
        Index(
            "uq_issues_open_source",
            "source_measurable_id",
            "source_week_start",
            unique=True,
            postgresql_where=text("solved_at IS NULL AND source_measurable_id IS NOT NULL"),
        ),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id("i"))
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    priority: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    source_measurable_id: Mapped[str | None] = mapped_column(ForeignKey("measurables.id"))
    source_week_start: Mapped[date | None] = mapped_column(Date)


class Todo(Base):
    __tablename__ = "todos"
    __table_args__ = (CheckConstraint("char_length(btrim(title)) > 0", name="title_not_blank"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id("t"))
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[date] = mapped_column(Date)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_issue_id: Mapped[str | None] = mapped_column(ForeignKey("issues.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
