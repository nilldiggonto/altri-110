import { API_URL } from "@/lib/config"
import { getToken, signOut } from "@/lib/token"

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

function detailMessage(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  return `Request failed (${status})`
}

export async function api<T>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  const token = getToken()
  let res: Response
  try {
    res = await fetch(`${API_URL}/api${path}`, {
      method: init.method ?? "GET",
      headers: {
        ...(init.body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    })
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.")
  }
  if (res.status === 401 && token) signOut()
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, detailMessage(body?.detail, res.status))
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}
