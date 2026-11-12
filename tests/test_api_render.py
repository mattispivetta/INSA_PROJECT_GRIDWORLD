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
    """Supplied example: two reads must describe the same initial game."""
    first = client.get("/api/state")
    second = client.get("/api/state")
    assert first.status_code == second.status_code == 200
    assert first.json["state"]["turn"] == 0
    assert first.json["revision"] == 0
    assert second.json == first.json


def test_frame_format_and_headers(client):
    """Check the five fields, their types, the state and both HTTP headers."""
    pytest.fail("TODO: check the complete StateFrame contract")


def test_actions_and_turns(client):
    """Cover a free move, a blocked move and wait, checking turn and revision."""
    pytest.fail("TODO: check movement, collisions and waiting on N0")


def test_invalid_requests_preserve_the_frame(client):
    """Cover content type, malformed JSON, body shape, types and unknown actions."""
    # Use client.post(..., json=...) or data=... with content_type=... .
    # Compare the complete GET frame before and after each rejected request.
    pytest.fail("TODO: check error codes and absence of mutation")


def test_victory_then_quit(client):
    """Play the N0 route; check victory, ignored moves, quit, GET and later POSTs."""
    pytest.fail("TODO: check the game lifecycle and revision changes")


def test_independent_server_starts(api_engine):
    """Construct two applications and check their session IDs and revisions."""
    pytest.fail("TODO: check metadata for new server instances")


def test_concurrent_actions(api_engine):
    """Use one app and a separate test client in each ThreadPoolExecutor worker."""
    # Several wait requests should produce coherent frames with unique revisions.
    pytest.fail("TODO: check consistency when requests overlap")


def test_unavailable_engine_and_internal_error(api_engine, monkeypatch):
    """Check 503 for no engine and 500 without exposing internal error details."""
    # With TESTING=True, Flask propagates exceptions. For the 500 handler test,
    # set PROPAGATE_EXCEPTIONS=False on that test's app.
    pytest.fail("TODO: check unavailable engines and safe internal errors")
