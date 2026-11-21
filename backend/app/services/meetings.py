"""Level 10 Meeting lifecycle. The meetings row is the source of truth; every change locks it,
bumps version and commits in one transaction, so concurrent clicks serialize."""
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import can_write
from app.models import Meeting, MeetingAttendee, MeetingRating, User
from app.models.ids import as_dict
from app.rules.meeting import AGENDA, meeting_rating, next_section
from app.schemas.meeting import AgendaItemOut, AttendeeOut, MeetingOut, MeetingSummaryOut, RatingOut
from app.services.errors import conflict, not_found
from app.services.report import meeting_summary, meeting_work


def _forbidden(msg: str) -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, msg)


def state(db: Session, mt: Meeting, now: datetime) -> MeetingOut:
    attendees = db.scalars(
        select(MeetingAttendee).where(MeetingAttendee.meeting_id == mt.id)
        .order_by(MeetingAttendee.joined_at, MeetingAttendee.user_id)
    ).all()
    ratings = db.scalars(
        select(MeetingRating).where(MeetingRating.meeting_id == mt.id).order_by(MeetingRating.user_id)
    ).all()
    solved, created = meeting_work(db, mt, mt.ended_at or now)
    return MeetingOut.model_validate({
        **as_dict(mt),
        "server_now": now,
        "agenda": [AgendaItemOut(section=s, minutes=m) for s, m in AGENDA],
        "attendees": [AttendeeOut.model_validate(a) for a in attendees],
        "ratings": [RatingOut.model_validate(r) for r in ratings],
        "rating": meeting_rating(r.rating for r in ratings),
        "issues_solved": solved,
        "todos_created": created,
    })


def active_meeting(db: Session, team_id: str) -> Meeting | None:
    return db.scalar(select(Meeting).where(Meeting.team_id == team_id, Meeting.ended_at.is_(None)))


def fresh(db: Session, meeting_id: str) -> Meeting:
    return db.scalar(select(Meeting).where(Meeting.id == meeting_id).execution_options(populate_existing=True))


def _locked(db: Session, meeting_id: str) -> Meeting:
    mt = db.scalar(
        select(Meeting).where(Meeting.id == meeting_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    if not mt:
        raise not_found("Meeting")
    return mt


def _open(db: Session, meeting_id: str) -> Meeting:
    mt = _locked(db, meeting_id)
    if mt.ended_at:
        raise conflict("Meeting has ended")
    return mt


def _facilitator(db: Session, meeting_id: str, user: User) -> Meeting:
    mt = _locked(db, meeting_id)
    if mt.facilitator_id != user.id:
        raise _forbidden("Only the facilitator can do this")
    return mt


def _stamp(mt: Meeting, now: datetime) -> datetime:
    # Never before stored times, even if the clock was re-anchored.
    return max(now, mt.section_started_at)


def start(db: Session, team_id: str, user: User, now: datetime) -> MeetingOut:
    mt = Meeting(team_id=team_id, facilitator_id=user.id, started_at=now, section_started_at=now,
                 current_section=AGENDA[0][0], version=1)
    db.add(mt)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise conflict("A meeting is already running for this team")
    db.add(MeetingAttendee(meeting_id=mt.id, user_id=user.id, joined_at=now))
    db.commit()
    return state(db, mt, now)


def join(db: Session, meeting_id: str, user: User, now: datetime) -> MeetingOut:
    mt = _open(db, meeting_id)
    added = db.scalar(
        insert(MeetingAttendee).values(meeting_id=mt.id, user_id=user.id, joined_at=now)
        .on_conflict_do_nothing().returning(MeetingAttendee.user_id)
    )
    if added:
        mt.version += 1
    db.commit()
    return state(db, mt, now)


def advance(db: Session, meeting_id: str, user: User, to: str, now: datetime) -> MeetingOut:
    mt = _facilitator(db, meeting_id, user)
    if mt.ended_at:
        raise conflict("Meeting has ended")
    if to != mt.current_section:  # same section: repeated click, no-op
        if to != next_section(mt.current_section):
            raise conflict(f"Cannot move from {mt.current_section} to {to}")
        mt.current_section, mt.section_started_at = to, _stamp(mt, now)
        mt.version += 1
    db.commit()
    return state(db, mt, now)


def end(db: Session, meeting_id: str, user: User, now: datetime) -> MeetingOut:
    mt = _facilitator(db, meeting_id, user)
    if not mt.ended_at:  # already ended: repeated click, no-op
        mt.ended_at = _stamp(mt, now)
        mt.version += 1
    db.commit()
    return state(db, mt, now)


def rate(db: Session, meeting_id: str, user: User, rating: int, now: datetime) -> MeetingOut:
    if not can_write(user):
        raise _forbidden("Observers cannot rate")
    mt = _open(db, meeting_id)
    if not db.get(MeetingAttendee, (mt.id, user.id)):
        raise _forbidden("Join the meeting to rate it")
    if mt.current_section != "conclude":
        raise conflict("Ratings open in Conclude")
    db.execute(
        insert(MeetingRating).values(meeting_id=mt.id, user_id=user.id, rating=rating)
        .on_conflict_do_update(index_elements=[MeetingRating.meeting_id, MeetingRating.user_id],
                               set_={"rating": rating})
    )
    mt.version += 1
    db.commit()
    return state(db, mt, now)


def summary(db: Session, mt: Meeting) -> MeetingSummaryOut:
    if not mt.ended_at:
        raise conflict("Meeting has not ended")
    return MeetingSummaryOut(meeting_id=mt.id, started_at=mt.started_at, ended_at=mt.ended_at,
                             **meeting_summary(db, mt))
