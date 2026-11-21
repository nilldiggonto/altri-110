"use client"
import { useQuery } from "@tanstack/react-query"
import { useSyncExternalStore } from "react"

import { api } from "@/lib/api"
import { getToken, subscribeToken } from "@/lib/token"
import type { Me, TeamDetail, User } from "@/lib/types"

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
  return useQuery({ queryKey: keys.team(teamId).concat("detail"), queryFn: () => api<TeamDetail>(`/teams/${teamId}`) })
}
