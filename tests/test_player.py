
import pytest

from gridworld.models.player import Player
from gridworld.models.level import Level
from pathlib import Path

N0_PATH = str(Path(__file__).resolve().parent.parent / "levels" / "n0.json")


def test_player_initial_position():
    player = Player(1, 1)

    assert player.get_position() == (1, 1)


def test_move_to_updates_position():
    player = Player(1, 1)

    player.move_to(2, 3)

    assert player.get_position() == (2, 3)


def test_players_are_independent():
    player1 = Player(1, 1)
    player2 = Player(2, 2)

    player1.move_to(3, 1)

    assert player1.get_position() == (3, 1)
    assert player2.get_position() == (2, 2)


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (True, 1),
        (1, False),
        (1.5, 2),
        (1, 2.5),
        ("1", 2),
        (1, None),
    ],
)
def test_invalid_position_raises_value_error(x, y):
    with pytest.raises(ValueError):
        Player(x, y)


#def test_move_to_invalid_position_does_not_change_position():
#    player = Player(1, 1)
#
#    with pytest.raises(ValueError):
#        player.move_to(True, 2)

#    assert player.get_position() == (1, 1)


def test_player_state():
    player = Player(1, 2)

    assert player.to_state() == {
        "id": "player-1",
        "kind": "player",
        "x": 1,
        "y": 2,
        "appearance": "player",
    }


def test_player_state_is_independent():
    player = Player(1, 2)

    state = player.to_state()
    state["x"] = 99

    assert player.get_position() == (1, 2)

def test_moving_player_does_not_change_level_start():
    level = Level.load("levels/n0.json")
    player = Player(*level.get_start())
    player.move_to(2, 3)
    assert level.get_start() == (1, 1)

@pytest.mark.parametrize(
    ("x", "y"),
    [(True, 2), (2, False), (1.5, 2), (2, 2.5), ("1", 2), (2, None)],
)
def test_move_to_invalid_values(x, y):
    player = Player(1, 1)

    with pytest.raises(ValueError):
        player.move_to(x, y)

    assert player.get_position() == (1, 1)
def test_moving_player_does_not_change_level_start():
    level = Level.load(N0_PATH)
    player = Player(*level.get_start())

    player.move_to(2, 3)

    assert player.get_position() == (2, 3)
    assert level.get_start() == (1, 1)