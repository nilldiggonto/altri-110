from tests.conftest import APP_NOW, auth


def test_seeded_and_frozen(client, frozen_clock):
    r = client.get("/api/teams/team_lead/issues", headers=auth("u2"))
    assert r.status_code == 200, r.text
    assert frozen_clock.now() == APP_NOW
