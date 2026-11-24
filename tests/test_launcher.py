import json
import sys

import pytest

from gridworld import __main__ as launcher
from gridworld.controllers import pygame_input
from gridworld.views import pygame_render
from tests.helpers import RecordingRenderer, ScriptedInput


@pytest.fixture
def components(monkeypatch):
    renderers = {"terminal": RecordingRenderer(), "pygame": RecordingRenderer()}
    inputs = []

    def terminal_source():
        inputs.append("terminal")
        return ScriptedInput([":quit"])

    def pygame_source(renderer):
        assert renderer is renderers["pygame"]
        inputs.append("pygame")
        return ScriptedInput([":quit"])

    # Replace both constructors before main can open a window or read input.
    monkeypatch.setattr(launcher, "BashRender", lambda: renderers["terminal"])
    monkeypatch.setattr(launcher, "TerminalInput", terminal_source)
    monkeypatch.setattr(pygame_render, "PygameRender", lambda: renderers["pygame"])
    monkeypatch.setattr(pygame_input, "PygameInput", pygame_source)
    return renderers, inputs


@pytest.mark.parametrize("arguments, mode", [
    ([], "terminal"), (["--render", "terminal"], "terminal"),
    (["--render", "pygame"], "pygame"),
])
def test_renderer_selection_and_lifecycle(monkeypatch, components, arguments, mode):
    renderers, inputs = components
    monkeypatch.setattr(sys, "argv", ["gridworld"] + arguments)
    launcher.main()
    assert inputs == [mode]
    assert renderers[mode].events == ["start", "render", "close"]
    assert renderers[mode].states[0]["level"]["id"] == "n0"
    other_mode = "pygame" if mode == "terminal" else "terminal"
    assert renderers[other_mode].events == []


def test_selected_level(monkeypatch, components, tmp_path, level_data):
    renderers, inputs = components
    level_data["id"] = "selected"
    level_data["start"] = {"x": 0, "y": 0}
    path = tmp_path / "selected.json"
    path.write_text(json.dumps(level_data), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["gridworld", "--level", str(path)])
    launcher.main()
    state = renderers["terminal"].states[0]
    assert state["level"]["id"] == "selected"
    assert (state["entities"][0]["x"], state["entities"][0]["y"]) == (0, 0)


def test_invalid_renderer_fails_before_startup(monkeypatch, components, capsys):
    renderers, inputs = components
    monkeypatch.setattr(sys, "argv", ["gridworld", "--render", "unknown"])
    with pytest.raises(SystemExit) as error:
        launcher.main()
    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
    assert inputs == []
    assert all(renderer.events == [] for renderer in renderers.values())


def test_help_lists_renderers(monkeypatch, components, capsys):
    renderers, inputs = components
    monkeypatch.setattr(sys, "argv", ["gridworld", "--help"])
    with pytest.raises(SystemExit) as error:
        launcher.main()
    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "--render {terminal,pygame}" in output
    assert "--level" in output
    assert inputs == []
    assert all(renderer.events == [] for renderer in renderers.values())


@pytest.mark.parametrize("mode", ["terminal", "pygame"])
def test_renderer_closes_when_loop_fails(monkeypatch, components, mode):
    renderers, inputs = components
    renderer = renderers[mode]

    def failing_run(engine):
        assert renderer.events == ["start"]
        raise RuntimeError("Game loop failed")

    monkeypatch.setattr(sys, "argv", ["gridworld", "--render", mode])
    monkeypatch.setattr(launcher.Engine, "run", failing_run)
    with pytest.raises(RuntimeError, match="Game loop failed"):
        launcher.main()
    assert inputs == [mode]
    assert renderer.events == ["start", "close"]
