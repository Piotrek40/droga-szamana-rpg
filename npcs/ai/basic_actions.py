"""
Basic AI Actions - extracted from ai_behaviors.py
"""

import logging
from typing import Any, Dict
from .behavior_nodes import NodeStatus

logger = logging.getLogger(__name__)


def rest(npc: Any, context: Dict) -> NodeStatus:
    """Inteligentny odpoczynek z wyborem miejsca"""
    try:
        from ..npc_manager import NPCState, EmotionalState
        
        npc.change_state(NPCState.RESTING)
        
        # Wybierz miejsce odpoczynku na podstawie osobowości
        if "solitary" in npc.personality:
            rest_locations = ["cell", "library", "chapel"]
        elif "social" in npc.personality:
            rest_locations = ["common_room", "mess_hall", "exercise_yard"]
        else:
            rest_locations = ["cell", "common_room", "courtyard"]
        
        # Znajdź najlepsze miejsce do odpoczynku
        for location in rest_locations:
            if location in ["cell", f"cell_{npc.id[-1]}" if npc.id[-1].isdigit() else "cell_1"]:
                npc.location = location
                break
        
        # Regeneracja zależna od miejsca
        energy_regen = 5
        if npc.location.startswith("cell"):
            energy_regen = 7  # Więcej w swoim miejscu
        elif npc.location in ["chapel", "library"]:
            energy_regen = 6  # Spokojne miejsca
        
        npc.energy = min(npc.max_energy, npc.energy + energy_regen)
        
        # Zmniejszenie stresu
        if hasattr(npc, 'modify_emotion'):
            npc.modify_emotion(EmotionalState.NEUTRAL, 0.15)
            npc.modify_emotion(EmotionalState.SAD, -0.1)
            npc.modify_emotion(EmotionalState.ANGRY, -0.1)
        
        # Refleksja - przetwarzanie ważnych wspomnień
        try:
            if hasattr(npc, 'memory_system') and hasattr(npc.memory_system, 'episodic'):
                # Get recent important memories
                important_memories = npc.memory_system.episodic.get_important_memories(limit=3)
                for memory in important_memories:
                    # Konsolidacja pamięci podczas odpoczynku
                    if isinstance(memory, dict):
                        memory["strength"] = min(1.0, memory.get("strength", 0.5) + 0.05)
        except (AttributeError, TypeError) as e:
            logger.debug(f"Memory reflection failed for {npc.id}: {e}")
        
        return NodeStatus.SUCCESS
        
    except Exception as e:
        logger.error(f"Error in rest action: {e}")
        return NodeStatus.FAILURE


def explore_area(npc: Any, context: Dict) -> NodeStatus:
    """Eksploruje otoczenie"""
    try:
        from ..npc_manager import NPCState
        
        npc.change_state(NPCState.EXPLORING)
        
        # Wybierz losową lokację do eksploracji
        import random
        
        available_locations = context.get("available_locations", [
            "courtyard", "library", "chapel", "mess_hall", 
            "exercise_yard", "common_room", "workshop"
        ])
        
        # Usuń obecną lokację z opcji
        current = getattr(npc, 'location', 'unknown')
        if current in available_locations:
            available_locations.remove(current)
        
        if available_locations:
            new_location = random.choice(available_locations)
            npc.location = new_location
            
            # Zwiększ wiedzę o świecie
            if hasattr(npc, 'semantic_memory'):
                npc.semantic_memory[f"visited_{new_location}"] = True
        
        return NodeStatus.SUCCESS
        
    except Exception as e:
        logger.error(f"Error in explore_area action: {e}")
        return NodeStatus.FAILURE


def observe_environment(npc: Any, context: Dict) -> NodeStatus:
    """Obserwuje otoczenie"""
    try:
        from ..npc_manager import NPCState
        
        # Zapamiętaj co widzi
        if hasattr(npc, 'memory_system') and hasattr(npc.memory_system, 'store_episodic_memory'):
            observation = {
                "time": context.get("current_time", 0),
                "location": getattr(npc, 'current_location', getattr(npc, 'location', 'unknown')),
                "npcs_present": [n.id for n in context.get("npcs", {}).values() if hasattr(n, 'id') and n.id != npc.id],
                "items": context.get("items", [])
            }
            npc.memory_system.store_episodic_memory("observation", observation)
        elif hasattr(npc, 'memory_system') and hasattr(npc.memory_system, 'episodic'):
            observation = {
                "time": context.get("current_time", 0),
                "location": getattr(npc, 'current_location', getattr(npc, 'location', 'unknown')),
                "npcs_present": [n.id for n in context.get("npcs", {}).values() if hasattr(n, 'id') and n.id != npc.id],
                "items": context.get("items", [])
            }
            npc.memory_system.episodic.add_memory("observation", observation)
        
        return NodeStatus.SUCCESS
        
    except (AttributeError, TypeError) as e:
        logger.error(f"Błąd w akcji observe_surroundings: {e}")
        return NodeStatus.FAILURE


def work_on_goal(npc: Any, context: Dict) -> NodeStatus:
    """Pracuje nad długoterminowym celem"""
    try:
        if not hasattr(npc, 'goals'):
            return NodeStatus.FAILURE
        
        active_goals = [g for g in npc.goals if g.active and g.completion < 1.0]
        
        if not active_goals:
            return NodeStatus.FAILURE
        
        goal = active_goals[0]  # Pracuj nad pierwszym aktywnym celem
        progress_rate = 0.02
        
        # Check if goal has type attribute, otherwise determine from name
        goal_type = getattr(goal, 'type', None)
        if not goal_type and hasattr(goal, 'name'):
            goal_name = goal.name.lower()
            if 'wealth' in goal_name or 'money' in goal_name or 'gold' in goal_name:
                goal_type = 'wealth'
            elif 'friend' in goal_name or 'relationship' in goal_name or 'trust' in goal_name:
                goal_type = 'relationship'
            elif 'learn' in goal_name or 'knowledge' in goal_name or 'study' in goal_name:
                goal_type = 'knowledge'
            else:
                goal_type = 'general'
        
        if goal_type == "wealth":
            if hasattr(npc, 'wealth'):
                npc.wealth += 1
                goal.completion = min(1.0, npc.wealth / getattr(goal, 'target_value', 100))
            return NodeStatus.SUCCESS
        
        elif goal_type == "relationship":
            if hasattr(npc, 'relationships'):
                target = getattr(goal, 'target', 'player')
                if target in npc.relationships:
                    npc.relationships[target]["trust"] += 0.5
                    goal.completion = min(1.0, npc.relationships[target]["trust"] / 100)
            return NodeStatus.SUCCESS
        
        elif goal_type == "knowledge":
            if hasattr(npc, 'knowledge'):
                npc.knowledge.append(f"fact_{context.get('current_time', 0)}")
                goal.completion = min(1.0, len(npc.knowledge) / getattr(goal, 'target_value', 10))
            return NodeStatus.SUCCESS
        
        # Default progress for any goal type
        goal.completion = min(1.0, goal.completion + progress_rate)
        return NodeStatus.SUCCESS
        
    except (AttributeError, TypeError) as e:
        logger.error(f"Błąd w akcji work_on_goal: {e}")
        return NodeStatus.FAILURE


def maintain_items(npc: Any, context: Dict) -> NodeStatus:
    """Utrzymuje przedmioty w dobrej kondycji"""
    try:
        if hasattr(npc, 'inventory'):
            for item in npc.inventory[:]:  # Copy to allow modification
                if hasattr(item, 'durability') and item.durability < 0.5:
                    # Próbuj naprawić przedmiot
                    if hasattr(npc, 'gold') and npc.gold >= 5:
                        item.durability = min(1.0, item.durability + 0.2)
                        npc.gold -= 5
                        return NodeStatus.SUCCESS
        
        return NodeStatus.SUCCESS
        
    except Exception as e:
        logger.error(f"Error in maintain_items action: {e}")
        return NodeStatus.FAILURE


def personal_activity(npc: Any, context: Dict) -> NodeStatus:
    """Aktywność osobista na podstawie osobowości"""
    try:
        import random
        
        personality = getattr(npc, 'personality', [])
        
        if 'studious' in personality:
            # Czytaj w bibliotece
            npc.location = 'library'
            if hasattr(npc, 'knowledge'):
                npc.knowledge.append(f"study_session_{context.get('current_time', 0)}")
        
        elif 'social' in personality:
            # Szukaj towarzystwa
            social_locations = ['common_room', 'mess_hall', 'exercise_yard']
            npc.location = random.choice(social_locations)
        
        elif 'aggressive' in personality:
            # Trening walki
            npc.location = 'exercise_yard'
            if hasattr(npc, 'strength'):
                npc.strength = min(100, npc.strength + 1)
        
        else:
            # Domyślna aktywność
            npc.location = 'cell'
        
        return NodeStatus.SUCCESS
        
    except Exception as e:
        logger.error(f"Error in personal_activity action: {e}")
        return NodeStatus.FAILURE