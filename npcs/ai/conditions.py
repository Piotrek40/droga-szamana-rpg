"""
Condition functions for AI behavior trees - extracted from ai_behaviors.py
"""

import time
from typing import Any, Dict


def is_tired(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest zmęczony"""
    return getattr(npc, 'energy', 100) < 30


def is_hungry(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest głodny"""
    return getattr(npc, 'hunger', 0) > 70


def is_stressed(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest zestresowany"""
    return getattr(npc, 'stress', 0) > 60


def is_injured(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest ranny"""
    return getattr(npc, 'health', 100) < 50


def has_urgent_goal(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma pilny cel"""
    if not hasattr(npc, 'goals'):
        return False
    
    current_time = context.get('current_time', time.time())
    for goal in npc.goals:
        if goal.active and goal.is_urgent(current_time):
            return True
    return False


def is_bored(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC się nudzi"""
    # Prosta heurystyka - jeśli nie robi nic od dłuższego czasu
    last_activity = getattr(npc, 'last_activity_time', 0)
    current_time = context.get('current_time', time.time())
    return (current_time - last_activity) > 3600  # 1 godzina


def is_day_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest dzień"""
    hour = context.get("hour", 12)
    return 6 <= hour <= 18


def is_night_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest noc"""
    hour = context.get("hour", 12)
    return hour < 6 or hour > 20


def is_meal_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest pora posiłku"""
    hour = context.get("hour", 12)
    meal_times = [7, 12, 18]  # Śniadanie, obiad, kolacja
    return any(abs(hour - meal_time) <= 1 for meal_time in meal_times)


def is_in_danger(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest w niebezpieczeństwie"""
    # Sprawdź czy są wrogowie w pobliżu
    npcs_in_location = context.get("npcs", {})
    for other_npc in npcs_in_location.values():
        if (hasattr(other_npc, 'location') and 
            other_npc.location == npc.location and
            hasattr(npc, 'relationships') and
            other_npc.id in npc.relationships):
            
            relationship = npc.relationships[other_npc.id]
            if getattr(relationship, 'hostility', 0) > 70:
                return True
    
    return False


def has_weapons(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma broń"""
    if not hasattr(npc, 'inventory'):
        return False
    
    weapon_types = ['sword', 'dagger', 'axe', 'hammer', 'spear', 'club']
    for item in npc.inventory:
        if hasattr(item, 'type') and item.type in weapon_types:
            return True
    
    return False


def can_afford_bribe(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC może sobie pozwolić na łapówkę"""
    return getattr(npc, 'gold', 0) >= 50


def is_alone(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest sam"""
    npcs_in_location = context.get("npcs", {})
    count = sum(1 for n in npcs_in_location.values() 
                if getattr(n, 'location', None) == getattr(npc, 'location', None))
    return count <= 1


def is_in_darkness(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest ciemno (dla Brutusa)"""
    hour = context.get("hour", 12)
    is_dark = 20 <= hour or hour < 6
    # Sprawdź czy jest w ciemnym miejscu
    dark_locations = ["dungeon", "cell_basement", "storage_room"]
    return is_dark or getattr(npc, 'location', '') in dark_locations


def has_escape_plan(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma plan ucieczki"""
    if not hasattr(npc, 'goals'):
        return False
    
    for goal in npc.goals:
        if hasattr(goal, 'name') and 'escape' in goal.name.lower() and goal.active:
            return goal.completion > 0.3
    return False


def knows_about_tunnel(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC wie o tunelu"""
    return hasattr(npc, 'semantic_memory') and "tunnel_location" in npc.semantic_memory


def trusts_player(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ufa graczowi"""
    player_id = context.get("player_id", "player")
    if hasattr(npc, 'relationships') and player_id in npc.relationships:
        return getattr(npc.relationships[player_id], 'trust', 0) > 30
    return False


def fears_player(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC boi się gracza"""
    player_id = context.get("player_id", "player")
    if hasattr(npc, 'relationships') and player_id in npc.relationships:
        return getattr(npc.relationships[player_id], 'fear', 0) > 50
    return False


def is_being_watched(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest obserwowany"""
    npcs_in_location = context.get("npcs", {})
    guards = [n for n in npcs_in_location.values() 
              if hasattr(n, 'role') and n.role == "guard" and 
              getattr(n, 'location', None) == getattr(npc, 'location', None)]
    return len(guards) > 0


def has_information_to_trade(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma informacje do wymiany"""
    if not hasattr(npc, 'semantic_memory'):
        return False
    
    valuable_info = ["tunnel_location", "guard_schedules", "weapon_cache", "escape_routes"]
    return any(info in npc.semantic_memory for info in valuable_info)


def wants_to_trade(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC chce handlować"""
    # Handluj jeśli masz przedmioty i potrzebujesz złota
    return (hasattr(npc, 'inventory') and len(npc.inventory) > 0 and
            getattr(npc, 'gold', 0) < 20)


def is_guard_patrol_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest czas patrolu strażników"""
    hour = context.get("hour", 12)
    # Patrol o 6, 12, 18, 24
    patrol_hours = [6, 12, 18, 0]
    return hour in patrol_hours


def is_safe_location(npc: Any, context: Dict) -> bool:
    """Sprawdza czy lokacja jest bezpieczna"""
    safe_locations = ["cell", "library", "chapel"]
    return getattr(npc, 'location', '') in safe_locations


def has_contraband(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma nielegalne przedmioty"""
    if not hasattr(npc, 'inventory'):
        return False
    
    contraband_types = ['weapon', 'lockpick', 'drugs', 'alcohol']
    for item in npc.inventory:
        if hasattr(item, 'type') and item.type in contraband_types:
            return True
    
    return False


def is_execution_scheduled(npc: Any, context: Dict) -> bool:
    """Sprawdza czy zaplanowano egzekucję"""
    # Sprawdź w kontekście gry czy są zaplanowane egzekucje
    scheduled_events = context.get("scheduled_events", [])
    return any("execution" in event.get("type", "") for event in scheduled_events)


def remembers_player_kindness(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC pamięta życzliwość gracza"""
    if not hasattr(npc, 'memory_system'):
        return False
    
    # Szukaj pozytywnych interakcji z graczem
    try:
        if hasattr(npc.memory_system, 'episodic'):
            memories = npc.memory_system.episodic.get_memories_about("player", limit=10)
            positive_count = sum(1 for memory in memories 
                               if memory.get("emotional_value", 0) > 0)
            return positive_count >= 3
    except:
        pass
    
    return False


def is_medical_emergency(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest nagła sytuacja medyczna"""
    return (getattr(npc, 'health', 100) < 20 or 
            getattr(npc, 'bleeding', 0) > 0)


def needs_religious_comfort(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC potrzebuje otuchy religijnej"""
    personality = getattr(npc, 'personality', [])
    return ('religious' in personality and 
            getattr(npc, 'stress', 0) > 70)


def is_social_hour(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest pora towarzyska"""
    hour = context.get("hour", 12)
    # Wieczorne godziny towarzyskie
    return 19 <= hour <= 22