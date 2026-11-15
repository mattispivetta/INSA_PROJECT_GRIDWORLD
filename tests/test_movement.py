import copy
import json
from pathlib import Path

import pytest

from gridworld.engine import Engine
from gridworld.models.level import Level

N0_PATH = str(Path(__file__).resolve().parent.parent / "levels" / "n0.json")


# ==================================================
# OUTILS DE TEST
# Ces classes et fonctions ne testent rien : elles préparent un jeu
# et lisent son état. Si un nom change dans le moteur, on corrige ici.
# ==================================================

class ScriptedController:
    """Faux contrôleur : renvoie les actions de la liste, une par appel,
    puis "quit" quand la liste est vide (pour que run() se termine).
    Compte aussi combien de fois le moteur l'a appelé."""

    def __init__(self, actions=()):
        self._actions = list(actions)
        self.calls = 0

    def get_action(self):
        self.calls += 1
        return self._actions.pop(0) if self._actions else "quit"


class RecordingRenderer:
    """Faux renderer : mémorise chaque état reçu via update_render,
    et compte les appels à start/close (le moteur ne doit pas les faire)."""

    def __init__(self):
        self.received = []
        self.started = 0
        self.closed = 0

    def start(self):
        self.started += 1

    def update_render(self, state):
        self.received.append(state)

    def close(self):
        self.closed += 1


def make_game(grid, start, exit_, controller=None, renderer=None):
    """Construit un moteur sur une petite carte écrite directement dans le test.

    grid  : liste de chaînes ('#' = mur, '.' = sol)
    start : (x, y) du joueur au départ
    exit_ : (x, y) de la sortie (un sol, différent du départ)
    """
    level = Level({
        "id": "test",
        "grid": grid,
        "start": {"x": start[0], "y": start[1]},
        "exit": {"x": exit_[0], "y": exit_[1]},
    })
    return Engine(level, controller or ScriptedController(), renderer or RecordingRenderer())


def make_n0_game(controller=None, renderer=None):
    """Construit un moteur sur le vrai niveau N0 (pour les scénarios de l'énoncé)."""
    level = Level.load(N0_PATH)
    return Engine(level, controller or ScriptedController(), renderer or RecordingRenderer())


def act(game, action):
    """Applique une action (méthode publique du moteur)."""
    game.apply_action(action)


def position(game):
    """Position du joueur, lue dans l'état partagé (le joueur est la dernière entité)."""
    player = game.get_state()["entities"][-1]
    return player["x"], player["y"]


def turns(game):
    return game.get_state()["turn"]


def status(game):
    return game.get_state()["status"]


def message(game):
    return game.get_state()["message"]


def snapshot(game):
    """Copie complète de l'état, pour comparer 'avant' et 'après'."""
    return copy.deepcopy(game.get_state())


# ==================================================
# CARTES UTILISÉES DANS LES TESTS
# ==================================================

# Sens des directions (confirmé par le scénario 2 de l'énoncé)
DELTAS = {
    "north": (0, -1),
    "south": (0, 1),
    "west": (-1, 0),
    "east": (1, 0),
}

# Carte ouverte 3 x 3 : du sol partout, pas de mur extérieur.
# Sert aux déplacements réussis et aux limites de la grille.
OPEN_GRID = ["...",
             "...",
             "..."]

# Joueur au centre, un mur dans chacune des quatre directions.
#   . # .
#   # S #
#   . # .
WALLED_GRID = [".#.",
               "#.#",
               ".#."]


# ==================================================
# ÉTAT INITIAL
# ==================================================

def test_initial_state():
    """Au départ : 8 clés, partie en cours, tour 0, message vide, pas d'interaction."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))
    state = game.get_state()

    assert set(state) == {
        "level", "entities", "player_id", "interaction",
        "extras", "status", "turn", "message",
    }
    assert state["status"] == "playing"
    assert state["turn"] == 0
    assert state["message"] == ""
    assert state["interaction"] is None
    assert state["extras"] == {}
    assert position(game) == (1, 1)


# ==================================================
# DÉPLACEMENTS RÉUSSIS
# ==================================================

@pytest.mark.parametrize("action", ["north", "south", "west", "east"])
def test_successful_move(action):
    """Un déplacement vers une case libre met à jour la bonne coordonnée
    et consomme un tour. Testé dans les quatre directions."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))
    dx, dy = DELTAS[action]

    act(game, action)

    assert position(game) == (1 + dx, 1 + dy)
    assert turns(game) == 1


def test_move_changes_only_the_expected_coordinate():
    """Aller à l'est change x et laisse y intact (détecte une confusion x/y)."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))

    act(game, "east")

    assert position(game) == (2, 1)


# ==================================================
# MURS
# ==================================================

@pytest.mark.parametrize("action", ["north", "south", "west", "east"])
def test_wall_blocks_move_but_consumes_turn(action):
    """Un mur bloque le déplacement (la position ne change pas)
    mais le tour est quand même consommé."""
    game = make_game(WALLED_GRID, start=(1, 1), exit_=(0, 0))

    act(game, action)

    assert position(game) == (1, 1)
    assert turns(game) == 1


# ==================================================
# LIMITES DE LA GRILLE
# ==================================================

@pytest.mark.parametrize(
    "action, start, exit_",
    [
        ("north", (0, 0), (2, 2)),   # bord haut
        ("west",  (0, 0), (2, 2)),   # bord gauche : x = -1, piège de l'indice négatif
        ("south", (2, 2), (0, 0)),   # bord bas
        ("east",  (2, 2), (0, 0)),   # bord droit
    ],
)
def test_grid_boundary_blocks_move_but_consumes_turn(action, start, exit_):
    """Sortir de la grille est refusé comme un mur : pas de déplacement,
    pas d'exception, un tour consommé."""
    game = make_game(OPEN_GRID, start=start, exit_=exit_)

    act(game, action)

    assert position(game) == start
    assert turns(game) == 1


# ==================================================
# TOURS : ATTENTE, None, ACCUMULATION
# ==================================================

def test_wait_consumes_turn_without_moving():
    """'wait' consomme un tour et ne déplace pas le joueur."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))

    act(game, "wait")

    assert position(game) == (1, 1)
    assert turns(game) == 1


def test_none_action_changes_nothing():
    """None (pas d'action disponible) ne modifie pas l'état et ne consomme pas de tour."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))
    before = snapshot(game)

    act(game, None)

    assert snapshot(game) == before


def test_turns_accumulate_over_move_blocked_and_wait():
    """Le compteur s'additionne sur trois types d'actions à la suite
    (déplacement réussi, bloqué, attente) sans se réinitialiser."""
    game = make_game(OPEN_GRID, start=(0, 0), exit_=(2, 2))

    act(game, "east")    # réussi        -> tour 1
    act(game, "north")   # bloqué (bord) -> tour 2
    act(game, "wait")    # attente       -> tour 3

    assert position(game) == (1, 0)
    assert turns(game) == 3


# ==================================================
# ACTION NON PRISE EN CHARGE
# ==================================================

@pytest.mark.parametrize("action", ["jump", "", "up"])
def test_unsupported_action_raises_and_changes_nothing(action):
    """Une action hors vocabulaire lève ValueError AVANT toute modification.
    On joue d'abord un 'east' pour partir d'un état non initial : un moteur
    qui réinitialiserait l'état avant de lever l'erreur serait détecté."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))
    act(game, "east")
    before = snapshot(game)

    with pytest.raises(ValueError):
        act(game, action)

    assert snapshot(game) == before


# ==================================================
# VICTOIRE
# ==================================================

def test_reaching_exit_wins():
    """Marcher sur la sortie : status 'won', message exact 'Victory!'."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 1))

    act(game, "east")

    assert position(game) == (2, 1)
    assert status(game) == "won"
    assert message(game) == "Victory!"
    assert turns(game) == 1


@pytest.mark.parametrize("action", ["north", "south", "west", "east", "wait"])
def test_after_victory_state_is_frozen(action):
    """Après la victoire, déplacements et attente ne changent rien
    (ni position, ni tour, ni statut)."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 1))
    act(game, "east")                         # victoire
    before = snapshot(game)

    act(game, action)

    assert snapshot(game) == before


def test_n0_full_scenario():
    """Scénario 2 de l'énoncé, sur le vrai niveau N0."""
    game = make_n0_game()

    for action in ["east", "south", "south", "east", "east", "east", "north", "north"]:
        act(game, action)

    assert position(game) == (5, 1)
    assert turns(game) == 8
    assert status(game) == "won"
    assert message(game) == "Victory!"


def test_n0_blocked_move_at_start():
    """Scénario 1 de l'énoncé : 'west' au départ est bloqué mais consomme un tour."""
    game = make_n0_game()

    act(game, "west")

    assert position(game) == (1, 1)
    assert turns(game) == 1


# ==================================================
# get_state : sérialisable, indépendant, sans effet
# ==================================================

def test_get_state_is_json_serializable():
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))
    state = game.get_state()

    assert json.loads(json.dumps(state)) == state


def test_get_state_is_independent():
    """Modifier le dictionnaire renvoyé ne modifie pas le jeu."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))

    state = game.get_state()
    state["turn"] = 99
    state["entities"][-1]["x"] = 99

    assert turns(game) == 0
    assert position(game) == (1, 1)


def test_get_state_does_not_advance_game():
    """Lire l'état plusieurs fois ne consomme aucun tour."""
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2))

    game.get_state()
    game.get_state()

    assert turns(game) == 0


def test_state_level_matches_level_model():
    """La partie 'level' de l'état est exactement celle exportée par Level.to_state()."""
    level = Level.load(N0_PATH)
    game = Engine(level, ScriptedController(), RecordingRenderer())

    assert game.get_state()["level"] == level.to_state()


# ==================================================
# Délégation au contrôleur et au renderer
# ==================================================

def test_get_action_calls_controller_once():
    controller = ScriptedController(["east"])
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2), controller=controller)

    assert game.get_action() == "east"
    assert controller.calls == 1


def test_render_passes_state_to_renderer_once():
    renderer = RecordingRenderer()
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2), renderer=renderer)
    state = game.get_state()

    game.render(state)

    assert renderer.received == [state]


# ==================================================
# Boucle de jeu
# ==================================================

def test_run_renders_initial_state_and_quit_changes_nothing():
    """run() affiche l'état initial, ignore les None, joue 'east',
    puis s'arrête sur 'quit' sans consommer de tour."""
    controller = ScriptedController([None, "east", "quit"])
    renderer = RecordingRenderer()
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2),
                     controller=controller, renderer=renderer)

    game.run()

    assert renderer.received[0]["turn"] == 0  # premier rendu : état initial
    assert position(game) == (2, 1)
    assert turns(game) == 1                   # 'east' compte, 'quit' et None non


def test_run_does_not_start_or_close_renderer():
    """Le démarrage et la fermeture du renderer appartiennent au point d'entrée,
    pas au moteur."""
    renderer = RecordingRenderer()
    game = make_game(OPEN_GRID, start=(1, 1), exit_=(2, 2),
                     controller=ScriptedController(["quit"]), renderer=renderer)

    game.run()

    assert renderer.started == 0
    assert renderer.closed == 0