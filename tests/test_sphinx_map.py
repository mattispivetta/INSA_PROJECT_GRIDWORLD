"""The optional sphinx marker adds a public entity at the existing exit."""
import json
from pathlib import Path

import pytest

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level
from tests.helpers import RecordingRenderer, ScriptedInput


@pytest.mark.parametrize("marker", [None, False])
def test_map_without_sphinx_remains_ordinary(level_data, marker):
    if marker is not None:
        level_data["sphinx"] = marker
    level = Level(level_data)
    assert level.get_sphinx() is None
    assert level.is_exit(2, 2)


def test_supplied_sphinx_map_places_public_entity_on_exit():
    data = json.loads(Path("levels/sphinx.json").read_text())
    level = Level.load("levels/sphinx.json")
    assert data["sphinx"] is True
    assert level.get_sphinx() == {
        "id": "sphinx-1",
        "kind": "sphinx",
        "appearance": "sphinx",
        "x": data["exit"]["x"],
        "y": data["exit"]["y"],
    }
    assert level.get_sphinx()["x"] == 5
    assert level.get_sphinx()["y"] == 1
    assert level.is_exit(5, 1)
    assert Level.load("levels/n0.json").get_sphinx() is None
    assert set(data) == {"id", "grid", "start", "exit", "sphinx"}


def test_public_state_adds_sphinx_without_changing_other_fields(level_data):
    def make_engine(data):
        return Engine(Level(data), Controller(ScriptedInput([])), RecordingRenderer())

    ordinary = make_engine(level_data).get_state()
    level_data["sphinx"] = True
    engine = make_engine(level_data)
    state = engine.get_state()
    assert state["entities"] == [engine.level.get_sphinx(), engine.player.to_state()]
    assert {key: value for key, value in state.items() if key != "entities"} == {
        key: value for key, value in ordinary.items() if key != "entities"
    }
    assert engine.get_state() == state
    assert engine.player.get_position() == (1, 1)
    assert engine.turn == 0
