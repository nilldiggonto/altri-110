// Session token in localStorage, readable with useSyncExternalStore.
const KEY = "altri.token"
const listeners = new Set<() => void>()

export function getToken(): string | null {
  return typeof window === "undefined" ? null : window.localStorage.getItem(KEY)
}

export function setToken(token: string | null) {
  if (token) window.localStorage.setItem(KEY, token)
  else window.localStorage.removeItem(KEY)
  listeners.forEach((l) => l())
}

export function subscribeToken(listener: () => void) {
  listeners.add(listener)
  window.addEventListener("storage", listener)
  return () => {
    listeners.delete(listener)
    window.removeEventListener("storage", listener)
  }
}

/** Full reload clears all client state, including routes kept alive by Activity. */
export function signOut() {
  setToken(null)
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- full reload on purpose (Activity keeps state)
  window.location.href = "/login"
}
