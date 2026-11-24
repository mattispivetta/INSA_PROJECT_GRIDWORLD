from copy import deepcopy

from gridworld.contracts import Action, JsonState, Renderer
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level
from gridworld.models.player import Player
from gridworld.web_support import new_interaction


class Engine:
    def __init__(self, level: Level, controller: Controller, renderer: Renderer) -> None:
        self.level = level
        self.controller = controller
        self.renderer = renderer
        self.player = Player(*level.get_start())
        self.status = "playing"
        self.turn = 0
        self.message = ""
        self.running = True
        self.sphinx = None
        self.interaction = None

    def get_action(self) -> Action | None:
        return self.controller.get_action()

    def apply_action(self, action: Action) -> None:
        if action not in ("north", "east", "south", "west", "wait", "quit"):
            raise ValueError(f"Unknown action: {action}")
        if action == "quit":
            self.running = False
            self.interaction = None
            return
        if self.status != "playing" or self.interaction is not None:
            return

        moves = {"north": (0, -1), "east": (1, 0),
                 "south": (0, 1), "west": (-1, 0)}
        if action in moves:
            x, y = self.player.get_position()
            dx, dy = moves[action]
            if self.sphinx is not None and self.level.is_exit(x + dx, y + dy):
                self.start_sphinx_dialogue()
                self.turn += 1
                return
            if self.level.is_walkable(x + dx, y + dy):
                self.player.move_to(x + dx, y + dy)
        self.turn += 1
        if self.level.is_exit(*self.player.get_position()):
            self.status = "won"
            self.message = "Victory!"

    def start_sphinx_dialogue(self) -> None:
        """Keep the player in place and publish the cached question."""
        self.interaction = new_interaction(self.sphinx)

    def apply_sphinx_verdict(self, verdict: dict) -> None:
        """Apply a checked answer without consuming another turn."""
        if verdict["correct"]:
            exit_guard = self.level.get_sphinx()
            self.player.move_to(exit_guard["x"], exit_guard["y"])
            self.interaction = None
            self.status = "won"
            self.message = "Victory!"
        else:
            self.interaction["status"] = "rejected"
            self.interaction["message"] = verdict["message"]

    def get_state(self) -> JsonState:
        entities = []
        sphinx = self.level.get_sphinx()
        if sphinx is not None:
            entities.append(sphinx)
        entities.append(self.player.to_state())
        return {
            "level": self.level.to_state(),
            "entities": entities,
            "player_id": "player-1",
            "status": self.status,
            "turn": self.turn,
            "message": self.message,
            "interaction": deepcopy(self.interaction),
            "extras": {},
        }

    def render(self, json_state: JsonState) -> None:
        self.renderer.update_render(json_state)

    def run(self) -> None:
        self.render(self.get_state())
        while self.running:
            action = self.get_action()
            if action is not None:
                self.apply_action(action)
                if self.running:
                    self.render(self.get_state())
