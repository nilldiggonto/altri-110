from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core import time as ct
from app.models import Issue, Measurable, Score, User
from app.rules.measurable import score_status
from app.schemas.work import CellOut, GoalOut, MeasurableRowOut, ScorecardOut
from app.services.errors import bad_request, not_found
from app.services.report import goal_of


def _f(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


def team_measurable(db: Session, team_id: str, measurable_id: str) -> Measurable:
    m = db.get(Measurable, measurable_id)
    if not m or m.team_id != team_id:
        raise not_found("Measurable")
    return m


def editable_week(week: date, now: datetime) -> date:
    if week.weekday() != 0:
        raise bad_request("week_start must be a Monday")
    if week > ct.week_of(now):
        raise bad_request("Cannot score a future week")
    return week


def get_scorecard(db: Session, team_id: str, now: datetime) -> ScorecardOut:
    current = ct.week_of(now)
    weeks = ct.last_weeks(current)
    ms = db.scalars(select(Measurable).where(Measurable.team_id == team_id).order_by(Measurable.id)).all()
    ids = [m.id for m in ms]
    scores = {
        (s.measurable_id, s.week_start): s.value
        for s in db.scalars(select(Score).where(Score.measurable_id.in_(ids), Score.week_start.in_(weeks)))
    }
    open_issues = {
        (i.source_measurable_id, i.source_week_start): i.id
        for i in db.scalars(select(Issue).where(Issue.source_measurable_id.in_(ids), Issue.solved_at.is_(None)))
    }
    rows = [
        MeasurableRowOut(
            id=m.id, name=m.name, unit=m.unit, owner_id=m.owner_id,
            goal=GoalOut(type=m.goal_type, value=_f(m.goal_value), min=_f(m.goal_min), max=_f(m.goal_max)),
            cells=[
                CellOut(
                    week_start=w, value=_f(scores.get((m.id, w))),
                    status=score_status(goal_of(m), scores.get((m.id, w)), w, current),
                    open_issue_id=open_issues.get((m.id, w)),
                )
                for w in weeks
            ],
        )
        for m in ms
    ]
    return ScorecardOut(weeks=weeks, current_week=current, measurables=rows)


def set_score(db: Session, team_id: str, measurable_id: str, week: date, value: float, user: User, now: datetime) -> None:
    """Upsert. Last save wins."""
    team_measurable(db, team_id, measurable_id)
    editable_week(week, now)
    v = Decimal(str(value))
    stmt = insert(Score).values(measurable_id=measurable_id, week_start=week, value=v, updated_at=now, updated_by=user.id)
    db.execute(stmt.on_conflict_do_update(
        index_elements=[Score.measurable_id, Score.week_start],
        set_={"value": v, "updated_at": now, "updated_by": user.id},
    ))
    db.commit()


def clear_score(db: Session, team_id: str, measurable_id: str, week: date, now: datetime) -> None:
    team_measurable(db, team_id, measurable_id)
    editable_week(week, now)
    db.query(Score).filter_by(measurable_id=measurable_id, week_start=week).delete()
    db.commit()
