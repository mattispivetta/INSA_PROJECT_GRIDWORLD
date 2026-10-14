import sys

from gridworld.contracts import JsonState


class BashRender:
    """To complete. Only refresh is supplied and must remain unchanged."""

    def __init__(self) -> None:
        pass

    def start(self) -> None:
        pass
    
    def state_to_string(self, json_state: JsonState) -> str:
        def state_to_string(self, json_state: JsonState) -> str:
    level = json_state["level"]
    tiles = level["tiles"]

    # Convertir le terrain en caractères
    symbols = {
        "floor": ".",
        "wall": "#",
        "exit": "E"
    }

    # Créer une copie de la grille sous forme de caractères
    grid = []
    for row in tiles:
        new_row = []
        for tile in row:
            new_row.append(symbols.get(tile, "?"))
        grid.append(new_row)

    # Ajouter les entités sur la grille
    for entity in json_state["entities"]:
        x = entity["x"]
        y = entity["y"]

        if entity["id"] == json_state["player_id"]:
            symbol = "P"
        else:
            symbol = "?"

        # Vérifier que les coordonnées sont dans la grille
        if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
            grid[y][x] = symbol

    # Convertir chaque ligne en chaîne de caractères
    lines = []
    for row in grid:
        lines.append("".join(row))

    # Ajouter le numéro du tour et le message
    lines.append(f"Turn: {json_state['turn']}")
    lines.append(json_state["message"])

    # Renvoyer le résultat sans afficher directement
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
        pass
