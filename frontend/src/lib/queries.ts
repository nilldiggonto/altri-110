"use client"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useSyncExternalStore } from "react"
import { toast } from "sonner"

import { api } from "@/lib/api"
import { getToken, subscribeToken } from "@/lib/token"
import type { Issue, Me, Rocks, Scorecard, TeamDetail, TodoList, User } from "@/lib/types"

export const keys = {
  me: ["me"] as const,
  users: ["users"] as const,
  team: (t: string) => ["team", t] as const,
  section: (t: string, s: string) => ["team", t, s] as const,
}

const noop = () => () => {}

/** Token, or null. `ready` is false until the browser value has been read (server render, hydration). */
export function useToken(): { token: string | null; ready: boolean } {
  const token = useSyncExternalStore(subscribeToken, getToken, () => null)
  const ready = useSyncExternalStore(noop, () => true, () => false)
  return { token, ready }
}

export function useMe() {
  const { token } = useToken()
  return useQuery({ queryKey: [...keys.me, token], queryFn: () => api<Me>("/me"), enabled: !!token })
}

export function useUsers() {
  return useQuery({ queryKey: keys.users, queryFn: () => api<User[]>("/auth/users"), staleTime: Infinity })
}

/** Names for every user id (Admins can view teams they aren't members of). */
export function useUserNames(): (id: string) => string {
  const { data } = useUsers()
  const names = new Map((data ?? []).map((u) => [u.id, u.name]))
  return (id) => names.get(id) ?? id
}

export function useTeam(teamId: string) {
  return useQuery({ queryKey: [...keys.team(teamId), "detail"], queryFn: () => api<TeamDetail>(`/teams/${teamId}`) })
}

export function useScorecard(teamId: string) {
  return useQuery({ queryKey: keys.section(teamId, "scorecard"), queryFn: () => api<Scorecard>(`/teams/${teamId}/scorecard`) })
}

export function useIssues(teamId: string, solved = false) {
  return useQuery({
    queryKey: [...keys.section(teamId, "issues"), solved ? "solved" : "open"],
    queryFn: () => api<Issue[]>(`/teams/${teamId}/issues${solved ? "?solved=true" : ""}`),
  })
}

export function useTodos(teamId: string) {
  return useQuery({ queryKey: keys.section(teamId, "todos"), queryFn: () => api<TodoList>(`/teams/${teamId}/todos`) })
}

export function useRocks(teamId: string) {
  return useQuery({ queryKey: keys.section(teamId, "rocks"), queryFn: () => api<Rocks>(`/teams/${teamId}/rocks`) })
}

/** Mutation that refreshes the given team sections and toasts errors. */
export function useTeamMutation<V, R = unknown>(
  teamId: string,
  sections: string[],
  fn: (vars: V) => Promise<R>,
  opts: { success?: string } = {},
) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      if (opts.success) toast.success(opts.success)
    },
    onError: (e) => {
      toast.error(e instanceof Error ? e.message : "Something went wrong")
    },
    onSettled: () => Promise.all(sections.map((s) => qc.invalidateQueries({ queryKey: keys.section(teamId, s) }))),
  })
}
