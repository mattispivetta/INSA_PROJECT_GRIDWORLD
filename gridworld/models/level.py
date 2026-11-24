import json

from gridworld.contracts import EntityState, LevelState
from gridworld.models.tile import Tile


class LevelError(ValueError):
    """JSON loading error or violation of the map contract."""


class Level:
    def __init__(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise LevelError("The map must be a JSON object")
        if not isinstance(data.get("id"), str) or not data["id"]:
            raise LevelError("The map id must be a non-empty string")

        grid = data.get("grid")
        if not isinstance(grid, list) or not grid:
            raise LevelError("The grid must be a non-empty list of rows")
        for row in grid:
            if not isinstance(row, str) or not row:
                raise LevelError("Each grid row must be a non-empty string")
            if len(row) != len(grid[0]):
                raise LevelError("Grid rows must have the same width")
            if any(cell not in ".#" for cell in row):
                raise LevelError("The grid can only contain '.' and '#'")

        self.id = data["id"]
        self.width = len(grid[0])
        self.height = len(grid)
        for name in ("start", "exit"):
            position = data.get(name)
            if not isinstance(position, dict):
                raise LevelError(f"{name} must contain x and y coordinates")
            x, y = position.get("x"), position.get("y")
            if type(x) is not int or type(y) is not int:
                raise LevelError(f"{name} coordinates must be integers")
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise LevelError(f"{name} must be inside the grid")
            if grid[y][x] == "#":
                raise LevelError(f"{name} must be on a floor tile")

        self.sphinx_position = (
            (data["exit"]["x"], data["exit"]["y"])
            if data.get("sphinx", False) else None
        )
        self.start = (data["start"]["x"], data["start"]["y"])
        self.tiles = [
            [Tile("wall" if cell == "#" else "floor") for cell in row]
            for row in grid
        ]
        self.tiles[data["exit"]["y"]][data["exit"]["x"]] = Tile("exit")

    @classmethod
    def load(cls, path: str) -> "Level":
        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, ValueError) as error:
            raise LevelError(f"Cannot load {path}: {error}") from error
        return cls(data)

    def get_start(self) -> tuple[int, int]:
        return self.start

    def get_sphinx(self) -> EntityState | None:
        """Return a public sphinx on the exit, or None for an ordinary map."""
        if self.sphinx_position is None:
            return None
        x, y = self.sphinx_position
        return {
            "id": "sphinx-1",
            "kind": "sphinx",
            "x": x,
            "y": y,
            "appearance": "sphinx",
        }

    def get_tile(self, x: int, y: int) -> Tile:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError("Tile coordinates are outside the grid")
        return self.tiles[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.get_tile(x, y).is_walkable()

    def is_exit(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.get_tile(x, y).is_exit()

    def to_state(self) -> LevelState:
        return {
            "id": self.id,
            "width": self.width,
            "height": self.height,
            "tiles": [[tile.to_state() for tile in row] for row in self.tiles],
        }
