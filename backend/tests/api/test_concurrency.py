"""Concurrent requests against a real uvicorn server (threads, separate DB sessions).

TestClient serializes requests, so these tests start uvicorn in a subprocess on a free port, with the
same test database and frozen clock, and release N requests at once behind a barrier.
"""
import os
import socket
import subprocess
import sys
import threading
import time
from datetime import date
from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select

from app.models import Issue, Meeting
from tests.conftest import auth

BACKEND = Path(__file__).resolve().parents[2]
N = 12
WRITERS = ["u1", "u2", "u3", "u4"]  # Admin and Team Members of team_lead


@pytest.fixture(scope="module")
def server(migrated):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=BACKEND, env=os.environ.copy(),
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if httpx.get(url + "/health").status_code == 200:
                break
        except httpx.TransportError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("test server did not start")
    yield url
    proc.terminate()
    proc.wait(10)


def burst(url: str, method: str, path: str, n: int = N) -> list[httpx.Response]:
    """Fire n requests from n threads, released together, each from a writer of team_lead."""
    barrier = threading.Barrier(n)
    out: list[httpx.Response | Exception] = [None] * n

    def go(i: int) -> None:
        with httpx.Client(base_url=url, timeout=20) as c:
            barrier.wait()
            try:
                out[i] = c.request(method, path, headers=auth(WRITERS[i % len(WRITERS)]))
            except Exception as e:  # noqa: BLE001
                out[i] = e

    threads = [threading.Thread(target=go, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    errors = [r for r in out if isinstance(r, Exception)]
    assert not errors, errors
    return out


def test_concurrent_make_it_an_issue_returns_one_issue(server, db):
    m, week = "m3", "2026-11-02"  # off track, no open Issue in the seed
    assert db.scalar(select(func.count()).select_from(Issue).where(
        Issue.source_measurable_id == m, Issue.solved_at.is_(None))) == 0

    rs = burst(server, "POST", f"/api/teams/team_lead/measurables/{m}/scores/{week}/issue")

    assert {r.status_code for r in rs} <= {200, 201}, [r.text for r in rs]
    ids = {r.json()["issue"]["id"] for r in rs}
    assert len(ids) == 1
    assert sum(r.json()["created"] for r in rs) == 1
    rows = db.scalars(select(Issue).where(Issue.source_measurable_id == m, Issue.source_week_start == date.fromisoformat(week))).all()
    assert [i.id for i in rows] == list(ids)
    assert rows[0].title.endswith("week of Nov 2")


def test_make_it_an_issue_returns_existing_seeded_issue(server):
    # i5 is the seed's open Issue for m1, week of Nov 2.
    rs = burst(server, "POST", "/api/teams/team_lead/measurables/m1/scores/2026-11-02/issue", n=4)
    assert {r.json()["issue"]["id"] for r in rs} == {"i5"}
    assert not any(r.json()["created"] for r in rs)


def test_after_solving_a_new_issue_can_be_made(server, db):
    path = "/api/teams/team_lead/measurables/m3/scores/2026-11-02/issue"
    with httpx.Client(base_url=server) as c:
        first = c.post(path, headers=auth("u2")).json()["issue"]["id"]
        c.post(f"/api/teams/team_lead/issues/{first}/solve", json={"note": "fixed"}, headers=auth("u2"))
        second = c.post(path, headers=auth("u2")).json()
    assert second["created"] and second["issue"]["id"] != first


def test_concurrent_meeting_start_gives_one_meeting(server, db):
    rs = burst(server, "POST", "/api/teams/team_lead/meetings")
    codes = sorted(r.status_code for r in rs)
    assert codes.count(201) == 1 and set(codes) == {201, 409}, codes
    assert db.scalar(select(func.count()).select_from(Meeting).where(
        Meeting.team_id == "team_lead", Meeting.ended_at.is_(None))) == 1
