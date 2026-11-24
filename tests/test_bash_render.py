from copy import deepcopy
import json
from pathlib import Path

from gridworld.views.bash_render import BashRender


def test_render_known_state_without_side_effects(capsys):
    state = json.loads(Path("initial_state.json").read_text())
    state["message"] = "Victory!"
    before = deepcopy(state)
    text = BashRender().state_to_string(state)
    assert text == "#######\n#P.#.E#\n#..#..#\n#.....#\n#######\nTurn: 0\nVictory!"
    assert state == before
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_entities_are_drawn_in_order():
    state = json.loads(Path("initial_state.json").read_text())
    state["entities"].insert(0, {"id": "unknown", "kind": "other", "appearance": "other", "x": 1, "y": 1})
    renderer = BashRender()
    assert renderer.state_to_string(state).splitlines()[1] == "#P.#.E#"
    state["entities"].reverse()
    assert renderer.state_to_string(state).splitlines()[1] == "#?.#.E#"


def test_update_converts_then_refreshes_once(monkeypatch):
    renderer = BashRender()
    state = {"message": "supplied state"}
    calls = []

    def convert(received):
        assert received is state
        calls.append("convert")
        return "display text"

    def refresh(text):
        calls.append(("refresh", text))

    monkeypatch.setattr(renderer, "state_to_string", convert)
    monkeypatch.setattr(renderer, "refresh", refresh)
    renderer.update_render(state)
    assert calls == ["convert", ("refresh", "display text")]


def test_close_can_be_called_twice():
    renderer = BashRender()
    renderer.start()
    renderer.close()
    renderer.close()
