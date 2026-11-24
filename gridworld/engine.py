from gridworld.contracts import Action, JsonState, Renderer
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level
from gridworld.sphinx_service import Riddle, Verdict
from uuid import uuid4

VALID_ACTIONS = {"north", "east", "south", "west", "wait", "quit"}
MOVES = {"north": (0, -1), "east": (1, 0), "south": (0, 1), "west": (-1, 0), "wait": (0, 0)}
BLOCKING_STATUSES = {"question", "pending", "rejected", "error"}
MSG_ACCEPTED = "The passage is open."
MSG_REJECTED = "That answer was not accepted. Try again."
MSG_ERROR = "The evaluator is unavailable. Try again."


class DialogueError(Exception):
    """Refus métier, traduit en erreur HTTP par api_render."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

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
        self.sphinx = self.level.get_sphinx()
    if self.sphinx is None:
        self.riddle = None
        self.passage_open = True
    else:
        r = self.sphinx["riddle"]
        self.riddle = Riddle(
            id=r["id"],
            question=r["question"],
            expected_answer=r["expected_answer"],
        )
        self.passage_open = False
    self.interaction = None
    self._eval_token = None   # jeton de l'évaluation en cours (privé, jamais exposé)   # dict public tant qu'un dialogue est actif, sinon None
        #raise NotImplementedError("initialize the game without rendering or starting the view")

    def get_action(self) -> Action | None:
        return self.controller.get_action()
        #raise NotImplementedError("delegate to the controller")

    def apply_action(self, action: Action) -> None:
        if action not in VALID_ACTIONS:
            raise ValueError(f"Unknown action {action!r}")
        if action == "quit":
            self.abort_dialogue()      # quitter efface le dialogue et invalide l'évaluation
            return
        if self.status != "playing":
            return

        # Dans le dialogue : déplacements et wait ne changent rien (ni tour, ni état).
        if self.interaction is not None and self.interaction["status"] in BLOCKING_STATUSES:
            return
            # Passage ouvert : le premier pas efface le dialogue et son message.
        if self.interaction is not None and self.interaction["status"] == "accepted":
            self.interaction = None

        dx, dy = MOVES[action]
        x, y = self.player_position
        nx, ny = x + dx, y + dy

    # Tentative d'entrer sur le sphinx alors que le passage est fermé : rencontre.
        if (
            self.sphinx is not None
            and not self.passage_open
            and (nx, ny) == (self.sphinx["x"], self.sphinx["y"])
        ):
            self.turn += 1
            self._eval_token = None                     # la tentative consomme un tour
            self.interaction = {
                "id": uuid4().hex,             # nouvel identifiant à chaque rencontre
                "actor_id": self.sphinx["id"],
                "status": "question",
                "question": self.riddle.question,
                "message": "",
            }
            return                             # le joueur ne bouge pas

        if self.level.is_walkable(nx, ny):
            self.player_position = (nx, ny)
        self.turn += 1
        if self.level.is_exit(*self.player_position):
            self.status = "won"
            self.message = "Victory!"
    def begin_answer(self, interaction_id: str, answer: str):
        """Passe en 'pending'. À appeler sous le verrou du jeu.
        Renvoie (riddle, answer, token) pour lancer l'évaluation."""
        it = self.interaction
        if it is None or it["id"] != interaction_id:
            raise DialogueError("stale_interaction", "No matching active dialogue.")
        if it["status"] == "pending":
            raise DialogueError("evaluation_pending", "An evaluation is already running.")
        if it["status"] == "accepted":
            raise DialogueError("interaction_complete", "The riddle is already solved.")
        token = uuid4().hex
        self._eval_token = token
        it["status"] = "pending"
        it["message"] = ""
        return self.riddle, answer, token

    def finish_evaluation(self, token: str, verdict: Verdict | None) -> bool:
        """Applique un verdict (sous le verrou). None = panne technique."""
        if token != self._eval_token or self.interaction is None:
            return False                      # verdict périmé : ignoré
        self._eval_token = None

        accepted = getattr(verdict, "accepted", None)
        if not isinstance(accepted, bool):    # None, "false", 0, etc. -> panne, pas refus
            self.interaction["status"] = "error"
            self.interaction["message"] = MSG_ERROR
        elif accepted:
            self.interaction["status"] = "accepted"
            self.interaction["message"] = MSG_ACCEPTED
            self.passage_open = True
        else:
            self.interaction["status"] = "rejected"
            self.interaction["message"] = MSG_REJECTED
        return True
    def cancel(self, interaction_id: str) -> None:
        """Ferme le dialogue (sous le verrou). Le passage reste fermé."""
        it = self.interaction
        if it is None or it["id"] != interaction_id:
            raise DialogueError("stale_interaction", "No matching active dialogue.")
        if it["status"] == "accepted":
            raise DialogueError("interaction_complete", "The riddle is already solved.")
        self.abort_dialogue()

    def abort_dialogue(self) -> None:
        """Efface le dialogue et invalide toute évaluation en cours."""
        self.interaction = None
        self._eval_token = None      # le verdict tardif ne correspondra plus à rien

    def get_state(self) -> JsonState:
        x,y = self.player_position
        entities = []
        if self.sphinx is not None:
            entities.append({
                "id": self.sphinx["id"],
                "kind": self.sphinx["kind"],
                "x": self.sphinx["x"],
                "y": self.sphinx["y"],
                "appearance": self.sphinx["appearance"],
            })
        entities.append({
            "id": "player-1",
            "kind": "player",
            "x": x,
            "y": y,
            "appearance": "player",
        })
        js : JsonState = {
            "level": self.level.to_state(),
            "entities": entities,
            "player_id": "player-1",
            "status": self.status,
            "turn": self.turn,
            "message": self.message,
            "interaction": None if self.interaction is None else dict(self.interaction),
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
