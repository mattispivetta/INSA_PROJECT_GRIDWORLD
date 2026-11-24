import sys

from gridworld.contracts import JsonState


class BashRender:
    """Display the shared game state in the terminal."""

    def __init__(self) -> None:
        pass

    def start(self) -> None:
        pass

    def state_to_string(self, json_state: JsonState) -> str:
        symbols = {"floor": ".", "wall": "#", "exit": "E"}
        rows = [
            [symbols[tile] for tile in row]
            for row in json_state["level"]["tiles"]
        ]
        for entity in json_state["entities"]:
            symbol = "P" if entity["appearance"] == "player" else "?"
            rows[entity["y"]][entity["x"]] = symbol
        lines = ["".join(row) for row in rows]
        lines.append(f"Turn: {json_state['turn']}")
        if json_state["message"]:
            lines.append(json_state["message"])
        return "\n".join(lines)

    def refresh(self, text: str) -> None:
        """SUPPLIED: replace the ANSI terminal display without adding print calls.

        No resources or instance attributes are required. When output is
        redirected to a file, write plain text without control codes.
        """
        if not isinstance(text, str):
            raise TypeError("refresh expects a string")
        prefix = "\033[2J\033[H" if sys.stdout.isatty() else ""
        sys.stdout.write(prefix + text + ("" if text.endswith("\n") else "\n"))
        sys.stdout.flush()

    def update_render(self, json_state: JsonState) -> None:
        self.refresh(self.state_to_string(json_state))

    def close(self) -> None:
        pass
