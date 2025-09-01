#!/usr/bin/env python3
"""
Demonstracja zaawansowanego systemu AI NPCów
Pokazuje behavior trees, pamięć, rutyny i interakcje społeczne
"""

import sys
import os
import time
import random
from datetime import datetime

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from npcs.npc_manager import NPCManager, NPCState, EmotionalState
from npcs.ai_behaviors import create_behavior_tree
from mechanics.combat import CombatSystem, BodyPart, DamageType

# Kolory dla lepszej czytelności
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Wyświetla nagłówek"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_section(text):
    """Wyświetla sekcję"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- {text} ---{Colors.ENDC}")


def demonstrate_behavior_trees():
    """Demonstracja systemu Behavior Trees"""
    print_header("DEMONSTRACJA BEHAVIOR TREES")
    
    # Utwórz NPCa
    manager = NPCManager()
    
    # Pobierz Brutusa (naczelnika)
    brutus = manager.get_npc("brutus")
    if not brutus:
        print(f"{Colors.RED}Nie znaleziono NPCa Brutus{Colors.ENDC}")
        return
    
    print(f"NPC: {Colors.BOLD}{brutus.name}{Colors.ENDC}")
    print(f"Rola: {brutus.role}")
    print(f"Osobowość: {', '.join(brutus.personality)}")
    print(f"Dziwactwa: {', '.join(brutus.quirks)}")
    
    # Utwórz behavior tree
    print_section("Tworzenie Behavior Tree")
    tree = create_behavior_tree(brutus.role, brutus.personality)
    brutus.behavior_tree = tree
    
    print(f"{Colors.GREEN}✓ Behavior tree utworzone{Colors.ENDC}")
    
    # Symuluj różne sytuacje
    scenarios = [
        {
            "name": "Normalny dzień - godzina 9:00",
            "context": {
                "hour": 9,
                "npcs": manager.npcs,
                "events": []
            }
        },
        {
            "name": "Wykrycie ucieczki więźnia",
            "context": {
                "hour": 14,
                "npcs": manager.npcs,
                "events": [],
                "prisoner_escaping": True
            }
        },
        {
            "name": "Ciemność (fobia Brutusa)",
            "context": {
                "hour": 22,
                "npcs": manager.npcs,
                "events": [],
                "is_dark": True
            }
        },
        {
            "name": "Atak na naczelnika",
            "context": {
                "hour": 12,
                "npcs": manager.npcs,
                "events": [{"type": "attack", "participants": ["brutus", "player"]}]
            }
        }
    ]
    
    for scenario in scenarios:
        print_section(scenario["name"])
        
        # Zapisz stan początkowy
        initial_state = brutus.current_state
        initial_location = brutus.location
        
        # Wykonaj behavior tree
        context = scenario["context"]
        context["time"] = time.time()
        
        status = tree.execute(brutus, context)
        
        print(f"Stan początkowy: {initial_state.value}")
        print(f"Stan końcowy: {Colors.YELLOW}{brutus.current_state.value}{Colors.ENDC}")
        print(f"Lokalizacja: {initial_location} → {Colors.YELLOW}{brutus.location}{Colors.ENDC}")
        print(f"Status wykonania: {status.value}")
        
        # Pokaż dominującą emocję
        dominant = brutus.get_dominant_emotion()
        print(f"Dominująca emocja: {Colors.YELLOW}{dominant.value}{Colors.ENDC}")


def demonstrate_memory_system():
    """Demonstracja systemu pamięci"""
    print_header("DEMONSTRACJA SYSTEMU PAMIĘCI")
    
    manager = NPCManager()
    
    # Użyj Anny (więźnia planującego ucieczkę)
    anna = manager.get_npc("anna")
    if not anna:
        print(f"{Colors.RED}Nie znaleziono NPCa Anna{Colors.ENDC}")
        return
    
    print(f"NPC: {Colors.BOLD}{anna.name}{Colors.ENDC}")
    print(f"Rola: {anna.role}")
    
    # Dodaj różne typy wspomnień
    print_section("Dodawanie wspomnień")
    
    # Pamięć epizodyczna
    anna.add_memory(
        event_type="discovered_tunnel",
        description="Odkryła tunel za kuchnią",
        participants=["anna"],
        location="kitchen",
        importance=0.9,
        emotional_impact={"surprise": 0.6, "happy": 0.4}
    )
    print(f"{Colors.GREEN}✓ Dodano wspomnienie epizodyczne (odkrycie tunelu){Colors.ENDC}")
    
    # Pamięć semantyczna
    anna.memory.semantic.add_knowledge(
        "tunnel_location",
        {"position": "behind_kitchen", "guarded": False, "best_time": "3am"},
        "escape_routes",
        strength=0.95
    )
    print(f"{Colors.GREEN}✓ Dodano wiedzę semantyczną (lokalizacja tunelu){Colors.ENDC}")
    
    # Pamięć proceduralna
    anna.memory.procedural.learn_skill(
        "lockpicking",
        ["insert_pick", "apply_tension", "feel_pins", "rotate", "open"],
        {"difficulty": "medium", "tools_needed": ["lockpick"]}
    )
    print(f"{Colors.GREEN}✓ Dodano umiejętność (otwieranie zamków){Colors.ENDC}")
    
    # Pamięć emocjonalna
    anna.memory.emotional.tag_emotion("guard_room", "fear", 0.8)
    anna.memory.emotional.tag_emotion("tunnel_entrance", "hope", 0.7)
    print(f"{Colors.GREEN}✓ Dodano skojarzenia emocjonalne{Colors.ENDC}")
    
    # Przywołaj wspomnienia
    print_section("Przywołanie wspomnień")
    
    # Szukaj wspomnień o tunelu
    tunnel_memories = anna.recall_memories(
        query_type="discovered_tunnel",
        limit=5
    )
    
    print(f"\nWspomnienia o tunelu ({len(tunnel_memories)} znalezione):")
    for memory in tunnel_memories:
        print(f"  - {memory['description']}")
        print(f"    Ważność: {memory.get('importance', 0):.2f}")
        print(f"    Siła: {memory.get('strength', 0):.2f}")
    
    # Sprawdź wiedzę o tunelu
    tunnel_info = anna.memory.semantic.retrieve("tunnel_location")
    if tunnel_info:
        print(f"\nWiedza o tunelu:")
        print(f"  Pozycja: {tunnel_info.get('position')}")
        print(f"  Strzeżony: {tunnel_info.get('guarded')}")
        print(f"  Najlepszy czas: {tunnel_info.get('best_time')}")
    
    # Test umiejętności
    print_section("Test umiejętności otwierania zamków")
    success, steps = anna.memory.procedural.execute_skill("lockpicking", {})
    print(f"Próba otwarcia zamka: {Colors.GREEN if success else Colors.RED}{'Sukces' if success else 'Porażka'}{Colors.ENDC}")
    if success:
        print(f"Kroki: {' → '.join(steps)}")
    
    # Sprawdź reakcję emocjonalną
    print_section("Reakcje emocjonalne na miejsca")
    for location in ["guard_room", "tunnel_entrance", "cell_1"]:
        response = anna.memory.emotional.get_emotional_response(location)
        dominant_emotion = max(response.items(), key=lambda x: x[1])
        print(f"{location}: {Colors.YELLOW}{dominant_emotion[0]}{Colors.ENDC} ({dominant_emotion[1]:.2f})")


def demonstrate_social_interactions():
    """Demonstracja interakcji społecznych"""
    print_header("DEMONSTRACJA INTERAKCJI SPOŁECZNYCH")
    
    manager = NPCManager()
    
    # Pobierz NPCów do interakcji
    marek = manager.get_npc("marek")  # Skorumpowany strażnik
    piotr = manager.get_npc("piotr")  # Gadatliwy informator
    
    if not marek or not piotr:
        print(f"{Colors.RED}Nie znaleziono NPCów do demonstracji{Colors.ENDC}")
        return
    
    print(f"Uczestnicy interakcji:")
    print(f"  1. {Colors.BOLD}{marek.name}{Colors.ENDC} - {marek.role} ({', '.join(marek.personality)})")
    print(f"  2. {Colors.BOLD}{piotr.name}{Colors.ENDC} - {piotr.role} ({', '.join(piotr.personality)})")
    
    # Początkowa relacja
    print_section("Stan początkowy relacji")
    initial_relationship = piotr.get_relationship(marek.id)
    print(f"Piotr → Marek:")
    print(f"  Zaufanie: {initial_relationship.trust:.1f}")
    print(f"  Sympatia: {initial_relationship.affection:.1f}")
    print(f"  Szacunek: {initial_relationship.respect:.1f}")
    print(f"  Strach: {initial_relationship.fear:.1f}")
    print(f"  Ogólna dyspozycja: {Colors.YELLOW}{initial_relationship.get_overall_disposition():.1f}{Colors.ENDC}")
    
    # Symuluj serię interakcji
    print_section("Seria interakcji")
    
    interactions = [
        ("friendly_chat", "Przyjazna rozmowa", 0.5),
        ("information_trade", "Handel informacjami", 1.0),
        ("help", "Pomoc w potrzebie", 1.5),
        ("bribe", "Próba przekupstwa", 1.0)
    ]
    
    for interaction_type, description, intensity in interactions:
        print(f"\n{Colors.CYAN}→ {description}{Colors.ENDC}")
        
        # Piotr interaguje z Markiem
        piotr.interact_with(marek.id, interaction_type, intensity)
        
        # Marek odpowiada
        if interaction_type == "bribe" and marek.can_be_bribed(50):
            marek.accept_bribe(50, piotr.id)
            print(f"  {Colors.GREEN}Marek przyjął łapówkę!{Colors.ENDC}")
        else:
            marek.interact_with(piotr.id, "friendly_chat", 0.3)
        
        # Pokaż zmianę relacji
        new_relationship = piotr.get_relationship(marek.id)
        trust_change = new_relationship.trust - initial_relationship.trust
        print(f"  Zmiana zaufania: {'+' if trust_change >= 0 else ''}{trust_change:.1f}")
        
        # Aktualizuj początkową relację dla następnej iteracji
        initial_relationship = new_relationship
    
    # Końcowa relacja
    print_section("Stan końcowy relacji")
    final_relationship = piotr.get_relationship(marek.id)
    print(f"Piotr → Marek:")
    print(f"  Zaufanie: {Colors.GREEN if final_relationship.trust > 0 else Colors.RED}{final_relationship.trust:.1f}{Colors.ENDC}")
    print(f"  Sympatia: {Colors.GREEN if final_relationship.affection > 0 else Colors.RED}{final_relationship.affection:.1f}{Colors.ENDC}")
    print(f"  Szacunek: {Colors.GREEN if final_relationship.respect > 0 else Colors.RED}{final_relationship.respect:.1f}{Colors.ENDC}")
    print(f"  Strach: {Colors.YELLOW}{final_relationship.fear:.1f}{Colors.ENDC}")
    print(f"  Ogólna dyspozycja: {Colors.BOLD}{final_relationship.get_overall_disposition():.1f}{Colors.ENDC}")
    
    # Dzielenie się informacjami
    print_section("Dzielenie się informacjami")
    
    # Piotr ma informację o tunelu
    piotr.semantic_memory["tunnel_location"] = "behind_kitchen"
    
    # Sprawdź czy podzieli się z Markiem
    info = piotr.share_information("tunnel", marek.id)
    if info:
        print(f"{Colors.GREEN}Piotr podzielił się informacją o tunelu: {info}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}Piotr nie chce podzielić się informacją (za mało zaufania){Colors.ENDC}")


def demonstrate_daily_routines():
    """Demonstracja codziennych rutyn"""
    print_header("DEMONSTRACJA CODZIENNYCH RUTYN")
    
    manager = NPCManager()
    
    # Śledź rutynę Brutusa przez cały dzień
    brutus = manager.get_npc("brutus")
    if not brutus:
        print(f"{Colors.RED}Nie znaleziono NPCa Brutus{Colors.ENDC}")
        return
    
    print(f"Śledzenie rutyny: {Colors.BOLD}{brutus.name}{Colors.ENDC}")
    print(f"Harmonogram dnia:")
    
    # Symuluj cały dzień
    activities_log = []
    hours = list(range(6, 24)) + list(range(0, 6))
    
    for hour in hours:
        # Ustaw kontekst
        context = {
            "hour": hour,
            "time": time.time(),
            "npcs": manager.npcs,
            "events": []
        }
        
        # Zapisz stan
        old_state = brutus.current_state
        old_location = brutus.location
        
        # Wykonaj behavior tree
        if brutus.behavior_tree:
            brutus.behavior_tree.execute(brutus, context)
        
        # Sprawdź harmonogram
        brutus._check_schedule(time.time())
        
        # Zapisz aktywność
        scheduled = brutus.schedule.get(str(hour), "free_time")
        activities_log.append({
            "hour": hour,
            "scheduled": scheduled,
            "actual_state": brutus.current_state.value,
            "location": brutus.location,
            "energy": brutus.energy,
            "hunger": brutus.hunger
        })
        
        # Symuluj upływ czasu (1 godzina = 60 minut w grze)
        brutus.update(60.0, context)
    
    # Wyświetl log aktywności
    print_section("Przebieg dnia")
    
    current_period = None
    for activity in activities_log:
        hour = activity["hour"]
        
        # Określ porę dnia
        if 6 <= hour < 12:
            period = "RANEK"
            color = Colors.YELLOW
        elif 12 <= hour < 18:
            period = "POPOŁUDNIE"
            color = Colors.CYAN
        elif 18 <= hour < 22:
            period = "WIECZÓR"
            color = Colors.BLUE
        else:
            period = "NOC"
            color = Colors.HEADER
        
        if period != current_period:
            print(f"\n{color}{period}{Colors.ENDC}")
            current_period = period
        
        # Wyświetl aktywność
        state_color = Colors.GREEN if activity["actual_state"] != "idle" else Colors.ENDC
        print(f"  {hour:02d}:00 - {state_color}{activity['actual_state']:<12}{Colors.ENDC} "
              f"@ {activity['location']:<15} "
              f"(E:{activity['energy']:.0f} H:{activity['hunger']:.0f})")
        
        # Zaznacz ważne wydarzenia
        if activity["actual_state"] == "fleeing":
            print(f"    {Colors.RED}⚠ ALARM! Ucieczka!{Colors.ENDC}")
        elif activity["actual_state"] == "eating":
            print(f"    {Colors.GREEN}🍽 Posiłek{Colors.ENDC}")
        elif activity["actual_state"] == "sleeping":
            print(f"    {Colors.BLUE}💤 Sen{Colors.ENDC}")


def demonstrate_emergent_behavior():
    """Demonstracja emergentnych zachowań"""
    print_header("DEMONSTRACJA EMERGENTNYCH ZACHOWAŃ")
    
    manager = NPCManager()
    
    print("Symulacja 10 minut życia więzienia...")
    print("(Obserwuj spontaniczne interakcje i wydarzenia)\n")
    
    # Symuluj 10 cykli
    for minute in range(10):
        print(f"\n{Colors.CYAN}=== Minuta {minute + 1} ==={Colors.ENDC}")
        
        current_hour = (12 + minute // 60) % 24
        context = {
            "hour": current_hour,
            "time": time.time() + minute * 60,
            "npcs": manager.npcs,
            "events": manager.world_events[-10:]
        }
        
        # Aktualizuj wszystkich NPCów
        manager.update()
        
        # Sprawdź interesujące wydarzenia
        recent_events = manager.world_events[-5:]
        for event in recent_events:
            event_type = event.get("type", "unknown")
            participants = event.get("participants", [])
            
            # Wyświetl tylko nowe wydarzenia
            if event.get("timestamp", 0) > time.time() - 1:
                if event_type == "npc_interaction":
                    interaction = event.get("interaction_type", "unknown")
                    color = Colors.GREEN if interaction in ["help", "friendly_chat"] else Colors.YELLOW
                    print(f"  {color}↔ {participants[0]} {interaction} z {participants[1]}{Colors.ENDC}")
                elif event_type == "attack":
                    print(f"  {Colors.RED}⚔ {participants[0]} atakuje {participants[1]}!{Colors.ENDC}")
                elif event_type == "escape_attempt":
                    print(f"  {Colors.YELLOW}🏃 {participants[0]} próbuje uciec!{Colors.ENDC}")
        
        # Pokaż stan wybranych NPCów
        tracked_npcs = ["brutus", "anna", "marek"]
        states = []
        for npc_id in tracked_npcs:
            npc = manager.get_npc(npc_id)
            if npc:
                emotion = npc.get_dominant_emotion()
                emoji = {
                    EmotionalState.HAPPY: "😊",
                    EmotionalState.ANGRY: "😠",
                    EmotionalState.FEAR: "😨",
                    EmotionalState.SAD: "😢",
                    EmotionalState.NEUTRAL: "😐"
                }.get(emotion, "😐")
                
                states.append(f"{npc.name}: {npc.current_state.value} {emoji}")
        
        print(f"  Stan NPCów: {' | '.join(states)}")
        
        # Symuluj przypadkowe wydarzenia
        if random.random() < 0.3:
            random_events = [
                ("fire", "Pożar w kuchni!"),
                ("riot", "Bunt więźniów!"),
                ("inspection", "Niespodziewana inspekcja!"),
                ("blackout", "Awaria prądu!")
            ]
            
            event_type, description = random.choice(random_events)
            print(f"\n  {Colors.RED}⚠ WYDARZENIE: {description}{Colors.ENDC}")
            
            # Dodaj do kontekstu
            context[event_type] = True
            manager.add_world_event({
                "type": event_type,
                "description": description,
                "location": "prison",
                "timestamp": time.time()
            })


def main():
    """Główna funkcja demonstracyjna"""
    print_header("ZAAWANSOWANY SYSTEM AI NPCów")
    print("Demonstracja pełnego systemu sztucznej inteligencji")
    print("dla postaci niezależnych w grze Droga Szamana RPG")
    
    demos = [
        ("Behavior Trees", demonstrate_behavior_trees),
        ("System Pamięci", demonstrate_memory_system),
        ("Interakcje Społeczne", demonstrate_social_interactions),
        ("Codzienne Rutyny", demonstrate_daily_routines),
        ("Zachowania Emergentne", demonstrate_emergent_behavior)
    ]
    
    while True:
        print(f"\n{Colors.BOLD}Wybierz demonstrację:{Colors.ENDC}")
        for i, (name, _) in enumerate(demos, 1):
            print(f"  {i}. {name}")
        print(f"  0. Wyjście")
        
        try:
            choice = input(f"\n{Colors.CYAN}Wybór: {Colors.ENDC}")
            choice = int(choice)
            
            if choice == 0:
                print(f"\n{Colors.GREEN}Dziękujemy za obejrzenie demonstracji!{Colors.ENDC}")
                break
            elif 1 <= choice <= len(demos):
                demos[choice - 1][1]()
                input(f"\n{Colors.YELLOW}Naciśnij Enter aby kontynuować...{Colors.ENDC}")
            else:
                print(f"{Colors.RED}Nieprawidłowy wybór{Colors.ENDC}")
        except (ValueError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}Do widzenia!{Colors.ENDC}")
            break
        except Exception as e:
            print(f"{Colors.RED}Błąd: {e}{Colors.ENDC}")


if __name__ == "__main__":
    main()