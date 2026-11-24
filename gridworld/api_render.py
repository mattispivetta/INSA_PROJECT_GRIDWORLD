import json
import threading
import time
from pathlib import Path

import pytest

from gridworld.controllers.controller import Controller
from gridworld.engine import DialogueError, Engine
from gridworld.models.level import Level
from gridworld.sphinx_service import (
    FakeSphinxService,
    ServiceError,
    Verdict,
)

ROOT = Path(__file__).resolve().parent.parent


class NoInput:
    def read_key(self):
        return None


class NoRender:
    def start(self): pass
    def update_render(self, state): pass
    def close(self): pass


def make_engine(path):
    level = Level.load(str(ROOT / path))
    return Engine(level, Controller(NoInput()), NoRender())


def open_dialogue(engine):
    engine.apply_action("east")
    engine.apply_action("east")
    return engine.get_state()["interaction"]["id"]


def judge_like_api(engine, service, iid, answer="an echo"):
    riddle, text, token = engine.begin_answer(iid, answer)
    try:
        verdict = service.judge(riddle, text)
    except ServiceError:
        verdict = None
    return engine.finish_evaluation(token, verdict)


# ---------- Étape 1 ----------

def test_sphinx_is_visible_without_secret():
    engine = make_engine("levels/sphinx.json")
    state = engine.get_state()
    sphinxes = [e for e in state["entities"] if e["kind"] == "sphinx"]
    assert len(sphinxes) == 1
    assert (sphinxes[0]["x"], sphinxes[0]["y"]) == (3, 1)
    assert state["entities"][-1]["id"] == state["player_id"]
    assert state["interaction"] is None
    raw = json.dumps(state)
    assert "expected_answer" not in raw
    assert "riddle" not in raw
    assert engine.riddle.expected_answer not in raw


def test_n0_is_unchanged():
    state = make_engine("levels/n0.json").get_state()
    assert state["extras"] == {}
    assert all(e["kind"] != "sphinx" for e in state["entities"])


# ---------- Étape 2 ----------

def test_encounter_opens_dialogue_and_freezes_moves():
    engine = make_engine("levels/sphinx.json")
    engine.apply_action("east")
    engine.apply_action("east")
    state = engine.get_state()
    player = state["entities"][-1]
    assert (player["x"], player["y"]) == (2, 1)
    assert state["turn"] == 2
    it = state["interaction"]
    assert set(it) == {"id", "actor_id", "status", "question", "message"}
    assert it["status"] == "question"
    for action in ("east", "west", "north", "south", "wait"):
        engine.apply_action(action)
        assert engine.get_state() == state


# ---------- Étape 3 ----------

def test_begin_answer_goes_pending_without_changing_turn():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    engine.begin_answer(iid, "It is an echo.")
    state = engine.get_state()
    assert state["interaction"]["status"] == "pending"
    assert state["turn"] == 2


def test_second_answer_while_pending_is_refused():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    engine.begin_answer(iid, "one")
    with pytest.raises(DialogueError) as exc:
        engine.begin_answer(iid, "two")
    assert exc.value.code == "evaluation_pending"


def test_wrong_interaction_id_is_stale():
    engine = make_engine("levels/sphinx.json")
    open_dialogue(engine)
    with pytest.raises(DialogueError) as exc:
        engine.begin_answer("not-the-id", "x")
    assert exc.value.code == "stale_interaction"


def test_stale_token_is_ignored():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    engine.begin_answer(iid, "x")
    assert engine.finish_evaluation("old-token", Verdict(True, "x")) is False
    assert engine.get_state()["interaction"]["status"] == "pending"


# ---------- Étape 4 ----------

@pytest.mark.parametrize("outcome, status, message", [
    ("accepted", "accepted", "The passage is open."),
    ("rejected", "rejected", "That answer was not accepted. Try again."),
    ("timeout", "error", "The evaluator is unavailable. Try again."),
    ("unavailable", "error", "The evaluator is unavailable. Try again."),
    ("invalid", "error", "The evaluator is unavailable. Try again."),
])
def test_outcomes_give_fixed_public_messages(outcome, status, message):
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    assert judge_like_api(engine, FakeSphinxService(outcome), iid) is True
    state = engine.get_state()
    assert state["interaction"]["status"] == status
    assert state["interaction"]["message"] == message
    assert state["turn"] == 2
    assert "Fake" not in json.dumps(state)
    assert engine.passage_open is (status == "accepted")


@pytest.mark.parametrize("outcome", ["rejected", "timeout", "unavailable", "invalid"])
def test_retry_after_refusal_or_failure_keeps_question(outcome):
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    question = engine.get_state()["interaction"]["question"]
    judge_like_api(engine, FakeSphinxService(outcome), iid)
    engine.apply_action("east")
    assert engine.get_state()["turn"] == 2
    judge_like_api(engine, FakeSphinxService("accepted"), iid)
    it = engine.get_state()["interaction"]
    assert it["status"] == "accepted"
    assert it["question"] == question


def test_string_false_is_not_a_valid_verdict():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    _, _, token = engine.begin_answer(iid, "x")
    engine.finish_evaluation(token, Verdict("false", "x"))
    assert engine.get_state()["interaction"]["status"] == "error"
    assert engine.passage_open is False


def test_accepted_then_three_east_reaches_victory():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    judge_like_api(engine, FakeSphinxService("accepted"), iid)
    engine.apply_action("east")
    state = engine.get_state()
    assert state["interaction"] is None
    assert (state["entities"][-1]["x"], state["entities"][-1]["y"]) == (3, 1)
    assert state["turn"] == 3
    engine.apply_action("east")
    engine.apply_action("east")
    state = engine.get_state()
    assert state["turn"] == 5
    assert state["status"] == "won"
    assert state["message"] == "Victory!"


# ---------- Étape 5 ----------

def test_cancel_closes_dialogue_and_keeps_passage_closed():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    engine.cancel(iid)
    state = engine.get_state()
    assert state["interaction"] is None
    assert engine.passage_open is False
    assert state["turn"] == 2


def test_stale_verdict_after_cancel_and_new_encounter_is_ignored():
    engine = make_engine("levels/sphinx.json")
    old_iid = open_dialogue(engine)
    _, _, old_token = engine.begin_answer(old_iid, "an echo")
    engine.cancel(old_iid)
    engine.apply_action("east")
    before = engine.get_state()
    assert before["interaction"]["id"] != old_iid
    assert before["interaction"]["status"] == "question"
    assert engine.finish_evaluation(old_token, Verdict(True, "x")) is False
    assert engine.get_state() == before
    assert engine.passage_open is False


def test_quit_invalidates_pending_evaluation():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    _, _, token = engine.begin_answer(iid, "an echo")
    engine.apply_action("quit")
    assert engine.get_state()["interaction"] is None
    assert engine.finish_evaluation(token, Verdict(True, "x")) is False
    assert engine.passage_open is False


def test_cancel_with_wrong_id_or_after_acceptance_is_refused():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    with pytest.raises(DialogueError) as exc:
        engine.cancel("not-the-id")
    assert exc.value.code == "stale_interaction"
    judge_like_api(engine, FakeSphinxService("accepted"), iid)
    with pytest.raises(DialogueError) as exc:
        engine.cancel(iid)
    assert exc.value.code == "interaction_complete"
