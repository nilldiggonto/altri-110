"use client"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api, ApiError } from "@/lib/api"
import { useUsers } from "@/lib/queries"
import { setToken } from "@/lib/token"
import type { Role, User } from "@/lib/types"

export const ROLE_LABEL: Record<Role, string> = { admin: "Admin", team_member: "Team Member", observer: "Observer" }

export function LoginPicker() {
  const users = useUsers()
  const router = useRouter()
  const qc = useQueryClient()
  const login = useMutation({
    mutationFn: (userId: string) => api<{ token: string; user: User }>("/auth/login", { method: "POST", body: { user_id: userId } }),
    onSuccess: ({ token }) => {
      qc.clear()
      setToken(token)
      router.replace("/")
    },
  })

  if (users.isPending) {
    return (
      <div className="space-y-2" aria-busy="true">
        {Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-14 w-full" />)}
      </div>
    )
  }
  if (users.isError) {
    return (
      <div role="alert" className="flex items-center justify-between gap-4 rounded-lg border p-4 text-sm">
        <span>{users.error instanceof ApiError ? users.error.message : "Could not load users."}</span>
        <Button variant="outline" onClick={() => users.refetch()}>Retry</Button>
      </div>
    )
  }
  return (
    <ul className="divide-y rounded-lg border">
      {users.data.map((u) => (
        <li key={u.id}>
          <button
            type="button"
            disabled={login.isPending}
            onClick={() => login.mutate(u.id)}
            className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left outline-none hover:bg-muted focus-visible:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-60"
          >
            <span>
              <span className="block font-medium">{u.name}</span>
              <span className="block text-sm text-muted-foreground">{u.email}</span>
            </span>
            <Badge variant={u.role === "observer" ? "outline" : "secondary"}>{ROLE_LABEL[u.role]}</Badge>
          </button>
        </li>
      ))}
      {login.isError && <li role="alert" className="px-4 py-3 text-sm text-destructive">{login.error.message}</li>}
    </ul>
  )
}
