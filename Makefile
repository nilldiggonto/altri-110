.PHONY: up test rules-report rules-report-docker e2e
up:
	docker compose up --build
test:
	@echo "TODO"
# Fresh seed, then print the report. Override the date: make rules-report APP_NOW=2026-11-16T06:00:00Z
rules-report:
	cd backend && .venv/bin/python -m app.seed.load --reset >/dev/null && APP_NOW=$(or $(APP_NOW),2026-11-11T15:00:00Z) .venv/bin/python -m app.cli.rules_report

# Same, inside the running compose stack
rules-report-docker:
	docker compose exec backend sh -c "python -m app.seed.load --reset >/dev/null && APP_NOW=$(or $(APP_NOW),2026-11-11T15:00:00Z) python -m app.cli.rules_report"
e2e:
	@echo "TODO"
