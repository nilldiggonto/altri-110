"use client"
import { CheckIcon, FlagIcon, ListPlusIcon, PlusIcon } from "lucide-react"
import { useState } from "react"

import { useTeamCtx } from "@/components/shell/team-context"
import { EmptyState, Person, SectionCard, SectionError, SectionLoading } from "@/components/team/section"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import { PRIORITIES } from "@/lib/format"
import { useIssues, useTeamMutation, useUserNames } from "@/lib/queries"
import { formatDay, formatStamp } from "@/lib/time"
import type { Issue } from "@/lib/types"
import { cn } from "@/lib/utils"

const PRIORITY_ITEMS = [
  { value: "none", label: "No priority" },
  ...PRIORITIES.map((p) => ({ value: String(p), label: `P${p}` })),
]

export function IssuesSection({ teamId, canWrite, title = "Issues" }: { teamId: string; canWrite: boolean; title?: string }) {
  const [view, setView] = useState<"open" | "solved">("open")
  const [creating, setCreating] = useState(false)
  const open = useIssues(teamId, false)
  const solved = useIssues(teamId, true)
  const q = view === "open" ? open : solved

  return (
    <SectionCard
      title={title}
      description={view === "open" ? "Highest priority first (P5 to P1), then oldest." : "Most recently solved first."}
      actions={
        <>
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "open", label: "Open", count: open.data?.length },
              { value: "solved", label: "Solved", count: solved.data?.length },
            ]}
          />
          {canWrite && <Button onClick={() => setCreating(true)}><PlusIcon /> New Issue</Button>}
        </>
      }
    >
      {q.isPending ? <SectionLoading /> : q.isError ? <SectionError error={q.error} onRetry={() => q.refetch()} /> :
        q.data.length === 0 ? (
          view === "open"
            ? <EmptyState title="No open Issues" hint={canWrite ? "Add one, or make one from an off-track score." : undefined} />
            : <EmptyState title="Nothing solved yet" hint="Solved Issues show here with their note." />
        ) : (
          <ul className="divide-y">
            {q.data.map((i) => view === "open"
              ? <OpenIssueRow key={i.id} teamId={teamId} issue={i} canWrite={canWrite} />
              : <SolvedIssueRow key={i.id} issue={i} />)}
          </ul>
        )}
      {canWrite && <NewIssueDialog teamId={teamId} open={creating} onOpenChange={setCreating} />}
    </SectionCard>
  )
}

export function Segmented<T extends string>({ value, onChange, options }: {
  value: T; onChange: (v: T) => void; options: { value: T; label: string; count?: number }[]
}) {
  return (
    <div role="tablist" className="inline-flex rounded-lg bg-muted p-0.5">
      {options.map((o) => (
        <button
          key={o.value}
          role="tab"
          type="button"
          aria-selected={value === o.value}
          onClick={() => onChange(o.value)}
          className="inline-flex h-7 items-center gap-1.5 rounded-md px-3 text-sm text-muted-foreground outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 aria-selected:bg-card aria-selected:text-foreground aria-selected:shadow-xs"
        >
          {o.label}
          {o.count !== undefined && <span className="text-xs tabular opacity-70">{o.count}</span>}
        </button>
      ))}
    </div>
  )
}

function PriorityPill({ p }: { p: number | null }) {
  if (p === null) return <span className="text-xs text-muted-foreground">No priority</span>
  return (
    <span className={cn(
      "inline-flex h-6 min-w-9 items-center justify-center rounded-md px-1.5 text-xs font-semibold tabular",
      p >= 4 ? "bg-danger-soft text-danger" : p === 3 ? "bg-warning-soft text-warning" : "bg-muted text-muted-foreground",
    )}>
      P{p}
    </span>
  )
}

function OpenIssueRow({ teamId, issue, canWrite }: { teamId: string; issue: Issue; canWrite: boolean }) {
  const name = useUserNames()
  const [dialog, setDialog] = useState<"solve" | "todo" | null>(null)
  const setPriority = useTeamMutation(teamId, ["issues"], (priority: number | null) =>
    api(`/teams/${teamId}/issues/${issue.id}`, { method: "PATCH", body: { priority } }))

  return (
    <li className="flex gap-4 px-5 py-4 hover:bg-muted/30">
      <div className={cn("shrink-0", canWrite ? "w-28" : "w-12")}>
        {canWrite ? (
          <Select
            items={PRIORITY_ITEMS}
            value={issue.priority === null ? "none" : String(issue.priority)}
            onValueChange={(v) => setPriority.mutate(v === "none" || v === null ? null : Number(v))}
          >
            <SelectTrigger size="sm" aria-label={`Priority for ${issue.title}`} className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PRIORITY_ITEMS.map((it) => <SelectItem key={it.value} value={it.value}>{it.label}</SelectItem>)}
            </SelectContent>
          </Select>
        ) : <PriorityPill p={issue.priority} />}
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-medium">{issue.title}</p>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <Person name={name(issue.owner_id)} />
          <span>Created {formatStamp(issue.created_at)}</span>
        </div>
        {issue.source && (
          <Badge variant="outline" className="mt-2 h-auto max-w-full font-normal whitespace-normal text-muted-foreground">
            <FlagIcon /> From Scorecard: {issue.source.measurable_name}, week of {formatDay(issue.source.week_start)}
          </Badge>
        )}
        {canWrite && (
          <div className="mt-3 flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setDialog("todo")}><ListPlusIcon /> Add To-Do</Button>
            <Button variant="secondary" size="sm" onClick={() => setDialog("solve")}><CheckIcon /> Solve</Button>
          </div>
        )}
      </div>
      {canWrite && <SolveDialog teamId={teamId} issue={issue} open={dialog === "solve"} onOpenChange={(o) => setDialog(o ? "solve" : null)} />}
      {canWrite && <AddTodoDialog teamId={teamId} issue={issue} open={dialog === "todo"} onOpenChange={(o) => setDialog(o ? "todo" : null)} />}
    </li>
  )
}

function SolvedIssueRow({ issue }: { issue: Issue }) {
  const name = useUserNames()
  return (
    <li className="px-5 py-3.5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-medium">{issue.title}</p>
        <span className="text-xs text-success">Solved {issue.solved_at && formatStamp(issue.solved_at)}</span>
      </div>
      {issue.resolution_note && <p className="mt-1 max-w-prose text-sm text-muted-foreground">{issue.resolution_note}</p>}
      <div className="mt-1.5 text-xs text-muted-foreground"><Person name={name(issue.owner_id)} /></div>
    </li>
  )
}

type DialogProps = { teamId: string; open: boolean; onOpenChange: (o: boolean) => void }

function NewIssueDialog({ teamId, open, onOpenChange }: DialogProps) {
  const [title, setTitle] = useState("")
  const [priority, setPriority] = useState("none")
  const create = useTeamMutation(teamId, ["issues"], () =>
    api(`/teams/${teamId}/issues`, { method: "POST", body: { title, priority: priority === "none" ? null : Number(priority) } }),
  { success: "Issue added" })

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (o) { setTitle(""); setPriority("none") } }}>
      <DialogContent>
        <form
          className="space-y-4"
          onSubmit={(e) => { e.preventDefault(); if (title.trim()) create.mutate(undefined, { onSuccess: () => onOpenChange(false) }) }}
        >
          <DialogHeader>
            <DialogTitle>New Issue</DialogTitle>
            <DialogDescription>You will be the owner.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="issue-title">Title</Label>
            <Input id="issue-title" required maxLength={300} value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
          </div>
          <div className="space-y-2">
            <Label>Priority (optional)</Label>
            <Select items={PRIORITY_ITEMS} value={priority} onValueChange={(v) => setPriority(v ?? "none")}>
              <SelectTrigger aria-label="Priority" className="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                {PRIORITY_ITEMS.map((it) => <SelectItem key={it.value} value={it.value}>{it.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={!title.trim() || create.isPending}>{create.isPending ? "Adding" : "Add Issue"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function SolveDialog({ teamId, issue, open, onOpenChange }: DialogProps & { issue: Issue }) {
  const [note, setNote] = useState("")
  const solve = useTeamMutation(teamId, ["issues", "scorecard"], () =>
    api(`/teams/${teamId}/issues/${issue.id}/solve`, { method: "POST", body: { note } }),
  { success: "Issue solved" })

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (o) setNote("") }}>
      <DialogContent>
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); if (note.trim()) solve.mutate(undefined, { onSuccess: () => onOpenChange(false) }) }}>
          <DialogHeader>
            <DialogTitle>Solve Issue</DialogTitle>
            <DialogDescription>{issue.title}</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor={`note-${issue.id}`}>How was it solved?</Label>
            <Textarea id={`note-${issue.id}`} required maxLength={5000} rows={4} value={note} onChange={(e) => setNote(e.target.value)} autoFocus />
            <p className="text-xs text-muted-foreground">Required. It is kept with the solved Issue.</p>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={!note.trim() || solve.isPending}>{solve.isPending ? "Solving" : "Mark solved"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function AddTodoDialog({ teamId, issue, open, onOpenChange }: DialogProps & { issue: Issue }) {
  const { detail, me } = useTeamCtx()
  const owners = detail.owners.map((u) => ({ value: u.id, label: u.name }))
  const defaultOwner = owners.some((o) => o.value === me.user.id) ? me.user.id : owners[0]?.value ?? ""
  const [title, setTitle] = useState("")
  const [owner, setOwner] = useState(defaultOwner)
  const add = useTeamMutation(teamId, ["todos"], () =>
    api(`/teams/${teamId}/issues/${issue.id}/todos`, { method: "POST", body: { title, owner_id: owner } }),
  { success: "To-Do added" })

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (o) { setTitle(""); setOwner(defaultOwner) } }}>
      <DialogContent>
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); if (title.trim() && owner) add.mutate(undefined, { onSuccess: () => onOpenChange(false) }) }}>
          <DialogHeader>
            <DialogTitle>Add To-Do</DialogTitle>
            <DialogDescription>For: {issue.title}. Due in 7 days.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor={`todo-${issue.id}`}>Title</Label>
            <Input id={`todo-${issue.id}`} required maxLength={300} value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
          </div>
          <div className="space-y-2">
            <Label>Owner</Label>
            <Select items={owners} value={owner} onValueChange={(v) => setOwner(v ?? defaultOwner)}>
              <SelectTrigger aria-label="Owner" className="w-60"><SelectValue /></SelectTrigger>
              <SelectContent>
                {owners.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={!title.trim() || !owner || add.isPending}>{add.isPending ? "Adding" : "Add To-Do"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
