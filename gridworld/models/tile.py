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


class Tile:
    """Terrain without player or rendering logic."""

    def __init__(self, kind: TileKind) -> None:
        if kind not in ("floor", "wall", "exit"):
            raise ValueError(f"Unknown tile kind: {kind!r}")

        self._kind: TileKind = kind

    def is_walkable(self) -> bool:
        """Return whether this tile can be crossed."""
        return self._kind in ("floor", "exit")

    def is_exit(self) -> bool:
        """Return whether this tile is an exit."""
        return self._kind == "exit"

    def to_state(self) -> TileKind:
        """Return the terrain kind."""
        return self._kind
