from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, Db, can_write
from app.core.security import issue_token
from app.models import Membership, Team, User
from app.schemas.core import LoginIn, LoginOut, MeOut, TeamOut, UserOut
from app.services.errors import not_found

router = APIRouter(tags=["auth"])


@router.get("/auth/users", response_model=list[UserOut], summary="Seeded users for the sign-in switcher")
def list_users(db: Db):
    return db.scalars(select(User).order_by(User.id)).all()


@router.post("/auth/login", response_model=LoginOut, summary="Sign in as a seeded user")
def login(body: LoginIn, db: Db):
    user = db.get(User, body.user_id)
    if not user:
        raise not_found("User")
    return LoginOut(token=issue_token(user.id), user=UserOut.model_validate(user))


@router.get("/me", response_model=MeOut, summary="Current user and the teams they can open")
def me(user: CurrentUser, db: Db):
    q = select(Team).order_by(Team.name)
    if user.role != "admin":
        q = q.join(Membership, Membership.team_id == Team.id).where(Membership.user_id == user.id)
    teams = [TeamOut.model_validate(t) for t in db.scalars(q)]
    return MeOut(user=UserOut.model_validate(user), teams=teams, can_write=can_write(user))
