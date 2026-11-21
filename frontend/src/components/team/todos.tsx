"use client"
import { CircleAlertIcon, LinkIcon } from "lucide-react"
import { useState } from "react"

import { Segmented } from "@/components/team/issues"
import { EmptyState, Person, SectionCard, SectionError, SectionLoading } from "@/components/team/section"
import { Checkbox } from "@/components/ui/checkbox"
import { api } from "@/lib/api"
import { useTeamMutation, useTodos, useUserNames } from "@/lib/queries"
import { formatDay, formatStamp } from "@/lib/time"
import type { Completion, Todo } from "@/lib/types"
import { cn } from "@/lib/utils"

const TARGET = 90

export function TodosSection({ teamId, canWrite, only, title = "To-Dos" }: {
  teamId: string
  canWrite: boolean
  /** Restrict to these ids (the meeting's new To-Dos). */
  only?: string[]
  title?: string
}) {
  const q = useTodos(teamId)
  const [view, setView] = useState<"open" | "done">("open")
  const all = q.data?.todos.filter((t) => !only || only.includes(t.id)) ?? []
  const open = all.filter((t) => !t.done_at)
  const done = all.filter((t) => t.done_at)
  const rows = only ? all : view === "open" ? open : done

  return (
    <SectionCard
      title={title}
      description={q.data && !only ? <CompletionLine c={q.data.last_closed_week} /> : undefined}
      actions={!only && (
        <Segmented
          value={view}
          onChange={setView}
          options={[{ value: "open", label: "Open", count: q.data ? open.length : undefined }, { value: "done", label: "Done", count: q.data ? done.length : undefined }]}
        />
      )}
    >
      {q.isPending ? <SectionLoading /> : q.isError ? <SectionError error={q.error} onRetry={() => q.refetch()} /> :
        rows.length === 0 ? (
          only ? <EmptyState title="No new To-Dos yet" hint="To-Dos added during the meeting show here." />
            : view === "open" ? <EmptyState title="All caught up" hint="Add To-Dos from an Issue." />
              : <EmptyState title="Nothing done yet" />
        ) : (
          <ul className="divide-y">
            {rows.map((t) => <TodoRow key={t.id} teamId={teamId} todo={t} canWrite={canWrite} />)}
          </ul>
        )}
    </SectionCard>
  )
}

function CompletionLine({ c }: { c: Completion }) {
  if (c.rate_percent === null) return <>Week of {formatDay(c.week_start)}: no To-Dos were due.</>
  return (
    <>
      Week of {formatDay(c.week_start)}: {c.done} of {c.due} done,{" "}
      <span className={cn("font-medium", c.meets_target ? "text-success" : "text-danger")}>
        {c.rate_percent}%
      </span>{" "}
      (target {TARGET}%)
    </>
  )
}

function TodoRow({ teamId, todo, canWrite }: { teamId: string; todo: Todo; canWrite: boolean }) {
  const name = useUserNames()
  const done = !!todo.done_at
  const toggle = useTeamMutation(teamId, ["todos"], (d: boolean) =>
    api(`/teams/${teamId}/todos/${todo.id}`, { method: "PATCH", body: { done: d } }))
  const id = `todo-${todo.id}`

  return (
    <li className="flex items-start gap-3 px-5 py-3.5 hover:bg-muted/30">
      <Checkbox
        id={id}
        className="mt-0.5"
        checked={toggle.isPending ? toggle.variables : done}
        disabled={!canWrite || toggle.isPending}
        onCheckedChange={(c) => toggle.mutate(!!c)}
        aria-label={`${done ? "Undo" : "Mark done"}: ${todo.title}`}
      />
      <div className="min-w-0 flex-1">
        <label htmlFor={id} className={cn("font-medium", done && "text-muted-foreground line-through", canWrite && "cursor-pointer")}>
          {todo.title}
        </label>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <Person name={name(todo.owner_id)} />
          <span className={cn(todo.overdue && "font-medium text-danger")}>
            {todo.overdue && <CircleAlertIcon className="mr-1 inline size-3.5 align-[-2px]" />}
            Due {formatDay(todo.due_date)}{todo.overdue && ", overdue"}
          </span>
          {todo.done_at && <span className="text-success">Done {formatStamp(todo.done_at)}</span>}
          {todo.source_issue_title && (
            <span className="inline-flex min-w-0 items-center gap-1"><LinkIcon className="size-3" /> <span className="truncate">{todo.source_issue_title}</span></span>
          )}
        </div>
      </div>
    </li>
  )
}
