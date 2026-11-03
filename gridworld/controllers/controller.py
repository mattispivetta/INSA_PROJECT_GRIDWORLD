from gridworld.contracts import Action, InputSource


class Controller:
    """To implement. Read a key and translate it into an action."""

    def __init__(self, input_source: InputSource) -> None:
        self._input_source = input_source

    def key_to_action(self, key: str) -> Action | None:
        if key=="z" or key=="Z" or key=="ArrowUp":
            return "north"
        elif key=="s" or key=="S" or key=="ArrowDown":
            return "south"
        elif key=="q" or key=="Q" or key=="ArrowLeft":
            return "west"
        elif key=="d" or key=="D" or key=="ArrowRight":
            return "east"
        elif key==" ":
            return "wait"
        elif key=="Escape" or key==":quit":
            return "quit"
        else:
            return None

    def get_action(self) -> Action | None:
        key = self._input_source.read_key()
        return self.key_to_action(key)
