"use client"
import { useEffect, useState } from "react"

import { serverNow } from "@/lib/server-clock"
import { formatDuration } from "@/lib/time"
import type { Meeting } from "@/lib/types"
import { cn } from "@/lib/utils"

/** Server time, re-rendered every second. */
export function useServerNow(stop?: string | null): number {
  const [now, setNow] = useState(() => serverNow())
  useEffect(() => {
    if (stop) return
    const id = setInterval(() => setNow(serverNow()), 1000)
    return () => clearInterval(id)
  }, [stop])
  return stop ? Date.parse(stop) : now
}

/** Section timer. Counts down the planned minutes; past zero it shows time over, never advances. */
export function SectionTimer({ meeting }: { meeting: Meeting }) {
  const now = useServerNow(meeting.ended_at)
  const planned = (meeting.agenda.find((a) => a.section === meeting.current_section)?.minutes ?? 0) * 60_000
  const elapsed = Math.max(0, now - Date.parse(meeting.section_started_at))
  const over = elapsed > planned
  const pct = planned ? Math.min(100, (elapsed / planned) * 100) : 100
  const total = Math.max(0, now - Date.parse(meeting.started_at))

  return (
    <div className={cn("rounded-xl p-4", over ? "bg-danger-soft" : "bg-secondary")} role="timer" aria-live="off">
      <p className={cn("text-xs font-medium uppercase tracking-wide", over ? "text-danger" : "text-secondary-foreground")}>
        {over ? "Over time" : "Time left in section"}
      </p>
      <p className={cn("mt-1 text-4xl font-semibold tabular tracking-tight", over ? "text-danger" : "text-foreground")}>
        {over ? `+${formatDuration(elapsed - planned)}` : formatDuration(planned - elapsed)}
      </p>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-card/80" aria-hidden="true">
        <div className={cn("h-full rounded-full transition-[width] duration-1000 ease-linear", over ? "bg-danger" : "bg-primary")} style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-2 text-xs text-muted-foreground tabular">
        {formatDuration(elapsed)} of {formatDuration(planned)} · meeting {formatDuration(total)}
      </p>
    </div>
  )
}
