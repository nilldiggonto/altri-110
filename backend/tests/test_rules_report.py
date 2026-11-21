"""The committed rules_report.json matches what the command prints for a fresh seed at APP_NOW."""
import json
import os
import subprocess
import sys

from app.cli.rules_report import render
from app.core.clock import parse_utc
from app.core.config import ROOT
from app.services.report import rules_report
from tests.conftest import APP_NOW


def test_committed_report_is_current(db):
    assert render(db, APP_NOW) == (ROOT / "rules_report.json").read_text()


def test_command_prints_the_report(seeded):
    out = subprocess.run(
        [sys.executable, "-m", "app.cli.rules_report"], cwd=ROOT / "backend",
        env=os.environ.copy(), capture_output=True, text=True, check=True,
    ).stdout
    assert out == (ROOT / "rules_report.json").read_text()


def test_report_at_another_date_moves_the_window(db):
    # Monday 2026-11-16 00:00 Chicago: a new current week, everything computed from the data.
    r = rules_report(db, parse_utc("2026-11-16T06:00:00Z"))
    lead = r["teams"]["team_lead"]
    weeks = list(lead["measurable_status"]["m1"])
    assert weeks[0] == "2026-08-24" and weeks[-1] == "2026-11-16" and len(weeks) == 13
    assert list(lead["todo_completion"]) == weeks
    assert set(r["teams"]) == {"team_lead", "team_sales", "team_ops"}
    # A to-do due Nov 11-15 and not done is now overdue.
    assert set(json.loads((ROOT / "rules_report.json").read_text())["teams"]["team_lead"]["overdue_todos"]) <= set(
        lead["overdue_todos"])
