"use client"
import { createContext, useContext } from "react"

import type { Me, TeamDetail } from "@/lib/types"

export type TeamCtx = { teamId: string; detail: TeamDetail; me: Me; canWrite: boolean }

export const TeamContext = createContext<TeamCtx | null>(null)

export function useTeamCtx(): TeamCtx {
  const ctx = useContext(TeamContext)
  if (!ctx) throw new Error("useTeamCtx must be used inside TeamShell")
  return ctx
}
