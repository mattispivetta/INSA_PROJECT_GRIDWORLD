from gridworld.contracts import Action, InputSource


class Controller:
    def __init__(self, input_source: InputSource) -> None:
        self.input_source = input_source

    def key_to_action(self, key: str) -> Action | None:
        if key in ("z", "Z", "ArrowUp"):
            return "north"
        if key in ("d", "D", "ArrowRight"):
            return "east"
        if key in ("s", "S", "ArrowDown"):
            return "south"
        if key in ("q", "Q", "ArrowLeft"):
            return "west"
        if key == " ":
            return "wait"
        if key in ("Escape", ":quit"):
            return "quit"
        return None

    def get_action(self) -> Action | None:
        key = self.input_source.read_key()
        if key is None:
            return None
        return self.key_to_action(key)
