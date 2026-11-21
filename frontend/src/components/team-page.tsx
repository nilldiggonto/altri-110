"use client"
import { useTeamCtx } from "@/components/shell/team-context"
import { formatDay } from "@/lib/time"

export function TeamPage() {
  const { detail } = useTeamCtx()
  return (
    <div className="space-y-1">
      <h1 className="text-2xl font-semibold tracking-tight">{detail.team.name}</h1>
      <p className="text-sm text-muted-foreground">Today is {formatDay(detail.today, true)}, company time.</p>
    </div>
  )
}
