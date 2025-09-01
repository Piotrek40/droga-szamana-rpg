#!/usr/bin/env python3
"""
Launcher graficznego interfejsu dla Droga Szamana RPG.
Uruchamia grę w oknie z prawdziwym GUI zamiast w terminalu.
"""

import sys
import os

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game_state import game_state
from ui.gui_interface import launch_gui


def main():
    """Uruchamia grę z graficznym interfejsem."""
    print("Uruchamianie Droga Szamana RPG...")
    print("Inicjalizacja graficznego interfejsu...")
    
    # Inicjalizuj grę
    game_state.init_game("Bohater")
    
    # Uruchom GUI
    launch_gui(game_state)


if __name__ == "__main__":
    main()