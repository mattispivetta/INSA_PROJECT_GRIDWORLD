import pytest

from gridworld.models.tile import Tile


@pytest.mark.parametrize("kind, walkable, exit_tile", [
    ("floor", True, False),
    ("wall", False, False),
    ("exit", True, True),
])
def test_tile_kind(kind, walkable, exit_tile):
    tile = Tile(kind)
    assert tile.to_state() == kind
    assert tile.is_walkable() is walkable
    assert tile.is_exit() is exit_tile


def test_unknown_tile_kind():
    with pytest.raises(ValueError):
        Tile("water")
