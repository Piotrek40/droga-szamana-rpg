"""Mechanics module - systemy mechanik gry."""

from .combat import CombatSystem, CombatStats, combat_system
from .economy import Economy, Item, Market
from .crafting import CraftingSystem

__all__ = [
    'CombatSystem',
    'CombatStats',
    'combat_system',  # Singleton - używaj tego!
    'Economy',
    'Item',
    'Market',
    'CraftingSystem',
]
