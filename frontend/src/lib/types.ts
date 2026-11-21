// Mirrors backend/app/schemas. Dates are "YYYY-MM-DD" strings, timestamps ISO UTC.
export type Role = "admin" | "team_member" | "observer"
export type User = { id: string; name: string; email: string; role: Role }
export type Team = { id: string; name: string }
export type Me = { user: User; teams: Team[]; can_write: boolean }
export type TeamDetail = {
  team: Team
  members: User[]
  owners: User[]
  current_week: string
  last_closed_week: string
  today: string
}

export type CellStatus = "on_track" | "off_track" | "pending"
export type Goal = { type: "at_least" | "at_most" | "between" | "exactly"; value: number | null; min: number | null; max: number | null }
export type Cell = { week_start: string; value: number | null; status: CellStatus; open_issue_id: string | null }
export type MeasurableRow = { id: string; name: string; unit: string; owner_id: string; goal: Goal; cells: Cell[] }
export type Scorecard = { weeks: string[]; current_week: string; measurables: MeasurableRow[] }

export type Issue = {
  id: string
  title: string
  owner_id: string
  priority: number | null
  created_at: string
  solved_at: string | null
  resolution_note: string | null
  source: { measurable_id: string; measurable_name: string; week_start: string } | null
}
export type Todo = {
  id: string
  title: string
  owner_id: string
  due_date: string
  done_at: string | null
  created_at: string
  source_issue_id: string | null
  source_issue_title: string | null
  overdue: boolean
}
export type Completion = { week_start: string; due: number; done: number; rate_percent: number | null; meets_target: boolean | null }
export type TodoList = { todos: Todo[]; last_closed_week: Completion }
export type Milestone = { id: string; title: string; due_date: string; done: boolean }
export type Rock = {
  id: string
  title: string
  owner_id: string
  quarter: string
  status: "on_track" | "off_track" | "complete"
  progress_percent: number
  milestones: Milestone[]
}
export type Rocks = { quarter: string; rocks: Rock[] }

export type Section = "scorecard" | "ids" | "conclude"
export type Meeting = {
  id: string
  team_id: string
  facilitator_id: string
  started_at: string
  ended_at: string | null
  current_section: Section
  section_started_at: string
  version: number
  server_now: string
  agenda: { section: Section; minutes: number }[]
  attendees: { user_id: string; joined_at: string | null }[]
  ratings: { user_id: string; rating: number }[]
  rating: number | null
  issues_solved: string[]
  todos_created: string[]
}
export type MeetingSummary = {
  meeting_id: string
  started_at: string
  ended_at: string
  scorecard_week: string
  measurable_status: Record<string, CellStatus>
  issues_solved: string[]
  todos_created: string[]
  attendee_ids: string[]
  rating: number | null
}
