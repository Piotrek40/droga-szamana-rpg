"""
Zaawansowane funkcje zachowań NPCów dla systemu Behavior Trees
Rozszerzenie podstawowego systemu o złożone interakcje i strategie
"""

from typing import List, Optional, Dict, Any
import random
import time

# Import specific classes to avoid circular dependency
from .ai_behaviors import (
    BehaviorNode, NodeStatus, 
    SelectorNode, SequenceNode, ParallelNode,
    ActionNode, ConditionalNode,
    PriorityNode, InterruptableSequenceNode, TimeGatedNode,
    RandomSelectorNode, RepeatNode, CooldownNode, ProbabilityNode,
    # Import necessary functions
    is_hungry, is_tired, is_injured,
    eat_meal, sleep, rest, patrol,
    is_work_time, is_sleep_time, is_meal_time
)


def create_advanced_warden_behavior(personality: List[str]) -> BehaviorNode:
    """Tworzy zaawansowane zachowania naczelnika więzienia"""
    warden_root = PriorityNode("advanced_warden")
    
    # System autorytetu i kontroli
    authority_system = ParallelNode("authority_system", success_threshold=2)
    
    # Inspekcje więzienia
    inspection_routine = InterruptableSequenceNode("inspection_routine",
        interrupt_checker=lambda n, c: is_riot_starting(n, c))
    
    morning_inspection = SequenceNode("morning_inspection")
    morning_inspection.add_child(TimeGatedNode("morning_time",
        ConditionalNode("is_morning", lambda n, c: 6 <= c.get("hour", 12) < 10),
        6, 10))
    morning_inspection.add_child(ActionNode("inspect_cells", inspect_prison_cells))
    morning_inspection.add_child(ActionNode("check_prisoners", check_prisoner_count))
    morning_inspection.add_child(ActionNode("document_issues", document_violations))
    inspection_routine.add_child(morning_inspection)
    
    evening_inspection = SequenceNode("evening_inspection")
    evening_inspection.add_child(TimeGatedNode("evening_time",
        ConditionalNode("is_evening", lambda n, c: 18 <= c.get("hour", 12) < 22),
        18, 22))
    evening_inspection.add_child(ActionNode("evening_rounds", evening_security_check))
    evening_inspection.add_child(ActionNode("lock_down", initiate_lockdown))
    inspection_routine.add_child(evening_inspection)
    
    authority_system.add_child(inspection_routine)
    
    # Zarządzanie strażnikami
    guard_management = SequenceNode("guard_management")
    guard_management.add_child(ConditionalNode("guards_present",
        lambda n, c: any(npc.role == "guard" for npc in c.get("npcs", {}).values())))
    guard_management.add_child(ActionNode("assign_duties", assign_guard_duties))
    guard_management.add_child(CooldownNode("evaluate_guards_cooldown",
        ActionNode("evaluate_performance", evaluate_guards), 3600))
    authority_system.add_child(guard_management)
    
    # System kar i nagród
    discipline_system = SelectorNode("discipline_system")
    
    punishment_sequence = SequenceNode("punishment")
    punishment_sequence.add_child(ConditionalNode("violation_detected",
        lambda n, c: "violation" in n.semantic_memory))
    punishment_sequence.add_child(ActionNode("decide_punishment", decide_punishment))
    punishment_sequence.add_child(ActionNode("execute_punishment", execute_punishment))
    discipline_system.add_child(punishment_sequence)
    
    reward_sequence = SequenceNode("rewards")
    reward_sequence.add_child(ConditionalNode("good_behavior_noticed",
        lambda n, c: random.random() < 0.1))
    reward_sequence.add_child(ActionNode("grant_privilege", grant_prisoner_privilege))
    discipline_system.add_child(reward_sequence)
    
    authority_system.add_child(discipline_system)
    
    warden_root.add_child_with_priority(authority_system, 90.0)
    
    # Specjalne zachowania Brutusa
    if "sadistic" in personality:
        sadistic_behavior = create_sadistic_behavior()
        warden_root.add_child_with_priority(sadistic_behavior, 85.0)
    
    if "fears_darkness" in personality:
        darkness_avoidance = create_darkness_avoidance_behavior()
        warden_root.add_child_with_priority(darkness_avoidance, 95.0)
    
    # Zarządzanie kryzysowe
    crisis_management = create_crisis_management_behavior()
    warden_root.add_child_with_priority(crisis_management, 100.0)
    
    return warden_root


def create_advanced_guard_behavior(personality: List[str]) -> BehaviorNode:
    """Tworzy zaawansowane zachowania strażnika"""
    guard_root = PriorityNode("advanced_guard")
    
    # System patroli z inteligentnym trasowaniem
    patrol_system = SequenceNode("intelligent_patrol")
    
    # Planowanie trasy patrolu
    route_planning = SequenceNode("route_planning")
    route_planning.add_child(ConditionalNode("start_shift",
        lambda n, c: c.get("hour", 12) in [8, 14, 20]))
    route_planning.add_child(ActionNode("plan_route", plan_patrol_route))
    route_planning.add_child(ActionNode("check_equipment", check_guard_equipment))
    patrol_system.add_child(route_planning)
    
    # Wykonywanie patrolu
    patrol_execution = InterruptableSequenceNode("patrol_execution",
        interrupt_checker=lambda n, c: is_suspicious_activity(n, c) or is_under_attack(n, c))
    
    patrol_execution.add_child(ActionNode("follow_route", follow_patrol_route))
    patrol_execution.add_child(ProbabilityNode("random_check",
        ActionNode("random_cell_check", random_cell_inspection), 0.3))
    patrol_execution.add_child(ActionNode("log_patrol", log_patrol_activity))
    patrol_system.add_child(patrol_execution)
    
    guard_root.add_child_with_priority(patrol_system, 70.0)
    
    # System wykrywania i reagowania na zagrożenia
    threat_detection = ParallelNode("threat_detection", success_threshold=1)
    
    # Wykrywanie ucieczek
    escape_detection = SequenceNode("escape_detection")
    escape_detection.add_child(ConditionalNode("prisoner_out_of_place",
        sees_prisoner_escaping))
    escape_detection.add_child(ActionNode("raise_alarm", raise_escape_alarm))
    escape_detection.add_child(ActionNode("pursue_escapee", pursue_escapee))
    threat_detection.add_child(escape_detection)
    
    # Wykrywanie przemytu
    contraband_detection = SequenceNode("contraband_detection")
    contraband_detection.add_child(ConditionalNode("suspicious_behavior",
        lambda n, c: is_suspicious_activity(n, c)))
    contraband_detection.add_child(ActionNode("search_prisoner", search_for_contraband))
    contraband_detection.add_child(ActionNode("confiscate", confiscate_items))
    threat_detection.add_child(contraband_detection)
    
    # Wykrywanie bójek
    fight_detection = SequenceNode("fight_detection")
    fight_detection.add_child(ConditionalNode("fight_in_progress",
        lambda n, c: "fight" in [e.get("type") for e in c.get("events", [])[-5:]]))
    fight_detection.add_child(ActionNode("break_up_fight", intervene_in_fight))
    fight_detection.add_child(ActionNode("detain_fighters", detain_combatants))
    threat_detection.add_child(fight_detection)
    
    guard_root.add_child_with_priority(threat_detection, 85.0)
    
    # Korupcja (dla Marka)
    if "corruptible" in personality:
        corruption_behavior = create_corruption_behavior()
        guard_root.add_child_with_priority(corruption_behavior, 60.0)
    
    # Współpraca ze strażnikami
    teamwork = create_guard_teamwork_behavior()
    guard_root.add_child_with_priority(teamwork, 65.0)
    
    return guard_root


def create_advanced_prisoner_behavior(personality: List[str]) -> BehaviorNode:
    """Tworzy zaawansowane zachowania więźnia"""
    prisoner_root = PriorityNode("advanced_prisoner")
    
    # System przetrwania w więzieniu
    survival_system = ParallelNode("prison_survival", success_threshold=2)
    
    # Unikanie zagrożeń
    threat_avoidance = SelectorNode("threat_avoidance")
    
    avoid_guards = SequenceNode("avoid_guards")
    avoid_guards.add_child(ConditionalNode("guard_nearby",
        lambda n, c: any(npc.role == "guard" and npc.location == n.location 
                        for npc in c.get("npcs", {}).values())))
    avoid_guards.add_child(ConditionalNode("has_contraband", has_contraband))
    avoid_guards.add_child(ActionNode("act_casual", act_casual))
    threat_avoidance.add_child(avoid_guards)
    
    avoid_enemies = SequenceNode("avoid_enemies")
    avoid_enemies.add_child(ConditionalNode("enemy_nearby",
        lambda n, c: any(n.get_relationship(npc.id).get_overall_disposition() < -50 
                        and npc.location == n.location
                        for npc in c.get("npcs", {}).values())))
    avoid_enemies.add_child(ActionNode("change_location", flee))
    threat_avoidance.add_child(avoid_enemies)
    
    survival_system.add_child(threat_avoidance)
    
    # Budowanie sojuszy
    alliance_building = SequenceNode("alliance_building")
    alliance_building.add_child(ConditionalNode("needs_allies",
        lambda n, c: sum(1 for r in n.relationships.values() 
                        if r.get_overall_disposition() > 30) < 2))
    alliance_building.add_child(ActionNode("find_potential_ally", find_potential_allies))
    alliance_building.add_child(ActionNode("build_trust", build_prisoner_trust))
    survival_system.add_child(alliance_building)
    
    # Zdobywanie zasobów
    resource_acquisition = SelectorNode("resource_acquisition")
    
    legal_acquisition = SequenceNode("legal_acquisition")
    legal_acquisition.add_child(ConditionalNode("can_work", 
        lambda n, c: n.energy > 30))
    legal_acquisition.add_child(ActionNode("work_for_resources", work_for_payment))
    resource_acquisition.add_child(legal_acquisition)
    
    trading = SequenceNode("trading")
    trading.add_child(ConditionalNode("has_tradeable_items",
        lambda n, c: any(item in n.inventory for item in ["cigarettes", "food", "information"])))
    trading.add_child(ActionNode("find_trader", find_trading_partner))
    trading.add_child(ActionNode("negotiate_trade", negotiate_prison_trade))
    resource_acquisition.add_child(trading)
    
    theft = SequenceNode("theft")
    theft.add_child(ConditionalNode("desperate_for_resources",
        lambda n, c: n.hunger > 70 or n.gold < 5))
    theft.add_child(ConditionalNode("opportunity_to_steal",
        lambda n, c: not is_being_watched(n, c)))
    theft.add_child(ActionNode("steal", attempt_theft))
    resource_acquisition.add_child(theft)
    
    survival_system.add_child(resource_acquisition)
    
    prisoner_root.add_child_with_priority(survival_system, 75.0)
    
    # Planowanie ucieczki (dla Anny)
    if "planner" in personality or "escape_artist" in personality:
        escape_planning = create_escape_planning_behavior()
        prisoner_root.add_child_with_priority(escape_planning, 80.0)
    
    # Handel informacjami (dla Piotra)
    if "talkative" in personality or "informant" in personality:
        information_network = create_information_network_behavior()
        prisoner_root.add_child_with_priority(information_network, 70.0)
    
    # Gang/grupa więzienna
    gang_behavior = create_prison_gang_behavior(personality)
    prisoner_root.add_child_with_priority(gang_behavior, 65.0)
    
    return prisoner_root


def create_creature_behavior(personality: List[str]) -> BehaviorNode:
    """Tworzy zachowania dla stworzeń (np. szczurów)"""
    creature_root = PriorityNode("creature_behavior")
    
    # Podstawowe instynkty
    instincts = ParallelNode("basic_instincts", success_threshold=1)
    
    # Szukanie jedzenia
    foraging = SequenceNode("foraging")
    foraging.add_child(ConditionalNode("is_hungry", is_hungry))
    foraging.add_child(ActionNode("search_food", search_for_scraps))
    foraging.add_child(ActionNode("eat_found_food", eat_scraps))
    instincts.add_child(foraging)
    
    # Unikanie ludzi
    avoidance = SequenceNode("human_avoidance")
    avoidance.add_child(ConditionalNode("human_nearby",
        lambda n, c: any(npc.role in ["guard", "prisoner", "warden"] 
                        and npc.location == n.location
                        for npc in c.get("npcs", {}).values())))
    avoidance.add_child(ActionNode("scurry_away", scurry_to_hiding))
    instincts.add_child(avoidance)
    
    # Eksploracja
    exploration = SequenceNode("exploration")
    exploration.add_child(ConditionalNode("safe_to_explore",
        lambda n, c: not is_being_watched(n, c)))
    exploration.add_child(ActionNode("explore", creature_explore))
    instincts.add_child(exploration)
    
    creature_root.add_child_with_priority(instincts, 90.0)
    
    # Zachowania nocne
    nocturnal = SequenceNode("nocturnal_activity")
    nocturnal.add_child(TimeGatedNode("night_time",
        ConditionalNode("is_night", lambda n, c: True),
        20, 5))
    nocturnal.add_child(ActionNode("night_activity", increased_activity))
    creature_root.add_child_with_priority(nocturnal, 70.0)
    
    return creature_root


def create_deep_personality_behavior(personality: List[str], role: str) -> Optional[BehaviorNode]:
    """Tworzy głębokie zachowania osobowościowe"""
    if not personality:
        return None
    
    personality_root = PriorityNode("deep_personality")
    
    # Cechy introwertyczne vs ekstrawertyczne
    if "quiet" in personality or "solitary" in personality:
        introvert_behavior = create_introvert_behavior()
        personality_root.add_child_with_priority(introvert_behavior, 50.0)
    elif "talkative" in personality or "social" in personality:
        extrovert_behavior = create_extrovert_behavior()
        personality_root.add_child_with_priority(extrovert_behavior, 50.0)
    
    # Poziom agresji
    if "aggressive" in personality or "violent" in personality:
        aggressive_behavior = create_aggressive_behavior()
        personality_root.add_child_with_priority(aggressive_behavior, 60.0)
    elif "peaceful" in personality or "calm" in personality:
        peaceful_behavior = create_peaceful_behavior()
        personality_root.add_child_with_priority(peaceful_behavior, 60.0)
    
    # Inteligencja i planowanie
    if "intelligent" in personality or "clever" in personality:
        intelligent_behavior = create_intelligent_behavior()
        personality_root.add_child_with_priority(intelligent_behavior, 55.0)
    
    # Moralność
    if "honest" in personality:
        moral_behavior = create_moral_behavior()
        personality_root.add_child_with_priority(moral_behavior, 45.0)
    elif "dishonest" in personality or "cunning" in personality:
        immoral_behavior = create_immoral_behavior()
        personality_root.add_child_with_priority(immoral_behavior, 45.0)
    
    # Lęki i fobie
    if "cowardly" in personality or any("fear" in trait for trait in personality):
        fear_behavior = create_fear_based_behavior(personality)
        personality_root.add_child_with_priority(fear_behavior, 70.0)
    
    # Obsesje i manie
    if any("obsessed" in trait for trait in personality):
        obsessive_behavior = create_obsessive_behavior(personality)
        personality_root.add_child_with_priority(obsessive_behavior, 65.0)
    
    return personality_root if personality_root.children else None


def create_habit_system(npc_id: str) -> BehaviorNode:
    """Tworzy system nawyków i rutyn"""
    habit_root = SelectorNode("habit_system")
    
    # Poranne nawyki
    morning_habits = SequenceNode("morning_habits")
    morning_habits.add_child(TimeGatedNode("morning",
        ConditionalNode("just_woke_up", lambda n, c: True),
        5, 8))
    morning_habits.add_child(ActionNode("morning_ritual", perform_morning_ritual))
    habit_root.add_child(morning_habits)
    
    # Nawyki stresowe
    stress_habits = SequenceNode("stress_habits")
    stress_habits.add_child(ConditionalNode("is_stressed",
        lambda n, c: n.emotional_states.get(EmotionalState.FEAR, 0) > 0.3 or
                     n.emotional_states.get(EmotionalState.ANGRY, 0) > 0.3))
    stress_habits.add_child(ActionNode("stress_response", perform_stress_habit))
    habit_root.add_child(stress_habits)
    
    # Nawyki społeczne
    social_habits = SequenceNode("social_habits")
    social_habits.add_child(ConditionalNode("in_social_situation",
        lambda n, c: n.current_state.value == "socializing"))
    social_habits.add_child(ActionNode("social_quirk", perform_social_quirk))
    habit_root.add_child(social_habits)
    
    return habit_root


def create_emotional_reaction_system(personality: List[str]) -> BehaviorNode:
    """Tworzy system reakcji emocjonalnych"""
    emotion_root = PriorityNode("emotional_reactions")
    
    # Reakcje na traumę
    trauma_response = SequenceNode("trauma_response")
    trauma_response.add_child(ConditionalNode("trauma_triggered",
        lambda n, c: n.memory.emotional.check_triggers(c) > 0.5))
    trauma_response.add_child(ActionNode("trauma_reaction", react_to_trauma))
    emotion_root.add_child_with_priority(trauma_response, 90.0)
    
    # Reakcje na radość
    joy_response = SequenceNode("joy_response")
    joy_response.add_child(ConditionalNode("very_happy",
        lambda n, c: n.emotional_states.get(EmotionalState.HAPPY, 0) > 0.7))
    joy_response.add_child(ProbabilityNode("express_joy",
        ActionNode("celebrate", express_happiness), 0.5))
    emotion_root.add_child_with_priority(joy_response, 40.0)
    
    # Reakcje na złość
    anger_response = SequenceNode("anger_response")
    anger_response.add_child(ConditionalNode("very_angry",
        lambda n, c: n.emotional_states.get(EmotionalState.ANGRY, 0) > 0.7))
    anger_response.add_child(ActionNode("anger_outlet", find_anger_outlet))
    emotion_root.add_child_with_priority(anger_response, 60.0)
    
    # Reakcje na smutek
    sadness_response = SequenceNode("sadness_response")
    sadness_response.add_child(ConditionalNode("very_sad",
        lambda n, c: n.emotional_states.get(EmotionalState.SAD, 0) > 0.6))
    sadness_response.add_child(ActionNode("seek_comfort", seek_emotional_support))
    emotion_root.add_child_with_priority(sadness_response, 50.0)
    
    return emotion_root


# ============= HELPER FUNCTIONS FOR ADVANCED BEHAVIORS =============

def personal_activity(npc: Any, context: Dict) -> NodeStatus:
    """Wykonuje osobistą aktywność w zależności od osobowości"""
    from .ai_behaviors import NodeStatus
    
    # Różne aktywności dla różnych typów osobowości
    if "quiet" in npc.personality:
        # Ciche aktywności - czytanie, medytacja
        npc.energy += 5
    elif "aggressive" in npc.personality:
        # Agresywne aktywności - ćwiczenia, trening
        npc.strength += 0.1 if hasattr(npc, 'strength') else None
    elif "social" in npc.personality:
        # Społeczne aktywności - rozmowy, plotki
        npc.social_need = max(0, npc.social_need - 10) if hasattr(npc, 'social_need') else None
    else:
        # Domyślna aktywność - odpoczynek
        npc.energy = min(100, npc.energy + 2)
    
    return NodeStatus.SUCCESS


def morning_routine(npc: Any, context: Dict) -> NodeStatus:
    """Poranna rutyna NPCa"""
    from .ai_behaviors import NodeStatus
    
    # Różne rutyny dla różnych ról
    if npc.role == "guard":
        # Strażnik - sprawdza broń, przygotowuje się do patrolu
        if hasattr(npc, 'weapon'):
            npc.weapon['condition'] = 100
    elif npc.role == "prisoner":
        # Więzień - myje się, przygotowuje do dnia
        npc.hygiene = 100 if hasattr(npc, 'hygiene') else None
    
    npc.morning_done = True
    return NodeStatus.SUCCESS


def evening_routine(npc: Any, context: Dict) -> NodeStatus:
    """Wieczorna rutyna NPCa"""
    from .ai_behaviors import NodeStatus
    
    # Przygotowanie do snu
    npc.energy = min(100, npc.energy + 10)
    npc.evening_done = True
    return NodeStatus.SUCCESS


def seek_emotional_support(npc: Any, context: Dict) -> NodeStatus:
    """Szuka wsparcia emocjonalnego"""
    from .ai_behaviors import NodeStatus
    
    # Szukaj przyjaciół
    for other_npc in context.get("npcs", {}).values():
        if other_npc.id != npc.id:
            if hasattr(npc, 'relationships'):
                trust = npc.relationships.get(other_npc.id, {}).get("trust", 0)
                if trust > 50:
                    # Znaleziono przyjaciela
                    npc.emotional_support = True
                    return NodeStatus.SUCCESS
    
    return NodeStatus.FAILURE


def inspect_prison_cells(npc: Any, context: Dict) -> NodeStatus:
    """Inspekcja cel więziennych"""
    from .npc_manager import NPCState
    
    npc.change_state(NPCState.PATROLLING)
    cells_to_inspect = ["cell_1", "cell_2", "cell_3", "cell_4"]
    
    violations_found = []
    for cell in cells_to_inspect:
        npc.location = cell
        
        # Sprawdź obecność więźniów
        npcs_in_cell = [n for n in context.get("npcs", {}).values() 
                       if n.location == cell and n.role == "prisoner"]
        
        # Sprawdź naruszenia
        for prisoner in npcs_in_cell:
            if has_contraband(prisoner, context):
                violations_found.append({
                    "type": "contraband",
                    "prisoner": prisoner.id,
                    "cell": cell
                })
            
            if prisoner.current_state.value not in ["sleeping", "resting", "idle"]:
                if context.get("hour", 12) in range(22, 24) or context.get("hour", 12) in range(0, 6):
                    violations_found.append({
                        "type": "curfew_violation",
                        "prisoner": prisoner.id,
                        "cell": cell
                    })
    
    # Zapisz naruszenia
    if violations_found:
        npc.semantic_memory["violations_found"] = violations_found
        npc.add_memory(
            event_type="inspection",
            description=f"Znalazł {len(violations_found)} naruszeń podczas inspekcji",
            participants=[npc.id],
            location="cell_block",
            importance=0.5
        )
    
    return NodeStatus.SUCCESS


def check_prisoner_count(npc: Any, context: Dict) -> NodeStatus:
    """Sprawdza liczbę więźniów"""
    prisoners = [n for n in context.get("npcs", {}).values() if n.role == "prisoner"]
    expected_count = npc.semantic_memory.get("expected_prisoner_count", 4)
    
    if len(prisoners) < expected_count:
        # Brakuje więźniów!
        npc.semantic_memory["missing_prisoners"] = expected_count - len(prisoners)
        context["emergency"] = "missing_prisoners"
        return NodeStatus.FAILURE
    
    return NodeStatus.SUCCESS


def document_violations(npc: Any, context: Dict) -> NodeStatus:
    """Dokumentuje naruszenia"""
    violations = npc.semantic_memory.get("violations_found", [])
    
    if violations:
        # Zapisz w raporcie
        report = {
            "date": time.time(),
            "violations": violations,
            "reported_by": npc.id
        }
        
        npc.semantic_memory["violation_reports"] = npc.semantic_memory.get("violation_reports", [])
        npc.semantic_memory["violation_reports"].append(report)
        
        # Wyczyść bieżące naruszenia
        del npc.semantic_memory["violations_found"]
    
    return NodeStatus.SUCCESS


# Dodaj więcej funkcji pomocniczych według potrzeb...