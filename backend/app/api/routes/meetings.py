from fastapi import APIRouter

from app.api.deps import Db, MeetingRead, TeamRead, TeamWrite
from app.core.clock import now
from app.schemas.meeting import AdvanceIn, MeetingOut, MeetingSummaryOut, RatingIn
from app.services import meetings
from app.services.errors import not_found

router = APIRouter(tags=["meetings"])


@router.get("/teams/{team_id}/meetings/active", response_model=MeetingOut, summary="404 when none is running")
def get_active(ctx: TeamRead, db: Db):
    mt = meetings.active_meeting(db, ctx.team.id)
    if not mt:
        raise not_found("Active meeting")
    return meetings.state(db, mt, now())


@router.post("/teams/{team_id}/meetings", response_model=MeetingOut, status_code=201,
             summary="Start a meeting; the caller facilitates. 409 if one is running")
def start_meeting(ctx: TeamWrite, db: Db):
    return meetings.start(db, ctx.team.id, ctx.user, now())


@router.get("/meetings/{meeting_id}", response_model=MeetingOut)
def get_meeting(ctx: MeetingRead, db: Db):
    return meetings.state(db, ctx.meeting, now())


@router.post("/meetings/{meeting_id}/join", response_model=MeetingOut, summary="Idempotent")
def join_meeting(ctx: MeetingRead, db: Db):
    return meetings.join(db, ctx.meeting.id, ctx.user, now())


@router.post("/meetings/{meeting_id}/advance", response_model=MeetingOut,
             summary="Facilitator only. `to` must be the next section; the current one is a no-op")
def advance_meeting(body: AdvanceIn, ctx: MeetingRead, db: Db):
    return meetings.advance(db, ctx.meeting.id, ctx.user, body.to, now())


@router.post("/meetings/{meeting_id}/end", response_model=MeetingOut, summary="Facilitator only, any section")
def end_meeting(ctx: MeetingRead, db: Db):
    return meetings.end(db, ctx.meeting.id, ctx.user, now())


@router.put("/meetings/{meeting_id}/rating", response_model=MeetingOut,
            summary="Attending Admin or Team Member, in Conclude, until the end")
def rate_meeting(body: RatingIn, ctx: MeetingRead, db: Db):
    return meetings.rate(db, ctx.meeting.id, ctx.user, body.rating, now())


@router.get("/meetings/{meeting_id}/summary", response_model=MeetingSummaryOut, summary="Ended meetings only")
def get_summary(ctx: MeetingRead, db: Db):
    return meetings.summary(db, ctx.meeting)
