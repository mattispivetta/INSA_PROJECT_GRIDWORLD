import pytest

from tests.helpers import RecordingRenderer, ScriptedInput


def test_scripted_input_returns_each_key():
    source = ScriptedInput(["d", None, ":quit"])
    assert source.read_key() == "d"
    assert source.read_key() is None
    assert source.read_key() == ":quit"
    assert source.reads == 3


def test_scripted_input_fails_when_exhausted():
    source = ScriptedInput([])
    with pytest.raises(AssertionError, match="No scripted keys left"):
        source.read_key()


def test_renderers_do_not_share_recordings():
    first = RecordingRenderer()
    second = RecordingRenderer()
    state = {"turn": 0}
    first.start()
    first.update_render(state)
    first.close()
    assert first.events == ["start", "render", "close"]
    assert first.states == [state]
    assert second.states == []
    assert second.events == []


def test_fresh_game_can_quit(engine, renderer):
    engine.run()
    assert len(renderer.states) == 1
    assert renderer.states[0]["turn"] == 0
    assert renderer.states[0]["entities"][0]["x"] == 1
    assert renderer.states[0]["entities"][0]["y"] == 1


@pytest.mark.parametrize("action", ["east", "south"])
def test_game_fixture_starts_fresh(engine, renderer, action):
    assert engine.get_state()["turn"] == 0
    assert renderer.states == []
    engine.apply_action(action)
    engine.render(engine.get_state())
    assert renderer.states[0]["turn"] == 1
