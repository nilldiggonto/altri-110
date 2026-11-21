"use client"
import { EyeIcon } from "lucide-react"

import { useTeamCtx } from "@/components/shell/team-context"
import { IssuesSection } from "@/components/team/issues"
import { RocksSection } from "@/components/team/rocks"
import { ScorecardSection } from "@/components/team/scorecard"
import { TodosSection } from "@/components/team/todos"
import { formatDay } from "@/lib/time"

export function TeamPage() {
  const { teamId, detail, canWrite } = useTeamCtx()
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-primary">Week of {formatDay(detail.current_week)}</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">{detail.team.name}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Today is {formatDay(detail.today, true)} (company time) · {detail.members.length} members
          </p>
        </div>
        {!canWrite && (
          <p className="inline-flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm text-secondary-foreground">
            <EyeIcon className="size-4" /> You are an Observer: you can view, not change.
          </p>
        )}
      </div>
      <ScorecardSection teamId={teamId} canWrite={canWrite} />
      <div className="grid gap-6 lg:grid-cols-2">
        <IssuesSection teamId={teamId} canWrite={canWrite} />
        <TodosSection teamId={teamId} canWrite={canWrite} />
      </div>
      <RocksSection teamId={teamId} />
    </div>
  )
}
