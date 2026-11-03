import pytest
from gridworld.contracts import InputSource, JsonState, Renderer
from gridworld.models.level import Level


class FakeInputSource:
    """Source d'entrée simulée consommant une séquence de touches.
    
    Respecte le contrat InputSource (méthode read_key).
    Fait échouer explicitement le test si la séquence est épuisée.
    """

    def __init__(self, sequence: list[str]) -> None:
        self._sequence = list(sequence)

    def read_key(self) -> str | None:
        if not self._sequence:
            raise RuntimeError(
                "FakeInputSource : La séquence de touches prédéfinies est vide ! "
                "Le moteur a demandé plus de saisies que prévu."
            )
        return self._sequence.pop(0)


class RecordingRenderer:
    """Renderer 'headless' enregistrant les états reçus sans interface graphique.
    
    Respecte le contrat Renderer (start, update_render, close).
    """

    def __init__(self) -> None:
        self.history: list[JsonState] = []
        self.is_started: bool = False
        self.is_closed: bool = False

    def start(self) -> None:
        self.is_started = True

    def update_render(self, json_state: JsonState) -> None:
        self.history.append(json_state)

    def close(self) -> None:
        self.is_closed = True


@pytest.fixture
def sample_level_data() -> dict:
    """Fixture renvoyant les données brutes d'un petit niveau 3x3 valide."""
    return {
        "id": "test-level",
        "grid": [
            "###",
            "#.#",
            "###",
        ],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 1, "y": 1},
    }


@pytest.fixture
def sample_level_data_with_exit() -> dict:
    """Fixture renvoyant un niveau 3x3 avec un départ et une sortie distincts."""
    return {
        "id": "test-level-exit",
        "grid": [
            "###",
            "#..",
            "###",
        ],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 2, "y": 1},
    }


@pytest.fixture
def fresh_level(sample_level_data_with_exit) -> Level:
    """Fixture créant un nouvel objet Level indépendant pour chaque test."""
    return Level(sample_level_data_with_exit)


@pytest.fixture
def make_input_source():
    """Factory fixture pour instancier un FakeInputSource à la demande."""
    def _factory(sequence: list[str]) -> FakeInputSource:
        return FakeInputSource(sequence)
    return _factory


@pytest.fixture
def recording_renderer() -> RecordingRenderer:
    """Fixture fournissant un RecordingRenderer vierge."""
    return RecordingRenderer()