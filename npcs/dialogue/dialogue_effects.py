"""
System aplikowania efektów dialogowych z integracją EventBus.

Obsługuje wszystkie efekty wynikające z wyborów dialogowych:
- Zmiany reputacji
- Zdobywanie wiedzy
- Otrzymywanie przedmiotów
- Rozpoczynanie questów
- Modyfikacje relacji
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Import EventBus - używamy istniejącego systemu
from core.event_bus import (
    event_bus,
    GameEvent,
    EventCategory,
    EventPriority
)


class DialogueEffectType(Enum):
    """Typy efektów dialogowych."""
    KNOWLEDGE = "knowledge"
    REPUTATION = "reputation"
    ITEM = "item"
    QUEST = "quest"
    RELATIONSHIP = "relationship"
    FLAG = "flag"
    UNLOCK_TOPIC = "unlock_topic"
    GOLD = "gold"
    SKILL_XP = "skill_xp"
    STAT_CHANGE = "stat_change"
    SPAWN_NPC = "spawn_npc"
    REMOVE_NPC = "remove_npc"
    LOCATION_UNLOCK = "location_unlock"


@dataclass
class DialogueEffect:
    """Pojedynczy efekt dialogowy."""
    effect_type: DialogueEffectType
    value: Any
    condition: Optional[Dict[str, Any]] = None  # Warunek aplikacji
    message: Optional[str] = None  # Wiadomość dla gracza


class DialogueEffectApplicator:
    """
    Aplikator efektów dialogowych z EventBus.

    Odpowiada za:
    - Aplikowanie efektów wyborów dialogowych
    - Emitowanie eventów do innych systemów
    - Walidację efektów przed aplikacją
    """

    def __init__(self, dialogue_memory=None):
        """
        Inicjalizacja aplikatora.

        Args:
            dialogue_memory: Referencja do DialogueMemory
        """
        self.dialogue_memory = dialogue_memory
        self.applied_effects_log: List[Dict[str, Any]] = []

    def set_dialogue_memory(self, memory) -> None:
        """Ustaw referencję do DialogueMemory."""
        self.dialogue_memory = memory

    def apply_effects(
        self,
        effects: Dict[str, Any],
        player,
        npc_id: str,
        node_id: str,
        dialogue_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Zastosuj efekty wyboru dialogowego.

        Args:
            effects: Słownik efektów do zastosowania
            player: Obiekt gracza
            npc_id: ID NPCa
            node_id: ID węzła dialogowego
            dialogue_context: Dodatkowy kontekst

        Returns:
            Lista wiadomości o zastosowanych efektach
        """
        if not effects:
            return []

        messages = []
        applied = []

        for effect_type, effect_value in effects.items():
            try:
                result = self._apply_single_effect(
                    effect_type, effect_value, player, npc_id, node_id, dialogue_context
                )
                if result:
                    messages.append(result)
                    applied.append(effect_type)
            except Exception as e:
                print(f"[DialogueEffects] Błąd przy {effect_type}: {e}")

        # Zaloguj zastosowane efekty
        if applied:
            self.applied_effects_log.append({
                'npc_id': npc_id,
                'node_id': node_id,
                'effects': applied
            })

        return messages

    def _apply_single_effect(
        self,
        effect_type: str,
        effect_value: Any,
        player,
        npc_id: str,
        node_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Zastosuj pojedynczy efekt.

        Args:
            effect_type: Typ efektu
            effect_value: Wartość efektu
            player: Obiekt gracza
            npc_id: ID NPCa
            node_id: ID węzła
            context: Kontekst dialogu

        Returns:
            Wiadomość o efekcie lub None
        """
        # Knowledge - wiedza globalna
        if effect_type == "knowledge":
            return self._apply_knowledge(effect_value, player)

        # Reputation - reputacja u frakcji
        elif effect_type == "reputation":
            return self._apply_reputation(effect_value, player)

        # Item - przedmioty
        elif effect_type == "item":
            return self._apply_item(effect_value, player, npc_id)

        # Quest - zadania
        elif effect_type == "quest":
            return self._apply_quest(effect_value, player, npc_id)

        # Relationship - relacja z konkretnym NPCem
        elif effect_type == "relationship":
            return self._apply_relationship(effect_value, npc_id)

        # Flag - flaga dialogowa
        elif effect_type == "flag":
            return self._apply_flag(effect_value, npc_id)

        # Unlock topic - odblokuj temat
        elif effect_type == "unlock_topic":
            return self._apply_unlock_topic(effect_value, npc_id)

        # Gold - złoto
        elif effect_type == "gold":
            return self._apply_gold(effect_value, player, npc_id)

        # Skill XP - doświadczenie umiejętności
        elif effect_type == "skill_xp":
            return self._apply_skill_xp(effect_value, player)

        # Location unlock - odblokowanie lokacji
        elif effect_type == "location_unlock":
            return self._apply_location_unlock(effect_value, player)

        # Mark branch completed
        elif effect_type == "complete_branch":
            return self._apply_complete_branch(effect_value, npc_id)

        return None

    def _apply_knowledge(self, knowledge_id: str, player) -> str:
        """Dodaj wiedzę."""
        # Dodaj do DialogueMemory
        if self.dialogue_memory:
            self.dialogue_memory.add_knowledge(knowledge_id)

        # Dodaj do gracza jeśli ma metodę
        if hasattr(player, 'add_knowledge'):
            player.add_knowledge(knowledge_id)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='knowledge_gained',
            category=EventCategory.DIALOGUE,
            data={
                'knowledge_id': knowledge_id,
                'source': 'dialogue'
            },
            priority=EventPriority.NORMAL
        ))

        return f"Zdobyto wiedzę: {knowledge_id}"

    def _apply_reputation(self, rep_data, player) -> str:
        """Zmień reputację."""
        if isinstance(rep_data, (list, tuple)):
            faction, amount = rep_data
        elif isinstance(rep_data, dict):
            faction = rep_data.get('faction')
            amount = rep_data.get('amount', 0)
        else:
            return None

        if hasattr(player, 'change_reputation'):
            player.change_reputation(faction, amount)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='reputation_changed',
            category=EventCategory.DIALOGUE,
            data={
                'faction': faction,
                'amount': amount,
                'source': 'dialogue'
            },
            priority=EventPriority.NORMAL
        ))

        direction = "wzrosła" if amount > 0 else "spadła"
        return f"Reputacja u {faction} {direction} o {abs(amount)}"

    def _apply_item(self, item_data, player, npc_id: str) -> str:
        """Daj przedmiot."""
        if isinstance(item_data, str):
            item_id = item_data
            quantity = 1
        elif isinstance(item_data, dict):
            item_id = item_data.get('id')
            quantity = item_data.get('quantity', 1)
        elif isinstance(item_data, (list, tuple)):
            item_id = item_data[0]
            quantity = item_data[1] if len(item_data) > 1 else 1
        else:
            return None

        if hasattr(player, 'add_item'):
            player.add_item(item_id, quantity)

        # Emituj event handlowy/dialogowy
        event_bus.emit(GameEvent(
            event_type='item_received',
            category=EventCategory.DIALOGUE,
            data={
                'item_id': item_id,
                'quantity': quantity,
                'source': 'dialogue',
                'from_npc': npc_id
            },
            source=npc_id,
            target='player',
            priority=EventPriority.NORMAL
        ))

        if quantity > 1:
            return f"Otrzymano: {item_id} x{quantity}"
        return f"Otrzymano: {item_id}"

    def _apply_quest(self, quest_data, player, npc_id: str) -> str:
        """Rozpocznij/zaktualizuj quest."""
        if isinstance(quest_data, str):
            quest_id = quest_data
            action = 'start'
        elif isinstance(quest_data, dict):
            quest_id = quest_data.get('id')
            action = quest_data.get('action', 'start')
        else:
            return None

        if action == 'start':
            if hasattr(player, 'start_quest'):
                player.start_quest(quest_id)

            # Emituj event
            event_bus.emit(GameEvent(
                event_type='quest_started',
                category=EventCategory.QUEST,
                data={
                    'quest_id': quest_id,
                    'giver_npc': npc_id
                },
                source=npc_id,
                priority=EventPriority.HIGH
            ))
            return f"Rozpoczęto zadanie: {quest_id}"

        elif action == 'complete':
            if hasattr(player, 'complete_quest'):
                player.complete_quest(quest_id)

            event_bus.emit(GameEvent(
                event_type='quest_completed',
                category=EventCategory.QUEST,
                data={
                    'quest_id': quest_id,
                    'completed_via': 'dialogue'
                },
                priority=EventPriority.HIGH
            ))
            return f"Ukończono zadanie: {quest_id}"

        elif action == 'update':
            stage = quest_data.get('stage')
            if hasattr(player, 'update_quest'):
                player.update_quest(quest_id, stage)

            event_bus.emit(GameEvent(
                event_type='quest_updated',
                category=EventCategory.QUEST,
                data={
                    'quest_id': quest_id,
                    'stage': stage
                },
                priority=EventPriority.NORMAL
            ))
            return f"Zaktualizowano zadanie: {quest_id}"

        return None

    def _apply_relationship(self, rel_data, npc_id: str) -> Optional[str]:
        """Zmień relację z NPCem."""
        if not self.dialogue_memory:
            return None

        if isinstance(rel_data, int):
            amount = rel_data
            target_npc = npc_id
        elif isinstance(rel_data, dict):
            amount = rel_data.get('amount', 0)
            target_npc = rel_data.get('npc_id', npc_id)
        elif isinstance(rel_data, (list, tuple)):
            target_npc = rel_data[0]
            amount = rel_data[1]
        else:
            return None

        new_level = self.dialogue_memory.modify_relationship(target_npc, amount)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='relationship_changed',
            category=EventCategory.DIALOGUE,
            data={
                'npc_id': target_npc,
                'change': amount,
                'new_level': new_level
            },
            target=target_npc,
            priority=EventPriority.NORMAL
        ))

        direction = "poprawiła się" if amount > 0 else "pogorszyła się"
        return f"Relacja z {target_npc} {direction}"

    def _apply_flag(self, flag_data, npc_id: str) -> Optional[str]:
        """Ustaw flagę dialogową."""
        if not self.dialogue_memory:
            return None

        if isinstance(flag_data, str):
            flag_name = flag_data
            flag_value = True
        elif isinstance(flag_data, dict):
            flag_name = flag_data.get('name')
            flag_value = flag_data.get('value', True)
        elif isinstance(flag_data, (list, tuple)):
            flag_name = flag_data[0]
            flag_value = flag_data[1] if len(flag_data) > 1 else True
        else:
            return None

        target_npc = flag_data.get('npc_id', npc_id) if isinstance(flag_data, dict) else npc_id
        self.dialogue_memory.set_flag(target_npc, flag_name, flag_value)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='dialogue_flag_set',
            category=EventCategory.DIALOGUE,
            data={
                'npc_id': target_npc,
                'flag': flag_name,
                'value': flag_value
            },
            priority=EventPriority.LOW
        ))

        return None  # Flagi są ciche

    def _apply_unlock_topic(self, topic_data, npc_id: str) -> Optional[str]:
        """Odblokuj temat rozmowy."""
        if not self.dialogue_memory:
            return None

        if isinstance(topic_data, str):
            topic = topic_data
            target_npc = npc_id
        elif isinstance(topic_data, dict):
            topic = topic_data.get('topic')
            target_npc = topic_data.get('npc_id', npc_id)
        else:
            return None

        self.dialogue_memory.unlock_topic(target_npc, topic)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='dialogue_topic_unlocked',
            category=EventCategory.DIALOGUE,
            data={
                'npc_id': target_npc,
                'topic': topic
            },
            priority=EventPriority.NORMAL
        ))

        return f"Odblokowano nowy temat rozmowy"

    def _apply_gold(self, gold_data, player, npc_id: str) -> Optional[str]:
        """Dodaj/odejmij złoto."""
        if isinstance(gold_data, int):
            amount = gold_data
        elif isinstance(gold_data, dict):
            amount = gold_data.get('amount', 0)
        else:
            return None

        if hasattr(player, 'gold'):
            player.gold += amount
        elif hasattr(player, 'add_gold'):
            player.add_gold(amount)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='gold_received' if amount > 0 else 'gold_spent',
            category=EventCategory.ECONOMY,
            data={
                'amount': abs(amount),
                'source': 'dialogue',
                'npc_id': npc_id
            },
            priority=EventPriority.NORMAL
        ))

        if amount > 0:
            return f"Otrzymano {amount} złota"
        else:
            return f"Zapłacono {abs(amount)} złota"

    def _apply_skill_xp(self, skill_data, player) -> Optional[str]:
        """Dodaj doświadczenie umiejętności."""
        if isinstance(skill_data, dict):
            skill_name = skill_data.get('skill')
            amount = skill_data.get('amount', 1)
        elif isinstance(skill_data, (list, tuple)):
            skill_name = skill_data[0]
            amount = skill_data[1] if len(skill_data) > 1 else 1
        else:
            return None

        if hasattr(player, 'add_skill_xp'):
            player.add_skill_xp(skill_name, amount)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='skill_xp_gained',
            category=EventCategory.PLAYER_ACTION,
            data={
                'skill': skill_name,
                'amount': amount,
                'source': 'dialogue'
            },
            priority=EventPriority.NORMAL
        ))

        return f"Zdobyto doświadczenie w {skill_name}"

    def _apply_location_unlock(self, location_data, player) -> Optional[str]:
        """Odblokuj lokację."""
        if isinstance(location_data, str):
            location_id = location_data
        elif isinstance(location_data, dict):
            location_id = location_data.get('id')
        else:
            return None

        if hasattr(player, 'unlock_location'):
            player.unlock_location(location_id)

        # Emituj event
        event_bus.emit(GameEvent(
            event_type='location_unlocked',
            category=EventCategory.DISCOVERY,
            data={
                'location_id': location_id,
                'source': 'dialogue'
            },
            priority=EventPriority.HIGH
        ))

        return f"Odkryto nową lokację: {location_id}"

    def _apply_complete_branch(self, branch_id: str, npc_id: str) -> Optional[str]:
        """Oznacz gałąź dialogową jako ukończoną."""
        if not self.dialogue_memory:
            return None

        self.dialogue_memory.mark_branch_completed(npc_id, branch_id)

        event_bus.emit(GameEvent(
            event_type='dialogue_branch_completed',
            category=EventCategory.DIALOGUE,
            data={
                'npc_id': npc_id,
                'branch_id': branch_id
            },
            priority=EventPriority.LOW
        ))

        return None  # Ukończenie gałęzi jest ciche

    def get_applied_effects_summary(self) -> Dict[str, int]:
        """
        Pobierz podsumowanie zastosowanych efektów.

        Returns:
            Słownik z liczbą efektów według typu
        """
        summary = {}
        for log_entry in self.applied_effects_log:
            for effect in log_entry.get('effects', []):
                summary[effect] = summary.get(effect, 0) + 1
        return summary
