import json
import pytest
from gridworld.models.level import Level, LevelError

@pytest.fixture
def valid_level_data():
    """Données représentant un niveau valide."""
    return {
        "id": "test-level",
        "grid": [
            "#####",
            "#...#",
            "#.#.#",
            "#...#",
            "#####",
        ],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 3, "y": 3},
    }


@pytest.fixture
def level(valid_level_data):
    """Construit un niveau valide pour les tests."""
    return Level(valid_level_data)


# --------------------------------------------------
# 1. Chargement d'un niveau valide
# --------------------------------------------------

def test_valid_json_loads(tmp_path, valid_level_data):
    path = tmp_path / "level.json"
    path.write_text(json.dumps(valid_level_data), encoding="utf-8")

    level = Level.load(str(path))

    assert level.get_start() == (1, 1)
    assert level.is_exit(3, 3)


# --------------------------------------------------
# 2. Chargement du fichier N0
# --------------------------------------------------

def test_n0_dimensions_and_positions():
    level = Level.load("levels/n0.json")

    assert level.get_start() == (1, 1)
    assert level.is_exit(5, 1)

    # N0 est une grille de 7 colonnes et 5 lignes.
    assert level.to_state()["id"] == "n0" 
    assert level.to_state()["height"] == 5
    assert level.to_state()["width"] == 7
    # La case (6, 4) doit donc exister.
    assert level.get_tile(6, 4) is not None

    # La colonne 7 est en dehors de la grille.
    with pytest.raises(IndexError):
        level.get_tile(7, 4)


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


# --------------------------------------------------
# 4. Coordonnées hors de la grille
# --------------------------------------------------

@pytest.mark.parametrize(
    "x, y",
    [
        (-1, 0),
        (0, -1),
        (5, 0),
        (0, 5),
        (100, 100),
        (True, 0),
        (0, 1.5),
    ],
)
def test_get_tile_out_of_bounds(level, x, y):
    with pytest.raises(IndexError):
        level.get_tile(x, y)


@pytest.mark.parametrize(
    "x, y",
    [
        (-1, 0),
        (0, -1),
        (5, 0),
        (0, 5),
    ],
)
def test_is_walkable_out_of_bounds(level, x, y):
    assert level.is_walkable(x, y) is False


@pytest.mark.parametrize(
    "x, y",
    [
        (-1, 0),
        (0, -1),
        (5, 0),
        (0, 5),
    ],
)
def test_is_exit_out_of_bounds(level, x, y):
    assert level.is_exit(x, y) is False


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
def test_invalid_level_data_raises_error(invalid_data):
    with pytest.raises(LevelError):
        Level(invalid_data)


# --------------------------------------------------
# 7. Indépendance des objets Level
# --------------------------------------------------

def test_two_levels_are_independent(valid_level_data):
    level1 = Level(valid_level_data)
    level2 = Level(valid_level_data)

    level1_state = level1.to_state()
    level2_state = level2.to_state()

    assert level1_state == level2_state
    assert level1.get_tile(1, 1) is not level2.get_tile(1, 1)

