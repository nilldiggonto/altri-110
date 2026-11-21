"use client"
import { CheckCircle2Icon, ChevronRightIcon, CircleIcon } from "lucide-react"
import { useState } from "react"

import { EmptyState, Person, SectionCard, SectionError, SectionLoading } from "@/components/team/section"
import { useRocks, useUserNames } from "@/lib/queries"
import { formatDay } from "@/lib/time"
import type { Rock } from "@/lib/types"
import { cn } from "@/lib/utils"

const STATUS: Record<Rock["status"], { label: string; cls: string; bar: string }> = {
  on_track: { label: "On track", cls: "bg-success-soft text-success", bar: "bg-success" },
  off_track: { label: "Off track", cls: "bg-danger-soft text-danger", bar: "bg-danger" },
  complete: { label: "Complete", cls: "bg-secondary text-secondary-foreground", bar: "bg-primary" },
}

export function RocksSection({ teamId }: { teamId: string }) {
  const q = useRocks(teamId)
  return (
    <SectionCard title="Rocks" description={q.data ? `${q.data.quarter.replace("-", " ")} goals. Read-only.` : "This quarter's goals."}>
      {q.isPending ? <SectionLoading rows={3} /> : q.isError ? <SectionError error={q.error} onRetry={() => q.refetch()} /> :
        q.data.rocks.length === 0 ? <EmptyState title="No Rocks this quarter" /> : (
          <ul className="divide-y">{q.data.rocks.map((r) => <RockRow key={r.id} rock={r} />)}</ul>
        )}
    </SectionCard>
  )
}

function RockRow({ rock }: { rock: Rock }) {
  const [open, setOpen] = useState(false)
  const name = useUserNames()
  const s = STATUS[rock.status]
  const panel = `rock-${rock.id}`
  const done = rock.milestones.filter((m) => m.done).length

  return (
    <li>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panel}
        onClick={() => setOpen(!open)}
        className="flex w-full flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3.5 text-left outline-none hover:bg-muted/30 focus-visible:bg-muted/40 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset"
      >
        <ChevronRightIcon className={cn("size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-90")} aria-hidden="true" />
        <div className="min-w-0 flex-1 basis-56">
          <p className="font-medium">{rock.title}</p>
          <div className="mt-1 text-xs text-muted-foreground"><Person name={name(rock.owner_id)} /></div>
        </div>
        <span className={cn("rounded-md px-2 py-0.5 text-xs font-medium", s.cls)}>{s.label}</span>
        <div className="flex w-44 items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted" role="progressbar" aria-valuenow={rock.progress_percent} aria-valuemin={0} aria-valuemax={100} aria-label={`${rock.title} progress`}>
            <div className={cn("h-full rounded-full", s.bar)} style={{ width: `${rock.progress_percent}%` }} />
          </div>
          <span className="w-10 text-right text-sm tabular">{rock.progress_percent}%</span>
        </div>
      </button>
      <div id={panel} hidden={!open} className="bg-muted/30 px-5 pt-1 pb-4 pl-14">
        {rock.milestones.length === 0 ? <p className="py-2 text-sm text-muted-foreground">No Milestones.</p> : (
          <>
            <p className="py-2 text-xs text-muted-foreground">{done} of {rock.milestones.length} Milestones done</p>
            <ul className="space-y-1.5">
              {rock.milestones.map((m) => (
                <li key={m.id} className="flex items-center gap-2 text-sm">
                  {m.done
                    ? <CheckCircle2Icon className="size-4 text-success" aria-label="Done" />
                    : <CircleIcon className="size-4 text-muted-foreground" aria-label="Not done" />}
                  <span className={cn("flex-1", m.done && "text-muted-foreground")}>{m.title}</span>
                  <span className="text-xs text-muted-foreground tabular">Due {formatDay(m.due_date)}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </li>
  )
}
