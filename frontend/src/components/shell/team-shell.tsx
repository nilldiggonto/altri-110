"use client"
import { ChevronDownIcon, LogOutIcon } from "lucide-react"
import Link from "next/link"
import { useParams, usePathname, useRouter } from "next/navigation"
import { useEffect, type ReactNode } from "react"

import { ROLE_LABEL } from "@/components/shell/login-picker"
import { TeamContext } from "@/components/shell/team-context"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { ApiError } from "@/lib/api"
import { useMe, useTeam, useToken } from "@/lib/queries"
import { signOut } from "@/lib/token"
import { cn } from "@/lib/utils"
import type { Me } from "@/lib/types"

export function TeamShell({ children }: { children: ReactNode }) {
  const { teamId } = useParams<{ teamId: string }>()
  const { token, ready } = useToken()
  const router = useRouter()
  const me = useMe()
  const team = useTeam(teamId)

  useEffect(() => {
    if (ready && !token) router.replace("/login")
  }, [ready, token, router])

  let body: ReactNode
  if (team.isError || me.isError) {
    const err = (team.error ?? me.error) as Error
    const denied = err instanceof ApiError && err.status === 403
    body = (
      <div role="alert" className="mx-auto max-w-md px-4 py-24 text-center">
        <h1 className="text-lg font-semibold">{denied ? "You don't have access to this team" : "Something went wrong"}</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {denied ? "It may not exist, or you aren't a member. Pick one of your teams above." : err.message}
        </p>
        {!denied && <Button className="mt-6" variant="outline" onClick={() => { me.refetch(); team.refetch() }}>Retry</Button>}
      </div>
    )
  } else if (!me.data || !team.data) {
    body = <ShellSkeleton />
  } else {
    body = (
      <TeamContext.Provider value={{ teamId, detail: team.data, me: me.data, canWrite: me.data.can_write }}>
        <div key={teamId} className="contents">{children}</div>
      </TeamContext.Provider>
    )
  }

  return (
    <>
      <Header teamId={teamId} me={me.data} teamName={team.data?.team.name} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">{body}</main>
    </>
  )
}

function Header({ teamId, me, teamName }: { teamId: string; me?: Me; teamName?: string }) {
  const pathname = usePathname()
  const base = `/teams/${teamId}`
  const tabs = [
    { href: base, label: "Team" },
    { href: `${base}/meeting`, label: "Meeting" },
  ]
  return (
    <header className="border-b">
      <div className="mx-auto flex h-14 w-full max-w-7xl items-center gap-4 px-4">
        <Link href="/" className="font-semibold tracking-tight">altri</Link>
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" className="gap-1 font-medium" />} disabled={!me}>
            {teamName ?? "Teams"}
            <ChevronDownIcon />
          </DropdownMenuTrigger>
          <DropdownMenuContent className="min-w-48">
            <DropdownMenuGroup>
              <DropdownMenuLabel>{me?.user.role === "admin" ? "All teams" : "Your teams"}</DropdownMenuLabel>
              {me?.teams.map((t) => (
                <DropdownMenuItem key={t.id} render={<Link href={`/teams/${t.id}`} />} className={cn(t.id === teamId && "font-medium")}>
                  {t.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
        <nav aria-label="Team sections" className="flex items-center gap-1">
          {tabs.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              aria-current={pathname === t.href ? "page" : undefined}
              className="rounded-md px-3 py-1.5 text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 aria-[current=page]:bg-muted aria-[current=page]:text-foreground"
            >
              {t.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto">
          {me && (
            <DropdownMenu>
              <DropdownMenuTrigger render={<Button variant="ghost" className="gap-1" />}>
                {me.user.name}
                <span className="text-muted-foreground">({ROLE_LABEL[me.user.role]})</span>
                <ChevronDownIcon />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={signOut}>
                  <LogOutIcon /> Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  )
}

export function ShellSkeleton() {
  return (
    <div className="space-y-4" aria-busy="true">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}
