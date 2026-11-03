import json
import pytest

def test_etat_complet_et_json(nv_level):
    state=nv_level.get_state()

    required_keys = ["level", "entities", "player_id", "status", "turn", "message", "interaction", "extras"]
    for key in required_keys:
        assert key in state, f"Le champ obligatoire '{key}' est absent de l'état."
        
    serialized = json.dumps(state)
    assert isinstance(serialized, str)
    deserialized = json.loads(serialized)
    assert deserialized["turn"] == state["turn"]

def test_lecture_state_avance_pas_jeu(nv_level):
    initial_turn = nv_level.get_state()["turn"]
    
    for _ in range(5):
        current_state = nv_level.get_state()
        assert current_state["turn"] == initial_turn

def test_state_data_isolation(nv_level):
    state1 = nv_level.get_state()
    
    state1["turn"] = 677
    state1["message"] = "Message modifié"
    
    state2 = nv_level.get_state()
    
    assert state2["turn"] != 677
    assert state2["message"] != "Message modifié"