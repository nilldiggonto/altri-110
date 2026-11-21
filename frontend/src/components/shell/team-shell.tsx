"use client"
import { useQueryClient } from "@tanstack/react-query"
import { ChevronDownIcon, LogOutIcon } from "lucide-react"
import Link from "next/link"
import { useParams, usePathname, useRouter } from "next/navigation"
import { useEffect, type ReactNode } from "react"

import { ROLE_LABEL } from "@/components/shell/login-picker"
import { RealtimeProvider, useLinkStatus } from "@/components/shell/realtime"
import { TeamContext } from "@/components/shell/team-context"
import { Avatar } from "@/components/team/section"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { ApiError } from "@/lib/api"
import { clearEndedMeeting, meetingKey, useActiveMeeting } from "@/lib/meeting"
import { useMe, useTeam, useToken } from "@/lib/queries"
import { signOut } from "@/lib/token"
import { cn } from "@/lib/utils"
import type { Me, Meeting } from "@/lib/types"

export function TeamShell({ children }: { children: ReactNode }) {
  const { teamId } = useParams<{ teamId: string }>()
  const { token, ready: tokenReady } = useToken()
  const router = useRouter()
  const me = useMe()
  const team = useTeam(teamId)

  useEffect(() => {
    if (tokenReady && !token) router.replace("/login")
  }, [tokenReady, token, router])

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

  const ready = !!(me.data && team.data)
  const page = (
    <>
      <Header teamId={teamId} me={me.data} teamName={team.data?.team.name} ready={ready} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">{body}</main>
    </>
  )
  // Socket only once REST confirmed access to this team.
  return ready ? <RealtimeProvider key={teamId} teamId={teamId}>{page}</RealtimeProvider> : page
}

function LiveDot({ ready, teamId }: { ready: boolean; teamId: string }) {
  const status = useLinkStatus()
  if (!ready) return null
  const label = status === "live" ? "Live updates on" : status === "connecting" ? "Connecting" : "Offline, reconnecting"
  return (
    <span className="hidden items-center gap-1.5 text-xs text-muted-foreground sm:flex" title={label} data-team={teamId}>
      <span className={cn("size-2 rounded-full", status === "live" ? "bg-success" : status === "connecting" ? "bg-warning" : "bg-danger animate-pulse")} aria-hidden="true" />
      <span className="sr-only lg:not-sr-only">{label}</span>
    </span>
  )
}

function Header({ teamId, me, teamName, ready }: { teamId: string; me?: Me; teamName?: string; ready: boolean }) {
  const pathname = usePathname()
  const qc = useQueryClient()
  const meeting = useActiveMeeting(teamId, ready)
  useEffect(() => {
    // An ended meeting stays on the Meeting page for its summary; once you navigate away it is done.
    if (!pathname.endsWith("/meeting") && qc.getQueryData<Meeting | null>(meetingKey(teamId))?.ended_at) clearEndedMeeting(qc, teamId)
  }, [pathname, qc, teamId])
  const running = !!meeting.data && !meeting.data.ended_at
  const base = `/teams/${teamId}`
  const tabs = [
    { href: base, label: "Team" },
    { href: `${base}/meeting`, label: "Meeting" },
  ]
  return (
    <header className="sticky top-0 z-40 border-b bg-card/80 backdrop-blur supports-backdrop-filter:bg-card/70">
      <div className="mx-auto flex h-14 w-full max-w-7xl items-center gap-2 px-4 sm:gap-4">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span aria-hidden="true" className="flex size-7 items-center justify-center rounded-lg bg-primary text-sm text-primary-foreground">a</span>
          <span className="hidden sm:inline">altri</span>
        </Link>
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" className="min-w-0 gap-1 px-1.5 font-medium sm:px-2.5" />} disabled={!me}>
            <span className="max-w-28 truncate sm:max-w-48">{teamName ?? "Teams"}</span>
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
              className="inline-flex items-center rounded-md px-2.5 py-1.5 text-sm sm:px-3 text-muted-foreground outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 aria-[current=page]:bg-muted aria-[current=page]:text-foreground"
            >
              {t.label}
              {t.label === "Meeting" && running && (
                <span className="ml-1.5 inline-flex items-center gap-1 rounded-full bg-danger-soft p-1 text-[0.65rem] font-semibold text-danger sm:px-1.5 sm:py-0.5">
                  <span className="size-1.5 animate-pulse rounded-full bg-danger" aria-hidden="true" />
                  <span className="sr-only sm:not-sr-only">Live</span>
                </span>
              )}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <LiveDot ready={ready} teamId={teamId} />
          {me && (
            <DropdownMenu>
              <DropdownMenuTrigger render={<Button variant="ghost" className="gap-1 px-1 sm:px-2.5" />}>
                <Avatar name={me.user.name} className="size-7" />
                <span className="hidden md:inline">{me.user.name}</span>
                <span className="hidden text-muted-foreground md:inline">({ROLE_LABEL[me.user.role]})</span>
                <span className="sr-only md:hidden">{me.user.name}, {ROLE_LABEL[me.user.role]}</span>
                <ChevronDownIcon className="hidden sm:block" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="min-w-52">
                <DropdownMenuGroup>
                  <DropdownMenuLabel>{me.user.name} · {ROLE_LABEL[me.user.role]}</DropdownMenuLabel>
                  <DropdownMenuItem onClick={signOut}>
                    <LogOutIcon /> Sign out
                  </DropdownMenuItem>
                </DropdownMenuGroup>
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
