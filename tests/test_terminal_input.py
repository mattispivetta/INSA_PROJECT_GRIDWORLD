import pytest

from gridworld.controllers.terminal_input import TerminalInput


@pytest.mark.parametrize("text", [" ", "Z", ":quit", ""])
def test_terminal_preserves_input(monkeypatch, text):
    monkeypatch.setattr("builtins.input", lambda: text)
    assert TerminalInput().read_key() == text


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
def test_terminal_quits_on_interruption(monkeypatch, error):
    def interrupted_input():
        raise error()

    monkeypatch.setattr("builtins.input", interrupted_input)
    assert TerminalInput().read_key() == ":quit"
