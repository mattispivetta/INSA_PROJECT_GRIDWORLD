
import pytest

from gridworld.models.tile import Tile


def test_floor_is_walkable():
    tile = Tile("floor")

    assert tile.is_walkable() is True
    assert tile.is_exit() is False
    assert tile.to_state() == "floor"


def test_wall_is_not_walkable():
    tile = Tile("wall")

    assert tile.is_walkable() is False
    assert tile.is_exit() is False
    assert tile.to_state() == "wall"


def test_exit_is_walkable():
    tile = Tile("exit")

    assert tile.is_walkable() is True
    assert tile.is_exit() is True
    assert tile.to_state() == "exit"


@pytest.mark.parametrize("kind", ["water", "", None, 42])
def test_unknown_tile_raises_value_error(kind):
    with pytest.raises(ValueError):
        Tile(kind)
