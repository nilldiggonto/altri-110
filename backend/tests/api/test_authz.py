"""Server-side authorization: team boundaries, Observer writes, meeting control, input validation.

Seed roles: u1 Admin; u3 Team Member of team_lead only; u6 Team Member of team_sales only;
u5 Observer on team_lead.
"""
import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.security import issue_token
from tests.conftest import auth

LEAD = "/api/teams/team_lead"
OFF_TRACK = ("m3", "2026-11-02")  # off-track cell with no open Issue

TEAM_READS = ["", "/scorecard", "/issues", "/issues?solved=true", "/todos", "/rocks", "/meetings/active"]

TEAM_WRITES = [
    ("put", "/measurables/m1/scores/2026-11-09", {"value": 1}),
    ("delete", "/measurables/m1/scores/2026-11-02", None),
    ("post", f"/measurables/{OFF_TRACK[0]}/scores/{OFF_TRACK[1]}/issue", None),
    ("post", "/issues", {"title": "x"}),
    ("patch", "/issues/i1", {"priority": 1}),
    ("post", "/issues/i1/solve", {"note": "done"}),
    ("post", "/issues/i1/todos", {"title": "x", "owner_id": "u3"}),
    ("patch", "/todos/t12", {"done": True}),
    ("post", "/meetings", None),
]


def call(client, method, path, body, user):
    kw = {"headers": auth(user)}
    if body is not None:
        kw["json"] = body
    return getattr(client, method)(path, **kw)


# Team boundaries

@pytest.mark.parametrize("path", TEAM_READS)
def test_member_cannot_read_other_team(client, path):
    assert client.get(LEAD + path, headers=auth("u6")).status_code == 403


@pytest.mark.parametrize("team", ["team_lead", "team_nope", "x" * 64])
def test_guessed_team_id_gets_same_refusal(client, team):
    r = client.get(f"/api/teams/{team}/issues", headers=auth("u6"))
    assert r.status_code == 403 and r.json()["detail"] == "No access to this team"


def test_member_reads_own_team_and_admin_reads_all(client):
    assert client.get("/api/teams/team_sales/issues", headers=auth("u6")).status_code == 200
    for team in ("team_lead", "team_sales", "team_ops"):
        assert client.get(f"/api/teams/{team}/issues", headers=auth("u1")).status_code == 200


@pytest.mark.parametrize("method, path, body", TEAM_WRITES)
def test_member_cannot_write_other_team(client, method, path, body):
    assert call(client, method, LEAD + path, body, "u6").status_code == 403


def test_other_teams_records_not_reachable_through_own_team(client):
    # i1, t12 and m1 belong to team_lead; u6 uses their own team's path.
    sales = "/api/teams/team_sales"
    assert call(client, "patch", sales + "/issues/i1", {"priority": 1}, "u6").status_code == 404
    assert call(client, "patch", sales + "/todos/t12", {"done": True}, "u6").status_code == 404
    assert call(client, "put", sales + "/measurables/m1/scores/2026-11-09", {"value": 1}, "u6").status_code == 404


def test_other_teams_meeting_refused(client):
    for path in ("", "/summary", "/join"):
        method = "post" if path == "/join" else "get"
        assert call(client, method, f"/api/meetings/mt1{path}", None, "u6").status_code == 403
    assert client.get("/api/meetings/mt_guess", headers=auth("u6")).status_code == 403


def test_teams_listed_in_me_follow_membership(client):
    assert sorted(t["id"] for t in client.get("/api/me", headers=auth("u6")).json()["teams"]) == ["team_sales"]


def test_websocket_refused_for_other_team(client):
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/api/ws/teams/team_lead?token={issue_token('u6')}"):
            pass
    assert e.value.code == 1008


# Sign-in

@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer u1.forged"}, {"Authorization": "Bearer junk"}])
def test_missing_or_forged_token_is_401(client, headers):
    assert client.get(LEAD + "/issues", headers=headers).status_code == 401


# Observer

@pytest.mark.parametrize("method, path, body", TEAM_WRITES)
def test_observer_write_refused(client, method, path, body):
    r = call(client, method, LEAD + path, body, "u5")
    assert r.status_code == 403 and r.json()["detail"] == "Observers cannot change data"


def test_observer_write_changes_nothing(client):
    before = client.get(LEAD + "/issues", headers=auth("u5")).json()
    call(client, "post", LEAD + "/issues", {"title": "sneaky"}, "u5")
    call(client, "post", LEAD + "/issues/i1/solve", {"note": "x"}, "u5")
    assert client.get(LEAD + "/issues", headers=auth("u5")).json() == before


def test_observer_can_read_and_join_but_not_rate(client):
    assert client.get(LEAD + "/scorecard", headers=auth("u5")).status_code == 200
    mt = call(client, "post", LEAD + "/meetings", None, "u3").json()["id"]
    assert call(client, "post", f"/api/meetings/{mt}/join", None, "u5").status_code == 200
    call(client, "post", f"/api/meetings/{mt}/advance", {"to": "ids"}, "u3")
    call(client, "post", f"/api/meetings/{mt}/advance", {"to": "conclude"}, "u3")
    assert call(client, "put", f"/api/meetings/{mt}/rating", {"rating": 9}, "u5").status_code == 403


# Meeting control

@pytest.fixture
def meeting(client):
    r = call(client, "post", LEAD + "/meetings", None, "u3")
    assert r.status_code == 201 and r.json()["facilitator_id"] == "u3"
    return r.json()["id"]


def test_only_facilitator_advances_or_ends(client, meeting):
    for user in ("u1", "u2", "u5"):  # Admin, Team Member, Observer of the team
        assert call(client, "post", f"/api/meetings/{meeting}/advance", {"to": "ids"}, user).status_code == 403
        assert call(client, "post", f"/api/meetings/{meeting}/end", None, user).status_code == 403
    assert call(client, "post", f"/api/meetings/{meeting}/advance", {"to": "ids"}, "u3").status_code == 200
    assert call(client, "post", f"/api/meetings/{meeting}/end", None, "u3").status_code == 200


def test_one_active_meeting_per_team(client, meeting):
    assert call(client, "post", LEAD + "/meetings", None, "u2").status_code == 409


# Input validation

@pytest.mark.parametrize(
    "method, path, body",
    [
        ("post", "/issues", {}),
        ("post", "/issues", {"title": "   "}),
        ("post", "/issues", {"title": "x" * 301}),
        ("post", "/issues", {"title": "x", "priority": 6}),
        ("post", "/issues", {"title": "x", "priority": 0}),
        ("post", "/issues", {"title": "x", "owner_id": "u1"}),  # owner is always the creator
        ("patch", "/issues/i1", {"priority": "high"}),
        ("post", "/issues/i1/solve", {}),
        ("post", "/issues/i1/solve", {"note": " "}),
        ("post", "/issues/i1/todos", {"title": "x", "owner_id": "u5"}),  # Observer cannot own
        ("post", "/issues/i1/todos", {"title": "x", "owner_id": "u6"}),  # not on this team
        ("put", "/measurables/m1/scores/2026-11-10", {"value": 1}),  # not a Monday
        ("put", "/measurables/m1/scores/2026-11-16", {"value": 1}),  # future week
        ("put", "/measurables/m1/scores/2026-11-09", {"value": "NaN"}),
        ("put", "/measurables/m1/scores/not-a-date", {"value": 1}),
        ("post", "/measurables/m2/scores/2026-11-02/issue", None),  # on track, not off track
    ],
)
def test_invalid_input_is_422(client, method, path, body):
    assert call(client, method, LEAD + path, body, "u3").status_code == 422


@pytest.mark.parametrize("rating", [0, 11, 7.5, None])
def test_rating_out_of_range_is_422(client, meeting, rating):
    assert call(client, "put", f"/api/meetings/{meeting}/rating", {"rating": rating}, "u3").status_code == 422


def test_advance_to_unknown_section_is_422(client, meeting):
    assert call(client, "post", f"/api/meetings/{meeting}/advance", {"to": "lunch"}, "u3").status_code == 422
