"""Rules report: every computed value in brief 2.6, from the DB, for a given now."""
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import time as ct
from app.models import Issue, Measurable, Meeting, MeetingAttendee, MeetingRating, Milestone, Rock, Score, Team, Todo
from app.rules.issues import issue_order
from app.rules.measurable import Goal, score_status
from app.rules.meeting import meeting_rating
from app.rules.rocks import MilestoneFacts, rock_progress, rock_status
from app.rules.todos import TodoFacts, completion, is_overdue


def goal_of(m: Measurable) -> Goal:
    return Goal(m.goal_type, m.goal_value, m.goal_min, m.goal_max)


def _iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _measurable_statuses(db: Session, team_id: str, weeks: list[date], current_week: date) -> dict:
    ms = db.scalars(select(Measurable).where(Measurable.team_id == team_id).order_by(Measurable.id)).all()
    scores = {
        (s.measurable_id, s.week_start): s.value
        for s in db.scalars(select(Score).where(Score.measurable_id.in_([m.id for m in ms])))
    }
    return {
        m.id: {w.isoformat(): score_status(goal_of(m), scores.get((m.id, w)), w, current_week) for w in weeks}
        for m in ms
    }


def _meeting_summary(db: Session, mt: Meeting) -> dict[str, Any]:
    week = ct.week_of(mt.started_at) - timedelta(weeks=1)  # last closed week at meeting time
    window = (mt.started_at, mt.ended_at)
    solved = db.scalars(
        select(Issue.id).where(Issue.team_id == mt.team_id, Issue.solved_at.between(*window))
    ).all()
    created = db.scalars(
        select(Todo.id).where(Todo.team_id == mt.team_id, Todo.created_at.between(*window))
    ).all()
    attendees = db.scalars(select(MeetingAttendee.user_id).where(MeetingAttendee.meeting_id == mt.id)).all()
    ratings = db.scalars(select(MeetingRating.rating).where(MeetingRating.meeting_id == mt.id)).all()
    status = _measurable_statuses(db, mt.team_id, [week], ct.week_of(mt.started_at))
    return {
        "scorecard_week": week.isoformat(),
        "measurable_status": {mid: s[week.isoformat()] for mid, s in status.items()},
        "issues_solved": sorted(solved),
        "todos_created": sorted(created),
        "attendee_ids": sorted(attendees),
        "rating": meeting_rating(ratings),
    }


def team_report(db: Session, team_id: str, now: datetime) -> dict[str, Any]:
    today = ct.local_date(now)
    current_week = ct.week_start(today)
    weeks = ct.last_weeks(current_week)

    todos = [
        TodoFacts(t.id, t.due_date, t.done_at)
        for t in db.scalars(select(Todo).where(Todo.team_id == team_id))
    ]
    todo_completion = {}
    for w in weeks:
        c = completion(todos, w, ct.week_bounds_utc(w)[1])
        todo_completion[w.isoformat()] = c and c.__dict__

    rocks = db.scalars(
        select(Rock).where(Rock.team_id == team_id, Rock.quarter == ct.quarter_of(today)).order_by(Rock.id)
    ).all()
    mss: dict[str, list[MilestoneFacts]] = defaultdict(list)
    for m in db.scalars(select(Milestone).where(Milestone.rock_id.in_([r.id for r in rocks]))):
        mss[m.rock_id].append(MilestoneFacts(m.due_date, m.done))

    unsolved = db.scalars(select(Issue).where(Issue.team_id == team_id, Issue.solved_at.is_(None))).all()
    meetings = db.scalars(
        select(Meeting).where(Meeting.team_id == team_id, Meeting.ended_at.is_not(None)).order_by(Meeting.id)
    ).all()

    return {
        "measurable_status": _measurable_statuses(db, team_id, weeks, current_week),
        "todo_completion": todo_completion,
        "overdue_todos": sorted(t.id for t in todos if is_overdue(t, today)),
        "rocks": {
            r.id: {"status": rock_status(r.status, mss[r.id], today), "progress_percent": rock_progress(r.status, mss[r.id])}
            for r in rocks
        },
        "issue_order": [i.id for i in issue_order(unsolved)],
        "meetings": {mt.id: _meeting_summary(db, mt) for mt in meetings},
    }


def rules_report(db: Session, now: datetime) -> dict[str, Any]:
    teams = db.scalars(select(Team.id).order_by(Team.id)).all()
    return {"now": _iso_z(now), "teams": {t: team_report(db, t, now) for t in teams}}
