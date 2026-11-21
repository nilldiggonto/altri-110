"use client"
import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { api, ApiError } from "@/lib/api"
import { keys } from "@/lib/queries"
import { syncServerClock } from "@/lib/server-clock"
import type { Meeting, MeetingSummary } from "@/lib/types"

export const meetingKey = (teamId: string) => [...keys.team(teamId), "meeting"] as const

/** Store a meeting state unless we already hold a newer one of the same meeting. */
export function putMeeting(qc: QueryClient, teamId: string, next: Meeting | null) {
  if (next) syncServerClock(next.server_now)
  qc.setQueryData<Meeting | null>(meetingKey(teamId), (old) => {
    if (!next) return old?.ended_at ? old : null // keep an ended meeting on screen for its summary
    if (old && old.id === next.id && old.version > next.version) return old
    return next
  })
}

/** The team's active meeting (or the one that just ended while we watched). null: none. */
export function useActiveMeeting(teamId: string, enabled = true) {
  const qc = useQueryClient()
  return useQuery({
    queryKey: meetingKey(teamId),
    queryFn: async () => {
      try {
        const m = await api<Meeting>(`/teams/${teamId}/meetings/active`)
        syncServerClock(m.server_now)
        // A newer state may have arrived over the socket while this request was in flight.
        const cached = qc.getQueryData<Meeting | null>(meetingKey(teamId))
        return cached && cached.id === m.id && cached.version > m.version ? cached : m
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) {
          const old = qc.getQueryData<Meeting | null>(meetingKey(teamId))
          return old?.ended_at ? old : null
        }
        throw e
      }
    },
    enabled,
  })
}

export function useMeetingSummary(meetingId: string | undefined) {
  return useQuery({
    queryKey: ["meeting-summary", meetingId],
    queryFn: () => api<MeetingSummary>(`/meetings/${meetingId}/summary`),
    enabled: !!meetingId,
    staleTime: Infinity,
  })
}

/** Meeting action: the response is the new state, stored right away (the socket echo may follow). */
export function useMeetingAction<V>(teamId: string, fn: (vars: V) => Promise<Meeting>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (m) => putMeeting(qc, teamId, m),
    onError: (e) => {
      toast.error(e instanceof Error ? e.message : "Something went wrong")
      qc.invalidateQueries({ queryKey: meetingKey(teamId) })
    },
  })
}

export function clearEndedMeeting(qc: QueryClient, teamId: string) {
  qc.setQueryData(meetingKey(teamId), null)
  qc.invalidateQueries({ queryKey: meetingKey(teamId) })
}
