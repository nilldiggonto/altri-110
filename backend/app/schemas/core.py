from app.schemas.common import Id, In, Out


class UserOut(Out):
    id: str
    name: str
    email: str
    role: str


class TeamOut(Out):
    id: str
    name: str


class LoginIn(In):
    user_id: Id


class LoginOut(Out):
    token: str
    user: UserOut


class MeOut(Out):
    user: UserOut
    teams: list[TeamOut]
    can_write: bool


class TeamDetailOut(Out):
    team: TeamOut
    members: list[UserOut]
    owners: list[UserOut]  # Admins and Team Members: valid To-Do owners
    current_week: str
    last_closed_week: str
    today: str
