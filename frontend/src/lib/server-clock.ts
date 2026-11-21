// The server owns time (it runs from APP_NOW, not the wall clock). Keep the offset between the
// server's now and this browser's now, refreshed from every message that carries server_now.
let offsetMs = 0

export function syncServerClock(serverNowIso: string, receivedAt = Date.now()) {
  offsetMs = Date.parse(serverNowIso) - receivedAt
}

export function serverNow(): number {
  return Date.now() + offsetMs
}
