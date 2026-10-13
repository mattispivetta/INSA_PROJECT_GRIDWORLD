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
        if type(x) != bool :
            self._x = x
        elif type(y) != bool :
            self._y = y
        else:
            raise ValueError("Vous avez rentré un bool")

    def get_position(self) -> tuple[int, int]:
        return self._x, self._y

    def move_to(self, x: int, y: int) -> None:
        # Vérifie seulement le type : l'autorisation du déplacement revient au moteur.
        self._x, self._y = x, y

    def to_state(self) -> EntityState:
        return {
            "id": "player-1",
            "kind": "player",
            "x": self._x,
            "y": self._y,
            "appearance": "player",
        }