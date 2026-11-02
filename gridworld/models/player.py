# from gridworld.contracts import EntityState


# class Player:
#     """To implement. Player position; collisions belong to the engine."""

#     def __init__(self, x: int, y: int) -> None:
#         raise NotImplementedError("store integer coordinates, excluding bool")

#     def get_position(self) -> tuple[int, int]:
#         raise NotImplementedError("return x, y")

#     def move_to(self, x: int, y: int) -> None:
#         raise NotImplementedError("update coordinates validated by the engine")

#     def to_state(self) -> EntityState:
#         raise NotImplementedError("return id=player-1, kind=player, x, y, appearance=player in a new dict")



from gridworld.contracts import EntityState


class Player:
    """Player position; collisions belong to the engine."""

    def __init__(self, x: int, y: int) -> None:
        if (type(x) != bool and type(y) != bool) and (type(x) == int and type(y) == int):
            self._x = x
            self._y = y
        else:
            raise ValueError("vous avez rentré un bool !")

    def get_position(self) -> tuple[int, int]:
        """Return the player's current coordinates."""
        return self._x, self._y

    def move_to(self, x: int, y: int) -> None:
        """Update the player's position without checking collisions."""
        if (type(x) != bool and type(y) != bool) and (type(x) == int and type(y) == int):
            self._x = x
            self._y = y
        else:
            raise ValueError("Le couple (x,y) n'est pas de la forme (int, int)")
        # return self._x, self._y

    def to_state(self) -> EntityState:
        """Return a new dictionary representing the player."""
        return {
            "id": "player-1",
            "kind": "player",
            "x": self._x,
            "y": self._y,
            "appearance": "player",
        }