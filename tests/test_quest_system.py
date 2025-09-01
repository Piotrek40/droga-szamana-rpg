#!/usr/bin/env python3
"""
Test systemu questów emergentnych dla Droga Szamana RPG
Sprawdza integrację wszystkich komponentów
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quests.quest_engine import QuestEngine, QuestSeed, QuestState, DiscoveryMethod
from quests.emergent_quests import (
    PrisonEscapeQuest, ContrabandTradeQuest, PrisonGangWarQuest,
    CorruptionExposureQuest, PrisonDiseaseQuest, InformationGatheringQuest,
    RevengeQuest, create_quest_seed_library, QuestIntegrationManager
)
from quests.quest_consequences import ConsequenceTracker, ConsequenceType
from datetime import datetime, timedelta
import json


def test_quest_seeds():
    """Testuje tworzenie i aktywację ziaren questów"""
    print("\n=== TEST: Ziarna questów ===")
    
    seeds = create_quest_seed_library()
    print(f"Utworzono {len(seeds)} ziaren questów:")
    
    for seed_id, seed in seeds.items():
        print(f"  • {seed.name} (ID: {seed_id})")
        print(f"    - Priorytet: {seed.priority}")
        print(f"    - Czasochłonny: {seed.time_sensitive}")
        print(f"    - Metody odkrycia: {', '.join(m.value for m in seed.discovery_methods)}")
    
    # Test aktywacji
    test_world_state = {
        "location": "wiezienie",
        "player_imprisoned": True,
        "time_in_prison": 5,
        "economy.shortage": 0.6,
        "gang_tensions": 0.8,
        "recent_violence": True
    }
    
    print("\n=== TEST: Aktywacja questów ===")
    for seed_id, seed in seeds.items():
        if seed.check_activation(test_world_state):
            print(f"  ✓ {seed.name} - AKTYWNY")
        else:
            print(f"  ✗ {seed.name} - nieaktywny")


def test_prison_escape_quest():
    """Testuje questa ucieczki z więzienia"""
    print("\n=== TEST: Quest ucieczki z więzienia ===")
    
    # Stwórz seed
    seed = QuestSeed(
        quest_id="test_escape",
        name="Ucieczka testowa",
        activation_conditions={"player_imprisoned": True},
        discovery_methods=[DiscoveryMethod.FOUND],
        initial_clues={"cela": "Ściana jest słaba"},
        time_sensitive=False,
        priority=8
    )
    
    # Stwórz quest
    quest = PrisonEscapeQuest("test_escape", seed)
    print(f"Quest utworzony: {quest.quest_id}")
    print(f"Trasy ucieczki: {list(quest.escape_routes.keys())}")
    
    # Test odkrycia
    discovery_result = quest.discover(DiscoveryMethod.FOUND, "cela")
    print(f"\nOdkrycie questa:")
    print(f"  Sukces: {discovery_result['success']}")
    print(f"  Dialog: {discovery_result.get('dialogue', 'Brak')}")
    
    # Test śledztwa
    player_state = {
        "skills": {"skradanie": 20},
        "inventory": ["narzedzia"],
        "relationships": {"wiezien_1": 50}
    }
    
    inv_result = quest.investigate("scout", "mury", player_state)
    print(f"\nŚledztwo - rozpoznanie murów:")
    print(f"  Odkrycia: {inv_result.get('discoveries', [])}")
    print(f"  Dialogi: {inv_result.get('dialogue', [])}")
    
    # Test sprawdzania możliwości ucieczki
    can_escape, reason = quest.can_attempt_escape()
    print(f"\nMożliwość ucieczki:")
    print(f"  Można uciec: {can_escape}")
    print(f"  Powód: {reason}")


def test_contraband_quest():
    """Testuje questa przemytu"""
    print("\n=== TEST: Quest przemytu ===")
    
    seed = QuestSeed(
        quest_id="test_contraband",
        name="Przemyt testowy",
        activation_conditions={"economy.shortage": 0.7},
        discovery_methods=[DiscoveryMethod.OVERHEARD],
        initial_clues={"stołówka": "Brakuje wszystkiego"},
        time_sensitive=True,
        expiry_hours=120,
        priority=6
    )
    
    quest = ContrabandTradeQuest("test_contraband", seed)
    print(f"Quest utworzony: {quest.quest_id}")
    print(f"Popyt rynkowy:")
    for item, demand in quest.market_demand.items():
        print(f"  • {item}: {demand:.1f}")
    
    print(f"Trasy przemytu: {quest.trade_routes}")


def test_gang_war_quest():
    """Testuje questa wojny gangów"""
    print("\n=== TEST: Quest wojny gangów ===")
    
    seed = QuestSeed(
        quest_id="test_gang_war",
        name="Wojna gangów",
        activation_conditions={"gang_tensions": 0.8},
        discovery_methods=[DiscoveryMethod.WITNESSED],
        initial_clues={"dziedziniec": "Napięcie wisi w powietrzu"},
        time_sensitive=True,
        expiry_hours=48,
        priority=9
    )
    
    quest = PrisonGangWarQuest("test_gang_war", seed)
    print(f"Quest utworzony: {quest.quest_id}")
    print(f"Gangi:")
    for gang, strength in quest.gang_strength.items():
        print(f"  • {gang}: siła {strength}")
    
    print(f"\nNapięcia między gangami:")
    for gang1, tensions in quest.gang_tensions.items():
        for gang2, tension in tensions.items():
            print(f"  {gang1} vs {gang2}: {tension:.1f}")
    
    # Test eskalacji
    event = {"type": "violence", "participants": ["gang1", "gang2"]}
    escalation = quest.track_conflict_escalation(event)
    print(f"\nEskalacja konfliktu:")
    print(f"  Poziom napięcia: {escalation['current_tension']:.1f}")
    print(f"  Ostrzeżenia: {escalation.get('warnings', [])}")


def test_consequences():
    """Testuje system konsekwencji"""
    print("\n=== TEST: System konsekwencji ===")
    
    tracker = ConsequenceTracker()
    
    # Dodaj konsekwencję natychmiastową
    immediate_data = {
        "effects": [
            {
                "target_type": "npc",
                "target_id": "all_prisoners",
                "effect_type": "relationship",
                "magnitude": -5.0
            }
        ],
        "type": "IMMEDIATE",
        "scope": "LOCAL",
        "delay_hours": 0
    }
    
    cons_id = tracker.add_consequence("test_quest", "betrayal", immediate_data)
    print(f"Dodano konsekwencję natychmiastową: {cons_id}")
    
    # Dodaj konsekwencję opóźnioną
    delayed_data = {
        "effects": [
            {
                "target_type": "location",
                "target_id": "cells",
                "effect_type": "danger",
                "magnitude": 0.5
            }
        ],
        "type": "DELAYED",
        "scope": "LOCAL",
        "delay_hours": 24
    }
    
    cons_id2 = tracker.add_consequence("test_quest", "violence", delayed_data)
    print(f"Dodano konsekwencję opóźnioną: {cons_id2}")
    
    # Pokaż timeline
    timeline = tracker.get_consequence_timeline()
    print(f"\nTimeline konsekwencji ({len(timeline)} wydarzeń):")
    for event in timeline:
        print(f"  • {event['time']}: {event['type']} - {event.get('quest', 'Unknown')}")
    
    # Test karmy
    karma = tracker.get_karma_score()
    print(f"\nKarma:")
    for aspect, value in karma.items():
        print(f"  • {aspect}: {value:.1f}%")


def test_quest_integration():
    """Testuje integrację questów z grą"""
    print("\n=== TEST: Integracja questów ===")
    
    # Symulacja podstawowych komponentów gry
    class MockGameState:
        def __init__(self):
            self.current_location = "cela_1"
            self.player = MockPlayer()
            self.npc_manager = None
            self.time_in_prison = 5
            
        def add_message(self, msg, msg_type="normal"):
            print(f"  [GAME] {msg}")
            
        def add_journal_entry(self, entry):
            print(f"  [JOURNAL] {entry}")
    
    class MockPlayer:
        def __init__(self):
            self.health = 100
            self.gold = 50
            self.inventory = {"narzedzia": 1}
            self.skills = {"skradanie": 20, "walka": 15}
            self.reputation = {"wiezniowie": 10, "straznicy": -20}
    
    # Stwórz komponenty
    quest_engine = QuestEngine()
    game_state = MockGameState()
    
    # Podstawowa integracja
    quest_engine.world_state = {
        "location": "wiezienie",
        "player_imprisoned": True,
        "time_in_prison": 5,
        "economy.shortage": 0.6
    }
    
    quest_engine.player_state = {
        "location": game_state.current_location,
        "health": game_state.player.health,
        "gold": game_state.player.gold,
        "inventory": list(game_state.player.inventory.keys()),
        "skills": game_state.player.skills,
        "relationships": game_state.player.reputation
    }
    
    # Zarejestruj questy
    seeds = create_quest_seed_library()
    for seed in seeds.values():
        quest_engine.register_seed(seed)
    
    print("System questów zintegrowany")
    print(f"Zarejestrowano {len(quest_engine.quest_seeds)} ziaren questów")
    
    # Symuluj update
    quest_engine.update(datetime.now())
    
    # Sprawdź aktywne questy
    active = quest_engine.get_active_quests()
    print(f"\nAktywne questy: {len(active)}")
    for quest in active:
        print(f"  • {quest.seed.name} - stan: {quest.state.value}")
    
    # Sprawdź odkrywalne questy
    discoverable = quest_engine.get_discoverable_quests()
    print(f"\nOdkrywalne questy: {len(discoverable)}")
    for quest in discoverable:
        print(f"  • {quest.seed.name}")
        for loc, clue in quest.seed.initial_clues.items():
            print(f"    - {loc}: {clue}")


def test_quest_branches():
    """Testuje różne gałęzie rozwiązań questów"""
    print("\n=== TEST: Gałęzie rozwiązań ===")
    
    # Stwórz questa ucieczki
    seed = create_quest_seed_library()["prison_escape"]
    quest = PrisonEscapeQuest("escape_test", seed)
    
    print(f"Quest: {quest.seed.name}")
    print(f"Dostępne gałęzie rozwiązania:")
    
    for branch_id, branch in quest.branches.items():
        print(f"\n  • {branch_id}: {branch.description}")
        print(f"    Wymagania: {branch.requirements}")
        
        # Sprawdź czy gracz może wybrać
        test_player_state = {
            "skills": {"skradanie": 35, "przywodztwo": 45},
            "inventory": ["narzedzia"],
            "allies": 4,
            "discovered_routes": 2,
            "gold": 1500,
            "reputation": {"naczelnik": 35}
        }
        
        can_choose = branch.can_choose(test_player_state)
        print(f"    Gracz może wybrać: {'TAK' if can_choose else 'NIE'}")


def run_all_tests():
    """Uruchamia wszystkie testy"""
    print("=" * 60)
    print("TESTY SYSTEMU QUESTÓW EMERGENTNYCH")
    print("=" * 60)
    
    test_quest_seeds()
    test_prison_escape_quest()
    test_contraband_quest()
    test_gang_war_quest()
    test_consequences()
    test_quest_branches()
    test_quest_integration()
    
    print("\n" + "=" * 60)
    print("WSZYSTKIE TESTY ZAKOŃCZONE")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()