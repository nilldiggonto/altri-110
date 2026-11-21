from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import Id, In, Note, Out, Title

Priority = Annotated[int, Field(ge=1, le=5)]


class GoalOut(Out):
    type: str
    value: float | None
    min: float | None
    max: float | None


class CellOut(Out):
    week_start: date
    value: float | None
    status: Literal["on_track", "off_track", "pending"]
    open_issue_id: str | None


class MeasurableRowOut(Out):
    id: str
    name: str
    unit: str
    owner_id: str
    goal: GoalOut
    cells: list[CellOut]


class ScorecardOut(Out):
    weeks: list[date]
    current_week: date
    measurables: list[MeasurableRowOut]


class ScoreIn(In):
    value: float = Field(allow_inf_nan=False, ge=-1e13, le=1e13)


class IssueSourceOut(Out):
    measurable_id: str
    measurable_name: str
    week_start: date


class IssueOut(Out):
    id: str
    title: str
    owner_id: str
    priority: int | None
    created_at: datetime
    solved_at: datetime | None
    resolution_note: str | None
    source: IssueSourceOut | None


class MakeIssueOut(Out):
    issue: IssueOut
    created: bool


class IssueCreateIn(In):
    title: Title
    priority: Priority | None = None


class IssuePatchIn(In):
    priority: Priority | None


class SolveIn(In):
    note: Note


class TodoCreateIn(In):
    title: Title
    owner_id: Id


class TodoOut(Out):
    id: str
    title: str
    owner_id: str
    due_date: date
    done_at: datetime | None
    created_at: datetime
    source_issue_id: str | None
    source_issue_title: str | None
    overdue: bool


class CompletionOut(Out):
    week_start: date
    due: int
    done: int
    rate_percent: int | None
    meets_target: bool | None


class TodoListOut(Out):
    todos: list[TodoOut]
    last_closed_week: CompletionOut


class TodoPatchIn(In):
    done: bool


class MilestoneOut(Out):
    id: str
    title: str
    due_date: date
    done: bool


class RockOut(Out):
    id: str
    title: str
    owner_id: str
    quarter: str
    status: Literal["on_track", "off_track", "complete"]
    progress_percent: int
    milestones: list[MilestoneOut]


class RocksOut(Out):
    quarter: str
    rocks: list[RockOut]
