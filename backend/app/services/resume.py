from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Issue, Meeting, Score, Todo


def latest_persisted(db: Session) -> datetime | None:
    """Latest timestamp the app has written. The running clock resumes from here after a restart."""
    cols = (Meeting.started_at, Meeting.section_started_at, Meeting.ended_at, Issue.created_at,
            Issue.solved_at, Todo.created_at, Todo.done_at, Score.updated_at)
    values = [db.scalar(select(func.max(c))) for c in cols]
    return max((v for v in values if v), default=None)
