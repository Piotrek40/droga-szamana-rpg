"""
System Behavior Trees dla NPCów
Pełna implementacja drzew decyzyjnych z węzłami selektorów, sekwencji, warunków i akcji
"""

import random
import time
from enum import Enum
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

# Import advanced behaviors if available
try:
    from .advanced_behaviors import (
        create_advanced_warden_behavior,
        create_advanced_guard_behavior,
        create_advanced_prisoner_behavior,
        create_advanced_creature_behavior,
        create_creature_behavior,
        create_deep_personality_behavior,
        create_habit_system,
        create_emotional_reaction_system
    )
except ImportError:
    # Fallback if advanced behaviors not available
    create_advanced_warden_behavior = None
    create_advanced_guard_behavior = None
    create_advanced_prisoner_behavior = None
    create_advanced_creature_behavior = None
    create_creature_behavior = None
    create_deep_personality_behavior = None
    create_habit_system = None
    create_emotional_reaction_system = None


class NodeStatus(Enum):
    """Status wykonania węzła"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode(ABC):
    """Abstrakcyjna klasa bazowa dla węzłów behavior tree"""
    
    def __init__(self, name: str):
        self.name = name
        self.children: List[BehaviorNode] = []
    
    @abstractmethod
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        """Wykonuje logikę węzła"""
        pass
    
    def add_child(self, child: 'BehaviorNode'):
        """Dodaje węzeł potomny"""
        self.children.append(child)
        return self


class SelectorNode(BehaviorNode):
    """Węzeł selektora - wykonuje dzieci do pierwszego sukcesu"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        for child in self.children:
            status = child.execute(npc, context)
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE


class SequenceNode(BehaviorNode):
    """Węzeł sekwencji - wykonuje wszystkie dzieci po kolei"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        for child in self.children:
            status = child.execute(npc, context)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.SUCCESS


class RandomSelectorNode(BehaviorNode):
    """Węzeł losowego selektora"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        shuffled = list(self.children)
        random.shuffle(shuffled)
        
        for child in shuffled:
            status = child.execute(npc, context)
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE


class PriorityNode(BehaviorNode):
    """Węzeł z priorytetem - wykonuje dzieci według priorytetu"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.priorities: Dict[BehaviorNode, float] = {}
    
    def add_child_with_priority(self, child: BehaviorNode, priority: float):
        """Dodaje dziecko z priorytetem"""
        self.add_child(child)
        self.priorities[child] = priority
        return self
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        # Sortuj dzieci według priorytetu
        sorted_children = sorted(self.children, 
                                key=lambda c: self.priorities.get(c, 0), 
                                reverse=True)
        
        for child in sorted_children:
            status = child.execute(npc, context)
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE


class DecoratorNode(BehaviorNode):
    """Abstrakcyjna klasa dla dekoratorów"""
    
    def __init__(self, name: str, child: BehaviorNode):
        super().__init__(name)
        self.child = child


class InverterNode(DecoratorNode):
    """Odwraca wynik dziecka"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        status = self.child.execute(npc, context)
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return NodeStatus.RUNNING


class RepeatNode(DecoratorNode):
    """Powtarza wykonanie dziecka określoną liczbę razy"""
    
    def __init__(self, name: str, child: BehaviorNode, times: int):
        super().__init__(name, child)
        self.times = times
        self.current_count = 0
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        for _ in range(self.times):
            status = self.child.execute(npc, context)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.SUCCESS


class ConditionalNode(BehaviorNode):
    """Węzeł warunkowy - sprawdza warunek"""
    
    def __init__(self, name: str, condition_func):
        super().__init__(name)
        self.condition_func = condition_func
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        try:
            if self.condition_func(npc, context):
                return NodeStatus.SUCCESS
            return NodeStatus.FAILURE
        except Exception as e:
            logger.error(f"Błąd w warunku {self.name}: {e}")
            return NodeStatus.FAILURE


class ActionNode(BehaviorNode):
    """Węzeł akcji - wykonuje konkretną akcję"""
    
    def __init__(self, name: str, action_func):
        super().__init__(name)
        self.action_func = action_func
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        try:
            result = self.action_func(npc, context)
            if result is None:
                return NodeStatus.SUCCESS
            return result
        except Exception as e:
            logger.error(f"Błąd w akcji {self.name}: {e}")
            return NodeStatus.FAILURE


# ============= WARUNKI =============

def is_hungry(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest głodny"""
    return npc.hunger > 60


def is_very_hungry(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest bardzo głodny"""
    return npc.hunger > 80


def is_tired(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest zmęczony"""
    return npc.energy < 30


def is_exhausted(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest wyczerpany"""
    return npc.energy < 10


def is_thirsty(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest spragniony"""
    return npc.thirst > 60


def is_injured(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest ranny"""
    return npc.health < npc.max_health * 0.5


def is_critically_injured(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest krytycznie ranny"""
    return npc.health < npc.max_health * 0.2


def is_under_attack(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest atakowany"""
    recent_events = context.get("events", [])
    for event in recent_events[-5:]:  # Ostatnie 5 wydarzeń
        if event.get("type") == "attack" and npc.id in event.get("participants", []):
            return True
    return False


def sees_player(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC widzi gracza"""
    player_location = context.get("player_location")
    return player_location == npc.location


def sees_prisoner_escaping(npc: Any, context: Dict) -> bool:
    """Sprawdza czy strażnik widzi uciekającego więźnia"""
    if npc.role != "guard":
        return False
    
    # Sprawdź czy jakiś więzień jest poza celą
    npcs_in_location = context.get("npcs", {})
    for other_npc in npcs_in_location.values():
        if other_npc.role == "prisoner" and not other_npc.location.startswith("cell_"):
            # Więzień poza celą!
            return True
    return False


def is_work_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy to czas pracy"""
    hour = context.get("hour", 12)
    return 8 <= hour < 18


def is_sleep_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy to czas snu"""
    hour = context.get("hour", 12)
    return 22 <= hour or hour < 6


def is_meal_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy to pora posiłku"""
    hour = context.get("hour", 12)
    return hour in [7, 12, 18]


def is_social_time(npc: Any, context: Dict) -> bool:
    """Sprawdza czy to czas na socjalizację"""
    hour = context.get("hour", 12)
    return 19 <= hour < 22


def has_important_info(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma ważne informacje"""
    return len(npc.semantic_memory) > 0


def can_afford_bribe(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC może sobie pozwolić na łapówkę"""
    return npc.gold >= 50


def is_alone(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest sam"""
    npcs_in_location = context.get("npcs", {})
    count = sum(1 for n in npcs_in_location.values() if n.location == npc.location)
    return count <= 1


def is_in_darkness(npc: Any, context: Dict) -> bool:
    """Sprawdza czy jest ciemno (dla Brutusa)"""
    hour = context.get("hour", 12)
    is_dark = 20 <= hour or hour < 6
    # Sprawdź czy jest w ciemnym miejscu
    dark_locations = ["dungeon", "cell_basement", "storage_room"]
    return is_dark or npc.location in dark_locations


def has_escape_plan(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma plan ucieczki"""
    for goal in npc.goals:
        goal_name = str(goal.name) if goal.name is not None else ""
        if "escape" in goal_name.lower() and goal.active:
            return goal.completion > 0.3
    return False


def knows_about_tunnel(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC wie o tunelu"""
    return "tunnel_location" in npc.semantic_memory


def trusts_player(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ufa graczowi"""
    player_id = context.get("player_id", "player")
    if player_id in npc.relationships:
        return npc.relationships[player_id].trust > 30
    return False


def fears_player(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC boi się gracza"""
    player_id = context.get("player_id", "player")
    if player_id in npc.relationships:
        return npc.relationships[player_id].fear > 50
    return False


# ============= ADVANCED CONDITIONS =============

def is_environmental_danger(npc: Any, context: Dict) -> bool:
    """Sprawdza zagrożenia środowiskowe"""
    return context.get("fire", False) or context.get("flood", False) or context.get("riot", False)

def needs_medical_attention(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC potrzebuje pomocy medycznej"""
    has_serious_injury = any(injury.severity > 0.5 for injuries in npc.injuries.values() for injury in injuries)
    return npc.health < npc.max_health * 0.3 or has_serious_injury

def has_urgent_goal(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma pilny cel"""
    current_time = time.time()
    return any(goal.is_urgent(current_time) for goal in npc.goals if goal.active)


def pursue_urgent_goal(npc: Any, context: Dict) -> NodeStatus:
    """Realizuje najpilniejszy cel NPCa"""
    if not hasattr(npc, 'goals'):
        return NodeStatus.FAILURE
    
    current_time = time.time()
    urgent_goals = [g for g in npc.goals if g.active and g.is_urgent(current_time)]
    
    if not urgent_goals:
        return NodeStatus.FAILURE
    
    # Sortuj według priorytetu
    goal = max(urgent_goals, key=lambda g: g.priority)
    
    # Wykonaj akcję związaną z celem
    if goal.type == "escape":
        if hasattr(npc, 'escape_progress'):
            npc.escape_progress += 0.1
        else:
            npc.escape_progress = 0.1
        goal.completion = min(1.0, npc.escape_progress)
        return NodeStatus.SUCCESS
    
    elif goal.type == "survive":
        if npc.hunger > 70:
            return eat_available_food(npc, context)
        elif npc.energy < 30:
            return rest(npc, context)
        return NodeStatus.SUCCESS
    
    elif goal.type == "revenge":
        if hasattr(npc, 'revenge_plan'):
            npc.revenge_plan["progress"] += 0.05
        else:
            npc.revenge_plan = {"target": goal.target, "progress": 0.05}
        goal.completion = min(1.0, npc.revenge_plan.get("progress", 0))
        return NodeStatus.SUCCESS
    
    goal.completion = min(1.0, goal.completion + 0.1)
    return NodeStatus.SUCCESS


def work_on_goal(npc: Any, context: Dict) -> NodeStatus:
    """Pracuje nad długoterminowym celem"""
    if not hasattr(npc, 'goals'):
        return NodeStatus.FAILURE
    
    active_goals = [g for g in npc.goals if g.active and g.completion < 1.0]
    
    if not active_goals:
        return NodeStatus.FAILURE
    
    goal = active_goals[0]  # Pracuj nad pierwszym aktywnym celem
    progress_rate = 0.02
    
    if goal.type == "wealth":
        if hasattr(npc, 'wealth'):
            npc.wealth += 1
            goal.completion = min(1.0, npc.wealth / goal.target_value)
        return NodeStatus.SUCCESS
    
    elif goal.type == "relationship":
        if hasattr(npc, 'relationships'):
            target = goal.target
            if target in npc.relationships:
                npc.relationships[target]["trust"] += 0.5
                goal.completion = min(1.0, npc.relationships[target]["trust"] / 100)
        return NodeStatus.SUCCESS
    
    elif goal.type == "knowledge":
        if hasattr(npc, 'knowledge'):
            npc.knowledge.append(f"fact_{context.get('current_time', 0)}")
            goal.completion = min(1.0, len(npc.knowledge) / goal.target_value)
        return NodeStatus.SUCCESS
    
    goal.completion = min(1.0, goal.completion + progress_rate)
    return NodeStatus.SUCCESS


def is_being_watched(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC jest obserwowany"""
    npcs_in_location = context.get("npcs", {})
    for other in npcs_in_location.values():
        if other.id != npc.id and other.location == npc.location:
            if other.role == "guard" or "watching" in str(other.current_state).lower():
                return True
    return False

def has_contraband(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC ma przedmioty zabronione"""
    contraband_items = ["knife", "lockpick", "rope", "weapon", "drugs"]
    return any(item in npc.inventory for item in contraband_items)

def can_work_together(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC może współpracować z innymi"""
    npcs_in_location = context.get("npcs", {})
    for other in npcs_in_location.values():
        if other.id != npc.id and other.location == npc.location:
            relationship = npc.get_relationship(other.id)
            if relationship.trust > 30 and relationship.get_overall_disposition() > 20:
                return True
    return False

def is_riot_starting(npc: Any, context: Dict) -> bool:
    """Sprawdza czy zaczyna się bunt"""
    recent_events = context.get("events", [])
    violence_count = sum(1 for e in recent_events[-10:] if e.get("type") in ["attack", "fight", "assault"])
    return violence_count >= 3

def knows_secret_route(npc: Any, context: Dict) -> bool:
    """Sprawdza czy NPC zna tajną drogę"""
    return any(key in npc.semantic_memory for key in ["tunnel_location", "secret_passage", "hidden_route"])

def is_suspicious_activity(npc: Any, context: Dict) -> bool:
    """Sprawdza czy dzieją się podejrzane rzeczy"""
    if npc.role != "guard":
        return False
    
    npcs_in_location = context.get("npcs", {})
    hour = context.get("hour", 12)
    
    # Sprawdz więźniów poza celami w nocy
    if 22 <= hour or hour < 6:
        for other in npcs_in_location.values():
            if other.role == "prisoner" and not other.location.startswith("cell_"):
                return True
    
    # Sprawdz skupiska więźniów
    prisoner_count = sum(1 for n in npcs_in_location.values() 
                        if n.role == "prisoner" and n.location == npc.location)
    if prisoner_count >= 3:
        return True
    
    return False

# ============= AKCJE =============

def flee(npc: Any, context: Dict) -> NodeStatus:
    """Inteligentna ucieczka z analizą zagrożenia"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.FLEEING)
    threat_level = context.get("threat_level", 0.5)
    npc.modify_emotion(EmotionalState.FEAR, 0.3 + threat_level * 0.4)
    
    # Analiza zagrożenia i wybor trasy ucieczki
    threat_source = context.get("threat_source")
    current_location = npc.location
    
    # Wybierz bezpieczne miejsce na podstawie roli i sytuacji
    if npc.role == "prisoner":
        if threat_source and threat_source.get("role") == "guard":
            # Uciekaj do tłumu lub ukryj się
            safe_locations = ["mess_hall", "exercise_yard", "workshop", "laundry"]
        else:
            # Uciekaj do celi lub do strażników
            safe_locations = [f"cell_{i}" for i in range(1, 5)] + ["guard_room"]
    elif npc.role == "guard":
        # Strażnicy uciekają do wzmocnień
        safe_locations = ["guard_room", "armory", "warden_office", "watchtower"]
    else:
        safe_locations = ["main_hall", "courtyard", "infirmary"]
    
    # Filtruj dostępne lokacje
    available_locations = [loc for loc in safe_locations if loc != current_location]
    
    if not available_locations:
        available_locations = ["corridor_main", "main_hall"]
    
    # Wybierz najlepszą lokację na podstawie pamięci
    best_location = None
    best_safety = -1
    
    for location in available_locations:
        safety_score = 1.0
        
        # Sprawdź pamięć o tej lokacji
        location_memories = npc.recall_memories(
            query_type="location_assessment",
            location=location,
            limit=3
        )
        
        for memory in location_memories:
            if "danger" in memory.description.lower():
                safety_score *= 0.5
            if "safe" in memory.description.lower():
                safety_score *= 1.5
        
        # Sprawdź emocjonalne skojarzenia
        emotional_response = npc.memory.emotional.get_emotional_response(location)
        if emotional_response.get("fear", 0) > 0.5:
            safety_score *= 0.3
        if emotional_response.get("safe", 0) > 0.5:
            safety_score *= 2.0
        
        if safety_score > best_safety:
            best_safety = safety_score
            best_location = location
    
    new_location = best_location or random.choice(available_locations)
    npc.location = new_location
    
    # Zapisz pamięć o ucieczce
    npc.add_memory(
        event_type="fled",
        description=f"Uciekł do {new_location} przed {threat_source.get('name', 'zagrożeniem') if threat_source else 'zagrożeniem'}",
        participants=[npc.id] + ([threat_source['id']] if threat_source and 'id' in threat_source else []),
        location=new_location,
        importance=0.4 + threat_level * 0.3,
        emotional_impact={"fear": 0.5 + threat_level * 0.3, "surprise": 0.2}
    )
    
    # Nauka proceduralna - zapamiętaj skuteczną trasę ucieczki
    npc.memory.procedural.learn_sequence(
        f"escape_route_from_{current_location}",
        [current_location, new_location]
    )
    
    return NodeStatus.SUCCESS


def attack_target(npc: Any, context: Dict) -> NodeStatus:
    """Atakuje cel"""
    from .npc_manager import NPCState, EmotionalState
    
    target_id = context.get("attack_target")
    if not target_id:
        # Znajdź cel do ataku
        for event in context.get("events", [])[-5:]:
            if event.get("type") == "attack":
                participants = event.get("participants", [])
                if npc.id in participants:
                    # Znajdź atakującego
                    target_id = [p for p in participants if p != npc.id][0] if participants else None
                    break
    
    if not target_id:
        return NodeStatus.FAILURE
    
    npc.change_state(NPCState.ATTACKING)
    npc.modify_emotion(EmotionalState.ANGRY, 0.4)
    
    logger.info(f"{npc.name} atakuje {target_id}")
    
    return NodeStatus.SUCCESS


def patrol(npc: Any, context: Dict) -> NodeStatus:
    """Patroluje obszar"""
    from .npc_manager import NPCState
    
    if npc.role != "guard":
        return NodeStatus.FAILURE
    
    npc.change_state(NPCState.PATROLLING)
    
    # Określ trasę patrolu
    patrol_route = ["corridor_main", "cell_block", "guard_room", "courtyard", "cell_block"]
    
    # Znajdź następną lokację
    current_index = 0
    if npc.location in patrol_route:
        current_index = patrol_route.index(npc.location)
    
    next_index = (current_index + 1) % len(patrol_route)
    npc.location = patrol_route[next_index]
    
    # Sprawdź czy coś podejrzanego
    npcs_in_location = context.get("npcs", {})
    for other_npc in npcs_in_location.values():
        if other_npc.location == npc.location and other_npc.role == "prisoner":
            if not other_npc.location.startswith("cell_"):
                # Więzień poza celą!
                npc.add_memory(
                    event_type="suspicious_activity",
                    description=f"Zauważył {other_npc.name} poza celą",
                    participants=[npc.id, other_npc.id],
                    location=npc.location,
                    importance=0.7
                )
                return NodeStatus.RUNNING  # Kontynuuj obserwację
    
    return NodeStatus.SUCCESS


def eat_meal(npc: Any, context: Dict) -> NodeStatus:
    """Je posiłek"""
    from .npc_manager import NPCState, EmotionalState
    
    npc.change_state(NPCState.EATING)
    
    # Zmniejsz głód
    npc.hunger = max(0, npc.hunger - 40)
    npc.thirst = max(0, npc.thirst - 30)
    
    # Poprawa nastroju
    npc.modify_emotion(EmotionalState.HAPPY, 0.2)
    
    # Określ miejsce posiłku
    if npc.role == "guard":
        npc.location = "guard_room"
    elif npc.role == "warden":
        npc.location = "warden_office"
    else:
        npc.location = "mess_hall"
    
    npc.add_memory(
        event_type="meal",
        description="Zjadł posiłek",
        participants=[npc.id],
        location=npc.location,
        importance=0.1
    )
    
    return NodeStatus.SUCCESS


def sleep(npc: Any, context: Dict) -> NodeStatus:
    """Śpi"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.SLEEPING)
    
    # Regeneracja energii
    npc.energy = min(npc.max_energy, npc.energy + 10)
    
    # Określ miejsce snu
    if npc.role == "prisoner":
        # Więźniowie śpią w swoich celach
        if not npc.location.startswith("cell_"):
            npc.location = f"cell_{npc.id[-1]}" if npc.id[-1].isdigit() else "cell_1"
    elif npc.role == "guard":
        npc.location = "guard_quarters"
    elif npc.role == "warden":
        npc.location = "warden_quarters"
    
    return NodeStatus.SUCCESS


def work(npc: Any, context: Dict) -> NodeStatus:
    """Wykonuje pracę"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.WORKING)
    
    # Różne prace w zależności od roli
    if npc.role == "guard":
        return patrol(npc, context)
    elif npc.role == "warden":
        # Naczelnik pracuje w biurze
        npc.location = "warden_office"
        # Sprawdza raporty
        npc.add_memory(
            event_type="work",
            description="Przeglądał raporty strażników",
            participants=[npc.id],
            location=npc.location,
            importance=0.1
        )
    elif npc.role == "prisoner":
        # Więźniowie mogą pracować w różnych miejscach
        work_locations = ["laundry", "kitchen", "workshop"]
        npc.location = random.choice(work_locations)
        npc.energy = max(0, npc.energy - 5)
    
    return NodeStatus.SUCCESS


def socialize(npc: Any, context: Dict) -> NodeStatus:
    """Socjalizuje się z innymi"""
    from .npc_manager import NPCState, EmotionalState
    
    npc.change_state(NPCState.SOCIALIZING)
    
    # Znajdź kogoś do rozmowy
    npcs_in_location = context.get("npcs", {})
    potential_partners = [
        other for other in npcs_in_location.values()
        if other.id != npc.id and other.location == npc.location
    ]
    
    if potential_partners:
        partner = random.choice(potential_partners)
        
        # Określ typ interakcji na podstawie relacji
        relationship = npc.get_relationship(partner.id)
        disposition = relationship.get_overall_disposition()
        
        if disposition > 30:
            npc.interact_with(partner.id, "friendly_chat")
            npc.modify_emotion(EmotionalState.HAPPY, 0.1)
        elif disposition < -30:
            if random.random() < 0.3:  # 30% szans na konflikt
                npc.interact_with(partner.id, "insult")
                npc.modify_emotion(EmotionalState.ANGRY, 0.2)
            else:
                # Unikaj osoby
                return NodeStatus.FAILURE
        else:
            npc.interact_with(partner.id, "friendly_chat", 0.5)
        
        return NodeStatus.SUCCESS
    
    # Brak towarzystwa
    npc.modify_emotion(EmotionalState.SAD, 0.05)
    return NodeStatus.FAILURE


def gather_information(npc: Any, context: Dict) -> NodeStatus:
    """Zbiera informacje"""
    from .npc_manager import NPCState
    
    # Gadatliwy Piotr specjalizuje się w zbieraniu informacji
    if "talkative" not in npc.personality and "informant" not in npc.personality:
        return NodeStatus.FAILURE
    
    # Podsłuchuj rozmowy
    npcs_in_location = context.get("npcs", {})
    for other in npcs_in_location.values():
        if other.id != npc.id and other.location == npc.location:
            # Szansa na podsłuchanie
            if random.random() < 0.3:
                # Zdobądź losową informację
                info_types = ["guard_schedule", "weakness", "secret", "escape_plan"]
                info_type = random.choice(info_types)
                
                npc.semantic_memory[f"{info_type}_{other.id}"] = {
                    "source": other.id,
                    "timestamp": time.time(),
                    "reliability": random.uniform(0.3, 0.9)
                }
                
                npc.add_memory(
                    event_type="information_gathered",
                    description=f"Podsłuchał informację o {other.name}",
                    participants=[npc.id, other.id],
                    location=npc.location,
                    importance=0.4
                )
                
                return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def plan_escape(npc: Any, context: Dict) -> NodeStatus:
    """Planuje ucieczkę"""
    from .npc_manager import NPCState
    
    # Tylko więźniowie planują ucieczkę
    if npc.role != "prisoner":
        return NodeStatus.FAILURE
    
    # Cicha Anna specjalizuje się w planowaniu ucieczki
    if "quiet" in npc.personality or "escape" in str(npc.goals):
        # Zwiększ postęp planu
        for goal in npc.goals:
            goal_name = str(goal.name) if goal.name is not None else ""
            if "escape" in goal_name.lower():
                goal.completion = min(1.0, goal.completion + 0.05)
                
                if goal.completion > 0.8:
                    # Plan prawie gotowy, szukaj okazji
                    if is_alone(npc, context) and not is_work_time(npc, context):
                        # Dobry moment na ucieczkę!
                        npc.location = "tunnel_entrance"
                        npc.add_memory(
                            event_type="escape_attempt",
                            description="Próbował uciec przez tunel",
                            participants=[npc.id],
                            location="tunnel_entrance",
                            importance=0.9,
                            emotional_impact={"fear": 0.4, "happy": 0.3}
                        )
                        return NodeStatus.SUCCESS
        
        return NodeStatus.RUNNING
    
    return NodeStatus.FAILURE


def hide_in_shadows(npc: Any, context: Dict) -> NodeStatus:
    """Chowa się w cieniach (reakcja Brutusa na ciemność)"""
    from .npc_manager import NPCState, EmotionalState
    
    if is_in_darkness(npc, context) and "fears_darkness" in npc.quirks:
        npc.modify_emotion(EmotionalState.FEAR, 0.4)
        
        # Szuka jasnego miejsca
        light_locations = ["main_hall", "courtyard", "guard_room"]
        npc.location = random.choice(light_locations)
        
        npc.add_memory(
            event_type="fear_response",
            description="Uciekł z ciemnego miejsca",
            participants=[npc.id],
            location=npc.location,
            importance=0.3,
            emotional_impact={"fear": 0.5}
        )
        
        return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def accept_bribe(npc: Any, context: Dict) -> NodeStatus:
    """Przyjmuje łapówkę (Marek)"""
    from .npc_manager import EmotionalState
    
    if "corruptible" not in npc.personality:
        return NodeStatus.FAILURE
    
    # Sprawdź czy ktoś oferuje łapówkę
    bribe_offer = context.get("bribe_offer")
    if bribe_offer and bribe_offer["amount"] >= 50:
        npc.gold += bribe_offer["amount"]
        npc.modify_emotion(EmotionalState.HAPPY, 0.3)
        
        # Może otworzyć celę lub dać informację
        if random.random() < 0.5:
            npc.semantic_memory["bribe_debt"] = {
                "creditor": bribe_offer["from"],
                "favor_owed": True
            }
        
        return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def share_tunnel_info(npc: Any, context: Dict) -> NodeStatus:
    """Dzieli się informacją o tunelu (Stary Józek)"""
    
    if "tunnel_location" not in npc.semantic_memory:
        return NodeStatus.FAILURE
    
    # Sprawdź czy ktoś pyta lub czy ufa tej osobie
    asking_npc = context.get("asking_npc")
    if asking_npc:
        relationship = npc.get_relationship(asking_npc)
        if relationship.trust > 40 or relationship.fear > 60:
            # Podziel się informacją
            npc.add_memory(
                event_type="shared_secret",
                description=f"Powiedział o tunelu {asking_npc}",
                participants=[npc.id, asking_npc],
                location=npc.location,
                importance=0.6
            )
            return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def trade_information(npc: Any, context: Dict) -> NodeStatus:
    """Handluje informacjami (Gadatliwy Piotr)"""
    from .npc_manager import EmotionalState
    
    if "talkative" not in npc.personality:
        return NodeStatus.FAILURE
    
    # Sprawdź czy ma informacje do sprzedania
    if len(npc.semantic_memory) < 3:
        # Najpierw zbierz informacje
        return gather_information(npc, context)
    
    # Znajdź potencjalnego klienta
    npcs_in_location = context.get("npcs", {})
    for other in npcs_in_location.values():
        if other.id != npc.id and other.location == npc.location:
            if other.gold >= 10:  # Może zapłacić
                # Zaproponuj handel
                info_value = random.randint(10, 30)
                
                if random.random() < 0.3:  # 30% szans na sukces
                    npc.gold += info_value
                    npc.modify_emotion(EmotionalState.HAPPY, 0.2)
                    
                    # Przekaż losową informację
                    if npc.semantic_memory:
                        info_key = random.choice(list(npc.semantic_memory.keys()))
                        
                        npc.add_memory(
                            event_type="information_trade",
                            description=f"Sprzedał informację {info_key} za {info_value} złota",
                            participants=[npc.id, other.id],
                            location=npc.location,
                            importance=0.3
                        )
                        
                        return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def intimidate(npc: Any, context: Dict) -> NodeStatus:
    """Zastraszanie (Brutus)"""
    from .npc_manager import NPCState, EmotionalState
    
    if npc.role != "warden" and "sadistic" not in npc.personality:
        return NodeStatus.FAILURE
    
    # Znajdź cel do zastraszenia
    npcs_in_location = context.get("npcs", {})
    victims = [
        other for other in npcs_in_location.values()
        if other.id != npc.id and other.location == npc.location and other.role == "prisoner"
    ]
    
    if victims:
        victim = random.choice(victims)
        
        # Zastrasz
        npc.interact_with(victim.id, "threat", 1.5)
        npc.modify_emotion(EmotionalState.HAPPY, 0.2)  # Sadysta cieszy się z tego
        
        victim.modify_emotion(EmotionalState.FEAR, 0.5)
        victim.interact_with(npc.id, "fear", 2.0)
        
        npc.add_memory(
            event_type="intimidation",
            description=f"Zastraszył {victim.name}",
            participants=[npc.id, victim.id],
            location=npc.location,
            importance=0.4,
            emotional_impact={"happy": 0.3}
        )
        
        return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def rest(npc: Any, context: Dict) -> NodeStatus:
    """Inteligentny odpoczynek z wyoborem miejsca"""
    from .npc_manager import NPCState, EmotionalState
    
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
    important_memories = npc.recall_memories(limit=3)
    for memory in important_memories:
        # Konsolidacja pamięci podczas odpoczynku
        memory["strength"] = min(1.0, memory.get("strength", 0.5) + 0.05)
    
    return NodeStatus.SUCCESS


def seek_medical_attention(npc: Any, context: Dict) -> NodeStatus:
    """Szuka pomocy medycznej"""
    from .npc_manager import NPCState
    
    # Znajdź drogę do ambulatorium
    npc.location = "infirmary"
    npc.change_state(NPCState.FLEEING)  # Pilne
    
    # Komunikuj potrzebę pomocy
    npc.add_memory(
        event_type="medical_emergency",
        description="Szukał pomocy medycznej",
        participants=[npc.id],
        location="infirmary",
        importance=0.8,
        emotional_impact={"fear": 0.6, "sad": 0.7}
    )
    
    # Jeśli jest medyk w poblizu
    npcs_in_location = context.get("npcs", {})
    for other in npcs_in_location.values():
        if "medic" in other.role or "doctor" in other.role:
            # Poproś o pomoc
            npc.interact_with(other.id, "help", 1.5)
            return NodeStatus.SUCCESS
    
    return NodeStatus.RUNNING


def evacuate_area(npc: Any, context: Dict) -> NodeStatus:
    """Ewakuacja z zagrożonego obszaru"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.FLEEING)
    
    # Ostrzeż innych
    npcs_in_location = context.get("npcs", {})
    for other in npcs_in_location.values():
        if other.id != npc.id and other.location == npc.location:
            # Ostrzeżenie
            context["emergency_warning"] = True
    
    # Ewakuuj do bezpiecznego miejsca
    if context.get("fire"):
        safe_locations = ["courtyard", "exercise_yard", "main_gate"]
    elif context.get("flood"):
        safe_locations = ["upper_floor", "roof", "watchtower"]
    else:
        safe_locations = ["main_hall", "courtyard"]
    
    npc.location = random.choice(safe_locations)
    
    return NodeStatus.SUCCESS


def defend(npc: Any, context: Dict) -> NodeStatus:
    """Broni się przed atakiem"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.ATTACKING)
    
    # Użyj umiejętności walki
    success, result = npc.defend()
    
    if success:
        npc.modify_emotion(EmotionalState.ANGRY, 0.3)
        npc.modify_emotion(EmotionalState.FEAR, -0.1)
        return NodeStatus.SUCCESS
    else:
        npc.modify_emotion(EmotionalState.FEAR, 0.2)
        return NodeStatus.RUNNING


def explore_area(npc: Any, context: Dict) -> NodeStatus:
    """Eksploruje obszar"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.PATROLLING)
    
    # Zmień lokację jeśli to możliwe
    if hasattr(npc, 'explore_progress'):
        npc.explore_progress += 0.1
    else:
        npc.explore_progress = 0.1
    
    # Po pewnym czasie zmień lokację
    if npc.explore_progress >= 1.0:
        npc.explore_progress = 0
        # Tutaj można dodać faktyczną zmianę lokacji
        return NodeStatus.SUCCESS
    
    return NodeStatus.RUNNING


def observe_environment(npc: Any, context: Dict) -> NodeStatus:
    """Obserwuje otoczenie"""
    from .npc_manager import NPCState
    
    # Zapamiętaj co widzi
    if hasattr(npc, 'memory'):
        observation = {
            "time": context.get("current_time", 0),
            "location": npc.current_location,
            "npcs_present": [n.id for n in context.get("npcs", {}).values() if n.id != npc.id],
            "items": context.get("items", [])
        }
        npc.memory.store_episodic_memory("observation", observation)
    
    return NodeStatus.SUCCESS


def plan_action(npc: Any, context: Dict) -> NodeStatus:
    """Planuje następną akcję"""
    # Analizuj sytuację i ustal priorytet
    if npc.hunger > 70:
        npc.current_plan = "find_food"
    elif npc.energy < 30:
        npc.current_plan = "rest"
    elif hasattr(npc, 'goals') and npc.goals:
        npc.current_plan = "pursue_goal"
    else:
        npc.current_plan = "explore"
    
    return NodeStatus.SUCCESS


def check_surroundings(npc: Any, context: Dict) -> NodeStatus:
    """Sprawdza otoczenie"""
    # Szukaj zagrożeń i okazji
    threats = []
    opportunities = []
    
    for other_npc in context.get("npcs", {}).values():
        if other_npc.id != npc.id:
            if hasattr(npc, 'relationships') and npc.relationships.get(other_npc.id, {}).get("trust", 0) < -50:
                threats.append(other_npc.id)
            elif other_npc.role == "merchant":
                opportunities.append({"type": "trade", "target": other_npc.id})
    
    if threats:
        npc.current_threat = threats[0]
    if opportunities:
        npc.current_opportunity = opportunities[0]
    
    return NodeStatus.SUCCESS


def maintain_items(npc: Any, context: Dict) -> NodeStatus:
    """Konserwuje i naprawia przedmioty"""
    # Sprawdź stan ekwipunku
    if hasattr(npc, 'inventory'):
        for item_id, item in npc.inventory.items():
            if hasattr(item, 'durability') and item.durability < 50:
                # Napraw przedmiot jeśli możliwe
                if npc.role in ["guard", "warden"]:
                    item.durability = min(100, item.durability + 10)
                    return NodeStatus.SUCCESS
    
    return NodeStatus.SUCCESS


def practice_skills(npc: Any, context: Dict) -> NodeStatus:
    """Ćwiczy umiejętności"""
    # Trenuj umiejętności związane z rolą
    if npc.role == "guard":
        if hasattr(npc, 'combat_skill'):
            npc.combat_skill += 0.01
    elif npc.role == "prisoner":
        if hasattr(npc, 'stealth_skill'):
            npc.stealth_skill += 0.01
    
    return NodeStatus.SUCCESS


def seek_information(npc: Any, context: Dict) -> NodeStatus:
    """Szuka informacji"""
    # Zbieraj plotki i wiadomości
    if hasattr(npc, 'knowledge'):
        new_info = f"info_{context.get('current_time', 0)}"
        if new_info not in npc.knowledge:
            npc.knowledge.append(new_info)
    
    return NodeStatus.SUCCESS


def intimidate_prisoners(npc: Any, context: Dict) -> NodeStatus:
    """Zastraszanie więźniów (dla strażników)"""
    if npc.role not in ["guard", "warden"]:
        return NodeStatus.FAILURE
    
    # Zwiększ strach u więźniów w pobliżu
    for other_npc in context.get("npcs", {}).values():
        if other_npc.role == "prisoner" and other_npc.current_location == npc.current_location:
            if hasattr(other_npc, 'fear'):
                other_npc.fear = min(100, other_npc.fear + 10)
    
    return NodeStatus.SUCCESS


def inspect_cells(npc: Any, context: Dict) -> NodeStatus:
    """Inspekcja cel (dla strażników)"""
    if npc.role not in ["guard", "warden"]:
        return NodeStatus.FAILURE
    
    # Sprawdź cele w poszukiwaniu nielegalnych przedmiotów
    if hasattr(npc, 'inspection_progress'):
        npc.inspection_progress += 0.2
    else:
        npc.inspection_progress = 0.2
    
    if npc.inspection_progress >= 1.0:
        npc.inspection_progress = 0
        return NodeStatus.SUCCESS
    
    return NodeStatus.RUNNING


def personal_activity(npc: Any, context: Dict) -> NodeStatus:
    """Wykonuje osobistą aktywność w zależności od osobowości"""
    # Różne aktywności dla różnych typów osobowości
    if hasattr(npc, 'personality'):
        if "quiet" in npc.personality:
            # Ciche aktywności - czytanie, medytacja
            npc.energy = min(100, npc.energy + 5)
        elif "aggressive" in npc.personality:
            # Agresywne aktywności - ćwiczenia, trening
            if hasattr(npc, 'strength'):
                npc.strength += 0.1
        elif "social" in npc.personality:
            # Społeczne aktywności - rozmowy, plotki
            if hasattr(npc, 'social_need'):
                npc.social_need = max(0, npc.social_need - 10)
        else:
            # Domyślna aktywność - odpoczynek
            npc.energy = min(100, npc.energy + 2)
    
    return NodeStatus.SUCCESS


def morning_routine(npc: Any, context: Dict) -> NodeStatus:
    """Poranna rutyna NPCa"""
    # Różne rutyny dla różnych ról
    if npc.role == "guard":
        # Strażnik - sprawdza broń, przygotowuje się do patrolu
        if hasattr(npc, 'weapon'):
            npc.weapon['condition'] = 100
    elif npc.role == "prisoner":
        # Więzień - myje się, przygotowuje do dnia
        if hasattr(npc, 'hygiene'):
            npc.hygiene = 100
    
    if hasattr(npc, 'morning_done'):
        npc.morning_done = True
    return NodeStatus.SUCCESS


def evening_routine(npc: Any, context: Dict) -> NodeStatus:
    """Wieczorna rutyna NPCa"""
    # Przygotowanie do snu
    npc.energy = min(100, npc.energy + 10)
    if hasattr(npc, 'evening_done'):
        npc.evening_done = True
    return NodeStatus.SUCCESS


def desperate_food_search(npc: Any, context: Dict) -> NodeStatus:
    """Desperackie szukanie jedzenia"""
    from .npc_manager import NPCState
    
    # Szukaj jedzenia wszędzie
    food_locations = ["kitchen", "mess_hall", "storage", "garbage"]
    
    for location in food_locations:
        # Sprawdź pamięć o jedzeniu w tej lokacji
        food_memories = npc.recall_memories(
            query_type="food_found",
            location=location,
            limit=1
        )
        
        if food_memories:
            npc.location = location
            # Desperacja - zje wszystko
            npc.hunger = max(0, npc.hunger - 50)
            return NodeStatus.SUCCESS
    
    # Kradzież jedzenia od innych
    npcs_in_location = context.get("npcs", {})
    for other in npcs_in_location.values():
        if "food" in other.inventory:
            # Próba kradzieży lub prośby
            if npc.get_relationship(other.id).trust > 0:
                npc.interact_with(other.id, "beg_for_food", 1.0)
            else:
                npc.interact_with(other.id, "steal_attempt", 1.0)
            return NodeStatus.RUNNING
    
    return NodeStatus.FAILURE


def go_to_mess_hall(npc: Any, context: Dict) -> NodeStatus:
    """Idź do stołówki"""
    npc.location = "mess_hall"
    return NodeStatus.SUCCESS


def meal_socializing(npc: Any, context: Dict) -> NodeStatus:
    """Socjalizacja podczas posiłku"""
    from .npc_manager import NPCState
    
    # Znajdź kogoś do rozmowy przy posiłku
    npcs_in_location = context.get("npcs", {})
    dining_companions = [
        other for other in npcs_in_location.values()
        if other.id != npc.id and other.location == "mess_hall" 
        and other.current_state == NPCState.EATING
    ]
    
    if dining_companions:
        companion = random.choice(dining_companions)
        
        # Rozmów o różnych tematach
        topics = ["food_quality", "prison_gossip", "guard_behavior", "escape_rumors"]
        topic = random.choice(topics)
        
        # Wymień informacje
        if topic == "escape_rumors" and "escape_plan" in npc.semantic_memory:
            # Ostrożnie podziel się informacją
            if npc.get_relationship(companion.id).trust > 50:
                companion.semantic_memory["escape_rumor"] = {
                    "source": npc.id,
                    "credibility": 0.3
                }
        
        npc.interact_with(companion.id, "friendly_chat", 0.5)
        npc.modify_emotion(EmotionalState.HAPPY, 0.1)
        
        return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def eat_available_food(npc: Any, context: Dict) -> NodeStatus:
    """Zjada dostępne jedzenie"""
    if "food" in npc.inventory:
        npc.inventory["food"] -= 1
        if npc.inventory["food"] <= 0:
            del npc.inventory["food"]
        npc.hunger = max(0, npc.hunger - 30)
        return NodeStatus.SUCCESS
    return NodeStatus.FAILURE


def collapse_from_exhaustion(npc: Any, context: Dict) -> NodeStatus:
    """Upada z wyczerpania"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.RESTING)
    npc.energy = 0
    
    # Krytyczne wydarzenie
    npc.add_memory(
        event_type="collapsed",
        description="Upadł z wyczerpania",
        participants=[npc.id],
        location=npc.location,
        importance=0.7,
        emotional_impact={"fear": 0.4, "sad": 0.9}
    )
    
    # Inni mogą pomóc
    context["npc_needs_help"] = npc.id
    
    return NodeStatus.SUCCESS


def go_to_sleeping_area(npc: Any, context: Dict) -> NodeStatus:
    """Idź do miejsca do spania"""
    if npc.role == "prisoner":
        npc.location = f"cell_{npc.id[-1]}" if npc.id[-1].isdigit() else "cell_1"
    elif npc.role == "guard":
        npc.location = "guard_quarters"
    elif npc.role == "warden":
        npc.location = "warden_quarters"
    else:
        npc.location = "dormitory"
    
    return NodeStatus.SUCCESS


def take_power_nap(npc: Any, context: Dict) -> NodeStatus:
    """Krótka drzemka regeneracyjna"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.RESTING)
    npc.energy = min(npc.max_energy, npc.energy + 15)
    
    # Krótka drzemka nie regeneruje pełni sił
    npc.add_memory(
        event_type="nap",
        description="Wziął krótką drzemkę",
        participants=[npc.id],
        location=npc.location,
        importance=0.1
    )
    
    return NodeStatus.SUCCESS


def find_water(npc: Any, context: Dict) -> NodeStatus:
    """Szuka wody"""
    water_locations = ["bathroom", "kitchen", "mess_hall", "fountain"]
    
    # Znajdź najbliższe źródło wody
    for location in water_locations:
        # Sprawdź pamięć
        water_memories = npc.recall_memories(
            query_type="water_found",
            location=location,
            limit=1
        )
        
        if water_memories or random.random() < 0.3:
            npc.location = location
            return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def drink_water(npc: Any, context: Dict) -> NodeStatus:
    """Pije wodę"""
    npc.thirst = max(0, npc.thirst - 40)
    return NodeStatus.SUCCESS


def evening_routine(npc: Any, context: Dict) -> NodeStatus:
    """Wieczorna rutyna przed snem"""
    from .npc_manager import NPCState
    
    # Różne rutyny dla różnych osobowości
    if "organized" in npc.personality:
        # Przygotuj rzeczy na jutro
        npc.semantic_memory["tomorrow_prepared"] = True
    
    if "religious" in npc.personality:
        # Modlitwa
        npc.location = "chapel" if random.random() < 0.5 else npc.location
        npc.modify_emotion(EmotionalState.NEUTRAL, 0.2)
    
    if "paranoid" in npc.personality:
        # Sprawdź zabezpieczenia
        npc.semantic_memory["security_checked"] = time.time()
    
    # Higiena
    if random.random() < 0.7:
        npc.location = "bathroom"
    
    npc.energy = max(0, npc.energy - 5)
    return NodeStatus.SUCCESS


def deep_sleep_action(npc: Any, context: Dict) -> NodeStatus:
    """Głęboki sen - pełna regeneracja"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.SLEEPING)
    
    # Pełna regeneracja
    npc.energy = min(npc.max_energy, npc.energy + 15)
    npc.health = min(npc.max_health, npc.health + 2)
    
    # Przetwarzanie wspomnień podczas snu
    npc.memory.consolidate_all()
    
    # Sny - losowe przetwarzanie emocji
    if random.random() < 0.3:
        # Koszmar
        if npc.memory.emotional.trauma_memories:
            npc.modify_emotion(EmotionalState.FEAR, 0.2)
            npc.add_memory(
                event_type="nightmare",
                description="Miał koszmar",
                participants=[npc.id],
                location=npc.location,
                importance=0.2,
                emotional_impact={"fear": 0.3}
            )
    elif random.random() < 0.3:
        # Przyjemny sen
        if npc.memory.emotional.positive_memories:
            npc.modify_emotion(EmotionalState.HAPPY, 0.1)
    
    return NodeStatus.SUCCESS


def wake_up(npc: Any, context: Dict) -> NodeStatus:
    """Budzenie się"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.IDLE)
    
    # Stan po przebudzeniu zależy od jakości snu
    if npc.energy > 70:
        npc.modify_emotion(EmotionalState.HAPPY, 0.1)
    elif npc.energy < 30:
        npc.modify_emotion(EmotionalState.SAD, 0.1)
        npc.modify_emotion(EmotionalState.ANGRY, 0.1)
    
    return NodeStatus.SUCCESS


def morning_routine(npc: Any, context: Dict) -> NodeStatus:
    """Poranna rutyna"""
    from .npc_manager import NPCState
    
    # Różne poranki dla różnych NPców
    if npc.role == "guard":
        # Sprawdzenie ekwipunku
        if "weapon" not in npc.inventory:
            npc.location = "armory"
    elif npc.role == "prisoner":
        # Sprawdzenie celi
        if has_contraband(npc, context):
            # Ukryj przedmioty
            npc.semantic_memory["contraband_hidden"] = time.time()
    
    # Higiena poranna
    if random.random() < 0.8:
        npc.location = "bathroom"
        npc.thirst = max(0, npc.thirst - 10)
    
    # Planowanie dnia
    if "planner" in npc.personality:
        # Ustal cele na dziś
        for goal in npc.goals:
            if goal.active and goal.priority > 0.5:
                goal.priority = min(1.0, goal.priority + 0.1)
    
    return NodeStatus.SUCCESS


def extended_socializing(npc: Any, context: Dict) -> NodeStatus:
    """Rozszerzona socjalizacja podczas kolacji"""
    from .npc_manager import NPCState
    
    # Dłuższe rozmowy podczas kolacji
    npcs_at_dinner = context.get("npcs", {})
    dinner_group = [
        other for other in npcs_at_dinner.values()
        if other.location == "mess_hall" and other.id != npc.id
    ]
    
    if len(dinner_group) >= 2:
        # Rozmowa grupowa
        for other in dinner_group[:3]:  # Max 3 osoby
            npc.interact_with(other.id, "friendly_chat", 0.3)
        
        # Możliwość wymiany informacji
        if "talkative" in npc.personality:
            # Plotkowanie
            gossip = gather_gossip(npc, context)
            if gossip:
                for other in dinner_group:
                    if npc.get_relationship(other.id).trust > 20:
                        share_gossip(npc, other, gossip)
        
        npc.modify_emotion(EmotionalState.HAPPY, 0.2)
        return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def get_work_assignment(npc: Any, context: Dict) -> NodeStatus:
    """Pobiera przydzielone zadanie"""
    
    # Różne zadania dla różnych ról
    if npc.role == "prisoner":
        work_assignments = ["laundry", "kitchen", "workshop", "cleaning", "library"]
        npc.semantic_memory["current_work"] = random.choice(work_assignments)
    elif npc.role == "guard":
        work_assignments = ["patrol", "gate_duty", "cell_inspection", "escort_duty"]
        npc.semantic_memory["current_work"] = random.choice(work_assignments)
    else:
        npc.semantic_memory["current_work"] = "office_work"
    
    return NodeStatus.SUCCESS


def perform_work(npc: Any, context: Dict) -> NodeStatus:
    """Wykonuje przydzieloną pracę"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.WORKING)

    work_type = npc.memory.semantic.get("current_work", "general_work")
    
    # Lokalizacja pracy
    work_locations = {
        "laundry": "laundry_room",
        "kitchen": "kitchen",
        "workshop": "workshop",
        "cleaning": "corridor_main",
        "library": "library",
        "patrol": "corridor_main",
        "gate_duty": "main_gate",
        "cell_inspection": "cell_block",
        "escort_duty": "corridor_main",
        "office_work": "warden_office" if npc.role == "warden" else "guard_room"
    }
    
    npc.location = work_locations.get(work_type, npc.location)
    
    # Zużycie energii
    energy_cost = {
        "laundry": 8,
        "kitchen": 6,
        "workshop": 7,
        "cleaning": 5,
        "library": 3,
        "patrol": 10,
        "gate_duty": 4,
        "cell_inspection": 6,
        "escort_duty": 8,
        "office_work": 4
    }
    
    npc.energy = max(0, npc.energy - energy_cost.get(work_type, 5))
    
    # Możliwość znalezienia czegoś podczas pracy
    if random.random() < 0.1:
        find_during_work(npc, work_type)
    
    # Rozwiń umiejętność
    if work_type in ["workshop", "kitchen", "library"]:
        npc.memory.procedural.learn_skill(
            f"{work_type}_skill",
            [f"work_at_{work_type}", "use_tools", "complete_task"],
            context
        )
    
    return NodeStatus.SUCCESS


def take_work_break(npc: Any, context: Dict) -> NodeStatus:
    """Przerwa w pracy"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.RESTING)
    npc.energy = min(npc.max_energy, npc.energy + 5)
    
    # Krótka socjalizacja
    if random.random() < 0.5:
        socialize(npc, context)
    
    return NodeStatus.SUCCESS


def find_social_group(npc: Any, context: Dict) -> NodeStatus:
    """Znajduje grupę do socjalizacji"""
    
    # Preferowane miejsca socjalizacji
    social_locations = ["common_room", "exercise_yard", "mess_hall", "library"]
    
    # Znajdź miejsce z przyjaciółmi
    best_location = None
    best_score = 0
    
    npcs_dict = context.get("npcs", {})
    for location in social_locations:
        score = 0
        for other in npcs_dict.values():
            if other.location == location and other.id != npc.id:
                relationship = npc.get_relationship(other.id)
                if relationship.get_overall_disposition() > 0:
                    score += relationship.get_overall_disposition()
        
        if score > best_score:
            best_score = score
            best_location = location
    
    if best_location:
        npc.location = best_location
        return NodeStatus.SUCCESS
    
    # Brak przyjaciół - idź w losowe miejsce
    npc.location = random.choice(social_locations)
    return NodeStatus.RUNNING


def engage_in_group_activity(npc: Any, context: Dict) -> NodeStatus:
    """Uczestniczy w grupowej aktywności"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.SOCIALIZING)
    
    # Różne aktywności grupowe
    activities = [
        "card_game",
        "storytelling",
        "workout",
        "debate",
        "singing",
        "chess"
    ]
    
    activity = random.choice(activities)
    
    # Znajdź uczestników
    npcs_here = context.get("npcs", {})
    participants = [
        other for other in npcs_here.values()
        if other.location == npc.location and other.id != npc.id
    ]
    
    if participants:
        # Wspólna aktywność
        for participant in participants[:4]:  # Max 4 osoby
            npc.interact_with(participant.id, "group_activity", 0.5)
            
            # Budowanie relacji
            if activity in ["card_game", "chess"]:
                # Rywalizacja
                if random.random() < 0.5:
                    npc.modify_relationship(participant.id, respect=2, affection=1)
                else:
                    npc.modify_relationship(participant.id, respect=-1, affection=1)
            elif activity in ["storytelling", "singing"]:
                # Wspólna rozrywka
                npc.modify_relationship(participant.id, affection=3, familiarity=2)
            elif activity == "workout":
                # Wspólny trening
                npc.modify_relationship(participant.id, respect=2, trust=1)
        
        # Zapisz pamięć o aktywności
        npc.add_memory(
            event_type="group_activity",
            description=f"Uczestniczył w {activity} z {len(participants)} osobami",
            participants=[npc.id] + [p.id for p in participants],
            location=npc.location,
            importance=0.3,
            emotional_impact={"happy": 0.4, "surprise": 0.3}
        )
        
        npc.modify_emotion(EmotionalState.HAPPY, 0.3)
        return NodeStatus.SUCCESS
    
    # Brak towarzystwa
    npc.modify_emotion(EmotionalState.SAD, 0.1)
    return NodeStatus.FAILURE


def gather_gossip(npc: Any, context: Dict) -> Optional[Dict]:
    """Zbiera plotki"""
    
    # Sprawdź ostatnie wydarzenia
    recent_events = context.get("events", [])
    interesting_events = [
        e for e in recent_events[-20:]
        if e.get("importance", 0) > 0.3 and npc.id not in e.get("participants", [])
    ]
    
    if interesting_events:
        event = random.choice(interesting_events)
        return {
            "type": event.get("type"),
            "participants": event.get("participants"),
            "location": event.get("location"),
            "credibility": random.uniform(0.3, 0.9)
        }
    
    return None


def share_gossip(npc: Any, target: Any, gossip: Dict):
    """Dzieli się plotką"""
    
    # Przekaz plotkę
    target.semantic_memory[f"gossip_{time.time()}"] = {
        "content": gossip,
        "source": npc.id,
        "timestamp": time.time()
    }
    
    # Wzmocnij relację
    npc.modify_relationship(target.id, trust=1, affection=1, familiarity=2)


def find_during_work(npc: Any, work_type: str):
    """Znajduje coś podczas pracy"""
    
    findings = {
        "kitchen": ["food", "knife", "spoon"],
        "workshop": ["tool", "nail", "wire"],
        "laundry": ["soap", "cloth", "button"],
        "library": ["book", "paper", "pen"],
        "cleaning": ["coin", "key", "note"],
        "patrol": ["contraband", "weapon", "drugs"]
    }
    
    possible_finds = findings.get(work_type, ["trash"])
    found_item = random.choice(possible_finds)
    
    # Decyzja co zrobić ze znaleziskiem
    if npc.role == "guard" and found_item in ["contraband", "weapon", "drugs"]:
        # Zgłoś znalezisko
        npc.semantic_memory["found_contraband"] = {
            "item": found_item,
            "location": npc.location,
            "time": time.time()
        }
    else:
        # Zatrzymaj przedmiot
        npc.inventory[found_item] = npc.inventory.get(found_item, 0) + 1
    
    npc.add_memory(
        event_type="found_item",
        description=f"Znalazł {found_item} podczas pracy",
        participants=[npc.id],
        location=npc.location,
        importance=0.2
    )


# ============= ADVANCED BEHAVIOR NODES =============

class ParallelNode(BehaviorNode):
    """Węzeł równoległy - wykonuje wszystkie dzieci jednocześnie"""
    
    def __init__(self, name: str, success_threshold: int = 1, failure_threshold: int = 1):
        super().__init__(name)
        self.success_threshold = success_threshold
        self.failure_threshold = failure_threshold
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        successes = 0
        failures = 0
        running = 0
        
        for child in self.children:
            status = child.execute(npc, context)
            if status == NodeStatus.SUCCESS:
                successes += 1
            elif status == NodeStatus.FAILURE:
                failures += 1
            else:
                running += 1
        
        if successes >= self.success_threshold:
            return NodeStatus.SUCCESS
        if failures >= self.failure_threshold:
            return NodeStatus.FAILURE
        if running > 0:
            return NodeStatus.RUNNING
        return NodeStatus.FAILURE


class InterruptableSequenceNode(SequenceNode):
    """Sekwencja z możliwością przerwania przez ważniejsze zadanie"""
    
    def __init__(self, name: str, interrupt_checker=None):
        super().__init__(name)
        self.interrupt_checker = interrupt_checker
        self.current_child_index = 0
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        # Sprawdź czy należy przerwać
        if self.interrupt_checker and self.interrupt_checker(npc, context):
            self.current_child_index = 0  # Reset
            return NodeStatus.FAILURE
        
        # Kontynuuj od miejsca gdzie skończyliśmy
        while self.current_child_index < len(self.children):
            child = self.children[self.current_child_index]
            status = child.execute(npc, context)
            
            if status == NodeStatus.FAILURE:
                self.current_child_index = 0
                return NodeStatus.FAILURE
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            self.current_child_index += 1
        
        self.current_child_index = 0
        return NodeStatus.SUCCESS


class BlackboardNode(BehaviorNode):
    """Węzeł z dostępem do współdzielonej pamięci (blackboard)"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.blackboard = {}
    
    def set_value(self, key: str, value: Any):
        self.blackboard[key] = value
    
    def get_value(self, key: str, default=None):
        return self.blackboard.get(key, default)
    
    def clear_blackboard(self):
        self.blackboard.clear()
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        """Wykonuje dzieci z dostępem do blackboard"""
        # Dodaj blackboard do kontekstu
        context['blackboard'] = self.blackboard
        
        # Wykonaj pierwsze dziecko (jeśli istnieje)
        if self.children:
            return self.children[0].execute(npc, context)
        return NodeStatus.SUCCESS


class TimeGatedNode(DecoratorNode):
    """Węzeł wykonywany tylko w określonych godzinach"""
    
    def __init__(self, name: str, child: BehaviorNode, start_hour: int, end_hour: int):
        super().__init__(name, child)
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        hour = context.get("hour", 12)
        
        # Obsłuż przedział przez północ
        if self.start_hour > self.end_hour:
            if hour >= self.start_hour or hour < self.end_hour:
                return self.child.execute(npc, context)
        else:
            if self.start_hour <= hour < self.end_hour:
                return self.child.execute(npc, context)
        
        return NodeStatus.FAILURE


class CooldownNode(DecoratorNode):
    """Węzeł z cooldownem - nie może być wykonany zbyt często"""
    
    def __init__(self, name: str, child: BehaviorNode, cooldown_seconds: float):
        super().__init__(name, child)
        self.cooldown_seconds = cooldown_seconds
        self.last_execution = 0
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        current_time = time.time()
        if current_time - self.last_execution < self.cooldown_seconds:
            return NodeStatus.FAILURE
        
        result = self.child.execute(npc, context)
        if result == NodeStatus.SUCCESS:
            self.last_execution = current_time
        
        return result


class ProbabilityNode(DecoratorNode):
    """Węzeł wykonywany z określonym prawdopodobieństwem"""
    
    def __init__(self, name: str, child: BehaviorNode, probability: float):
        super().__init__(name, child)
        self.probability = min(1.0, max(0.0, probability))
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        if random.random() < self.probability:
            return self.child.execute(npc, context)
        return NodeStatus.FAILURE


# ============= TWORZENIE BEHAVIOR TREES =============

def create_behavior_tree(role: str, personality: List[str]) -> BehaviorNode:
    """Tworzy zaawansowane behavior tree dla NPCa"""
    
    # Główny węzeł z blackboardem
    root = BlackboardNode("root")
    priority_root = PriorityNode("priority_root")
    
    # Sekcja krytyczna - najwyższy priorytet z przerwaniem
    critical_selector = SelectorNode("critical_responses")
    
    # Zagrożenie życia - natychmiastowa reakcja
    life_threat_parallel = ParallelNode("life_threat_response", success_threshold=1)
    
    # Sprawdź różne zagrożenia równolegle
    attack_check = SequenceNode("attack_response")
    attack_check.add_child(ConditionalNode("is_under_attack", is_under_attack))
    attack_check.add_child(ProbabilityNode("fight_or_flight", 
        ActionNode("defend", defend) if "brave" in personality else ActionNode("flee", flee),
        0.7 if "brave" in personality else 0.3
    ))
    life_threat_parallel.add_child(attack_check)
    
    # Krytyczne obrażenia
    critical_injury_sequence = SequenceNode("critical_injury")
    critical_injury_sequence.add_child(ConditionalNode("is_critically_injured", is_critically_injured))
    critical_injury_sequence.add_child(ActionNode("seek_medical_help", seek_medical_attention))
    life_threat_parallel.add_child(critical_injury_sequence)
    
    # Pożar lub inne zagrożenie środowiskowe
    environmental_threat = SequenceNode("environmental_threat")
    environmental_threat.add_child(ConditionalNode("is_environmental_danger", 
        lambda n, c: c.get("fire", False) or c.get("flood", False)))
    environmental_threat.add_child(ActionNode("evacuate", evacuate_area))
    life_threat_parallel.add_child(environmental_threat)
    
    critical_selector.add_child(life_threat_parallel)
    
    priority_root.add_child_with_priority(critical_selector, 100.0)
    
    # Sekcja potrzeb fizjologicznych z przerwaniem
    needs_selector = InterruptableSequenceNode("physical_needs",
        interrupt_checker=lambda n, c: is_under_attack(n, c) or c.get("emergency", False)
    )
    
    # Kompleksowe zarządzanie głodem
    hunger_management = SelectorNode("hunger_management")
    
    # Ekstremny głód - priorytet
    extreme_hunger = SequenceNode("extreme_hunger")
    extreme_hunger.add_child(ConditionalNode("is_starving", lambda n, c: n.hunger > 90))
    extreme_hunger.add_child(ActionNode("desperate_food_search", desperate_food_search))
    hunger_management.add_child(extreme_hunger)
    
    # Normalny głód z czasem posiłku
    meal_time_eating = SequenceNode("scheduled_meal")
    meal_time_eating.add_child(ConditionalNode("is_meal_time", is_meal_time))
    meal_time_eating.add_child(ConditionalNode("is_hungry", is_hungry))
    meal_time_eating.add_child(ActionNode("go_to_mess_hall", go_to_mess_hall))
    meal_time_eating.add_child(ActionNode("eat_meal", eat_meal))
    meal_time_eating.add_child(ActionNode("socialize_during_meal", meal_socializing))
    hunger_management.add_child(meal_time_eating)
    
    # Oportunistyczne jedzenie
    opportunistic_eating = SequenceNode("opportunistic_eating")
    opportunistic_eating.add_child(ConditionalNode("food_available", 
        lambda n, c: "food" in n.inventory or c.get("food_nearby", False)))
    opportunistic_eating.add_child(ConditionalNode("moderately_hungry", 
        lambda n, c: n.hunger > 40))
    opportunistic_eating.add_child(ActionNode("eat_available_food", eat_available_food))
    hunger_management.add_child(opportunistic_eating)
    
    needs_selector.add_child(hunger_management)
    
    # Zarządzanie energią i snem
    energy_management = SelectorNode("energy_management")
    
    # Krytyczne wyczerpanie
    collapse_sequence = SequenceNode("collapse")
    collapse_sequence.add_child(ConditionalNode("about_to_collapse", 
        lambda n, c: n.energy < 5))
    collapse_sequence.add_child(ActionNode("collapse", collapse_from_exhaustion))
    energy_management.add_child(collapse_sequence)
    
    # Planowany sen
    scheduled_sleep = SequenceNode("scheduled_sleep")
    scheduled_sleep.add_child(TimeGatedNode("night_time", 
        ConditionalNode("is_tired", is_tired), 22, 6))
    scheduled_sleep.add_child(ActionNode("go_to_bed", go_to_sleeping_area))
    scheduled_sleep.add_child(ActionNode("sleep", sleep))
    energy_management.add_child(scheduled_sleep)
    
    # Drzemka w ciągu dnia
    power_nap = SequenceNode("power_nap")
    power_nap.add_child(ConditionalNode("very_tired_daytime", 
        lambda n, c: n.energy < 20 and 6 <= c.get("hour", 12) < 22))
    power_nap.add_child(CooldownNode("nap_cooldown", 
        ActionNode("take_nap", take_power_nap), 7200))  # Max co 2 godziny
    energy_management.add_child(power_nap)
    
    needs_selector.add_child(energy_management)
    
    # Zarządzanie pragnieniem
    thirst_management = SequenceNode("thirst_management")
    thirst_management.add_child(ConditionalNode("is_thirsty", is_thirsty))
    thirst_management.add_child(ActionNode("find_water", find_water))
    thirst_management.add_child(ActionNode("drink", drink_water))
    needs_selector.add_child(thirst_management)
    
    priority_root.add_child_with_priority(needs_selector, 80.0)
    
    # Zaawansowany system harmonogramu z elastycznością
    schedule_system = SelectorNode("advanced_schedule")
    
    # System snu z różnymi fazami
    sleep_system = SequenceNode("sleep_system")
    
    # Przygotowanie do snu
    bedtime_routine = SequenceNode("bedtime_routine")
    bedtime_routine.add_child(TimeGatedNode("pre_sleep_time",
        ConditionalNode("getting_tired", lambda n, c: n.energy < 40),
        21, 23))
    bedtime_routine.add_child(ActionNode("evening_hygiene", evening_routine))
    bedtime_routine.add_child(ActionNode("go_to_bed", go_to_sleeping_area))
    sleep_system.add_child(bedtime_routine)
    
    # Głęboki sen
    deep_sleep = SequenceNode("deep_sleep")
    deep_sleep.add_child(TimeGatedNode("night_hours",
        ConditionalNode("is_sleeping", lambda n, c: n.current_state.value == "sleeping"),
        23, 5))
    deep_sleep.add_child(ActionNode("sleep_deeply", deep_sleep_action))
    sleep_system.add_child(deep_sleep)
    
    # Budzenie się
    wake_routine = SequenceNode("wake_routine")
    wake_routine.add_child(TimeGatedNode("wake_time",
        ConditionalNode("time_to_wake", lambda n, c: True),
        5, 7))
    wake_routine.add_child(ActionNode("wake_up", wake_up))
    wake_routine.add_child(ActionNode("morning_routine", morning_routine))
    sleep_system.add_child(wake_routine)
    
    schedule_system.add_child(sleep_system)
    
    # System posiłków z preferencjami
    meal_system = SelectorNode("meal_system")
    
    # Śniadanie
    breakfast = SequenceNode("breakfast")
    breakfast.add_child(TimeGatedNode("breakfast_time",
        ConditionalNode("is_hungry_morning", lambda n, c: n.hunger > 30),
        6, 8))
    breakfast.add_child(ActionNode("go_to_breakfast", go_to_mess_hall))
    breakfast.add_child(ActionNode("eat_breakfast", eat_meal))
    breakfast.add_child(ProbabilityNode("breakfast_social",
        ActionNode("morning_chat", meal_socializing), 0.6))
    meal_system.add_child(breakfast)
    
    # Obiad
    lunch = SequenceNode("lunch")
    lunch.add_child(TimeGatedNode("lunch_time",
        ConditionalNode("is_hungry_noon", lambda n, c: n.hunger > 40),
        11, 14))
    lunch.add_child(ActionNode("go_to_lunch", go_to_mess_hall))
    lunch.add_child(ActionNode("eat_lunch", eat_meal))
    lunch.add_child(ActionNode("lunch_social", meal_socializing))
    meal_system.add_child(lunch)
    
    # Kolacja
    dinner = SequenceNode("dinner")
    dinner.add_child(TimeGatedNode("dinner_time",
        ConditionalNode("is_hungry_evening", lambda n, c: n.hunger > 35),
        17, 19))
    dinner.add_child(ActionNode("go_to_dinner", go_to_mess_hall))
    dinner.add_child(ActionNode("eat_dinner", eat_meal))
    dinner.add_child(ActionNode("dinner_social", extended_socializing))
    meal_system.add_child(dinner)
    
    schedule_system.add_child(meal_system)
    
    # System pracy z różnymi zadaniami
    work_system = InterruptableSequenceNode("work_system",
        interrupt_checker=lambda n, c: is_under_attack(n, c) or c.get("work_emergency", False)
    )
    
    work_assignment = SequenceNode("work_assignment")
    work_assignment.add_child(TimeGatedNode("work_hours",
        ConditionalNode("is_work_time", is_work_time),
        8, 17))
    work_assignment.add_child(ConditionalNode("not_too_tired",
        lambda n, c: n.energy > 20))
    work_assignment.add_child(ActionNode("get_assignment", get_work_assignment))
    work_assignment.add_child(ActionNode("do_work", perform_work))
    work_assignment.add_child(CooldownNode("work_break",
        ActionNode("take_break", take_work_break), 3600))  # Przerwa co godzinę
    work_system.add_child(work_assignment)
    
    schedule_system.add_child(work_system)
    
    # System socjalizacji z dynamicznymi grupami
    social_system = SelectorNode("social_system")
    
    # Planowana socjalizacja
    planned_social = SequenceNode("planned_social")
    planned_social.add_child(TimeGatedNode("social_hours",
        ConditionalNode("is_social_time", is_social_time),
        19, 22))
    planned_social.add_child(ConditionalNode("wants_to_socialize",
        lambda n, c: n.emotional_states.get(EmotionalState.SAD, 0) > 0.3 or 
                     "social" in n.personality))
    planned_social.add_child(ActionNode("find_friends", find_social_group))
    planned_social.add_child(ActionNode("group_activity", engage_in_group_activity))
    social_system.add_child(planned_social)
    
    # Spontaniczna socjalizacja
    spontaneous_social = SequenceNode("spontaneous_social")
    spontaneous_social.add_child(ConditionalNode("opportunity_to_socialize",
        lambda n, c: can_work_together(n, c) and random.random() < 0.3))
    spontaneous_social.add_child(ProbabilityNode("mood_for_chat",
        ActionNode("spontaneous_chat", socialize), 0.5))
    social_system.add_child(spontaneous_social)
    
    schedule_system.add_child(social_system)
    
    priority_root.add_child_with_priority(schedule_system, 60.0)
    
    # System celów i planowania
    goal_system = SelectorNode("goal_system")
    
    # Pilne cele
    urgent_goals = SequenceNode("urgent_goals")
    urgent_goals.add_child(ConditionalNode("has_urgent_goal", has_urgent_goal))
    urgent_goals.add_child(ActionNode("pursue_urgent_goal", pursue_urgent_goal))
    goal_system.add_child(urgent_goals)
    
    # Długoterminowe cele
    longterm_goals = SequenceNode("longterm_goals")
    longterm_goals.add_child(ConditionalNode("has_active_goal", 
        lambda n, c: any(g.active and g.completion < 1.0 for g in n.goals)))
    longterm_goals.add_child(ActionNode("work_on_goal", work_on_goal))
    goal_system.add_child(longterm_goals)
    
    priority_root.add_child_with_priority(goal_system, 50.0)
    
    # Zachowania specyficzne dla roli
    if role == "warden" and create_advanced_warden_behavior:
        warden_behavior = create_advanced_warden_behavior(personality)
        priority_root.add_child_with_priority(warden_behavior, 70.0)
    elif role == "guard" and create_advanced_guard_behavior:
        guard_behavior = create_advanced_guard_behavior(personality)
        priority_root.add_child_with_priority(guard_behavior, 70.0)
    elif role == "prisoner" and create_advanced_prisoner_behavior:
        prisoner_behavior = create_advanced_prisoner_behavior(personality)
        priority_root.add_child_with_priority(prisoner_behavior, 65.0)
    elif role == "creature":
        if create_advanced_creature_behavior:
            creature_behavior = create_advanced_creature_behavior(personality)
        else:
            creature_behavior = create_creature_behavior(personality)
        priority_root.add_child_with_priority(creature_behavior, 60.0)
    
    # System osobowości z głębokimi cechami
    if create_deep_personality_behavior:
        personality_behavior = create_deep_personality_behavior(personality, role)
        if personality_behavior:
            priority_root.add_child_with_priority(personality_behavior, 40.0)
    
    # System nawyków i rutyn
    if create_habit_system:
        habit_system = create_habit_system(npc_id=personality[0] if personality else "default")
        priority_root.add_child_with_priority(habit_system, 30.0)
    
    # System reakcji emocjonalnych
    if create_emotional_reaction_system:
        emotional_system = create_emotional_reaction_system(personality)
        priority_root.add_child_with_priority(emotional_system, 35.0)
    
    # Domyślne zachowania z większą złożonością
    default_behavior = RandomSelectorNode("default_behavior")
    default_behavior.add_child(ActionNode("intelligent_rest", rest))
    default_behavior.add_child(ActionNode("explore", explore_area))
    default_behavior.add_child(ActionNode("observe_surroundings", observe_environment))
    default_behavior.add_child(ActionNode("maintain_equipment", maintain_items))
    default_behavior.add_child(ActionNode("personal_time", personal_activity))
    
    priority_root.add_child_with_priority(default_behavior, 10.0)
    
    # Przypisz do głównego węzła z blackboardem
    root.add_child(priority_root)
    return root


def create_warden_behavior(personality: List[str]) -> BehaviorNode:
    """Tworzy zachowania specyficzne dla naczelnika"""
    warden_selector = SelectorNode("warden_duties")
    
    # Patrol i kontrola
    patrol_sequence = SequenceNode("warden_patrol")
    patrol_sequence.add_child(ConditionalNode("sees_prisoner", sees_prisoner_escaping))
    patrol_sequence.add_child(ActionNode("catch_prisoner", attack_target))
    warden_selector.add_child(patrol_sequence)
    
    # Zastraszanie (jeśli sadysta)
    if "sadistic" in personality:
        intimidate_sequence = SequenceNode("intimidate_prisoners")
        intimidate_sequence.add_child(ConditionalNode("sees_prisoner", sees_player))
        intimidate_sequence.add_child(ActionNode("intimidate", intimidate))
        warden_selector.add_child(intimidate_sequence)
    
    # Ucieczka przed ciemnością (jeśli boi się ciemności)
    if "fears_darkness" in personality:
        darkness_sequence = SequenceNode("avoid_darkness")
        darkness_sequence.add_child(ConditionalNode("is_dark", is_in_darkness))
        darkness_sequence.add_child(ActionNode("flee_darkness", hide_in_shadows))
        warden_selector.add_child(darkness_sequence)
    
    # Praca biurowa
    warden_selector.add_child(ActionNode("office_work", work))
    
    return warden_selector


def create_guard_behavior(personality: List[str]) -> BehaviorNode:
    """Tworzy zachowania specyficzne dla strażnika"""
    guard_selector = SelectorNode("guard_duties")
    
    # Patrol
    patrol_sequence = SequenceNode("guard_patrol")
    patrol_sequence.add_child(ConditionalNode("is_work_time", is_work_time))
    patrol_sequence.add_child(ActionNode("patrol", patrol))
    guard_selector.add_child(patrol_sequence)
    
    # Łapanie uciekinierów
    catch_sequence = SequenceNode("catch_escapees")
    catch_sequence.add_child(ConditionalNode("sees_escaping", sees_prisoner_escaping))
    catch_sequence.add_child(ActionNode("catch", attack_target))
    guard_selector.add_child(catch_sequence)
    
    # Korupcja (jeśli skorumpowany)
    if "corruptible" in personality:
        bribe_sequence = SequenceNode("accept_bribes")
        bribe_sequence.add_child(ConditionalNode("can_afford", can_afford_bribe))
        bribe_sequence.add_child(ActionNode("take_bribe", accept_bribe))
        guard_selector.add_child(bribe_sequence)
    
    return guard_selector


def create_prisoner_behavior(personality: List[str]) -> BehaviorNode:
    """Tworzy zachowania specyficzne dla więźnia"""
    prisoner_selector = SelectorNode("prisoner_behavior")
    
    # Planowanie ucieczki (Cicha Anna)
    if "quiet" in personality or "planner" in personality:
        escape_sequence = SequenceNode("plan_escape")
        escape_sequence.add_child(ConditionalNode("has_plan", has_escape_plan))
        escape_sequence.add_child(ActionNode("execute_escape", plan_escape))
        prisoner_selector.add_child(escape_sequence)
    
    # Dzielenie się informacją o tunelu (Stary Józek)
    if "knowledgeable" in personality:
        share_sequence = SequenceNode("share_knowledge")
        share_sequence.add_child(ConditionalNode("knows_tunnel", knows_about_tunnel))
        share_sequence.add_child(ConditionalNode("trusts", trusts_player))
        share_sequence.add_child(ActionNode("share_info", share_tunnel_info))
        prisoner_selector.add_child(share_sequence)
    
    # Handel informacjami (Gadatliwy Piotr)
    if "talkative" in personality or "informant" in personality:
        trade_sequence = SequenceNode("information_trade")
        trade_sequence.add_child(ConditionalNode("has_info", has_important_info))
        trade_sequence.add_child(ActionNode("trade_info", trade_information))
        prisoner_selector.add_child(trade_sequence)
        
        # Zbieranie informacji
        gather_sequence = SequenceNode("gather_info")
        gather_sequence.add_child(InverterNode("not_has_info", 
                                              ConditionalNode("has_info", has_important_info)))
        gather_sequence.add_child(ActionNode("gather", gather_information))
        prisoner_selector.add_child(gather_sequence)
    
    # Praca (jeśli nie planuje ucieczki)
    work_sequence = SequenceNode("prisoner_work")
    work_sequence.add_child(ConditionalNode("work_time", is_work_time))
    work_sequence.add_child(ActionNode("do_labor", work))
    prisoner_selector.add_child(work_sequence)
    
    return prisoner_selector


def create_personality_behavior(personality: List[str]) -> Optional[BehaviorNode]:
    """Tworzy zachowania bazowane na cechach osobowości"""
    if not personality:
        return None
    
    personality_selector = SelectorNode("personality_traits")
    
    # Zachowania dla różnych cech
    if "aggressive" in personality:
        aggro_sequence = SequenceNode("aggressive_behavior")
        aggro_sequence.add_child(ConditionalNode("sees_enemy", 
                                                lambda n, c: n.get_dominant_emotion() == EmotionalState.ANGRY))
        aggro_sequence.add_child(ActionNode("act_aggressive", intimidate))
        personality_selector.add_child(aggro_sequence)
    
    if "cowardly" in personality:
        coward_sequence = SequenceNode("cowardly_behavior")
        coward_sequence.add_child(ConditionalNode("is_scared", 
                                                 lambda n, c: n.get_dominant_emotion() == EmotionalState.FEAR))
        coward_sequence.add_child(ActionNode("hide", flee))
        personality_selector.add_child(coward_sequence)
    
    if "greedy" in personality:
        greed_sequence = SequenceNode("greedy_behavior")
        greed_sequence.add_child(ConditionalNode("opportunity_for_gold", 
                                                lambda n, c: "bribe_offer" in c or "trade_offer" in c))
        greed_sequence.add_child(ActionNode("pursue_gold", accept_bribe))
        personality_selector.add_child(greed_sequence)
    
    if "helpful" in personality:
        help_sequence = SequenceNode("helpful_behavior")
        help_sequence.add_child(ConditionalNode("someone_needs_help", 
                                               lambda n, c: any(e.get("type") == "help_request" 
                                                              for e in c.get("events", []))))
        help_sequence.add_child(ActionNode("provide_help", 
                                          lambda n, c: n.interact_with(c.get("requester", "unknown"), "help")))
        personality_selector.add_child(help_sequence)
    
    return personality_selector if personality_selector.children else None


# Importy dla akcji
from enum import Enum
class EmotionalState(Enum):
    HAPPY = "happy"
    ANGRY = "angry"
    FEAR = "fear"
    SAD = "sad"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"