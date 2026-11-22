# altri

A Team page (Scorecard, Issues, To-Dos, Rocks) and a real-time Level 10 Meeting page for a weekly leadership meeting. Next.js + TypeScript + shadcn/ui + Tailwind, FastAPI, Postgres with Alembic migrations.

- Decision record: [docs/DECISIONS.md](docs/DECISIONS.md)
- Rules report: [rules_report.json](rules_report.json)

## Run it

```bash
docker compose up --build
```
- Open http://localhost:3000. The API runs on http://localhost:8000, with docs at http://localhost:8000/docs.
- If ports 8000 or 3000 are taken, pick others: `API_PORT=8030 WEB_PORT=3030 docker compose up --build`.
- On start, the backend runs migrations and loads `data/seed.json`. The loader only inserts missing rows, so restarts keep your data and rerunning it is safe.
- To start from a clean seed: `docker compose exec backend python -m app.seed.load --reset`.
- Sign in by picking a seeded user. Blake Brooks (Team Member) or Avery Admin can run a meeting; Ellis Evans is an Observer.

**Local development** needs Postgres 14+ with an `altri`/`altri` user, Python 3.12 and Node 24.
```bash
cd backend && python -m venv .venv && .venv/bin/pip install -e '.[dev]' && cd ..
make api                                    # migrate, seed, API on :8000
cd frontend && npm ci && npm run dev        # http://localhost:3000
```

## Rules report

```bash
make rules-report                            # fresh seed, report at the default APP_NOW
make rules-report APP_NOW=2026-11-16T06:00:00Z
make rules-report-docker                     # the same, inside the compose stack
```
- The command reseeds the database, then prints every computed value from 2.6 as JSON, in the format from the zip's README.
- `rules_report.json` is its output at the default APP_NOW, and a test fails if the two drift apart.
- Every value is computed from the data for the given date.

## Tests

```bash
make test           # backend tests, then the Playwright e2e test (all unattended)
make test-backend   # rules, API authorization, concurrency only
make e2e            # Playwright only
```
These run locally: they need the Postgres, venv and Node setup from Local development, plus `npx playwright install chromium` once.

| Layer | Where | What |
|---|---|---|
| Rules | `backend/tests/rules/` | Every rule in 2.6 with its boundaries: goal edges, the Monday 00:00 Chicago week end (to the second, across the Nov 1 DST change), exactly 90%, due today, no Milestones, rounding 12.5 to 13 and 8.25 to 8.3. Plus the seed records that sit minutes from a week boundary. |
| API | `backend/tests/api/test_authz.py` | A Team Member reading or writing another team is refused (403), including guessed ids and the WebSocket. An Observer is refused on every write route. Only the facilitator controls the meeting. Invalid input gets 422. |
| Concurrency | `backend/tests/api/test_concurrency.py` | 12 parallel Make it an Issue requests against a live uvicorn server return one Issue id and leave one row. Parallel meeting starts give one meeting. |
| E2E | `e2e/tests/meeting-sync.spec.ts` | Two browser contexts as two users. The facilitator starts the meeting and advances through the agenda to the end; the second browser follows each step within 2 s, including after a reload. |

**Fixture and clock strategy**
- **Backend tests:**
  - They use their own database, `altri_test` (override with `TEST_DATABASE_URL`), created and migrated automatically.
  - Each test that touches data gets the seed freshly truncated and reloaded, so tests never depend on each other.
  - The clock is frozen at APP_NOW (`APP_CLOCK=frozen`). Rule tests are pure functions on hand-built facts, and the clock is reset after each test.
- **E2E:**
  - It starts its own API (:8020, database `altri_e2e`, reseeded every run) and a production frontend build (:3020), so a dev stack is left alone. Override with `E2E_*` env vars.
  - The clock starts at APP_NOW and runs in real time, so the meeting timer moves.

**Failure artifact:** [docs/artifacts/e2e-failure-trace.zip](docs/artifacts/e2e-failure-trace.zip) is a Playwright trace of both browsers from a deliberately failing run, where the follower expects the wrong section. Make it again with `make e2e-failure-artifact` and open it with `npx playwright show-trace docs/artifacts/e2e-failure-trace.zip`.

## Assumptions
- **Rules report at other dates (face value):** the freshly seeded database is the current state. APP_NOW moves "today", the current week and the 13-week window; records are not rolled back to that date.
  - For an earlier APP_NOW, a To-Do done after APP_NOW still counts as done for "overdue", and Issues and meetings recorded after it are still included.
  - Milestones have no done timestamp, so an "as of" reading could not be made consistent anyway.
  - The completion rate still counts only To-Dos done by the end of each week, as the rule says.
- **The week a meeting reviews:** a meeting's `scorecard_week` and summary statuses are for the last closed week at the meeting's start.
- **Scores:** a score can be edited for the current or any past week, but not a future one. Make it an Issue works only on an off-track cell.
- **Roles:** an Admin can open every team. A To-Do owner must be an Admin or Team Member of that team. Observers can join meetings but not rate them.
- **Ratings:** ratings open in Conclude and lock when the meeting ends.
- **Clock:** the app clock runs from APP_NOW and never reads the system date. After a restart it resumes from the latest stored timestamp.

## Known limitations
- The real-time hub is in-process, so there is one API instance; scaling out needs Postgres LISTEN/NOTIFY or Redis (see DECISIONS).
- Sign-in is a seeded user picker with a signed bearer token. There are no sessions, expiry or logout on the server, and the WebSocket token appears in the URL.
- Past meeting summaries are recomputed from live data, not snapshotted (the design is in DECISIONS 5).
- `make test` runs locally; there is no compose test service yet.
- Desktop and mobile widths were checked by hand in Chromium only.

## AI tools used
- **Claude Code (Anthropic), in VS Code, used throughout:** scaffolding, the schema and migrations, the rules and services, the API, the frontend components, tests, and drafts of this README and the decision record.
- I reviewed every change before committing, ran the tests, and checked the rules report values by hand against the seed.
