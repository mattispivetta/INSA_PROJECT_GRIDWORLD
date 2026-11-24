import json

import pytest

from gridworld.models.level import Level, LevelError


def test_load_n0():
    level = Level.load("levels/n0.json")
    state = level.to_state()
    assert (state["width"], state["height"]) == (7, 5)
    assert state["id"] == "n0"
    assert level.get_start() == (1, 1)
    assert level.is_exit(5, 1)
    assert level.is_walkable(5, 1)
    assert not level.is_walkable(0, 0)


def test_load_selected_file(tmp_path, level_data):
    path = tmp_path / "small.json"
    path.write_text(json.dumps(level_data), encoding="utf-8")
    assert Level.load(str(path)).to_state()["id"] == "small"


@pytest.mark.parametrize("data", [None, [], {}])
def test_missing_map_structure(data):
    with pytest.raises(LevelError):
        Level(data)


@pytest.mark.parametrize("field, value", [
    ("id", ""), ("id", 12),
    ("grid", []), ("grid", "..."), ("grid", [""]),
    ("grid", [123]), ("grid", ["...", ".."]), ("grid", ["?.", ".."]),
    ("start", None), ("start", {}),
    ("start", {"x": True, "y": 1}), ("start", {"x": 1.5, "y": 1}),
    ("start", {"x": -1, "y": 1}), ("exit", {"x": 3, "y": 1}),
])
def test_invalid_map(level_data, field, value):
    level_data[field] = value
    with pytest.raises(LevelError):
        Level(level_data)


@pytest.mark.parametrize("position", ["start", "exit"])
def test_start_and_exit_cannot_be_walls(level_data, position):
    level_data["grid"][0] = "#.."
    level_data[position] = {"x": 0, "y": 0}
    with pytest.raises(LevelError):
        Level(level_data)


def test_malformed_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(LevelError) as error:
        Level.load(str(path))
    assert isinstance(error.value.__cause__, json.JSONDecodeError)


def test_missing_file(tmp_path):
    with pytest.raises(LevelError) as error:
        Level.load(str(tmp_path / "missing.json"))
    assert isinstance(error.value.__cause__, OSError)


@pytest.mark.parametrize("x, y", [(-1, 1), (1, -1), (3, 1), (1, 3)])
def test_outside_grid(level, x, y):
    with pytest.raises(IndexError):
        level.get_tile(x, y)
    assert not level.is_walkable(x, y)
    assert not level.is_exit(x, y)


def test_level_copies_input_and_exports(level_data):
    first = Level(level_data)
    second = Level(level_data)
    snapshot = first.to_state()
    snapshot["tiles"][0][0] = "wall"
    level_data["grid"][0] = "###"
    level_data["start"]["x"] = 0
    assert first.to_state() == second.to_state()
    assert first.get_tile(0, 0).to_state() == "floor"
    assert first.get_start() == (1, 1)
    assert json.loads(json.dumps(first.to_state())) == first.to_state()
