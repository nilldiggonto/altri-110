.PHONY: api up test test-backend rules-report rules-report-docker e2e
# Local dev API on :8000 (docs at /docs)
api:
	cd backend && .venv/bin/alembic upgrade head && .venv/bin/python -m app.seed.load && .venv/bin/uvicorn app.main:app --reload --port 8000

up:
	docker compose up --build
# Backend tests: rules, API authz, concurrency (Postgres altri_test, frozen clock)
test-backend:
	cd backend && .venv/bin/pytest -q

test: test-backend
# Fresh seed, then print the report. Override the date: make rules-report APP_NOW=2026-11-16T06:00:00Z
rules-report:
	cd backend && .venv/bin/python -m app.seed.load --reset >/dev/null && APP_NOW=$(or $(APP_NOW),2026-11-11T15:00:00Z) .venv/bin/python -m app.cli.rules_report

# Same, inside the running compose stack
rules-report-docker:
	docker compose exec backend sh -c "python -m app.seed.load --reset >/dev/null && APP_NOW=$(or $(APP_NOW),2026-11-11T15:00:00Z) python -m app.cli.rules_report"
e2e:
	@echo "TODO"
