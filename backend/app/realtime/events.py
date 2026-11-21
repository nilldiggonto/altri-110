"""Messages sent to team sockets. Publish only after the change is committed.

- {"type": "hello", "server_now", "meeting": state | null}: first message on connect.
- {"type": "meeting", "meeting": state}: live meeting state. Keep the one with the highest version.
- {"type": "changed", "sections": [...]}: team data changed, refetch those sections.
- {"type": "pong", "server_now"}: reply to {"type": "ping"}, for clock offset.
"""
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.clock import now
from app.realtime.hub import hub
from app.models import Meeting
from app.schemas.meeting import MeetingOut
from app.services import meetings

Section = str  # "scorecard" | "issues" | "todos"


def meeting_message(state: MeetingOut) -> dict:
    return {"type": "meeting", "meeting": state.model_dump(mode="json")}


def meeting_changed(state: MeetingOut) -> None:
    hub.publish(state.team_id, meeting_message(state))


def team_changed(db: Session, team_id: str, *sections: Section) -> None:
    hub.publish(team_id, {"type": "changed", "sections": list(sections)})
    if {"issues", "todos"} & set(sections):  # live meeting lists Issues solved and To-Dos created
        # Bump first, then read: a state at version N includes every write bumped at or before N,
        # so concurrent writes can't leave clients on an older list.
        mid = db.scalar(
            update(Meeting).where(Meeting.team_id == team_id, Meeting.ended_at.is_(None))
            .values(version=Meeting.version + 1).returning(Meeting.id)
        )
        db.commit()
        if mid:
            meeting_changed(meetings.state(db, meetings.fresh(db, mid), now()))
