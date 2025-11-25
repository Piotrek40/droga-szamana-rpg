"""
System dialogów dla Droga Szamana RPG.

Moduł zawiera profesjonalny system dialogów z:
- Pamięcią rozmów (DialogueMemory)
- Aplikatorem efektów z EventBus (DialogueEffectApplicator)
- Ujednoliconym kontrolerem (DialogueController)
"""

from npcs.dialogue.dialogue_memory import (
    DialogueMemory,
    NPCDialogueState,
    ConversationRecord
)
from npcs.dialogue.dialogue_effects import DialogueEffectApplicator
from npcs.dialogue.dialogue_controller import DialogueController

__all__ = [
    'DialogueMemory',
    'NPCDialogueState',
    'ConversationRecord',
    'DialogueEffectApplicator',
    'DialogueController'
]
