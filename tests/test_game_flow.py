import json
from pathlib import Path

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level
from tests.helpers import ScriptedInput


def test_winning_route_and_input_after_victory(renderer):
    keys = [None, "?", "d", "s", "s", "d", "d", "d", "z", "z", "q", " ", None, ":quit"]
    source = ScriptedInput(keys)
    engine = Engine(Level.load("levels/n0.json"), Controller(source), renderer)
    engine.run()

    initial = json.loads(Path("initial_state.json").read_text())
    assert renderer.states[0] == initial
    won = renderer.states[8]
    assert (won["entities"][0]["x"], won["entities"][0]["y"]) == (5, 1)
    assert won["turn"] == 8
    assert won["status"] == "won"
    assert won["message"] == "Victory!"
    assert all(state == won for state in renderer.states[8:])
    assert engine.get_state() == won
    assert source.reads == len(keys)
    assert "start" not in renderer.events
    assert "close" not in renderer.events


def test_absent_unknown_blocked_and_waiting_input(renderer):
    source = ScriptedInput([None, "?", "q", " ", ":quit"])
    engine = Engine(Level.load("levels/n0.json"), Controller(source), renderer)
    engine.run()
    assert [state["turn"] for state in renderer.states] == [0, 1, 2]
    for state in renderer.states:
        player = state["entities"][0]
        assert (player["x"], player["y"]) == (1, 1)
    assert source.reads == 5


def test_quit_stops_before_the_next_key(level, renderer):
    source = ScriptedInput([":quit", "d"])
    engine = Engine(level, Controller(source), renderer)
    initial = engine.get_state()
    engine.run()
    assert source.reads == 1
    assert renderer.states == [initial]
    assert engine.get_state() == initial
