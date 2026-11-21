from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import time as ct
from app.models import Milestone, Rock
from app.rules.rocks import MilestoneFacts, rock_progress, rock_status
from app.schemas.work import MilestoneOut, RockOut, RocksOut


def list_rocks(db: Session, team_id: str, now: datetime) -> RocksOut:
    today = ct.local_date(now)
    quarter = ct.quarter_of(today)
    rocks = db.scalars(select(Rock).where(Rock.team_id == team_id, Rock.quarter == quarter).order_by(Rock.id)).all()
    ms: dict[str, list[Milestone]] = defaultdict(list)
    for m in db.scalars(select(Milestone).where(Milestone.rock_id.in_([r.id for r in rocks]))
                        .order_by(Milestone.due_date, Milestone.id)):
        ms[m.rock_id].append(m)
    out = []
    for r in rocks:
        facts = [MilestoneFacts(m.due_date, m.done) for m in ms[r.id]]
        out.append(RockOut(
            id=r.id, title=r.title, owner_id=r.owner_id, quarter=r.quarter,
            status=rock_status(r.status, facts, today), progress_percent=rock_progress(r.status, facts),
            milestones=[MilestoneOut.model_validate(m) for m in ms[r.id]],
        ))
    return RocksOut(quarter=quarter, rocks=out)
