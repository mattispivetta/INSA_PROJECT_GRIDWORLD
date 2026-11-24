from copy import deepcopy
import json

import pytest


@pytest.mark.parametrize("action", ["north", None, "quit"])
def test_engine_delegates_input_once(engine, monkeypatch, action):
    calls = []

    def get_action():
        calls.append("read")
        return action

    monkeypatch.setattr(engine.controller, "get_action", get_action)
    assert engine.get_action() == action
    assert calls == ["read"]


def test_engine_forwards_supplied_state_once(engine, renderer):
    supplied = {"message": "a state supplied by the caller"}
    engine.render(supplied)
    assert len(renderer.states) == 1
    assert renderer.states[0] is supplied


def test_state_contract_and_read_only_access(engine, input_source, renderer):
    state = engine.get_state()
    assert set(state) == {"level", "entities", "player_id", "status", "turn", "message", "interaction", "extras"}
    assert state["level"] == {
        "id": "small", "width": 3, "height": 3,
        "tiles": [["floor", "floor", "floor"], ["floor", "floor", "floor"], ["floor", "floor", "exit"]],
    }
    assert state["entities"] == [{"id": "player-1", "kind": "player", "appearance": "player", "x": 1, "y": 1}]
    assert state["player_id"] == "player-1"
    assert state["status"] == "playing"
    assert state["turn"] == 0
    assert state["message"] == ""
    assert state["interaction"] is None
    assert state["extras"] == {}
    assert json.loads(json.dumps(state)) == state
    assert engine.get_state() == state
    assert input_source.reads == 0
    assert renderer.states == []


def test_nested_snapshots_are_independent(engine, level):
    first = engine.get_state()
    second = engine.get_state()
    before = deepcopy(second)
    first["level"]["tiles"][0][0] = "wall"
    first["entities"][0]["x"] = 99
    first["extras"]["note"] = ["changed"]
    first["message"] = "changed"
    model_state = level.to_state()
    model_state["tiles"][1][1] = "wall"
    assert engine.get_state() == before
    assert second == before


def test_old_snapshot_does_not_follow_movement(engine):
    state = engine.get_state()
    engine.apply_action("east")
    assert state["entities"][0]["x"] == 1
    assert state["turn"] == 0
    assert engine.get_state()["entities"][0]["x"] == 2
