import pytest
from gridworld.controllers.controller import Controller

def test_controller_keys (make_input_source):
    keys= ["z", "Z", "q", "Q", "s", "S", "d", "D", "up", "DOWN", "left", "RIGHT", " ", "Escape", ":quit"]
    expected_actions = [
        "north", "north",
        "west", "west",
        "south", "south",
        "east", "east",
        "north", "south", "west", "east",
        "wait", "quit", "quit"
    ]
    input_source=make_input_source(keys)
    controller=Controller(input_source)

    for expected in expected_actions:
        assert controller.get_action() == expected

    def test_controller_touches_inconnues_None_entree(make_input_source):
        input_source = make_input_source(["a", "F1", None, "unknown_key"])
        controller = Controller(input_source)
    
        for _ in range(4):
            assert controller.get_action() is None

    def test_controller_lit_unefois_entree(make_inout_source):
        input_source = make_input_source(["z"])

        compteur_lecture=0
        lecture=input_source.read_key

        def lecture():
            nonlocal compteur_lecture
            compteur_lecture+=1
            return lecture()

        input_source.read_key=compteur_lecture
        controller=Controller(input_source)

        action=controller.get_action()
        assert action=="north"
        assert compteur_lecture==1
        