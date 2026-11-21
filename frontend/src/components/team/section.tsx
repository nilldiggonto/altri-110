import { AlertCircleIcon } from "lucide-react"
import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

export function SectionCard({
  title, description, actions, children, className,
}: { title: string; description?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section aria-label={title} className={cn("overflow-hidden rounded-2xl border bg-card shadow-xs", className)}>
      <header className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
        <div className="min-w-0">
          <h2 className="text-base font-semibold tracking-tight">{title}</h2>
          {description && <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </header>
      {children}
    </section>
  )
}

export function SectionLoading({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-5" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => <Skeleton key={i} className="h-10 w-full" />)}
    </div>
  )
}

export function SectionError({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center justify-between gap-3 p-5 text-sm">
      <span className="flex items-center gap-2 text-danger">
        <AlertCircleIcon className="size-4" /> {error.message}
      </span>
      <Button variant="outline" size="sm" onClick={onRetry}>Retry</Button>
    </div>
  )
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="px-5 py-10 text-center">
      <p className="text-sm font-medium">{title}</p>
      {hint && <p className="mt-1 text-sm text-muted-foreground">{hint}</p>}
    </div>
  )
}

/** Small avatar circle with initials, for owners. */
export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name.split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase()
  return (
    <span
      aria-hidden="true"
      className={cn("inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-secondary text-[0.65rem] font-semibold text-secondary-foreground", className)}
    >
      {initials}
    </span>
  )
}

export function Person({ name }: { name: string }) {
  return (
    <span className="inline-flex min-w-0 items-center gap-2">
      <Avatar name={name} />
      <span className="truncate">{name}</span>
    </span>
  )
}
