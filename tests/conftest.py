import pytest

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level
from tests.helpers import RecordingRenderer, ScriptedInput


@pytest.fixture
def level_data():
    return {
        "id": "small",
        "grid": ["...", "...", "..."],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 2, "y": 2},
    }


@pytest.fixture
def level(level_data):
    return Level(level_data)


@pytest.fixture
def input_source():
    return ScriptedInput([":quit"])


@pytest.fixture
def renderer():
    return RecordingRenderer()


@pytest.fixture
def engine(level, input_source, renderer):
    return Engine(level, Controller(input_source), renderer)
