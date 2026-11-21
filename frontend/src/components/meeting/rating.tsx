"use client"
import { StarIcon } from "lucide-react"

import { useTeamCtx } from "@/components/shell/team-context"
import { Person, SectionCard } from "@/components/team/section"
import { api } from "@/lib/api"
import { useMeetingAction } from "@/lib/meeting"
import { useUserNames } from "@/lib/queries"
import type { Meeting } from "@/lib/types"
import { cn } from "@/lib/utils"

export function RatingPanel({ meeting }: { meeting: Meeting }) {
  const { teamId, me, canWrite } = useTeamCtx()
  const name = useUserNames()
  const mine = meeting.ratings.find((r) => r.user_id === me.user.id)?.rating
  const attending = meeting.attendees.some((a) => a.user_id === me.user.id)
  const rate = useMeetingAction(teamId, (rating: number) =>
    api<Meeting>(`/meetings/${meeting.id}/rating`, { method: "PUT", body: { rating } }))
  const shown = rate.isPending ? rate.variables : mine
  const byUser = new Map(meeting.ratings.map((r) => [r.user_id, r.rating]))

  return (
    <SectionCard
      title="Rate this meeting"
      description="1 is poor, 10 is great. You can change it until the meeting ends."
      actions={
        <div className="text-right">
          <p className="text-2xl font-semibold tabular">{meeting.rating?.toFixed(1) ?? "No rating yet"}</p>
          <p className="text-xs text-muted-foreground">{meeting.ratings.length ? `Average of ${meeting.ratings.length}` : "Average appears after the first rating"}</p>
        </div>
      }
    >
      <div className="space-y-5 p-5">
        {canWrite && attending ? (
          <fieldset>
            <legend className="mb-2 text-sm font-medium">Your rating</legend>
            <div className="grid grid-cols-5 gap-2 sm:grid-cols-10">
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <button
                  key={n}
                  type="button"
                  aria-pressed={shown === n}
                  disabled={rate.isPending}
                  onClick={() => rate.mutate(n)}
                  className={cn(
                    "h-11 rounded-lg border text-base font-semibold tabular outline-none transition-colors hover:border-primary hover:bg-accent focus-visible:ring-3 focus-visible:ring-ring/50",
                    shown === n && "border-primary bg-primary text-primary-foreground hover:bg-primary",
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
          </fieldset>
        ) : (
          <p className="text-sm text-muted-foreground">
            {canWrite ? "Join the meeting to rate it." : "Observers don't rate meetings."}
          </p>
        )}
        <ul className="divide-y rounded-xl border">
          {meeting.attendees.map((a) => {
            const r = byUser.get(a.user_id)
            return (
              <li key={a.user_id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                <Person name={name(a.user_id)} />
                {r !== undefined
                  ? <span className="inline-flex items-center gap-1 font-semibold tabular"><StarIcon className="size-3.5 text-warning" aria-hidden="true" />{r}</span>
                  : <span className="text-xs text-muted-foreground">Not rated</span>}
              </li>
            )
          })}
        </ul>
      </div>
    </SectionCard>
  )
}
