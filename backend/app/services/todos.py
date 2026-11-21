from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import time as ct
from app.models import Issue, Todo
from app.models.ids import as_dict
from app.rules.todos import TodoFacts, completion, is_overdue
from app.schemas.work import CompletionOut, TodoListOut, TodoOut
from app.services.errors import not_found


def todo_out(t: Todo, titles: dict[str, str], now: datetime) -> TodoOut:
    return TodoOut.model_validate({
        **as_dict(t),
        "source_issue_title": titles.get(t.source_issue_id) if t.source_issue_id else None,
        "overdue": is_overdue(TodoFacts(t.id, t.due_date, t.done_at), ct.local_date(now)),
    })


def list_todos(db: Session, team_id: str, now: datetime) -> TodoListOut:
    todos = db.scalars(select(Todo).where(Todo.team_id == team_id).order_by(Todo.due_date, Todo.id)).all()
    titles = dict(db.execute(select(Issue.id, Issue.title).where(Issue.team_id == team_id)).all())
    week = ct.week_of(now) - timedelta(weeks=1)
    c = completion([TodoFacts(t.id, t.due_date, t.done_at) for t in todos], week, ct.week_bounds_utc(week)[1])
    return TodoListOut(
        todos=[todo_out(t, titles, now) for t in todos],
        last_closed_week=CompletionOut(
            week_start=week, due=c.due if c else 0, done=c.done if c else 0,
            rate_percent=c.rate_percent if c else None, meets_target=c.meets_target if c else None,
        ),
    )


def set_done(db: Session, team_id: str, todo_id: str, done: bool, now: datetime) -> TodoOut:
    t = db.scalar(select(Todo).where(Todo.id == todo_id, Todo.team_id == team_id).with_for_update())
    if not t:
        raise not_found("To-Do")
    if done and t.done_at is None:
        t.done_at = now
    elif not done:
        t.done_at = None
    db.commit()
    titles = dict(db.execute(select(Issue.id, Issue.title).where(Issue.id == t.source_issue_id)).all())
    return todo_out(t, titles, now)
