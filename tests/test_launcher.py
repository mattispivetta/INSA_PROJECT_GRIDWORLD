# tests/test_launcher.py
import sys

import pytest

import gridworld.__main__ as launcher


class Recorder:
    """Garde la trace de ce que le lanceur crée et de l'ordre des appels."""

    def __init__(self):
        self.events = []          # "start", "run", "close" dans l'ordre
        self.created = []         # noms des composants instanciés
        self.level_paths = []     # chemins passés à Level.load
        self.engines = []         # moteurs créés
        self.renderers = []
        self.inputs = []
        self.run_error = None     # exception que engine.run() doit lever


@pytest.fixture
def rec(monkeypatch):
    r = Recorder()

    class FakeRenderer:
        name = "?"

        def __init__(self):
            r.created.append(self.name)
            r.renderers.append(self)

        def start(self):
            r.events.append("start")

        def update_render(self, json_state):
            pass

        def close(self):
            r.events.append("close")

    class FakeBashRender(FakeRenderer):
        name = "BashRender"

    class FakePygameRender(FakeRenderer):
        name = "PygameRender"

    class FakeTerminalInput:
        def __init__(self):
            r.created.append("TerminalInput")
            r.inputs.append(self)

        def read_key(self):
            raise AssertionError("le test ne doit pas lire le clavier")

    class FakePygameInput:
        def __init__(self, renderer):
            r.created.append("PygameInput")
            r.inputs.append(self)
            self.renderer = renderer

        def read_key(self):
            raise AssertionError("le test ne doit pas lire le clavier")

    class FakeLevel:
        @classmethod
        def load(cls, path):
            r.level_paths.append(path)
            return cls()

    class FakeEngine:
        def __init__(self, level, controller, renderer):
            self.level = level
            self.controller = controller
            self.renderer = renderer
            r.engines.append(self)

        def run(self):
            r.events.append("run")
            if r.run_error is not None:
                raise r.run_error

    monkeypatch.setattr(launcher, "BashRender", FakeBashRender)
    monkeypatch.setattr(launcher, "PygameRender", FakePygameRender)
    monkeypatch.setattr(launcher, "TerminalInput", FakeTerminalInput)
    monkeypatch.setattr(launcher, "PygameInput", FakePygameInput)
    monkeypatch.setattr(launcher, "Level", FakeLevel)
    monkeypatch.setattr(launcher, "Engine", FakeEngine)
    return r


def run_main(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["gridworld", *args])
    launcher.main()


def test_no_argument_selects_terminal_mode(rec, monkeypatch):
    run_main(monkeypatch)
    assert rec.created == ["BashRender", "TerminalInput"] or \
        sorted(rec.created) == ["BashRender", "TerminalInput"]
    assert "PygameRender" not in rec.created
    assert "PygameInput" not in rec.created


def test_render_terminal_selects_terminal_components(rec, monkeypatch):
    run_main(monkeypatch, "--render", "terminal")
    assert sorted(rec.created) == ["BashRender", "TerminalInput"]
    assert rec.engines[0].renderer is rec.renderers[0]
    assert rec.engines[0].controller._input_source is rec.inputs[0]


def test_render_pygame_selects_pygame_components(rec, monkeypatch):
    run_main(monkeypatch, "--render", "pygame")
    assert sorted(rec.created) == ["PygameInput", "PygameRender"]
    assert "BashRender" not in rec.created
    assert "TerminalInput" not in rec.created
    # l'entrée pygame est reliée au renderer pygame
    assert rec.inputs[0].renderer is rec.renderers[0]
    assert rec.engines[0].renderer is rec.renderers[0]


def test_default_level_is_n0(rec, monkeypatch):
    run_main(monkeypatch)
    assert rec.level_paths == ["levels/n0.json"]


def test_level_option_is_respected(rec, monkeypatch):
    run_main(monkeypatch, "--level", "levels/custom.json")
    assert rec.level_paths == ["levels/custom.json"]
    assert rec.engines[0].level is not None


def test_unsupported_renderer_is_rejected_before_startup(rec, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        run_main(monkeypatch, "--render", "opengl")
    assert exc.value.code != 0
    assert rec.created == []
    assert rec.level_paths == []
    assert rec.events == []


def test_renderer_starts_before_engine_and_closes_after(rec, monkeypatch):
    run_main(monkeypatch)
    assert rec.events == ["start", "run", "close"]


def test_renderer_is_closed_even_if_loop_raises(rec, monkeypatch):
    rec.run_error = RuntimeError("boom")
    with pytest.raises(RuntimeError, match="boom"):
        run_main(monkeypatch)
    assert rec.events == ["start", "run", "close"]