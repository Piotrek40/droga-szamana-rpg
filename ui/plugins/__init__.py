#!/usr/bin/env python3
"""
Modul pluginow interfejsu gry Droga Szamana.
Eksportuje wszystkie dostepne pluginy.
"""

from ui.plugins.abilities_plugin import AbilitiesPlugin
from ui.plugins.combat_plugin import CombatPlugin
from ui.plugins.crafting_plugin import CraftingPlugin
from ui.plugins.exploration_plugin import ExplorationPlugin
from ui.plugins.gathering_plugin import GatheringPlugin
from ui.plugins.quest_plugin import QuestPlugin
from ui.plugins.trade_plugin import TradePlugin

__all__ = [
    'AbilitiesPlugin',
    'CombatPlugin',
    'CraftingPlugin',
    'ExplorationPlugin',
    'GatheringPlugin',
    'QuestPlugin',
    'TradePlugin',
]
