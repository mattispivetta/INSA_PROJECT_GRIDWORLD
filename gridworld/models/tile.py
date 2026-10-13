# from gridworld.contracts import TileKind


# class Tile:
#     """To implement. Terrain without player or rendering logic."""

#     def __init__(self, kind: TileKind) -> None:
#         raise NotImplementedError("validate and store the tile kind")

#     def is_walkable(self) -> bool:
#         raise NotImplementedError("a wall tile is not walkable")

#     def is_exit(self) -> bool:
#         raise NotImplementedError("identify the exit")

#     def to_state(self) -> TileKind:
#         raise NotImplementedError("expose the terrain kind")

from gridworld.contracts import TileKind

_VALID_KINDS = ("floor", "wall", "exit")


class Tile:
    """Terrain without player or rendering logic."""

    def __init__(self, kind: TileKind) -> None:
        if kind not in _VALID_KINDS:
            raise ValueError(f"unknown tile kind: {kind!r}")
        self._kind = kind

    def is_walkable(self) -> bool:
        return self._kind != "wall"

    def is_exit(self) -> bool:
        return self._kind == "exit"

    def to_state(self) -> TileKind:
        return self._kind