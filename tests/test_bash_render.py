import pytest
from gridworld.views.bash_render import state_to_string
from gridworld.engine import Engine
from gridworld.models.level import Level

def test_rendu_fct_state_to_string(donnee):
    level=Level(donnee)
    state=level.get_state()

    rendered=state_to_string(state)

    assert f"Turn: {state['turn']}" in rendered
    assert state['message'] in rendered
    assert "###" in rendered

def test_update_appel_conversion_et_refresh(recording_renderer, level_data):
    simulation = {
        "level": level_data,
        "entities": [],
        "player_id": "p1",
        "status": "playing",
        "turn": 0,
        "message": "OK",
        "interaction": None,
        "extras": {},
    }
    
    recording_renderer.update_render(simulation)
    assert len(recording_renderer.history) == 1
    assert recording_renderer.history[0] == simulation

def test_delegation_engine(make_input_source,recording_renderer,level_data):
    input_source = make_input_source(["z"])
    level = Level(level_data)
    engine = Engine(level=level, input_source=input_source, renderer=recording_renderer)
    
    state = level.get_state()
    engine.render(state)
    
    assert len(recording_renderer.history) == 1
    assert recording_renderer.history[0] == state
    