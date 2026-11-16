
"""S2-01 API tests. Extend the example and replace every TODO failure."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from gridworld.api_render import create_app
from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level


class NoKeyboard:
    def read_key(self):
        raise AssertionError("HTTP tests must not read keyboard input")


class NoDisplay:
    def start(self):
        raise AssertionError("HTTP tests must not open a display")

    def update_render(self, state):
        raise AssertionError("HTTP tests must not render a local view")

    def close(self):
        pass


@pytest.fixture
def api_engine():
    path = Path(__file__).resolve().parents[1] / "levels" / "n0.json"
    return Engine(Level.load(str(path)), Controller(NoKeyboard()), NoDisplay())


@pytest.fixture
def client(api_engine):
    app = create_app(api_engine)
    app.config["TESTING"] = True
    return app.test_client()


def test_reading_does_not_advance_the_game(client):
    """Two reads must describe the same initial game."""
    first = client.get("/api/state")
    second = client.get("/api/state")

    assert first.status_code == second.status_code == 200
    assert first.json["state"]["turn"] == 0
    assert first.json["revision"] == 0
    assert second.json == first.json


def test_frame_format_and_headers(client):
    """Check the complete StateFrame contract."""
    response = client.get("/api/state")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.headers["Cache-Control"] == "no-store"

    frame = response.json

    assert set(frame.keys()) == {
        "state",
        "running",
        "session_id",
        "revision",
        "protocol_version",
    }

    assert isinstance(frame["state"], dict)
    assert isinstance(frame["running"], bool)
    assert isinstance(frame["session_id"], str)
    assert frame["revision"] == 0
    assert frame["protocol_version"] == 1

    assert set(frame["state"].keys()) == {
        "player",
        "enemies",
        "objects",
        "exit",
        "walls",
        "turn",
        "status",
        "message",
    }


def test_actions_and_turns(client):
    """Cover a free move, a blocked move and wait."""

    # First move east
    response = client.post("/api/actions", json={"action": "east"})

    assert response.status_code == 200
    assert response.json["state"]["turn"] == 1
    assert response.json["revision"] == 1

    # Move west: valid action, even if blocked by a wall
    response = client.post("/api/actions", json={"action": "west"})

    assert response.status_code == 200
    assert response.json["state"]["turn"] == 2
    assert response.json["revision"] == 2

    # Wait also consumes one turn
    response = client.post("/api/actions", json={"action": "wait"})

    assert response.status_code == 200
    assert response.json["state"]["turn"] == 3
    assert response.json["revision"] == 3


def test_invalid_requests_preserve_the_frame(client):
    """Check error codes and absence of mutation."""
    before = client.get("/api/state").json

    requests = [
        ({"data": "hello", "content_type": "text/plain"}, 415),
        ({"data": "{invalid json", "content_type": "application/json"}, 400),
        ({"json": ["east"]}, 400),
        ({"json": {}}, 422),
        ({"json": {"action": "east", "extra": 1}}, 422),
        ({"json": {"action": 123}}, 422),
        ({"json": {"action": "teleport"}}, 422),
    ]

    for kwargs, expected_status in requests:
        response = client.post("/api/actions", **kwargs)

        assert response.status_code == expected_status

        after = client.get("/api/state").json
        assert after == before


def test_victory_then_quit(client):
    """Check quit, GET and later POSTs."""

    # Check initial state
    initial = client.get("/api/state")
    assert initial.status_code == 200

    # Quit the game
    response = client.post("/api/actions", json={"action": "quit"})

    assert response.status_code == 200
    assert response.json["running"] is False
    assert response.json["revision"] == 1
    assert response.json["state"]["turn"] == 0

    # GET must still work after quit
    after_quit = client.get("/api/state")

    assert after_quit.status_code == 200
    assert after_quit.json == response.json

    # Further actions must be rejected
    rejected = client.post("/api/actions", json={"action": "east"})

    assert rejected.status_code == 409
    assert client.get("/api/state").json == after_quit.json


def test_independent_server_starts(api_engine):
    """Check metadata for new server instances."""

    app1 = create_app(api_engine)
    app2 = create_app(api_engine)

    client1 = app1.test_client()
    client2 = app2.test_client()

    frame1 = client1.get("/api/state").json
    frame2 = client2.get("/api/state").json

    assert frame1["session_id"] != frame2["session_id"]
    assert frame1["revision"] == 0
    assert frame2["revision"] == 0
    assert frame1["protocol_version"] == 1
    assert frame2["protocol_version"] == 1


def test_concurrent_actions(api_engine):
    """Check consistency when several requests overlap."""

    app = create_app(api_engine)

    def send_action(_):
        with app.test_client() as test_client:
            return test_client.post(
                "/api/actions",
                json={"action": "wait"},
            )

    with ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(send_action, range(5)))

    for response in responses:
        assert response.status_code == 200

    revisions = [response.json["revision"] for response in responses]

    assert sorted(revisions) == [1, 2, 3, 4, 5]

    with app.test_client() as test_client:
        final_frame = test_client.get("/api/state").json

    assert final_frame["revision"] == 5
    assert final_frame["state"]["turn"] == 5


def test_unavailable_engine_and_internal_error(api_engine, monkeypatch):
    """Check 503 and safe internal errors."""

    # Test unavailable engine
    app = create_app(None)
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        response = test_client.get("/api/state")
        assert response.status_code == 503

        response = test_client.post(
            "/api/actions",
            json={"action": "east"},
        )
        assert response.status_code == 503

    # Test internal server error
    app = create_app(api_engine)
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False

    def broken_state():
        raise RuntimeError("secret internal information")

    monkeypatch.setattr(api_engine, "get_state", broken_state)

    with app.test_client() as test_client:
        response = test_client.get("/api/state")

    assert response.status_code == 500
    assert "secret internal information" not in response.get_data(as_text=True)
