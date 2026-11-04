# tests/test_game_flow.py
import json
from pathlib import Path

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level

ROOT = Path(__file__).resolve().parent.parent
LEVEL_PATH = str(ROOT / "levels" / "n0.json")
INITIAL_STATE_PATH = ROOT / "initial_state.json"

# east, south, south, east, east, east, north, north
WINNING_KEYS = ["d", "s", "s", "d", "d", "d", "z", "z"]
QUIT = "Escape"


class ScriptedInput:
    """InputSource simulé : renvoie les touches du scénario, puis 'Escape'."""

    def __init__(self, keys):
        self._keys = iter(keys)
        self.reads = 0

    def read_key(self):
        self.reads += 1
        return next(self._keys, QUIT)


class RecordingRenderer:
    """Renderer qui enregistre chaque état reçu."""

    def __init__(self):
        self.states = []

    def start(self):
        pass

    def update_render(self, json_state):
        self.states.append(json_state)

    def close(self):
        pass


def run_scenario(keys):
    level = Level.load(LEVEL_PATH)
    inp = ScriptedInput(keys)
    renderer = RecordingRenderer()
    engine = Engine(level, Controller(inp), renderer)
    engine.run()
    return renderer, inp


def player_position(state):
    player = next(e for e in state["entities"] if e["id"] == state["player_id"])
    return (player["x"], player["y"])


def test_first_state_matches_initial_state_json():
    renderer, _ = run_scenario([QUIT])
    expected = json.loads(INITIAL_STATE_PATH.read_text())
    assert renderer.states[0] == expected


def test_winning_path():
    renderer, _ = run_scenario(WINNING_KEYS + [QUIT])
    final = renderer.states[-1]
    assert player_position(final) == (5, 1)
    assert final["turn"] == 8
    assert final["status"] == "won"
    assert final["message"] == "Victory!"


def test_blocked_move_keeps_position():
    # depuis (1,1), "north" mène dans un mur
    renderer, _ = run_scenario(["z", QUIT])
    assert player_position(renderer.states[-1]) == (1, 1)


def test_unknown_key_and_no_input_do_not_consume_turn():
    renderer, _ = run_scenario(["x", None, QUIT])
    assert len(renderer.states) == 1          # seulement l'état initial
    assert renderer.states[0]["turn"] == 0


def test_unknown_keys_between_moves_do_not_count():
    renderer, _ = run_scenario(["x", None, "d", "x", QUIT])
    assert renderer.states[-1]["turn"] == 1


def test_moves_and_wait_after_victory_leave_state_unchanged():
    renderer, _ = run_scenario(WINNING_KEYS + ["d", "s", " ", QUIT])
    final = renderer.states[-1]
    assert player_position(final) == (5, 1)
    assert final["turn"] == 8
    assert final["status"] == "won"


def test_loop_keeps_reading_after_victory_and_stops_on_quit():
    keys = WINNING_KEYS + ["d", " ", QUIT, "d"]
    renderer, inp = run_scenario(keys)
    assert inp.reads == len(keys) - 1         # la touche après quit n'est jamais lue
    assert renderer.states[-1]["turn"] == 8