"use client"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

import { Button } from "@/components/ui/button"
import { useMe, useToken } from "@/lib/queries"
import { signOut } from "@/lib/token"

/** "/" sends you to sign in, or to your first team. */
export function HomeRedirect() {
  const { token, ready } = useToken()
  const me = useMe()
  const router = useRouter()
  const first = me.data?.teams[0]

  useEffect(() => {
    if (ready && !token) router.replace("/login")
    else if (first) router.replace(`/teams/${first.id}`)
  }, [ready, token, first, router])

  if (me.data && !first) {
    return (
      <main className="mx-auto max-w-md flex-1 px-4 py-24 text-center">
        <h1 className="text-lg font-semibold">You are not on any team yet</h1>
        <p className="mt-2 text-sm text-muted-foreground">Ask an Admin to add you, or sign in as someone else.</p>
        <Button className="mt-6" variant="outline" onClick={signOut}>Sign in as someone else</Button>
      </main>
    )
  }
  return <main className="flex-1" aria-busy="true" />
}
