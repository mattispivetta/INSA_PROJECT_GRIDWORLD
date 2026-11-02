from gridworld.contracts import LevelState
from gridworld.models.tile import Tile


# class LevelError(ValueError):
#     """JSON loading error or violation of the map contract."""


# class Level:
#     """To implement. Terrain grid loaded from levels/n0.json."""

#     def __init__(self, data: dict) -> None:
#         raise NotImplementedError("validate the map and create its tiles")

#     @classmethod
#     def load(cls, path: str) -> "Level":
#         raise NotImplementedError("read JSON and convert errors to LevelError")

#     def get_start(self) -> tuple[int, int]:
#         raise NotImplementedError("return the starting coordinates")

#     def get_tile(self, x: int, y: int) -> Tile:
#         raise NotImplementedError("look up a tile; raise IndexError outside the grid")

#     def is_walkable(self, x: int, y: int) -> bool:
#         raise NotImplementedError("query the tile; return False outside the grid")

#     def is_exit(self, x: int, y: int) -> bool:
#         raise NotImplementedError("query the tile; return False outside the grid")

#     def to_state(self) -> LevelState:
#         raise NotImplementedError("create a new independent level state")


import json
from pathlib import Path


class LevelError(ValueError):
    """JSON loading error or violation of the map contract."""


class Level:
    """Terrain grid loaded from levels/n0.json."""

    def __init__(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise LevelError("Level data must be a dictionary")

        level_id = data.get("id")
        grid_data = data.get("grid")
        start_data = data.get("start")
        exit_data = data.get("exit")

        # Validate the level ID.
        if not isinstance(level_id, str) or not level_id:
            raise LevelError("id must be a non-empty string")

        # Validate the grid.
        if (
            not isinstance(grid_data, list)
            or not grid_data
            or any(not isinstance(row, str) or not row for row in grid_data)
        ):
            raise LevelError("grid must be a non-empty list of strings")

        width = len(grid_data[0])
        height = len(grid_data)

        if any(len(row) != width for row in grid_data):
            raise LevelError("All grid rows must have the same width")

        if any(char not in "#." for row in grid_data for char in row):
            raise LevelError("Grid may contain only '#' and '.'")

        # Validate start and exit coordinates.
        def parse_position(value: object, name: str) -> tuple[int, int]:
            if not isinstance(value, dict):
                raise LevelError(f"{name} must be a dictionary")

            x = value.get("x")
            y = value.get("y")

            if (
                isinstance(x, bool)
                or not isinstance(x, int)
                or isinstance(y, bool)
                or not isinstance(y, int)
            ):
                raise LevelError(
                    f"{name} coordinates must be integers"
                )

            if not (0 <= x < width and 0 <= y < height):
                raise LevelError(f"{name} is outside the grid")

            return x, y

        start = parse_position(start_data, "start")
        exit_pos = parse_position(exit_data, "exit")

        if start == exit_pos:
            raise LevelError("Start and exit must be different")

        if grid_data[start[1]][start[0]] != ".":
            raise LevelError("Start must be on a floor tile")

        if grid_data[exit_pos[1]][exit_pos[0]] != ".":
            raise LevelError("Exit must be on a floor tile")

        # Build the terrain grid.
        grid = []

        for y, row in enumerate(grid_data):
            tile_row = []

            for x, char in enumerate(row):
                if (x, y) == exit_pos:
                    kind = "exit"
                elif char == "#":
                    kind = "wall"
                else:
                    kind = "floor"

                try:
                    tile = Tile(kind)
                except (ValueError, TypeError) as exc:
                    raise LevelError(
                        f"Invalid tile at coordinates ({x}, {y})"
                    ) from exc

                tile_row.append(tile)

            grid.append(tile_row)

        self._id = level_id
        self._width = width
        self._height = height
        self._start = start
        self._exit = exit_pos
        self._grid = grid

    @classmethod
    def load(cls, path: str) -> "Level":
        """Load a level from a JSON file."""
        try:
            with Path(path).open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LevelError(
                f"Unable to load level from {path!r}"
            ) from exc

        try:
            return cls(data)
        except LevelError:
            raise
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise LevelError("Invalid level data") from exc

    def get_start(self) -> tuple[int, int]:
        """Return the immutable starting coordinates."""
        return self._start

    def get_tile(self, x: int, y: int) -> Tile:
        """Return a tile or raise IndexError outside the grid."""
        if (
            isinstance(x, bool)
            or not isinstance(x, int)
            or isinstance(y, bool)
            or not isinstance(y, int)
            or not (0 <= x < self._width and 0 <= y < self._height)
        ):
            raise IndexError(
                f"Tile coordinates out of bounds: ({x}, {y})"
            )

        return self._grid[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        """Return False for coordinates outside the grid."""
        try:
            return self.get_tile(x, y).is_walkable()
        except IndexError:
            return False

    def is_exit(self, x: int, y: int) -> bool:
        """Return False for coordinates outside the grid."""
        try:
            return self.get_tile(x, y).is_exit()
        except IndexError:
            return False

    def to_state(self) -> LevelState:
        """Return a new, independent JSON-compatible level state."""
        return {
            "id": self._id,
            "width": self._width,
            "height": self._height,
            "tiles": [
                [tile.to_state() for tile in row]
                for row in self._grid
            ],
        }