from gridworld.contracts import EntityState


class Player:
    def __init__(self, x: int, y: int) -> None:
        self.move_to(x, y)

    def get_position(self) -> tuple[int, int]:
        return self.x, self.y

    def move_to(self, x: int, y: int) -> None:
        if type(x) is not int or type(y) is not int:
            raise ValueError("Player coordinates must be integers")
        self.x = x
        self.y = y

    def to_state(self) -> EntityState:
        return {
            "id": "player-1",
            "kind": "player",
            "x": self.x,
            "y": self.y,
            "appearance": "player",
        }
