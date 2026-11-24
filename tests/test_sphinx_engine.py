import json
from pathlib import Path
import threading
from gridworld.sphinx_service import (
    FakeSphinxService, InvalidServiceResponse, ServiceError, Verdict,
)
from gridworld.api_render import create_app
from gridworld.sphinx_service import FakeSphinxService, Verdict
from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level

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


def test_sphinx_is_visible_without_secret():
    engine = make_engine("levels/sphinx.json")
    state = engine.get_state()

    sphinxes = [e for e in state["entities"] if e["kind"] == "sphinx"]
    assert len(sphinxes) == 1
    assert sphinxes[0]["id"] == "sphinx-1"
    assert (sphinxes[0]["x"], sphinxes[0]["y"]) == (3, 1)
    assert state["entities"][-1]["id"] == state["player_id"]
    assert state["interaction"] is None

    raw = json.dumps(state)
    assert "expected_answer" not in raw
    assert "riddle" not in raw
    assert engine.riddle.expected_answer not in raw
    assert engine.riddle.question not in raw
    assert "expected_answer" not in json.dumps(state["level"])
    assert "expected_answer" not in json.dumps(state["extras"])


def test_n0_is_unchanged():
    state = make_engine("levels/n0.json").get_state()
    assert state["extras"] == {}
    assert all(e["kind"] != "sphinx" for e in state["entities"])
    initial = json.loads((ROOT / "initial_state.json").read_text())
    assert state == initial
def test_encounter_opens_dialogue_and_freezes_moves():
    engine = make_engine("levels/sphinx.json")
    engine.apply_action("east")
    engine.apply_action("east")

    state = engine.get_state()
    player = state["entities"][-1]
    assert (player["x"], player["y"]) == (2, 1)
    assert state["turn"] == 2

    interaction = state["interaction"]
    assert set(interaction) == {"id", "actor_id", "status", "question", "message"}
    assert interaction["status"] == "question"
    assert interaction["actor_id"] == "sphinx-1"
    assert interaction["question"] == engine.riddle.question
    assert "expected_answer" not in json.dumps(state)
    assert engine.riddle.expected_answer not in json.dumps(state)

    for action in ("east", "west", "north", "south", "wait"):
        engine.apply_action(action)
        assert engine.get_state() == state     # ni tour, ni position, ni id différent
class BlockingSphinxService:
    """Bloque judge() jusqu'à release(), pour observer l'état 'pending'."""
    def __init__(self):
        self.gate = threading.Event()
        self.calls = 0

    def create_riddle(self, theme):
        raise NotImplementedError

    def judge(self, riddle, answer):
        self.calls += 1
        self.gate.wait(timeout=5)
        return Verdict(True, "ignored")


def test_answer_returns_202_and_pending_then_409_on_second():
    engine = make_engine("levels/sphinx.json")
    service = BlockingSphinxService()
    client = create_app(engine, service).test_client()

    client.post("/api/actions", json={"action": "east"})   # ADAPTER : format réel de ta route
    client.post("/api/actions", json={"action": "east"})
    frame = client.get("/api/state").get_json()
    iid = frame["state"]["interaction"]["id"]

    r = client.post("/api/answer", json={"interaction_id": iid, "answer": "It is an echo."})
    assert r.status_code == 202
    assert r.get_json()["state"]["interaction"]["status"] == "pending"
    assert r.get_json()["state"]["turn"] == 2

    got = client.get("/api/state")                          # GET reste disponible
    assert got.status_code == 200
    assert got.get_json()["state"]["interaction"]["status"] == "pending"

    r2 = client.post("/api/answer", json={"interaction_id": iid, "answer": "again"})
    assert r2.status_code == 409
    assert r2.get_json()["error"]["code"] == "evaluation_pending"
    assert service.calls <= 1                               # pas de 2e jugement

    service.gate.set()  
def judge_like_api(engine, service, iid, answer="an echo"):
    """Reproduit ce que fait evaluate() dans api_render."""
    riddle, text, token = engine.begin_answer(iid, answer)
    try:
        verdict = service.judge(riddle, text)
    except ServiceError:
        verdict = None
    return engine.finish_evaluation(token, verdict)


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
    assert "Fake" not in json.dumps(state)             # Verdict.message jamais exposé
    assert engine.passage_open is (status == "accepted")


@pytest.mark.parametrize("outcome", ["rejected", "timeout", "unavailable", "invalid"])
def test_retry_after_refusal_or_failure_keeps_question(outcome):
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    question = engine.get_state()["interaction"]["question"]
    judge_like_api(engine, FakeSphinxService(outcome), iid)
    engine.apply_action("east")                        # passage fermé : rien ne bouge
    assert engine.get_state()["turn"] == 2
    judge_like_api(engine, FakeSphinxService("accepted"), iid)
    it = engine.get_state()["interaction"]
    assert it["status"] == "accepted"
    assert it["question"] == question


def test_string_false_is_not_a_valid_verdict():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    _, _, token = engine.begin_answer(iid, "x")
    engine.finish_evaluation(token, Verdict("false", "x"))   # chaîne, pas booléen
    assert engine.get_state()["interaction"]["status"] == "error"
    assert engine.passage_open is False


def test_accepted_then_three_east_reaches_victory():
    engine = make_engine("levels/sphinx.json")
    iid = open_dialogue(engine)
    judge_like_api(engine, FakeSphinxService("accepted"), iid)

    engine.apply_action("east")
    state = engine.get_state()
    assert state["interaction"] is None                # message d'acceptation effacé
    assert (state["entities"][-1]["x"], state["entities"][-1]["y"]) == (3, 1)
    assert state["turn"] == 3

    engine.apply_action("east")
    engine.apply_action("east")
    state = engine.get_state()
    assert state["turn"] == 5
    assert state["status"] == "won"
    assert state["message"] == "Victory!"       