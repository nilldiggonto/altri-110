"""Idempotent seed loader for data/seed.json.

Default: insert seed rows that are missing, keep existing data (safe on every container start).
--reset: wipe all tables, then load the seed (a freshly seeded database).

Run: python -m app.seed.load [--reset]
"""
import argparse
import json
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.clock import parse_utc
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal
from app.models import (
    Company, Issue, Measurable, Meeting, MeetingAttendee, MeetingRating, Membership,
    Milestone, Rock, Score, Team, Todo, User,
)


def _ts(v: str | None):
    return parse_utc(v) if v else None


def _d(v: str | None):
    return date.fromisoformat(v) if v else None


def build_rows(seed: dict[str, Any]) -> list[tuple[type, list[dict[str, Any]]]]:
    co = seed["company"]
    rows: list[tuple[type, list[dict[str, Any]]]] = [
        (Company, [{"id": co["id"], "name": co["name"], "timezone": co["timezone"]}]),
        (Team, [{"id": t["id"], "company_id": co["id"], "name": t["name"]} for t in seed["teams"]]),
        (User, [{**u, "company_id": co["id"]} for u in seed["users"]]),
        (Membership, seed["memberships"]),
        (Measurable, [
            {
                "id": m["id"], "team_id": m["team_id"], "name": m["name"], "owner_id": m["owner_id"],
                "unit": m["unit"], "goal_type": m["goal"]["type"], "goal_value": m["goal"].get("value"),
                "goal_min": m["goal"].get("min"), "goal_max": m["goal"].get("max"),
            }
            for m in seed["measurables"]
        ]),
        (Score, [
            {"measurable_id": s["measurable_id"], "week_start": _d(s["week_start"]), "value": s["value"]}
            for s in seed["scores"]
        ]),
        (Rock, seed["rocks"]),
        (Milestone, [{**m, "due_date": _d(m["due_date"])} for m in seed["milestones"]]),
        (Issue, [
            {
                "id": i["id"], "team_id": i["team_id"], "title": i["title"], "owner_id": i["owner_id"],
                "priority": i["priority"], "created_at": _ts(i["created_at"]), "solved_at": _ts(i["solved_at"]),
                "resolution_note": i["resolution_note"],
                "source_measurable_id": (i["source"] or {}).get("measurable_id"),
                "source_week_start": _d((i["source"] or {}).get("week_start")),
            }
            for i in seed["issues"]
        ]),
        (Todo, [
            {**t, "due_date": _d(t["due_date"]), "done_at": _ts(t["done_at"]), "created_at": _ts(t["created_at"])}
            for t in seed["todos"]
        ]),
        (Meeting, [
            {
                "id": m["id"], "team_id": m["team_id"], "facilitator_id": m["facilitator_id"],
                "started_at": _ts(m["started_at"]), "ended_at": _ts(m["ended_at"]),
                "current_section": "conclude", "section_started_at": _ts(m["ended_at"]),
            }
            for m in seed["meetings"]
        ]),
        (MeetingAttendee, [
            {"meeting_id": m["id"], "user_id": u} for m in seed["meetings"] for u in m["attendee_ids"]
        ]),
        (MeetingRating, [
            {"meeting_id": m["id"], **r} for m in seed["meetings"] for r in m["ratings"]
        ]),
    ]
    return rows


def reset(db: Session) -> None:
    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    db.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


def load(db: Session, seed: dict[str, Any]) -> None:
    for model, items in build_rows(seed):
        if items:
            db.execute(insert(model).values(items).on_conflict_do_nothing())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reset", action="store_true", help="wipe all data before loading")
    args = p.parse_args()
    seed = json.loads(settings.seed_path.read_text())
    with SessionLocal.begin() as db:
        if args.reset:
            reset(db)
        load(db, seed)
    print(f"seed loaded{' (reset)' if args.reset else ''} from {settings.seed_path}")


if __name__ == "__main__":
    main()
