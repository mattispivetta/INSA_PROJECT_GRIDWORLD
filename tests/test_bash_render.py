# def test_rendu_fct_state_to_string(donnee):
#     level=Level(donnee)
#     state=level.get_state()

#     rendered=BashRender().state_to_string(state)

#     assert f"Turn: {state['turn']}" in rendered
#     assert state['message'] in rendered
#     assert "###" in rendered

# def test_update_appel_conversion_et_refresh(recording_renderer, level_data):
#     simulation = {
#         "level": level_data,
#         "entities": [],
#         "player_id": "p1",
#         "status": "playing",
#         "turn": 0,
#         "message": "OK",
#         "interaction": None,
#         "extras": {},
#     }
    
#     recording_renderer.update_render(simulation)
#     assert len(recording_renderer.history) == 1
#     assert recording_renderer.history[0] == simulation

# def test_delegation_engine(make_input_source,recording_renderer,level_data):
#     input_source = make_input_source(["z"])
#     level = Level(level_data)
#     engine = Engine(level=level, input_source=input_source, renderer=recording_renderer)
    
#     state = level.get_state()
#     engine.render(state)
    
#     assert len(recording_renderer.history) == 1
#     assert recording_renderer.history[0] == state



from gridworld.views.bash_render import BashRender
from gridworld.engine import Engine
from gridworld.models.level import Level
from gridworld.controllers.controller import Controller


def test_rendu_fct_state_to_string(sample_level_data_with_exit):
    level = Level(sample_level_data_with_exit)

    state = {
        "level": level.to_state(),
        "entities": [
            {
                "id": "player-1",
                "kind": "player",
                "x": 1,
                "y": 1,
                "appearance": "player",
            }
        ],
        "player_id": "player-1",
        "status": "playing",
        "turn": 0,
        "message": "Bienvenue",
        "interaction": None,
        "extras": {},
    }

    rendered = BashRender().state_to_string(state)

    assert "P" in rendered
    assert "E" in rendered
    assert "Turn: 0" in rendered
    assert "Bienvenue" in rendered


def test_update_appel_conversion_et_refresh(
    sample_level_data_with_exit, monkeypatch
):
    level = Level(sample_level_data_with_exit)
    state = {
        "level": level.to_state(),
        "entities": [],
        "player_id": "player-1",
        "status": "playing",
        "turn": 0,
        "message": "OK",
        "interaction": None,
        "extras": {},
    }

    renderer = BashRender()
    appels = []

    monkeypatch.setattr(
        renderer,
        "refresh",
        lambda text: appels.append(text),
    )

    renderer.update_render(state)

    assert len(appels) == 1
    assert "Turn: 0" in appels[0]
    assert "OK" in appels[0]


def test_delegation_engine(
    make_input_source, recording_renderer, sample_level_data_with_exit
):
    input_source = make_input_source(["z"])
    controller = Controller(input_source)
    level = Level(sample_level_data_with_exit)

    engine = Engine(
        level=level,
        controller=controller,
        renderer=recording_renderer,
    )

    state = engine.get_state()
    engine.render(state)

    assert len(recording_renderer.history) == 1
    assert recording_renderer.history[0] == state
