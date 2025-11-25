"""Core module - fundamenty gry Droga Szamana RPG."""

# WAŻNE: Kolejność importów jest krytyczna!
# event_bus musi być przed game_state (game_state zależy od event_bus)
from .event_bus import EventBus, event_bus, EventCategory, EventPriority
from .data_loader import DataLoader, data_loader
from .game_state import GameState, game_state, GameMode

__all__ = [
    'GameState',
    'game_state',
    'GameMode',
    'EventBus',
    'event_bus',
    'EventCategory',
    'EventPriority',
    'DataLoader',
    'data_loader',
]
