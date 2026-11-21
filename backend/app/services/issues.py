from datetime import date, datetime, timedelta

from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core import time as ct
from app.models import Issue, Measurable, Membership, Score, Todo, User
from app.models.ids import as_dict, new_id
from app.rules.issues import issue_order
from app.rules.measurable import score_status
from app.schemas.work import IssueOut, IssueSourceOut
from app.services.errors import bad_request, conflict, not_found
from app.services.report import goal_of
from app.services.scorecard import editable_week, team_measurable

TODO_DUE_DAYS = 7


def issue_out(i: Issue, names: dict[str, str]) -> IssueOut:
    src = None
    if i.source_measurable_id:
        src = IssueSourceOut(
            measurable_id=i.source_measurable_id,
            measurable_name=names.get(i.source_measurable_id, ""),
            week_start=i.source_week_start,
        )
    return IssueOut.model_validate({**as_dict(i), "source": src})


def _names(db: Session, team_id: str) -> dict[str, str]:
    return dict(db.execute(select(Measurable.id, Measurable.name).where(Measurable.team_id == team_id)).all())


def list_issues(db: Session, team_id: str, solved: bool) -> list[IssueOut]:
    q = select(Issue).where(Issue.team_id == team_id)
    if solved:
        rows = db.scalars(q.where(Issue.solved_at.is_not(None)).order_by(Issue.solved_at.desc(), Issue.id)).all()
    else:
        rows = issue_order(db.scalars(q.where(Issue.solved_at.is_(None))).all())
    names = _names(db, team_id)
    return [issue_out(i, names) for i in rows]


def team_issue(db: Session, team_id: str, issue_id: str, lock: bool = False) -> Issue:
    q = select(Issue).where(Issue.id == issue_id, Issue.team_id == team_id)
    i = db.scalar(q.with_for_update() if lock else q)
    if not i:
        raise not_found("Issue")
    return i


def create_issue(db: Session, team_id: str, title: str, priority: int | None, user: User, now: datetime) -> IssueOut:
    i = Issue(team_id=team_id, title=title, priority=priority, owner_id=user.id, created_at=now)
    db.add(i)
    db.commit()
    return issue_out(i, {})


def make_it_an_issue(db: Session, team_id: str, measurable_id: str, week: date, user: User, now: datetime) -> tuple[IssueOut, bool]:
    """Create the Issue for an off-track cell, or return the existing unsolved one.

    Duplicate-free under concurrency: the partial unique index uq_issues_open_source allows one
    unsolved Issue per (Measurable, week). INSERT .. ON CONFLICT DO NOTHING lets exactly one
    request win; the others read the winner's row.
    """
    m = team_measurable(db, team_id, measurable_id)
    editable_week(week, now)
    names = {m.id: m.name}

    existing = db.scalar(select(Issue).where(
        Issue.source_measurable_id == m.id, Issue.source_week_start == week, Issue.solved_at.is_(None)))
    if existing:
        return issue_out(existing, names), False

    value = db.scalar(select(Score.value).where(Score.measurable_id == m.id, Score.week_start == week))
    if score_status(goal_of(m), value, week, ct.week_of(now)) != "off_track":
        raise bad_request("Only an off-track score can become an Issue")

    title = f"{m.name}, week of {week.strftime('%b')} {week.day}"
    for _ in range(3):
        new = db.scalar(
            insert(Issue)
            .values(id=new_id("i")(), team_id=team_id, title=title, owner_id=user.id, created_at=now,
                    source_measurable_id=m.id, source_week_start=week)
            .on_conflict_do_nothing(
                index_elements=[Issue.source_measurable_id, Issue.source_week_start],
                index_where=text("solved_at IS NULL AND source_measurable_id IS NOT NULL"),
            )
            .returning(Issue)
        )
        db.commit()
        if new:
            return issue_out(new, names), True
        winner = db.scalar(select(Issue).where(
            Issue.source_measurable_id == m.id, Issue.source_week_start == week, Issue.solved_at.is_(None)))
        if winner:  # else the winner was solved in between: try again
            return issue_out(winner, names), False
    raise conflict("Could not create the Issue, try again")


def set_priority(db: Session, team_id: str, issue_id: str, priority: int | None) -> IssueOut:
    i = team_issue(db, team_id, issue_id)
    if i.solved_at:
        raise conflict("Issue is already solved")
    i.priority = priority
    db.commit()
    return issue_out(i, _names(db, team_id))


def solve_issue(db: Session, team_id: str, issue_id: str, note: str, now: datetime) -> IssueOut:
    team_issue(db, team_id, issue_id)
    done = db.execute(
        update(Issue).where(Issue.id == issue_id, Issue.solved_at.is_(None))
        .values(solved_at=now, resolution_note=note)
    ).rowcount
    db.commit()
    if not done:
        raise conflict("Issue is already solved")
    return issue_out(team_issue(db, team_id, issue_id), _names(db, team_id))


def valid_owner(db: Session, team_id: str, owner_id: str) -> None:
    ok = db.scalar(
        select(User.id).join(Membership, Membership.user_id == User.id)
        .where(Membership.team_id == team_id, User.id == owner_id, User.role.in_(("admin", "team_member")))
    )
    if not ok:
        raise bad_request("Owner must be an Admin or Team Member of this team")


def add_todo(db: Session, team_id: str, issue_id: str, title: str, owner_id: str, now: datetime) -> Todo:
    team_issue(db, team_id, issue_id)
    valid_owner(db, team_id, owner_id)
    t = Todo(team_id=team_id, title=title, owner_id=owner_id, source_issue_id=issue_id, created_at=now,
             due_date=ct.local_date(now) + timedelta(days=TODO_DUE_DAYS))
    db.add(t)
    db.commit()
    return t
