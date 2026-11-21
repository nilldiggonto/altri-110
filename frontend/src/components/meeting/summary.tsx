"use client"
import { ArrowLeftIcon, CheckCircle2Icon, ListTodoIcon, StarIcon, UsersIcon } from "lucide-react"
import Link from "next/link"
import type { ReactNode } from "react"

import { useTeamCtx } from "@/components/shell/team-context"
import { EmptyState, Person, SectionCard, SectionError, SectionLoading } from "@/components/team/section"
import { buttonVariants } from "@/components/ui/button"
import { useMeetingSummary } from "@/lib/meeting"
import { useIssues, useScorecard, useTodos, useUserNames } from "@/lib/queries"
import { formatDay, formatDuration, formatStamp } from "@/lib/time"
import type { CellStatus } from "@/lib/types"
import { cn } from "@/lib/utils"

const STATUS: Record<CellStatus, { label: string; cls: string }> = {
  on_track: { label: "On track", cls: "bg-success-soft text-success" },
  off_track: { label: "Off track", cls: "bg-danger-soft text-danger" },
  pending: { label: "Pending", cls: "bg-muted text-muted-foreground" },
}

export function MeetingSummaryView({ meetingId }: { meetingId: string }) {
  const { teamId } = useTeamCtx()
  const s = useMeetingSummary(meetingId)
  const name = useUserNames()
  const scorecard = useScorecard(teamId)
  const solved = useIssues(teamId, true)
  const todos = useTodos(teamId)
  const mName = new Map(scorecard.data?.measurables.map((m) => [m.id, m.name]))
  const issueTitle = new Map(solved.data?.map((i) => [i.id, i.title]))
  const todoTitle = new Map(todos.data?.todos.map((t) => [t.id, t.title]))

  if (s.isPending) return <SectionCard title="Meeting summary"><SectionLoading /></SectionCard>
  if (s.isError) return <SectionCard title="Meeting summary"><SectionError error={s.error} onRetry={() => s.refetch()} /></SectionCard>
  const d = s.data

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-success">Meeting ended</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">Meeting summary</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {formatStamp(d.started_at)} to {formatStamp(d.ended_at)} · {formatDuration(Date.parse(d.ended_at) - Date.parse(d.started_at))}
          </p>
        </div>
        <Link href={`/teams/${teamId}`} className={buttonVariants({ variant: "outline" })}>
          <ArrowLeftIcon /> Back to team
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat icon={<StarIcon />} label="Rating" value={d.rating?.toFixed(1) ?? "No rating"} />
        <Stat icon={<CheckCircle2Icon />} label="Issues solved" value={d.issues_solved.length} />
        <Stat icon={<ListTodoIcon />} label="To-Dos created" value={d.todos_created.length} />
        <Stat icon={<UsersIcon />} label="Attendees" value={d.attendee_ids.length} />
      </div>

      <SectionCard title="Scorecard" description={`Last closed week at the meeting: week of ${formatDay(d.scorecard_week)}`}>
        <ul className="divide-y">
          {Object.entries(d.measurable_status).map(([id, st]) => (
            <li key={id} className="flex items-center justify-between px-5 py-3 text-sm">
              <span className="font-medium">{mName.get(id) ?? id}</span>
              <span className={cn("rounded-md px-2 py-0.5 text-xs font-medium", STATUS[st].cls)}>{STATUS[st].label}</span>
            </li>
          ))}
        </ul>
      </SectionCard>

      <div className="grid gap-6 md:grid-cols-2">
        <SectionCard title="Issues solved">
          {d.issues_solved.length === 0 ? <EmptyState title="No Issues solved" /> : (
            <ul className="divide-y">{d.issues_solved.map((id) => <li key={id} className="px-5 py-3 text-sm">{issueTitle.get(id) ?? id}</li>)}</ul>
          )}
        </SectionCard>
        <SectionCard title="To-Dos created">
          {d.todos_created.length === 0 ? <EmptyState title="No To-Dos created" /> : (
            <ul className="divide-y">{d.todos_created.map((id) => <li key={id} className="px-5 py-3 text-sm">{todoTitle.get(id) ?? id}</li>)}</ul>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Attendees">
        <ul className="flex flex-wrap gap-x-6 gap-y-3 p-5 text-sm">
          {d.attendee_ids.map((id) => <li key={id}><Person name={name(id)} /></li>)}
        </ul>
      </SectionCard>
    </div>
  )
}

function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: ReactNode }) {
  return (
    <div className="rounded-2xl border bg-card p-4 shadow-xs">
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground [&_svg]:size-3.5">{icon}{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular">{value}</p>
    </div>
  )
}
