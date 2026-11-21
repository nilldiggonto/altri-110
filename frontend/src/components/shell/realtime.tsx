"use client"
import { useQueryClient } from "@tanstack/react-query"
import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

import { WS_URL } from "@/lib/config"
import { putMeeting } from "@/lib/meeting"
import { keys } from "@/lib/queries"
import { syncServerClock } from "@/lib/server-clock"
import { getToken } from "@/lib/token"
import type { Meeting } from "@/lib/types"

export type LinkStatus = "connecting" | "live" | "offline"

type Message =
  | { type: "hello"; server_now: string; meeting: Meeting | null }
  | { type: "meeting"; meeting: Meeting }
  | { type: "changed"; sections: string[] }
  | { type: "pong"; server_now: string }

const RealtimeContext = createContext<LinkStatus>("connecting")
export const useLinkStatus = () => useContext(RealtimeContext)

// Teams this tab has had a socket for. Module level: it survives remounts and Activity hide/show,
// so any later hello (reconnect, coming back to a team) refetches what changed while we were away.
const connectedBefore = new Set<string>()

const PING_MS = 20_000
const MAX_BACKOFF_MS = 10_000

/**
 * One socket per open team. Opened only after the team loaded over REST (so access is known);
 * a refused socket looks like a network drop to the browser, so we just back off and retry.
 * Every (re)connect starts with a full "hello" snapshot; after a reconnect all team data is
 * refetched, since "changed" events sent while we were away are lost.
 */
export function RealtimeProvider({ teamId, children }: { teamId: string; children: ReactNode }) {
  const qc = useQueryClient()
  const [status, setStatus] = useState<LinkStatus>("connecting")

  useEffect(() => {
    let ws: WebSocket | null = null
    let closed = false
    let attempt = 0
    let retry: ReturnType<typeof setTimeout> | undefined
    let ping: ReturnType<typeof setInterval> | undefined

    function connect() {
      const token = getToken()
      if (!token) return
      if (attempt > 0) setStatus("connecting")
      ws = new WebSocket(`${WS_URL}/api/ws/teams/${encodeURIComponent(teamId)}?token=${encodeURIComponent(token)}`)
      ws.onopen = () => {
        attempt = 0
        setStatus("live")
        ping = setInterval(() => ws?.readyState === WebSocket.OPEN && ws.send(JSON.stringify({ type: "ping" })), PING_MS)
      }
      ws.onmessage = (ev) => {
        const receivedAt = Date.now()
        let msg: Message
        try { msg = JSON.parse(ev.data) } catch { return }
        switch (msg.type) {
          case "hello":
            syncServerClock(msg.server_now, receivedAt)
            putMeeting(qc, teamId, msg.meeting)
            if (connectedBefore.has(teamId)) qc.invalidateQueries({ queryKey: keys.team(teamId) })
            connectedBefore.add(teamId)
            break
          case "meeting":
            putMeeting(qc, teamId, msg.meeting)
            break
          case "changed":
            msg.sections.forEach((s) => qc.invalidateQueries({ queryKey: keys.section(teamId, s) }))
            break
          case "pong":
            syncServerClock(msg.server_now, receivedAt)
            break
        }
      }
      ws.onclose = () => {
        clearInterval(ping)
        if (closed) return
        setStatus("offline")
        const delay = Math.min(MAX_BACKOFF_MS, 500 * 2 ** attempt++) * (0.75 + Math.random() / 2)
        retry = setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      // Runs on unmount and when Activity hides the route; re-show reconnects with a fresh snapshot.
      closed = true
      clearTimeout(retry)
      clearInterval(ping)
      ws?.close()
    }
  }, [qc, teamId])

  return <RealtimeContext.Provider value={status}>{children}</RealtimeContext.Provider>
}
