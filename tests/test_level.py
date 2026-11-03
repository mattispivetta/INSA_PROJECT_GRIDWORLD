import copy
import json
from pathlib import Path

import pytest

from gridworld.models.level import Level, LevelError

N0_PATH = str(Path(__file__).resolve().parent.parent / "levels" / "n0.json")


# Carte 5 x 5
#   x: 0 1 2 3 4
# y=0  # # # # #
# y=1  # S . . #     start (1, 1)
# y=2  # . # . #     mur en (2, 2)
# y=3  # . . E #     exit (3, 3)
# y=4  # # # # #


VALID = {
    "id": "test-level",
    "grid": [
        "#####",
        "#.#.#",
        "#...#",
        "#####",
    ],
    "start": {"x": 1, "y": 1},
    "exit": {"x": 3, "y": 3},
}


@pytest.fixture
#def level(valid_level_data):
#    """Construit un niveau valide pour les tests."""
#    return Level(valid_level_data)
def level():
    return Level(copy.deepcopy(VALID))

# --------------------------------------------------
# 1. Chargement d'un niveau valide
# --------------------------------------------------

# def test_valid_json_loads(tmp_path, valid_level_data):
#     path = tmp_path / "level.json"
#     path.write_text(json.dumps(valid_level_data), encoding="utf-8")

#     level = Level.load(str(path))

#     assert level.get_start() == (1, 1)
#     assert level.is_exit(3, 3)
def test_valid_json_loads(tmp_path):
    path = tmp_path / "level.json"
    path.write_text(json.dumps(VALID), encoding="utf-8")

    loaded = Level.load(str(path))

    assert loaded.get_start() == (1, 1)
    assert loaded.is_exit(3, 3)

# --------------------------------------------------
# 2. Chargement du fichier N0
# --------------------------------------------------

def test_n0_dimensions_and_positions():
    level = Level.load(N0_PATH)

    assert level.get_start() == (1, 1)
    assert level.is_exit(5, 1)

    # N0 est une grille de 7 colonnes et 5 lignes.
    assert level.to_state()["id"] == "n0" 
    assert level.to_state()["height"] == 5
    assert level.to_state()["width"] == 7
    # La case (6, 4) doit donc exister.
    assert level.get_tile(6, 4) == "wall"

    # La colonne 7 est en dehors de la grille.
    with pytest.raises(IndexError):
        level.get_tile(7, 4)
    with pytest.raises(IndexError):
        level.get_tile(6, 5)


# --------------------------------------------------
# 3. Accès aux cases et comportement des tuiles
# --------------------------------------------------

def test_get_tile_returns_correct_tiles(level):
    assert level.get_tile(1, 1).to_state() == "floor"
    assert level.get_tile(2, 2).to_state() == "wall"
    assert level.get_tile(3, 3).to_state() == "exit"


def test_is_walkable(level):
    assert level.is_walkable(1, 1) is True  # Sol
    assert level.is_walkable(2, 2) is False  # Mur
    assert level.is_walkable(3, 3) is True  # Sortie


def test_is_exit(level):
    assert level.is_exit(3, 3) is True
    assert level.is_exit(1, 1) is False
    assert level.is_exit(2, 2) is False

def test_axes_are_not_swapped():
    # Carte non carrée (4 colonnes, 3 lignes) : x et y ne sont pas interchangeables
    #   x: 0 1 2 3
    # y=0  # # # #
    # y=1  # . . #     start (1, 1), exit (2, 1)
    # y=2  # # # #
    level = Level({
        "id": "axes",
        "grid": ["####", "#..#", "####"],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 2, "y": 1},
    })

    assert level.is_exit(2, 1) is True
    assert level.is_exit(1, 2) is False
    assert level.get_tile(3, 2).to_state() == "wall"   # existe
    with pytest.raises(IndexError):
        level.get_tile(2, 3)                           # y = 3 : hors grille
    assert level.to_state()["width"] == 4
    assert level.to_state()["height"] == 3

# --------------------------------------------------
# 4. Coordonnées hors de la grille
# --------------------------------------------------
OUT_OF_BOUNDS = [(-1, 0), (0, -1), (-1, -1), (5, 0), (0, 5), (100, 100)]

@pytest.mark.parametrize("x, y",OUT_OF_BOUNDS)
def test_get_tile_out_of_bounds(level, x, y):
    with pytest.raises(IndexError):
        level.get_tile(x, y)
@pytest.mark.parametrize("x, y",OUT_OF_BOUNDS)
def test_get_tile_rejects_non_int_coordinates(level, x, y):
    with pytest.raises(IndexError):
        level.get_tile(x, y)



@pytest.mark.parametrize("x, y",OUT_OF_BOUNDS)
def test_is_walkable_out_of_bounds(level, x, y):
    assert level.is_walkable(x, y) is False


@pytest.mark.parametrize("x, y",OUT_OF_BOUNDS)
def test_is_exit_out_of_bounds(level, x, y):
    assert level.is_exit(x, y) is False

#un fichier dont le JSON est bien formé mais dont le contenu n’est pas un niveau.
@pytest.mark.parametrize("content", ["[]", "null", "42", '"texte"'])
def test_json_with_wrong_type_raises_level_error(tmp_path, content):
    path = tmp_path / "wrong.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(LevelError):
        Level.load(str(path))

# --------------------------------------------------
# 5. Fichier absent ou JSON incorrect
# --------------------------------------------------

def test_missing_file_raises_level_error(tmp_path):
    path = tmp_path / "missing.json"

    with pytest.raises(LevelError):
        Level.load(str(path))


def test_malformed_json_raises_level_error(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(LevelError):
        Level.load(str(path))


# --------------------------------------------------
# 6. Données de niveau invalides
# --------------------------------------------------

@pytest.mark.parametrize(
    "invalid_data",
    [
        # Identifiant absent
        {
            "grid": ["###", "#.#", "###"],
            "start": {"x": 1, "y": 1},
            "exit": {"x": 1, "y": 1},
        },
        # Grille vide
        {
            "id": "empty",
            "grid": [],
            "start": {"x": 0, "y": 0},
            "exit": {"x": 0, "y": 0},
        },
        # Lignes de longueurs différentes
        {
            "id": "uneven",
            "grid": ["####", "#.#", "####"],
            "start": {"x": 1, "y": 1},
            "exit": {"x": 2, "y": 1},
        },
        # Caractère de grille inconnu
        {
            "id": "unknown",
            "grid": ["###", "#X#", "###"],
            "start": {"x": 1, "y": 1},
            "exit": {"x": 1, "y": 1},
        },
        # Départ hors de la grille
        {
            "id": "bad-start",
            "grid": ["###", "#.#", "###"],
            "start": {"x": 10, "y": 10},
            "exit": {"x": 1, "y": 1},
        },
        # Sortie hors de la grille
        {
            "id": "bad-exit",
            "grid": ["###", "#.#", "###"],
            "start": {"x": 1, "y": 1},
            "exit": {"x": 10, "y": 10},
        },
        # Coordonnée non entière
        {
            "id": "bad-coordinate",
            "grid": ["###", "#.#", "###"],
            "start": {"x": 1.5, "y": 1},
            "exit": {"x": 1, "y": 1},
        },
        # Départ et sortie confondus
        {
            "id": "same-position",
            "grid": ["###", "#.#", "###"],
            "start": {"x": 1, "y": 1},
            "exit": {"x": 1, "y": 1},
        },
    ],
)
# def test_invalid_level_data_raises_error(invalid_data):
#     with pytest.raises(LevelError):
#         Level(invalid_data)
def test_invalid_level_data_raises_level_error(changes):
    data = copy.deepcopy(VALID)
    data.update(changes)

    with pytest.raises(LevelError):
        Level(data)


# --------------------------------------------------
# 7. Indépendance des objets Level
# --------------------------------------------------

def test_two_levels_are_independent():
    level1 = Level(copy.deepcopy(VALID))
    level2 = Level(copy.deepcopy(VALID))

    state1 = level1.to_state()
    state1["tiles"][1][1] = "wall"

    assert level2.is_walkable(1, 1) is True
    assert level1.to_state() == level2.to_state()

    # level1_state = level1.to_state()
    # level2_state = level2.to_state()

    # assert level1_state == level2_state
    # assert level1.get_tile(1, 1) is not level2.get_tile(1, 1)

# @pytest.mark.parametrize("key", ["id", "grid", "start", "exit"])
# def test_missing_key_raises_level_error(key):
#     data = copy.deepcopy(VALID)
#     del data[key]

#     with pytest.raises(LevelError):
#         Level(data)


# def test_non_dict_data_raises_level_error():
#     with pytest.raises(LevelError):
#         Level([])


# --------------------------------------------------
# État exporté
# --------------------------------------------------

# def test_exported_state_is_independent(level):
#     state = level.to_state()
#     state["tiles"][1][1] = "wall"

#     assert level.is_walkable(1, 1) is True
#     assert level.to_state()["tiles"][1][1] == "floor"


# def test_state_is_json_serializable(level):
#     state = level.to_state()

#     assert json.loads(json.dumps(state)) == state


