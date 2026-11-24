"""Sphinx encounter and HTTP integration with supplied fakes; no real LLM."""
from copy import deepcopy
import json
from threading import Event
from time import monotonic, sleep

import pytest

from gridworld.api_render import create_app
from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.llm_support import fake_llm_json
from gridworld.models.level import Level
from gridworld.sphinx import Sphinx
from gridworld.web_support import FakeSphinx
from gridworld.views.bash_render import BashRender
from tests.helpers import RecordingRenderer, ScriptedInput


@pytest.fixture
def engine():
    game = Engine(Level.load("levels/sphinx.json"), Controller(ScriptedInput([])), RecordingRenderer())
    game.sphinx = Sphinx(ask=fake_llm_json)
    game.sphinx.get_question()
    return game


def encounter(engine):
    for _ in range(4):
        engine.apply_action("east")
    return engine.get_state()["interaction"]


def wait_for_verdict(client):
    deadline = monotonic() + 2
    while monotonic() < deadline:
        frame = client.get("/api/state").get_json()
        interaction = frame["state"]["interaction"]
        if interaction is None or interaction["status"] != "pending":
            return frame
        sleep(0.005)
    pytest.fail("The supplied background evaluator did not complete")


def test_encounter_keeps_player_before_exit(engine):
    interaction = encounter(engine)
    assert engine.player.get_position() == (4, 1)
    assert engine.status == "playing"
    assert engine.turn == 4
    assert interaction["status"] == "question"
    assert interaction["question"] == engine.sphinx.get_question()
    assert interaction["actor_id"] == "sphinx-1"
    assert interaction["id"]


@pytest.mark.parametrize("action", ["north", "east", "south", "west", "wait"])
def test_dialogue_pauses_movement_and_turns(engine, action):
    encounter(engine)
    before = deepcopy(engine.get_state())
    engine.apply_action(action)
    assert engine.get_state() == before


def test_rejection_publishes_hint_without_movement(engine):
    encounter(engine)
    engine.apply_sphinx_verdict({"correct": False, "message": "Think about a sound."})
    assert engine.player.get_position() == (4, 1)
    assert engine.status == "playing"
    assert engine.turn == 4
    assert engine.interaction["status"] == "rejected"
    assert engine.interaction["message"] == "Think about a sound."


def test_acceptance_moves_to_exit_and_wins(engine):
    encounter(engine)
    engine.apply_sphinx_verdict({"correct": True, "message": "Correct!"})
    assert engine.player.get_position() == (5, 1)
    assert engine.status == "won"
    assert engine.message == "Victory!"
    assert engine.interaction is None
    assert engine.turn == 4


def test_quit_remains_available_during_dialogue(engine):
    encounter(engine)
    engine.apply_action("quit")
    assert engine.running is False
    assert engine.interaction is None
    assert engine.turn == 4


def test_reading_state_does_not_generate_a_question_or_leak_private_data(engine):
    calls = []
    def ask(prompt, data, kind):
        calls.append(kind)
        return fake_llm_json(prompt, data, kind)
    engine.sphinx = Sphinx(ask=ask)
    engine.sphinx.get_question()
    encounter(engine)
    for _ in range(3):
        state = engine.get_state()
        assert state["interaction"]["question"] == "What repeats your words without a mouth?"
        encoded = json.dumps(state)
        assert "expected_answer" not in encoded
        assert "history" not in encoded
        assert "an echo" not in encoded
    assert calls == ["riddle"]


def test_http_wrong_answer_then_correct_answer(engine):
    client = create_app(engine).test_client()
    for _ in range(4):
        response = client.post("/api/actions", json={"action": "east"})
        assert response.status_code == 200
    interaction = response.get_json()["state"]["interaction"]
    response = client.post("/api/answer", json={"interaction_id": interaction["id"], "answer": "a clock"})
    assert response.status_code == 202
    assert response.get_json()["state"]["interaction"]["status"] == "pending"
    refused = wait_for_verdict(client)
    assert refused["state"]["interaction"]["status"] == "rejected"
    assert refused["state"]["interaction"]["message"] == "Think about a sound."
    assert engine.player.get_position() == (4, 1)
    assert engine.sphinx.history == [{"answer": "a clock", "hint": "Think about a sound."}]
    question = engine.sphinx.get_question()
    response = client.post("/api/answer", json={"interaction_id": interaction["id"], "answer": "an echo"})
    assert response.status_code == 202
    won = wait_for_verdict(client)
    assert won["state"]["status"] == "won"
    assert won["state"]["message"] == "Victory!"
    assert won["state"]["interaction"] is None
    assert engine.player.get_position() == (5, 1)
    assert engine.turn == 4
    assert engine.sphinx.history == []
    assert engine.sphinx.get_question() == question


def test_cancel_reuses_question_and_completed_history(engine):
    client = create_app(engine).test_client()
    interaction = encounter(engine)
    client.post("/api/answer", json={"interaction_id": interaction["id"], "answer": "a clock"})
    wait_for_verdict(client)
    history = deepcopy(engine.sphinx.history)
    question = engine.sphinx.get_question()
    assert client.post("/api/cancel", json={"interaction_id": interaction["id"]}).status_code == 200
    assert engine.interaction is None
    engine.apply_action("east")
    assert engine.interaction["question"] == question
    assert engine.interaction["id"] != interaction["id"]
    assert engine.sphinx.history == history


class SlowSphinx(FakeSphinx):
    started = Event()
    released = Event()
    finished = Event()

    def answer(self, text):
        self.started.set()
        if not self.released.wait(2):
            raise RuntimeError("Test did not release its fake")
        result = super().answer(text)
        self.finished.set()
        return result


@pytest.mark.parametrize("closing", ["cancel", "quit"])
def test_late_answer_cannot_win_after_closing(engine, closing):
    SlowSphinx.started.clear()
    SlowSphinx.released.clear()
    SlowSphinx.finished.clear()
    engine.sphinx = SlowSphinx()
    interaction = encounter(engine)
    client = create_app(engine).test_client()
    assert client.post("/api/answer", json={"interaction_id": interaction["id"], "answer": "x"}).status_code == 202
    assert SlowSphinx.started.wait(1)
    assert client.get("/api/state").get_json()["state"]["interaction"]["status"] == "pending"
    if closing == "cancel":
        closed = client.post("/api/cancel", json={"interaction_id": interaction["id"]})
    else:
        closed = client.post("/api/actions", json={"action": "quit"})
    expected = closed.get_json()
    SlowSphinx.released.set()
    assert SlowSphinx.finished.wait(1)
    sleep(0.02)
    assert client.get("/api/state").get_json() == expected
    assert engine.status == "playing"
    assert engine.player.get_position() == (4, 1)


def test_exported_dialogue_is_independent_of_engine_and_other_snapshots(engine):
    encounter(engine)
    first = engine.get_state()
    second = engine.get_state()
    first["interaction"]["question"] = "Changed outside the engine"
    first["interaction"]["status"] = "error"
    assert engine.get_state() == second
    assert second["interaction"]["status"] == "question"


def test_exported_dialogue_does_not_change_after_a_verdict(engine):
    encounter(engine)
    snapshot = engine.get_state()
    engine.apply_sphinx_verdict({"correct": False, "message": "A new hint"})
    assert snapshot["interaction"]["status"] == "question"
    assert snapshot["interaction"]["message"] == ""


def test_player_stays_visible_on_the_sphinx_exit_after_victory(engine):
    encounter(engine)
    engine.apply_sphinx_verdict({"correct": True, "message": "Correct!"})
    state = engine.get_state()
    assert state["entities"][-1]["id"] == state["player_id"]
    assert BashRender().state_to_string(state).splitlines()[1][5] == "P"
