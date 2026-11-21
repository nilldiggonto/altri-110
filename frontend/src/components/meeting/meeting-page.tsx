"use client"
import { useQueryClient } from "@tanstack/react-query"
import { CalendarClockIcon, LogInIcon, PlayIcon } from "lucide-react"

import { AgendaPanel, SECTION_HINT, SECTION_LABEL } from "@/components/meeting/agenda"
import { RatingPanel } from "@/components/meeting/rating"
import { MeetingSummaryView } from "@/components/meeting/summary"
import { useTeamCtx } from "@/components/shell/team-context"
import { IssuesSection } from "@/components/team/issues"
import { ScorecardSection } from "@/components/team/scorecard"
import { Person, SectionError, SectionLoading } from "@/components/team/section"
import { TodosSection } from "@/components/team/todos"
import { Button } from "@/components/ui/button"
import { api, ApiError } from "@/lib/api"
import { meetingKey, useActiveMeeting, useMeetingAction } from "@/lib/meeting"
import { useUserNames } from "@/lib/queries"
import { formatStamp } from "@/lib/time"
import type { Meeting } from "@/lib/types"

export function MeetingPage() {
  const { teamId, me } = useTeamCtx()
  const q = useActiveMeeting(teamId)

  if (q.isPending) return <div className="rounded-2xl border bg-card"><SectionLoading rows={6} /></div>
  if (q.isError) return <div className="rounded-2xl border bg-card"><SectionError error={q.error} onRetry={() => q.refetch()} /></div>

  const m = q.data
  if (!m) return <NoMeeting />
  if (m.ended_at) return <MeetingSummaryView meetingId={m.id} />
  if (!m.attendees.some((a) => a.user_id === me.user.id)) return <JoinMeeting meeting={m} />
  return <LiveMeeting meeting={m} />
}

function Hero({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-xl rounded-2xl border bg-card p-8 text-center shadow-xs">
      <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-accent text-accent-foreground [&_svg]:size-6">{icon}</div>
      <h1 className="mt-4 text-2xl font-semibold tracking-tight">{title}</h1>
      <div className="mt-2 space-y-5 text-sm text-muted-foreground">{children}</div>
    </div>
  )
}

function NoMeeting() {
  const { teamId, canWrite } = useTeamCtx()
  const qc = useQueryClient()
  const start = useMeetingAction(teamId, () => api<Meeting>(`/teams/${teamId}/meetings`, { method: "POST" }))
  const conflict = start.error instanceof ApiError && start.error.status === 409

  return (
    <Hero icon={<CalendarClockIcon />} title="No meeting running">
      <p>The Level 10 Meeting runs Scorecard (5 min), IDS (60 min) and Conclude (10 min). Everyone on the team follows along live.</p>
      {canWrite ? (
        <Button
          size="lg"
          disabled={start.isPending}
          onClick={() => start.mutate(undefined, { onError: () => qc.invalidateQueries({ queryKey: meetingKey(teamId) }) })}
        >
          <PlayIcon /> {start.isPending ? "Starting" : "Start meeting"}
        </Button>
      ) : <p className="font-medium text-foreground">An Admin or Team Member can start it. You can join once it runs.</p>}
      {conflict && <p role="status">Someone just started one. Loading it.</p>}
      <p className="text-xs">You become the facilitator: only you can move to the next section or end it.</p>
    </Hero>
  )
}

function JoinMeeting({ meeting }: { meeting: Meeting }) {
  const { teamId } = useTeamCtx()
  const name = useUserNames()
  const join = useMeetingAction(teamId, () => api<Meeting>(`/meetings/${meeting.id}/join`, { method: "POST" }))
  return (
    <Hero icon={<LogInIcon />} title="Meeting in progress">
      <p>
        Started {formatStamp(meeting.started_at)} by <span className="text-foreground">{name(meeting.facilitator_id)}</span>.
        Now in <span className="font-medium text-foreground">{SECTION_LABEL[meeting.current_section]}</span>.
      </p>
      <ul className="flex flex-wrap justify-center gap-3">
        {meeting.attendees.map((a) => <li key={a.user_id}><Person name={name(a.user_id)} /></li>)}
      </ul>
      <Button size="lg" disabled={join.isPending} onClick={() => join.mutate(undefined)}>
        <LogInIcon /> {join.isPending ? "Joining" : "Join meeting"}
      </Button>
    </Hero>
  )
}

function LiveMeeting({ meeting }: { meeting: Meeting }) {
  const { teamId, canWrite } = useTeamCtx()
  const s = meeting.current_section
  return (
    <div className="grid items-start gap-6 lg:grid-cols-[20rem_minmax(0,1fr)]">
      <AgendaPanel meeting={meeting} />
      <div className="min-w-0 space-y-6">
        <div>
          <p className="text-sm font-medium text-primary">Now: {SECTION_LABEL[s]}</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">{SECTION_HINT[s]}</h2>
        </div>
        {s === "scorecard" && <ScorecardSection teamId={teamId} canWrite={canWrite} />}
        {s === "ids" && (
          <>
            <IssuesSection teamId={teamId} canWrite={canWrite} />
            <TodosSection teamId={teamId} canWrite={canWrite} />
          </>
        )}
        {s === "conclude" && (
          <>
            <TodosSection teamId={teamId} canWrite={canWrite} only={meeting.todos_created} title="New To-Dos from this meeting" />
            <RatingPanel meeting={meeting} />
          </>
        )}
      </div>
    </div>
  )
}
