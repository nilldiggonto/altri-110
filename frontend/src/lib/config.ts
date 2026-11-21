// Inlined at build time (NEXT_PUBLIC_). The browser talks to the API directly.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "")
export const WS_URL = API_URL.replace(/^http/, "ws")
