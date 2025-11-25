"""NPCs module - system postaci niezależnych."""

from .npc_manager import NPCManager, NPC, NPCState, EmotionalState
from .dialogue_system import DialogueSystem

__all__ = [
    'NPCManager',
    'NPC',
    'NPCState',
    'EmotionalState',
    'DialogueSystem',
]
