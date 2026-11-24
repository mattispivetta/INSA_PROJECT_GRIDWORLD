"""Check the two engine connections through an in-process HTTP client."""
import pytest
from gridworld.api_render import create_app
from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.engine import Engine
from gridworld.models.level import Level
from gridworld.views.bash_render import BashRender


@pytest.fixture
def engine():
    level = Level({"id": "test", "grid": ["#####", "#...#", "#####"],
                   "start": {"x": 1, "y": 1}, "exit": {"x": 3, "y": 1}})
    return Engine(level, Controller(TerminalInput()), BashRender())


def test_get_does_not_advance_game(engine):
    client = create_app(engine).test_client()
    before = engine.get_state()
    first = client.get("/api/state")
    second = client.get("/api/state")
    assert first.status_code == 200
    assert first.get_json() == second.get_json()
    assert first.get_json()["state"] == before == engine.get_state()


def test_post_moves_player(engine):
    client = create_app(engine).test_client()
    response = client.post("/api/actions", json={"action": "east"})
    assert response.status_code == 200
    frame = response.get_json()
    assert engine.player.get_position() == (2, 1)
    assert engine.turn == 1
    assert frame["state"] == engine.get_state()
    assert client.get("/api/state").get_json() == frame
