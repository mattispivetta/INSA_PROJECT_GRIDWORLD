import json

import pytest

from gridworld.models.player import Player


def test_players_move_independently(level):
    first = Player(*level.get_start())
    second = Player(*level.get_start())
    first.move_to(0, 2)
    assert first.get_position() == (0, 2)
    assert second.get_position() == (1, 1)
    assert level.get_start() == (1, 1)


def test_player_exports_new_dictionary():
    player = Player(1, 2)
    state = player.to_state()
    assert state == {"id": "player-1", "kind": "player", "x": 1, "y": 2, "appearance": "player"}
    assert json.loads(json.dumps(state)) == state
    state["x"] = 99
    assert player.to_state()["x"] == 1


@pytest.mark.parametrize("x, y", [(True, 1), (1, False), (1.5, 1), (1, "2")])
def test_coordinates_must_be_integers(x, y):
    with pytest.raises(ValueError):
        Player(x, y)
    player = Player(1, 1)
    with pytest.raises(ValueError):
        player.move_to(x, y)
    assert player.get_position() == (1, 1)
