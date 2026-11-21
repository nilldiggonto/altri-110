from datetime import date, timedelta

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from app.api.deps import Db, TeamRead, TeamWrite
from app.core import time as ct
from app.core.clock import now
from app.models import Membership, User
from app.realtime.events import team_changed
from app.schemas.core import TeamDetailOut, TeamOut, UserOut
from app.schemas.work import (
    IssueCreateIn, IssueOut, IssuePatchIn, MakeIssueOut, RocksOut, ScorecardOut, ScoreIn, SolveIn,
    TodoCreateIn, TodoListOut, TodoOut, TodoPatchIn,
)
from app.services import issues, rocks, scorecard, todos

router = APIRouter(prefix="/teams/{team_id}")


@router.get("", response_model=TeamDetailOut, tags=["teams"])
def get_team(ctx: TeamRead, db: Db):
    members = db.scalars(
        select(User).join(Membership, Membership.user_id == User.id)
        .where(Membership.team_id == ctx.team.id).order_by(User.name)
    ).all()
    today = ct.local_date(now())
    week = ct.week_start(today)
    return TeamDetailOut(
        team=TeamOut.model_validate(ctx.team),
        members=[UserOut.model_validate(u) for u in members],
        owners=[UserOut.model_validate(u) for u in members if u.role != "observer"],
        current_week=week.isoformat(), last_closed_week=(week - timedelta(weeks=1)).isoformat(),
        today=today.isoformat(),
    )


# Scorecard
@router.get("/scorecard", response_model=ScorecardOut, tags=["scorecard"], summary="Last 13 weeks incl. current")
def get_scorecard(ctx: TeamRead, db: Db):
    return scorecard.get_scorecard(db, ctx.team.id, now())


@router.put("/measurables/{measurable_id}/scores/{week_start}", status_code=204, tags=["scorecard"],
            summary="Set a score (last save wins)")
def put_score(measurable_id: str, week_start: date, body: ScoreIn, ctx: TeamWrite, db: Db):
    scorecard.set_score(db, ctx.team.id, measurable_id, week_start, body.value, ctx.user, now())
    team_changed(db, ctx.team.id, "scorecard")


@router.delete("/measurables/{measurable_id}/scores/{week_start}", status_code=204, tags=["scorecard"])
def delete_score(measurable_id: str, week_start: date, ctx: TeamWrite, db: Db):
    scorecard.clear_score(db, ctx.team.id, measurable_id, week_start, now())
    team_changed(db, ctx.team.id, "scorecard")


@router.post("/measurables/{measurable_id}/scores/{week_start}/issue", response_model=MakeIssueOut,
             tags=["scorecard"], summary="Make it an Issue (201 created, 200 existing unsolved one)")
def make_issue(measurable_id: str, week_start: date, ctx: TeamWrite, db: Db, response: Response):
    issue, created = issues.make_it_an_issue(db, ctx.team.id, measurable_id, week_start, ctx.user, now())
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    if created:
        team_changed(db, ctx.team.id, "scorecard", "issues")
    return MakeIssueOut(issue=issue, created=created)


# Issues
@router.get("/issues", response_model=list[IssueOut], tags=["issues"],
            summary="Unsolved in Issue order, or solved=true for solved ones (newest first)")
def list_issues(ctx: TeamRead, db: Db, solved: bool = False):
    return issues.list_issues(db, ctx.team.id, solved)


@router.post("/issues", response_model=IssueOut, status_code=201, tags=["issues"])
def create_issue(body: IssueCreateIn, ctx: TeamWrite, db: Db):
    out = issues.create_issue(db, ctx.team.id, body.title, body.priority, ctx.user, now())
    team_changed(db, ctx.team.id, "issues")
    return out


@router.patch("/issues/{issue_id}", response_model=IssueOut, tags=["issues"], summary="Set or clear priority")
def patch_issue(issue_id: str, body: IssuePatchIn, ctx: TeamWrite, db: Db):
    out = issues.set_priority(db, ctx.team.id, issue_id, body.priority)
    team_changed(db, ctx.team.id, "issues")
    return out


@router.post("/issues/{issue_id}/solve", response_model=IssueOut, tags=["issues"])
def solve_issue(issue_id: str, body: SolveIn, ctx: TeamWrite, db: Db):
    out = issues.solve_issue(db, ctx.team.id, issue_id, body.note, now())
    team_changed(db, ctx.team.id, "issues", "scorecard")
    return out


@router.post("/issues/{issue_id}/todos", response_model=TodoOut, status_code=201, tags=["issues"],
             summary="Add a follow-up To-Do, due in 7 days")
def add_todo(issue_id: str, body: TodoCreateIn, ctx: TeamWrite, db: Db):
    t = issues.add_todo(db, ctx.team.id, issue_id, body.title, body.owner_id, now())
    team_changed(db, ctx.team.id, "todos")
    return todos.todo_out(t, {}, now())


# To-Dos
@router.get("/todos", response_model=TodoListOut, tags=["todos"])
def list_todos(ctx: TeamRead, db: Db):
    return todos.list_todos(db, ctx.team.id, now())


@router.patch("/todos/{todo_id}", response_model=TodoOut, tags=["todos"], summary="Mark done or undo")
def patch_todo(todo_id: str, body: TodoPatchIn, ctx: TeamWrite, db: Db):
    out = todos.set_done(db, ctx.team.id, todo_id, body.done, now())
    team_changed(db, ctx.team.id, "todos")
    return out


# Rocks
@router.get("/rocks", response_model=RocksOut, tags=["rocks"], summary="Current quarter, read-only")
def list_rocks(ctx: TeamRead, db: Db):
    return rocks.list_rocks(db, ctx.team.id, now())
