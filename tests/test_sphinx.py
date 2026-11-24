"""Exercise the conversation without Ollama, HTTP or a game engine."""
from copy import deepcopy

import pytest

from gridworld.llm_support import GENERATION_PROMPT, JUDGE_PROMPT, fake_llm_json
from gridworld.sphinx import Sphinx


def test_question_is_generated_once():
    calls = []

    def ask(prompt, data, kind):
        calls.append((prompt, deepcopy(data), kind))
        return fake_llm_json(prompt, data, kind)

    sphinx = Sphinx(ask=ask)
    question = sphinx.get_question()
    assert question == "What repeats your words without a mouth?"
    assert sphinx.get_question() == question
    assert calls == [(GENERATION_PROMPT, {}, "riddle")]
    assert sphinx.riddle["expected_answer"] == "an echo"


def test_wrong_answers_keep_history_and_question():
    sphinx = Sphinx(ask=fake_llm_json)
    question = sphinx.get_question()
    first = sphinx.answer("a clock")
    second = sphinx.answer("a stone")
    assert first["correct"] is False
    assert second["correct"] is False
    assert sphinx.history == [
        {"answer": "a clock", "hint": first["message"]},
        {"answer": "a stone", "hint": second["message"]},
    ]
    assert first["message"] != second["message"]
    assert sphinx.get_question() == question


def test_correct_answer_clears_history_without_regenerating():
    calls = []

    def ask(prompt, data, kind):
        calls.append(kind)
        return fake_llm_json(prompt, data, kind)

    sphinx = Sphinx(ask=ask)
    question = sphinx.get_question()
    sphinx.answer("a clock")
    assert sphinx.answer("an echo") == {"correct": True, "message": "Correct!"}
    assert sphinx.history == []
    assert sphinx.get_question() == question
    assert calls == ["riddle", "verdict", "verdict"]


def test_judge_receives_reference_player_text_and_previous_history():
    calls = []

    def ask(prompt, data, kind):
        calls.append((prompt, deepcopy(data), kind))
        return fake_llm_json(prompt, data, kind)

    sphinx = Sphinx(ask=ask)
    first = sphinx.answer("a clock")
    sphinx.answer("a stone")
    assert calls[1] == (JUDGE_PROMPT, {
        "question": sphinx.get_question(), "expected_answer": "an echo",
        "player_answer": "a clock", "history": [],
    }, "verdict")
    assert calls[2][1]["history"] == [{"answer": "a clock", "hint": first["message"]}]
    assert calls[2][1]["player_answer"] == "a stone"


def test_success_message_is_fixed_by_python():
    def ask(prompt, data, kind):
        if kind == "riddle":
            return fake_llm_json(prompt, data, kind)
        return {"correct": True, "message": "You found it!"}

    sphinx = Sphinx(ask=ask)
    assert sphinx.answer("an echo") == {"correct": True, "message": "Correct!"}


def test_failed_evaluation_keeps_completed_history():
    def ask(prompt, data, kind):
        if kind == "verdict" and data["player_answer"] == "unavailable":
            raise RuntimeError("Ollama unavailable")
        return fake_llm_json(prompt, data, kind)

    sphinx = Sphinx(ask=ask)
    sphinx.answer("a clock")
    history = deepcopy(sphinx.history)
    with pytest.raises(RuntimeError, match="Ollama unavailable"):
        sphinx.answer("unavailable")
    assert sphinx.history == history


def test_generation_failure_can_be_retried():
    calls = 0

    def ask(prompt, data, kind):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("Ollama unavailable")
        return fake_llm_json(prompt, data, kind)

    sphinx = Sphinx(ask=ask)
    with pytest.raises(RuntimeError):
        sphinx.get_question()
    assert sphinx.riddle is None
    assert sphinx.get_question() == "What repeats your words without a mouth?"
    assert calls == 2


def test_fresh_sphinx_has_independent_history():
    first = Sphinx(ask=fake_llm_json)
    first.answer("a clock")
    second = Sphinx(ask=fake_llm_json)
    assert second.riddle is None
    assert second.history == []
    assert len(first.history) == 1
