"""Regression checks for the supplied HTTP plumbing, outside student TODOs."""
import json
from pathlib import Path

import pytest

from gridworld.api_render import create_app
from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level
from tests.helpers import RecordingRenderer, ScriptedInput


@pytest.fixture
def client():
    engine = Engine(Level.load("levels/n0.json"), Controller(ScriptedInput([])), RecordingRenderer())
    return create_app(engine).test_client()


def test_initial_frame_matches_the_existing_n0_state(client):
    response = client.get("/api/state")
    frame = response.get_json()
    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.headers["Cache-Control"] == "no-store"
    assert set(frame) == {"protocol_version", "session_id", "revision", "running", "state"}
    assert frame["protocol_version"] == 1
    assert isinstance(frame["session_id"], str) and frame["session_id"]
    assert frame["revision"] == 0
    assert frame["running"] is True
    assert frame["state"] == json.loads(Path("initial_state.json").read_text())


def test_n0_winning_route_and_quit(client):
    for action in ["east", "south", "south", "east", "east", "east", "north", "north"]:
        response = client.post("/api/actions", json={"action": action})
        assert response.status_code == 200
    won = response.get_json()
    assert won["state"]["status"] == "won"
    assert won["state"]["message"] == "Victory!"
    assert won["state"]["turn"] == won["revision"] == 8
    assert client.post("/api/actions", json={"action": "wait"}).get_json() == won
    closed = client.post("/api/actions", json={"action": "quit"}).get_json()
    assert closed["running"] is False
    assert closed["state"] == won["state"]
    assert client.get("/api/state").get_json() == closed
    assert client.post("/api/actions", json={"action": "east"}).status_code == 409


@pytest.mark.parametrize("body, content_type, status", [
    ('{"action":"wait"}', "text/plain", 415),
    ('{', "application/json", 400),
    ('null', "application/json", 422),
    ('{"action":true}', "application/json", 422),
    ('{"action":"east","extra":1}', "application/json", 422),
    ('{"action":"teleport"}', "application/json", 422),
])
def test_invalid_requests_leave_the_game_unchanged(client, body, content_type, status):
    before = client.get("/api/state").get_json()
    response = client.post("/api/actions", data=body, content_type=content_type)
    assert response.status_code == status
    assert set(response.get_json()) == {"error"}
    assert client.get("/api/state").get_json() == before
