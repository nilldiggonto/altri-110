import { Suspense } from "react"

import { ShellSkeleton, TeamShell } from "@/components/shell/team-shell"

export default function TeamLayout({ children }: LayoutProps<"/teams/[teamId]">) {
  return (
    <Suspense fallback={<main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6"><ShellSkeleton /></main>}>
      <TeamShell>{children}</TeamShell>
    </Suspense>
  )
}
