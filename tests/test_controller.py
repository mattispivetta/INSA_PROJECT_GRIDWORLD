import pytest

from gridworld.controllers.controller import Controller
from tests.helpers import ScriptedInput


@pytest.mark.parametrize("key, action", [
    ("z", "north"), ("Z", "north"), ("ArrowUp", "north"),
    ("d", "east"), ("D", "east"), ("ArrowRight", "east"),
    ("s", "south"), ("S", "south"), ("ArrowDown", "south"),
    ("q", "west"), ("Q", "west"), ("ArrowLeft", "west"),
    (" ", "wait"), ("Escape", "quit"), (":quit", "quit"),
    ("?", None), ("", None),
])
def test_key_mapping(key, action):
    controller = Controller(ScriptedInput([]))
    assert controller.key_to_action(key) == action


@pytest.mark.parametrize("key, action", [("d", "east"), (None, None), ("?", None), (":quit", "quit")])
def test_get_action_reads_once(key, action):
    source = ScriptedInput([key])
    controller = Controller(source)
    assert source.reads == 0
    assert controller.get_action() == action
    assert source.reads == 1
