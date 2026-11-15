from gridworld.contracts import Action, JsonState, Renderer
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level

VALID_ACTIONS = {"north", "east", "south", "west", "wait", "quit"}

class Engine:
    """To implement. Game transitions without I/O, and game orchestration."""

    def __init__(self, level: Level, controller: Controller, renderer: Renderer) -> None:
        self.level = level
        self.controller = controller
        self.renderer = renderer
        self.player_position = self.level.get_start()
        self.turn=0
        self.status = "playing"
        self.message = ""
        #raise NotImplementedError("initialize the game without rendering or starting the view")

    def get_action(self) -> Action | None:
        return self.controller.get_action()
        #raise NotImplementedError("delegate to the controller")

    def apply_action(self, action: Action) -> None:
        if action not in VALID_ACTIONS:
            raise ValueError(f"Unknow action{action!r}:")
        if self.status != "playing" or action == "quit":
            return
        x, y = self.player_position
        if action == "north":
            nx, ny= x, y-1
        elif action == "east":
            nx, ny= x+1, y
        elif action == "south":
            nx, ny= x, y+1
        elif action == "west":
            nx, ny= x-1, y
        else:
            nx, ny= x, y
        if self.level.is_walkable(nx, ny):
            self.player_position = (nx, ny)
        self.turn += 1
        if self.level.is_exit(*self.player_position):
            self.status = "won"
            self.message = "Victory!"
        #raise NotImplementedError("apply a transition without input/output")

    def get_state(self) -> JsonState:
        x,y = self.player_position
        js : JsonState = {
            "level": self.level.to_state(),
            "entities": [
                {
                    "id": "player-1",
                    "kind": "player",
                    "x": x,
                    "y": y,
                    "appearance": "player"
                }
            ],
            "player_id": "player-1",
            "status": self.status,
            "turn": self.turn,
            "message": self.message,
            "interaction": None,
            "extras": {},
        }
        return js
        #raise NotImplementedError("build the shared JsonState: terrain, entities (player last), player_id, interaction=None in S0")

    def render(self, json_state: JsonState) -> None:
        self.renderer.update_render(json_state)
        #raise NotImplementedError("forward this state to the renderer")

    def run(self) -> None:
        self.render(self.get_state())
        while True:
            action_mnt = self.get_action()
            if action_mnt is None :
                continue
            elif action_mnt == "quit": 
                break
            self.apply_action(action_mnt)
            self.render(self.get_state())
        #raise NotImplementedError("render, then loop until quit without busy-waiting")
