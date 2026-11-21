"use client"
import { CircleAlertIcon, CircleCheckIcon, CircleDashedIcon, FlagIcon } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { EmptyState, Person, SectionCard, SectionError, SectionLoading } from "@/components/team/section"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { api } from "@/lib/api"
import { formatGoal, formatValue } from "@/lib/format"
import { useScorecard, useTeamMutation, useUserNames } from "@/lib/queries"
import { formatDay } from "@/lib/time"
import type { Cell, CellStatus, Issue, MeasurableRow } from "@/lib/types"
import { cn } from "@/lib/utils"

const STATUS: Record<CellStatus, { label: string; cls: string; Icon: typeof CircleCheckIcon }> = {
  on_track: { label: "On track", cls: "bg-success-soft text-success", Icon: CircleCheckIcon },
  off_track: { label: "Off track", cls: "bg-danger-soft text-danger", Icon: CircleAlertIcon },
  pending: { label: "Pending", cls: "bg-muted text-muted-foreground", Icon: CircleDashedIcon },
}

export function ScorecardSection({ teamId, canWrite }: { teamId: string; canWrite: boolean }) {
  const q = useScorecard(teamId)
  const name = useUserNames()
  const scroller = useRef<HTMLDivElement>(null)
  const loaded = !!q.data
  useEffect(() => {
    // Newest weeks are on the right: start scrolled there.
    if (loaded && scroller.current) scroller.current.scrollLeft = scroller.current.scrollWidth
  }, [loaded])

  return (
    <SectionCard
      title="Scorecard"
      description="Last 13 weeks, current week on the right."
      actions={<Legend />}
    >
      {q.isPending ? <SectionLoading rows={5} /> : q.isError ? <SectionError error={q.error} onRetry={() => q.refetch()} /> :
        q.data.measurables.length === 0 ? <EmptyState title="No Measurables yet" hint="Measurables come from the seed data." /> : (
          <div ref={scroller} className="overflow-x-auto">
            <table className="w-full border-separate border-spacing-0 text-sm">
              <caption className="sr-only">Scores by week. Each cell shows the value and its status.</caption>
              <thead>
                <tr className="text-xs text-muted-foreground">
                  <th scope="col" className="sticky left-0 z-10 min-w-40 bg-card px-4 py-3 sm:min-w-52 sm:px-5 text-left font-medium shadow-[1px_0_0_var(--border)]">Measurable</th>
                  <th scope="col" className="px-3 py-3 text-left font-medium">Goal</th>
                  {q.data.weeks.map((w) => (
                    <th key={w} scope="col" className={cn("px-1 py-3 text-center font-medium whitespace-nowrap", w === q.data.current_week && "text-primary")}>
                      {formatDay(w)}
                      {w === q.data.current_week && <span className="block text-[0.65rem] font-normal">This week</span>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {q.data.measurables.map((m) => (
                  <tr key={m.id} className="group">
                    <th scope="row" className="sticky left-0 z-10 border-t bg-card px-4 py-2.5 sm:px-5 shadow-[1px_0_0_var(--border)] text-left font-normal group-hover:bg-muted">
                      <span className="block font-medium">{m.name}</span>
                      <span className="mt-1 block text-xs text-muted-foreground"><Person name={name(m.owner_id)} /></span>
                    </th>
                    <td className="border-t px-3 py-2.5 whitespace-nowrap text-muted-foreground tabular">
                      {formatGoal(m.goal, m.unit)} <span className="text-xs">{m.unit === "%" || m.unit === "$k" ? "" : m.unit}</span>
                    </td>
                    {m.cells.map((c) => (
                      <td key={c.week_start} className="border-t px-1 py-2">
                        <ScoreCell teamId={teamId} m={m} cell={c} canWrite={canWrite} isCurrent={c.week_start === q.data.current_week} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
    </SectionCard>
  )
}

function Legend() {
  return (
    <ul className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground" aria-label="Legend">
      {(Object.keys(STATUS) as CellStatus[]).map((s) => {
        const { label, cls, Icon } = STATUS[s]
        return (
          <li key={s} className="flex items-center gap-1.5">
            <span className={cn("inline-flex size-5 items-center justify-center rounded-md", cls)}><Icon className="size-3" /></span>
            {label}
          </li>
        )
      })}
      <li className="flex items-center gap-1.5"><FlagIcon className="size-3.5 text-danger" /> Open Issue</li>
    </ul>
  )
}

function ScoreCell({ teamId, m, cell, canWrite, isCurrent }: { teamId: string; m: MeasurableRow; cell: Cell; canWrite: boolean; isCurrent: boolean }) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState("")
  const { label, cls, Icon } = STATUS[cell.status]
  const shown = cell.value === null ? "" : formatValue(cell.value, m.unit)
  const week = formatDay(cell.week_start)
  const path = `/teams/${teamId}/measurables/${m.id}/scores/${cell.week_start}`

  const save = useTeamMutation(teamId, ["scorecard"], (value: number | null) =>
    value === null ? api(path, { method: "DELETE" }) : api(path, { method: "PUT", body: { value } }))
  const makeIssue = useTeamMutation(teamId, ["scorecard", "issues"], () =>
    api<{ issue: Issue; created: boolean }>(`${path}/issue`, { method: "POST" }))

  const face = (
    <>
      <span className="tabular">{shown}</span>
      <Icon className={cn("size-3.5 shrink-0 opacity-80", shown && "sr-only")} aria-hidden="true" />
      {!shown && <span className="sr-only">No score</span>}
      {cell.open_issue_id && <FlagIcon className="absolute top-1 right-1 size-3 text-danger" aria-label="Open Issue" />}
      <span className="sr-only">, {label}</span>
    </>
  )
  const faceCls = cn(
    "relative flex h-10 min-w-14 w-full items-center justify-center gap-1 rounded-lg px-2 text-sm font-medium whitespace-nowrap",
    cls, cell.status === "pending" && "border border-dashed border-border", isCurrent && "ring-1 ring-primary/30",
  )

  if (!canWrite) return <div className={faceCls} title={`${m.name}, ${week}: ${shown || "no score"}, ${label}`}>{face}</div>

  function submit(e: React.FormEvent) {
    e.preventDefault()
    const t = draft.trim()
    const value = t === "" ? null : Number(t)
    if (value !== null && !Number.isFinite(value)) return
    if (value === cell.value) return setOpen(false)
    save.mutate(value, { onSuccess: () => setOpen(false) })
  }

  return (
    <Popover open={open} onOpenChange={(o) => { setOpen(o); if (o) setDraft(cell.value === null ? "" : String(cell.value)) }}>
      <PopoverTrigger
        aria-label={`${m.name}, week of ${week}: ${shown || "no score"}, ${label}. Edit`}
        className={cn(faceCls, "cursor-pointer outline-none transition-shadow hover:ring-2 hover:ring-primary/40 focus-visible:ring-3 focus-visible:ring-ring/60")}
      >
        {face}
      </PopoverTrigger>
      <PopoverContent align="center" className="w-72 gap-3 p-4">
        <div>
          <p className="font-medium">{m.name}</p>
          <p className="text-xs text-muted-foreground">Week of {week} · Goal {formatGoal(m.goal, m.unit)}</p>
        </div>
        <form onSubmit={submit} className="space-y-2">
          <Label htmlFor={`v-${m.id}-${cell.week_start}`}>Score ({m.unit})</Label>
          <div className="flex gap-2">
            <Input
              id={`v-${m.id}-${cell.week_start}`}
              inputMode="decimal"
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              aria-invalid={draft.trim() !== "" && !Number.isFinite(Number(draft))}
              placeholder="Empty clears it"
              className="tabular"
            />
            <Button type="submit" disabled={save.isPending}>{save.isPending ? "Saving" : "Save"}</Button>
          </div>
          {draft.trim() !== "" && !Number.isFinite(Number(draft)) && <p className="text-xs text-danger">Enter a number, or leave it empty to clear.</p>}
        </form>
        {cell.status === "off_track" && (
          <div className="flex items-center justify-between gap-2 border-t pt-3">
            {cell.open_issue_id ? (
              <Badge variant="destructive"><FlagIcon /> Issue open</Badge>
            ) : <span className="text-xs text-muted-foreground">Off track this week</span>}
            {!cell.open_issue_id && (
              <Button
                variant="outline"
                size="sm"
                disabled={makeIssue.isPending}
                onClick={() => makeIssue.mutate(undefined, {
                  onSuccess: (r) => { toast.success(r.created ? "Issue created" : "An open Issue already exists"); setOpen(false) },
                })}
              >
                <FlagIcon /> Make it an Issue
              </Button>
            )}
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}
