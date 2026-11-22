# Decision record

## 1. Data model
- **Tables:** `companies`, `teams`, `users` (one role each: admin, team_member, observer), `memberships`, `measurables`, `scores` (key: measurable + week), `rocks`, `milestones`, `issues`, `todos`, `meetings`, `meeting_attendees`, `meeting_ratings`. Seed ids are kept; new rows get prefixed random ids.
- **Time:**
  - Timestamps are UTC `timestamptz`.
  - A week is the `date` of its Monday in company time, and a CHECK rejects any other weekday.
  - Due dates are plain company-time dates.
  - All conversion lives in `core/time.py`, which handles DST (the week of Oct 26 is 169 h).
- **Links:**
  - An Issue's source is the nullable pair (`source_measurable_id`, `source_week_start`), which is the Scorecard cell's natural key, so no link table is needed. A CHECK requires both or neither.
  - A To-Do links to its Issue with `source_issue_id`.
- **Database constraints:** priority 1 to 5, rating 1 to 10, non-blank titles, a solved Issue has a note, one active meeting per team, one unsolved Issue per cell.
- **Rules:** pure functions in `app/rules/`, shared by the API, the rules report and the tests.
- **Tradeoff:** the role is per user, not per team, which matches the seed. Per-team roles would move `role` onto `memberships`.

## 2. API design
- REST under `/api`, with OpenAPI at `/docs`. Team data lives under `/api/teams/{team_id}/...`, meetings under `/api/meetings/{id}`.
- **Authorization:** FastAPI dependencies on every route.
  - `TeamRead` gives the same 403 for another team and for a team that doesn't exist, so ids can't be probed.
  - `TeamWrite` refuses Observers.
  - Only the facilitator can advance or end a meeting.
  - Records are looked up inside the path's team, so another team's record returns 404.
- **Validation:** Pydantic models reject unknown fields and enforce lengths, ranges and no NaN. Database constraints back them up.
- **Idempotent writes:**
  - Advance takes `{"to": next}`, so a repeated click does nothing.
  - Join and rating are upserts.
  - A score edit is "last save wins".
- **Tradeoff:** sign-in is a seeded user picker with an HMAC bearer token, not real auth.

## 3. Real-time transport and meeting state
- **Transport:** one WebSocket per team, with the same access check as REST, done before the handshake completes. Every write goes through REST; the socket only pushes.
- **The server owns the state:**
  - The `meetings` row holds the section, `section_started_at` and a `version`.
  - Clients draw the timer from server time, correcting with a ping/pong offset.
  - An overrun shows as over time and never advances on its own.
  - Every meeting change, and every Issue or To-Do change during a meeting, bumps `version`. Clients keep the highest version they have seen, so a late older message never wins.
- **Recovery:**
  - Every connect starts with a full snapshot, which covers late joins, refreshes and reconnects (facilitator included).
  - Clients reconnect with backoff.
  - After a restart, the clock resumes from the latest stored timestamp.
- **Tradeoffs:**
  - The hub is in-process, which suits one API instance. Scaling out means fanning out through Postgres LISTEN/NOTIFY or Redis; the state is already in the database.
  - The token in the WS URL can show up in access logs; a short-lived ticket would fix that.

## 4. Duplicate-free Make it an Issue
- A partial unique index allows one unsolved Issue per (`source_measurable_id`, `source_week_start`) `WHERE solved_at IS NULL`.
- The service runs `INSERT ... ON CONFLICT DO NOTHING RETURNING`. One request inserts; the others read the winner's row (`created: false`). If the winner was solved in between, the request retries.
- The database arbitrates, so this holds across processes. `tests/api/test_concurrency.py` sends 12 parallel requests to a live server and asserts one id and one row.
- One active meeting per team uses the same pattern.

## 5. Keeping past summaries unchanged (described, not built)
- **Today:** summaries are recomputed from live data. Issues solved and To-Dos created between start and end are attributed by time window, plus attendees, ratings, and Measurable statuses for the reviewed week. So a later score edit would change an old summary.
- **Proposal:**
  - In the transaction that ends the meeting, write the summary as JSON to an immutable `meeting_summaries` row: no update route, and a trigger rejects UPDATE. It stores ids plus the titles at the time.
  - Ratings already lock at the end.
  - The summary endpoint reads the snapshot, and the seeded meetings get one at seed time.
  - The rules report keeps computing from the data, and a test checks the two agree on a fresh seed.
  - Storing `meeting_id` on solves and new To-Dos would also make the attribution exact, instead of by time window.
- **Tradeoff:** snapshots duplicate data and can't be corrected later, which is the point. An audit log of score and Issue changes, with summaries computed as of `ended_at`, is more flexible but much more work.
