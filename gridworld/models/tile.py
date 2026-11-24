from gridworld.contracts import TileKind


class Tile:
    def __init__(self, kind: TileKind) -> None:
        if kind not in ("floor", "wall", "exit"):
            raise ValueError(f"Unknown tile kind: {kind}")
        self.kind = kind

    def is_walkable(self) -> bool:
        return self.kind != "wall"

    def is_exit(self) -> bool:
        return self.kind == "exit"

    def to_state(self) -> TileKind:
        return self.kind
