// Company time zone. Never derive "today" from the browser: the server sends it (APP_NOW).
export const TZ = "America/Chicago"

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

/** "2026-11-09" -> "Nov 9". Date-only strings are calendar dates, not instants: no Date parsing. */
export function formatDay(d: string, withYear = false): string {
  const [y, m, day] = d.split("-").map(Number)
  return `${MONTHS[m - 1]} ${day}${withYear ? `, ${y}` : ""}`
}

const stamp = new Intl.DateTimeFormat("en-US", {
  timeZone: TZ, month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
})

/** ISO timestamp -> "Nov 11, 9:00 AM" in company time. */
export function formatStamp(iso: string): string {
  return stamp.format(new Date(iso))
}

/** Milliseconds -> "m:ss" (or "h:mm:ss"). */
export function formatDuration(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000))
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = String(total % 60).padStart(2, "0")
  return h ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`
}
