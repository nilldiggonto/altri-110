import { defineConfig, devices } from "@playwright/test"

// Own ports and database, so a running dev stack (and its data) is left alone.
const API_PORT = process.env.E2E_API_PORT ?? "8020"
const WEB_PORT = process.env.E2E_WEB_PORT ?? "3020"
const DATABASE_URL = process.env.E2E_DATABASE_URL ?? "postgresql+psycopg://altri:altri@localhost:5432/altri_e2e"
const PY = process.env.E2E_PYTHON ?? ".venv/bin/python"
export const WEB_URL = `http://localhost:${WEB_PORT}`

export default defineConfig({
  testDir: "tests",
  timeout: 60_000,
  expect: { timeout: 5_000 },
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: WEB_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: [
    {
      // Fresh seed on every run; real (running) clock from APP_NOW so the meeting timer moves.
      command: [
        `${PY} -m app.db.ensure`,
        `${PY} -m alembic upgrade head`,
        `${PY} -m app.seed.load --reset`,
        `${PY} -m uvicorn app.main:app --port ${API_PORT} --log-level warning`,
      ].join(" && "),
      cwd: "../backend",
      url: `http://localhost:${API_PORT}/health`,
      env: {
        DATABASE_URL,
        APP_NOW: "2026-11-11T15:00:00Z",
        APP_CLOCK: "running",
        CORS_ORIGINS: JSON.stringify([WEB_URL]),
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npm run build && npx next start -p ${WEB_PORT}`,
      cwd: "../frontend",
      url: WEB_URL + "/login",
      env: { NEXT_PUBLIC_API_URL: `http://localhost:${API_PORT}`, NEXT_DIST_DIR: ".next-e2e" },
      reuseExistingServer: false,
      timeout: 240_000,
    },
  ],
})
