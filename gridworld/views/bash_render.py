import sys

from gridworld.contracts import JsonState


class BashRender:
    """To complete. Only refresh is supplied and must remain unchanged."""

    def __init__(self) -> None:
        raise NotImplementedError("initialize the terminal view")

    def start(self) -> None:
        raise NotImplementedError("initialize any resources or instance attributes")
    
    def state_to_string(self, json_state: JsonState) -> str:
        level = json_state["level"]
        tiles = level["tiles"]

        # Convertir le terrain en caractères
        symbols = {
            "floor": ".",
            "wall": "#",
            "exit": "E",
        }

        # Créer une grille indépendante de l'état original
        grid = [
            [symbols.get(tile, "?") for tile in row]
            for row in tiles
        ]

        # Superposer les entités dans l'ordre fourni
        for entity in json_state["entities"]:
            x = entity["x"]
            y = entity["y"]

            if entity["id"] == json_state["player_id"]:
                appearance = "P"
            else:
                appearance = entity["appearance"]

                # Les apparences inconnues sont représentées par ?
                if appearance not in ("floor", "wall", "exit", "player"):
                    appearance = "?"

            if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                grid[y][x] = appearance

        # Transformer la grille en texte
        lines = ["".join(row) for row in grid]

        # Ajouter le numéro du tour et le message
        lines.append(f"Turn: {json_state['turn']}")
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
        raise NotImplementedError("call state_to_string then refresh, once each")

    def close(self) -> None:
        raise NotImplementedError("close idempotently; a no-op is acceptable")
