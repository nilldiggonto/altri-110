"""Auth and authorization. Every role rule in brief 2.4 is enforced here, on the server."""
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.db.session import get_db
from app.models import Meeting, Membership, Team, User

WRITE_ROLES = {"admin", "team_member"}

Db = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


def user_from_token(db: Session, token: str | None) -> User | None:
    uid = verify_token(token) if token else None
    return db.get(User, uid) if uid else None


def current_user(db: Db, cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> User:
    user = user_from_token(db, cred.credentials if cred else None)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def can_read_team(db: Session, user: User, team_id: str) -> bool:
    if user.role == "admin":
        return db.get(Team, team_id) is not None
    return db.get(Membership, (user.id, team_id)) is not None


def can_write(user: User) -> bool:
    return user.role in WRITE_ROLES


@dataclass(frozen=True)
class TeamCtx:
    team: Team
    user: User


def team_reader(db: Db, user: CurrentUser, team_id: Annotated[str, Path(max_length=64)]) -> TeamCtx:
    """Members (and Admins) may read. Same 403 whether the team exists or not, so ids can't be probed."""
    if not can_read_team(db, user, team_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No access to this team")
    return TeamCtx(db.get(Team, team_id), user)


def team_writer(ctx: Annotated[TeamCtx, Depends(team_reader)]) -> TeamCtx:
    if not can_write(ctx.user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Observers cannot change data")
    return ctx


TeamRead = Annotated[TeamCtx, Depends(team_reader)]
TeamWrite = Annotated[TeamCtx, Depends(team_writer)]


@dataclass(frozen=True)
class MeetingCtx:
    meeting: Meeting
    user: User


def meeting_reader(db: Db, user: CurrentUser, meeting_id: Annotated[str, Path(max_length=64)]) -> MeetingCtx:
    """Anyone who can read the meeting's team. Same 403 for a missing meeting."""
    mt = db.get(Meeting, meeting_id)
    if not mt or not can_read_team(db, user, mt.team_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No access to this meeting")
    return MeetingCtx(mt, user)


MeetingRead = Annotated[MeetingCtx, Depends(meeting_reader)]
