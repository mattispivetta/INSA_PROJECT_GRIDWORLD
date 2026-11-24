import pytest

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level


@pytest.mark.parametrize("action, x, y", [
    ("north", 1, 0), ("east", 2, 1), ("south", 1, 2), ("west", 0, 1),
])
def test_cardinal_move(engine, action, x, y):
    engine.apply_action(action)
    state = engine.get_state()
    assert (state["entities"][0]["x"], state["entities"][0]["y"]) == (x, y)
    assert state["turn"] == 1


def test_wall_blocks_but_consumes_turn(level_data, input_source, renderer):
    level_data["grid"][1] = "..#"
    engine = Engine(Level(level_data), Controller(input_source), renderer)
    before = engine.get_state()
    engine.apply_action("east")
    state = engine.get_state()
    assert state["entities"] == before["entities"]
    assert state["turn"] == 1


@pytest.mark.parametrize("action, x, y", [
    ("north", 1, 0), ("east", 2, 1), ("south", 1, 2), ("west", 0, 1),
])
def test_boundary_blocks_but_consumes_turn(level_data, input_source, renderer, action, x, y):
    level_data["start"] = {"x": x, "y": y}
    engine = Engine(Level(level_data), Controller(input_source), renderer)
    before = engine.get_state()
    engine.apply_action(action)
    state = engine.get_state()
    assert state["entities"] == before["entities"]
    assert state["turn"] == 1


def test_wait_consumes_turn_without_moving(engine):
    before = engine.get_state()
    engine.apply_action("wait")
    state = engine.get_state()
    assert state["entities"] == before["entities"]
    assert state["turn"] == 1


def test_invalid_action_preserves_state(engine):
    before = engine.get_state()
    with pytest.raises(ValueError):
        engine.apply_action("jump")
    assert engine.get_state() == before
