"use client"
import { CheckIcon, ChevronRightIcon, CrownIcon, SquareIcon } from "lucide-react"
import { useState } from "react"

import { SectionTimer } from "@/components/meeting/timer"
import { useTeamCtx } from "@/components/shell/team-context"
import { Person } from "@/components/team/section"
import { Button } from "@/components/ui/button"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { api } from "@/lib/api"
import { useMeetingAction } from "@/lib/meeting"
import { useUserNames } from "@/lib/queries"
import { formatStamp } from "@/lib/time"
import type { Meeting, Section } from "@/lib/types"
import { cn } from "@/lib/utils"

export const SECTION_LABEL: Record<Section, string> = { scorecard: "Scorecard", ids: "IDS", conclude: "Conclude" }
export const SECTION_HINT: Record<Section, string> = {
  scorecard: "Review last week's numbers. Off-track ones become Issues.",
  ids: "Identify, Discuss, Solve: work the Issues list top down.",
  conclude: "Recap new To-Dos, then everyone rates the meeting.",
}

export function AgendaPanel({ meeting }: { meeting: Meeting }) {
  const { teamId, me } = useTeamCtx()
  const name = useUserNames()
  const isFacilitator = meeting.facilitator_id === me.user.id
  const order = meeting.agenda.map((a) => a.section)
  const idx = order.indexOf(meeting.current_section)
  const next = order[idx + 1] as Section | undefined
  const [confirmEnd, setConfirmEnd] = useState(false)

  const advance = useMeetingAction(teamId, (to: Section) =>
    api<Meeting>(`/meetings/${meeting.id}/advance`, { method: "POST", body: { to } }))
  const end = useMeetingAction(teamId, () => api<Meeting>(`/meetings/${meeting.id}/end`, { method: "POST" }))
  const rated = new Map(meeting.ratings.map((r) => [r.user_id, r.rating]))

  return (
    <aside className="space-y-4 lg:sticky lg:top-20" aria-label="Meeting controls">
      <div className="rounded-2xl border bg-card p-4 shadow-xs">
        <div className="mb-4 flex items-start justify-between gap-2">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">Level 10 Meeting</h1>
            <p className="text-xs text-muted-foreground">Started {formatStamp(meeting.started_at)}</p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-danger-soft px-2 py-0.5 text-xs font-semibold text-danger">
            <span className="size-1.5 animate-pulse rounded-full bg-danger" aria-hidden="true" /> Live
          </span>
        </div>
        <SectionTimer meeting={meeting} />

        <ol className="mt-4 space-y-1" aria-label="Agenda">
          {meeting.agenda.map((a, i) => {
            const state = i < idx ? "done" : i === idx ? "current" : "upcoming"
            return (
              <li
                key={a.section}
                aria-current={state === "current" ? "step" : undefined}
                className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm", state === "current" && "bg-accent font-medium text-accent-foreground")}
              >
                <span className={cn(
                  "flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                  state === "done" ? "bg-success-soft text-success" : state === "current" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
                )}>
                  {state === "done" ? <CheckIcon className="size-3.5" aria-label="Done" /> : i + 1}
                </span>
                <span className="flex-1">{SECTION_LABEL[a.section]}</span>
                <span className="text-xs text-muted-foreground tabular">{a.minutes} min</span>
              </li>
            )
          })}
        </ol>

        <div className="mt-4 border-t pt-4">
          {isFacilitator ? (
            <div className="flex flex-col gap-2">
              {next ? (
                <Button size="lg" className="w-full" disabled={advance.isPending} onClick={() => advance.mutate(next)}>
                  Next: {SECTION_LABEL[next]} <ChevronRightIcon />
                </Button>
              ) : (
                <Button size="lg" className="w-full" onClick={() => setConfirmEnd(true)}>
                  <SquareIcon /> End meeting
                </Button>
              )}
              {next && <Button variant="ghost" className="w-full text-muted-foreground" onClick={() => setConfirmEnd(true)}>End meeting now</Button>}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              <CrownIcon className="mr-1 inline size-3.5 align-[-2px]" /> {name(meeting.facilitator_id)} is facilitating.
            </p>
          )}
        </div>
      </div>

      <div className="rounded-2xl border bg-card p-4 shadow-xs">
        <h2 className="text-sm font-semibold">Attendees <span className="font-normal text-muted-foreground">{meeting.attendees.length}</span></h2>
        <ul className="mt-3 space-y-2.5">
          {meeting.attendees.map((a) => (
            <li key={a.user_id} className="flex items-center justify-between gap-2 text-sm">
              <Person name={name(a.user_id)} />
              <span className="flex items-center gap-2 text-xs text-muted-foreground">
                {a.user_id === meeting.facilitator_id && <CrownIcon className="size-3.5 text-warning" aria-label="Facilitator" />}
                {meeting.current_section === "conclude" && rated.has(a.user_id) && <span className="text-success">Rated</span>}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <Dialog open={confirmEnd} onOpenChange={setConfirmEnd}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>End the meeting?</DialogTitle>
            <DialogDescription>
              {meeting.current_section === "conclude"
                ? `${meeting.ratings.length} of ${meeting.attendees.length} attendees have rated. Ratings close when it ends.`
                : "You are not in Conclude yet. Ratings can only be given in Conclude."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button disabled={end.isPending} onClick={() => end.mutate(undefined, { onSuccess: () => setConfirmEnd(false) })}>
              {end.isPending ? "Ending" : "End meeting"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </aside>
  )
}
