import pytest
from unittest.mock import patch
from gridworld.controllers.terminal_input import TerminalInput

def test_conserve_espace():
    with patch("builtins.input", return_value=" "):
        terminal_input = TerminalInput()
        assert terminal_input.read_key() == " "

def test_fin_fichier_et_interruption_clavier():
    terminal_input = TerminalInput()
    
    with patch("builtins.input", side_effect=EOFError):
        assert terminal_input.read_key() == ":quit"
        
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        assert terminal_input.read_key() == ":quit"
