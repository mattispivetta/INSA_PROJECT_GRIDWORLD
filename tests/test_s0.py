import pytest
from gridworld.controllers.controller import Controller
from gridworld.models.player import Player


def test_level_fixture_independence(fresh_level):
    """Vérifie que la fixture fournit un objet Level valide."""
    assert fresh_level.get_start() == (1, 1)
    assert fresh_level.is_walkable(1, 1) is True


def test_player_initialization():
    """Vérifie la création d'un joueur et le refus des booléens."""
    player = Player(1, 2)
    assert player.get_position() == (1, 2)

    with pytest.raises(ValueError):
        Player(True, 2)


def test_fake_input_source_and_controller(make_input_source):
    """Vérifie l'interaction entre Controller et FakeInputSource."""
    inputs = make_input_source(["z", "s", "q", "d", " "])
    controller = Controller(inputs)

    assert controller.get_action() == "north"
    assert controller.get_action() == "south"
    assert controller.get_action() == "west"
    assert controller.get_action() == "east"
    assert controller.get_action() == "wait"


def test_fake_input_source_overflow_fails(make_input_source):
    """Vérifie que le FakeInputSource lève une exception en cas de dépassement."""
    inputs = make_input_source(["z"])
    assert inputs.read_key() == "z"

    with pytest.raises(RuntimeError, match="séquence de touches prédéfinies est vide"):
        inputs.read_key()


def test_recording_renderer(recording_renderer):
    """Vérifie que le renderer enregistre les états correctement."""
    mock_state = {
        "level": {"id": "l1", "width": 1, "height": 1, "tiles": [["floor"]]},
        "entities": [],
        "player_id": "p1",
        "status": "playing",
        "turn": 0,
        "message": "OK",
        "interaction": None,
        "extras": {},
    }
    
    recording_renderer.start()
    recording_renderer.update_render(mock_state)
    
    assert recording_renderer.is_started is True
    assert len(recording_renderer.history) == 1
    assert recording_renderer.history[0]["message"] == "OK"