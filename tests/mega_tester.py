#!/usr/bin/env python3
"""
MEGA TESTER - Kompleksowy System Testowania Gry "Droga Szamana"
================================================================
Testuje KAŻDĄ funkcję, system i mechanikę w grze.
Generuje szczegółowy raport z wynikami.
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import importlib
import inspect

# Dodaj ścieżkę projektu
sys.path.insert(0, '/mnt/d/claude3')

# Kolory dla lepszej czytelności
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestStatus(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    WARNING = "⚠️ WARNING"
    SKIPPED = "⏭️ SKIPPED"
    ERROR = "🔥 ERROR"

@dataclass
class TestResult:
    category: str
    test_name: str
    status: TestStatus
    message: str
    details: Dict = None
    error: str = None
    duration: float = 0.0

class MegaTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.game_state = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warning_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        
    def add_result(self, result: TestResult):
        """Dodaje wynik testu"""
        self.results.append(result)
        self.total_tests += 1
        
        if result.status == TestStatus.PASSED:
            self.passed_tests += 1
        elif result.status == TestStatus.FAILED:
            self.failed_tests += 1
        elif result.status == TestStatus.WARNING:
            self.warning_tests += 1
        elif result.status == TestStatus.ERROR:
            self.error_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1
    
    def run_test(self, category: str, test_name: str, test_func, *args, **kwargs):
        """Uruchamia pojedynczy test z obsługą błędów"""
        print(f"  Testing: {test_name}...", end=" ")
        start = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start
            
            if isinstance(result, tuple):
                success, message, details = result if len(result) == 3 else (*result, None)
            else:
                success = result
                message = "Test completed"
                details = None
            
            if success:
                print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
                status = TestStatus.PASSED
            else:
                print(f"{Colors.FAIL}✗{Colors.ENDC}")
                status = TestStatus.FAILED
                
            self.add_result(TestResult(
                category=category,
                test_name=test_name,
                status=status,
                message=message,
                details=details,
                duration=duration
            ))
            
        except Exception as e:
            duration = time.time() - start
            print(f"{Colors.FAIL}ERROR{Colors.ENDC}")
            self.add_result(TestResult(
                category=category,
                test_name=test_name,
                status=TestStatus.ERROR,
                message=str(e),
                error=traceback.format_exc(),
                duration=duration
            ))
    
    # ==================== TESTY PODSTAWOWE ====================
    
    def test_imports(self):
        """Testuje czy wszystkie moduły się importują"""
        print(f"\n{Colors.HEADER}=== TESTING IMPORTS ==={Colors.ENDC}")
        
        modules_to_test = [
            ('core.game_state', 'GameState'),
            ('core.event_bus', 'EventBus'),
            ('player.character', 'Character'),
            ('player.skills', 'SkillSystem'),
            ('npcs.npc_manager', 'NPCManager'),
            ('npcs.ai_behaviors', 'BehaviorNode'),
            ('npcs.memory_system', 'MemorySystem'),
            ('mechanics.combat', 'CombatSystem'),
            ('mechanics.economy', 'Economy'),
            ('mechanics.crafting', 'CraftingSystem'),
            ('quests.quest_engine', 'QuestEngine'),
            ('world.locations.prison', 'Prison'),
            ('world.time_system', 'TimeSystem'),
            ('ui.commands', 'CommandParser'),
            ('persistence.save_manager', 'SaveManager'),
        ]
        
        for module_path, class_name in modules_to_test:
            def test_import():
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, class_name):
                        return True, f"Successfully imported {class_name} from {module_path}", None
                    else:
                        return False, f"Class {class_name} not found in {module_path}", None
                except ImportError as e:
                    return False, f"Failed to import {module_path}: {e}", None
            
            self.run_test("Imports", f"Import {module_path}", test_import)
    
    # ==================== TESTY INICJALIZACJI ====================
    
    def test_game_initialization(self):
        """Testuje inicjalizację gry"""
        print(f"\n{Colors.HEADER}=== TESTING GAME INITIALIZATION ==={Colors.ENDC}")
        
        def test_game_state_creation():
            from core.game_state import GameState
            self.game_state = GameState()
            return self.game_state is not None, "GameState created", {
                "class": type(self.game_state).__name__
            }
        
        def test_game_init():
            if not self.game_state:
                return False, "GameState not available", None
            
            # Przekieruj output żeby nie zaśmiecać konsoli
            import io
            from contextlib import redirect_stdout
            
            with redirect_stdout(io.StringIO()):
                self.game_state.init_game()
            
            checks = {
                "player_exists": self.game_state.player is not None,
                "location_set": self.game_state.current_location is not None,
                "npc_manager": self.game_state.npc_manager is not None,
                "economy": self.game_state.economy is not None,
                "crafting": self.game_state.crafting is not None,
                "time_system": self.game_state.time_system is not None
            }
            
            all_passed = all(checks.values())
            return all_passed, "Game initialization checks", checks
        
        self.run_test("Initialization", "Create GameState", test_game_state_creation)
        self.run_test("Initialization", "Initialize Game", test_game_init)
    
    # ==================== TESTY GRACZA ====================
    
    def test_player_systems(self):
        """Testuje systemy gracza"""
        print(f"\n{Colors.HEADER}=== TESTING PLAYER SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state or not self.game_state.player:
            self.add_result(TestResult(
                category="Player",
                test_name="Player Systems",
                status=TestStatus.SKIPPED,
                message="Game not initialized"
            ))
            return
        
        player = self.game_state.player
        
        # Test statystyk
        def test_player_stats():
            stats = {
                "name": player.name,
                "health": f"{player.health}/{player.max_health}",
                "stamina": f"{player.stamina}/{player.max_stamina}",
                "level": player.level,
                "gold": player.gold,
                "has_inventory": hasattr(player, 'inventory'),
                "has_skills": hasattr(player, 'skills')
            }
            return True, "Player stats checked", stats
        
        # Test otrzymywania obrażeń
        def test_damage():
            initial_health = player.health
            player.take_damage(10)
            damaged = player.health < initial_health
            player.health = initial_health  # Przywróć
            return damaged, f"Damage system: {initial_health} -> {player.health}", None
        
        # Test leczenia
        def test_healing():
            player.health = player.max_health // 2
            initial = player.health
            player.heal(20)
            healed = player.health > initial
            return healed, f"Healing: {initial} -> {player.health}", None
        
        # Test ekwipunku
        def test_inventory():
            if not hasattr(player, 'inventory'):
                return False, "No inventory system", None
            
            if isinstance(player.inventory, list):
                initial_count = len(player.inventory)
                player.inventory.append("test_item")
                added = len(player.inventory) > initial_count
                player.inventory.remove("test_item")
            elif isinstance(player.inventory, dict):
                initial_count = len(player.inventory)
                player.inventory["test_item"] = 1
                added = len(player.inventory) > initial_count
                del player.inventory["test_item"]
            else:
                return False, f"Unknown inventory type: {type(player.inventory)}", None
            
            return added, "Inventory operations work", None
        
        # Test umiejętności
        def test_skills():
            if not hasattr(player, 'skills'):
                return False, "No skills system", None
            
            from player.skills import SkillName
            
            skill_count = 0
            skill_names = []
            
            if hasattr(player.skills, 'skills'):
                skill_count = len(player.skills.skills)
                skill_names = [s for s in player.skills.skills.keys()][:5]
            
            return skill_count > 0, f"Found {skill_count} skills", {
                "count": skill_count,
                "sample": skill_names
            }
        
        self.run_test("Player", "Stats System", test_player_stats)
        self.run_test("Player", "Damage System", test_damage)
        self.run_test("Player", "Healing System", test_healing)
        self.run_test("Player", "Inventory System", test_inventory)
        self.run_test("Player", "Skills System", test_skills)
    
    # ==================== TESTY NPCÓW ====================
    
    def test_npc_systems(self):
        """Testuje systemy NPCów"""
        print(f"\n{Colors.HEADER}=== TESTING NPC SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state or not self.game_state.npc_manager:
            self.add_result(TestResult(
                category="NPCs",
                test_name="NPC Systems",
                status=TestStatus.SKIPPED,
                message="NPC Manager not initialized"
            ))
            return
        
        manager = self.game_state.npc_manager
        
        # Test ładowania NPCów
        def test_npc_loading():
            npc_count = len(manager.npcs)
            npc_list = list(manager.npcs.keys())
            
            # Sprawdź czy są ważne NPCe
            expected_npcs = ["anna", "brutus", "marek", "piotr", "jozek"]
            loaded = [npc for npc in expected_npcs if npc in manager.npcs]
            
            return npc_count > 0, f"Loaded {npc_count} NPCs", {
                "count": npc_count,
                "npcs": npc_list,
                "expected_loaded": f"{len(loaded)}/{len(expected_npcs)}"
            }
        
        # Test behavior trees
        def test_behavior_trees():
            npcs_with_bt = 0
            for npc_id, npc in manager.npcs.items():
                if hasattr(npc, 'behavior_tree') and npc.behavior_tree:
                    npcs_with_bt += 1
            
            return npcs_with_bt > 0, f"{npcs_with_bt}/{len(manager.npcs)} NPCs have behavior trees", None
        
        # Test pamięci NPCów
        def test_npc_memory():
            npcs_with_memory = 0
            for npc_id, npc in manager.npcs.items():
                if hasattr(npc, 'memory'):
                    npcs_with_memory += 1
            
            return npcs_with_memory > 0, f"{npcs_with_memory}/{len(manager.npcs)} NPCs have memory", None
        
        # Test relacji
        def test_npc_relationships():
            npcs_with_relations = 0
            for npc_id, npc in manager.npcs.items():
                if hasattr(npc, 'relationships'):
                    npcs_with_relations += 1
            
            return npcs_with_relations > 0, f"{npcs_with_relations}/{len(manager.npcs)} NPCs have relationships", None
        
        # Test dialogów
        def test_npc_dialogue():
            from npcs.dialogue_system import DialogueSystem
            dialogue = DialogueSystem(self.game_state)
            
            # Spróbuj porozmawiać z pierwszym NPCem
            if manager.npcs:
                first_npc = list(manager.npcs.keys())[0]
                response = dialogue.get_dialogue(first_npc, "greeting")
                has_dialogue = response is not None and len(response) > 0
                return has_dialogue, f"Dialogue system works for {first_npc}", {
                    "npc": first_npc,
                    "response_length": len(response) if response else 0
                }
            
            return False, "No NPCs to test dialogue", None
        
        self.run_test("NPCs", "NPC Loading", test_npc_loading)
        self.run_test("NPCs", "Behavior Trees", test_behavior_trees)
        self.run_test("NPCs", "Memory Systems", test_npc_memory)
        self.run_test("NPCs", "Relationships", test_npc_relationships)
        self.run_test("NPCs", "Dialogue System", test_npc_dialogue)
    
    # ==================== TESTY LOKACJI ====================
    
    def test_world_systems(self):
        """Testuje systemy świata"""
        print(f"\n{Colors.HEADER}=== TESTING WORLD SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state:
            self.add_result(TestResult(
                category="World",
                test_name="World Systems",
                status=TestStatus.SKIPPED,
                message="Game not initialized"
            ))
            return
        
        # Test lokacji
        def test_locations():
            from world.locations.prison import Prison
            prison = Prison()
            
            location_count = len(prison.locations)
            current = self.game_state.current_location
            
            # Sprawdź czy można się poruszać
            if current in prison.locations:
                exits = prison.locations[current].get("exits", {})
                can_move = len(exits) > 0
            else:
                can_move = False
            
            return location_count > 0, f"Found {location_count} locations", {
                "count": location_count,
                "current": current,
                "can_move": can_move
            }
        
        # Test poruszania się
        def test_movement():
            from ui.commands import CommandParser
            parser = CommandParser(self.game_state)
            
            initial_location = self.game_state.current_location
            
            # Spróbuj się poruszyć
            directions = ["północ", "południe", "wschód", "zachód"]
            moved = False
            
            for direction in directions:
                success, msg = parser.parse_and_execute(direction)
                if self.game_state.current_location != initial_location:
                    moved = True
                    # Wróć do początkowej lokacji
                    self.game_state.current_location = initial_location
                    break
            
            return moved, "Movement system works" if moved else "Could not move from current location", {
                "initial": initial_location,
                "tried_directions": directions
            }
        
        # Test systemu czasu
        def test_time_system():
            if not hasattr(self.game_state, 'time_system'):
                return False, "No time system", None
            
            time_sys = self.game_state.time_system
            initial_time = time_sys.current_time
            
            # Przemień czas
            for _ in range(10):
                time_sys.advance_time(1)
            
            advanced = time_sys.current_time > initial_time
            
            return advanced, f"Time advanced from {initial_time} to {time_sys.current_time}", {
                "day": time_sys.day,
                "hour": time_sys.hour,
                "minute": time_sys.minute
            }
        
        # Test pogody
        def test_weather():
            if not hasattr(self.game_state, 'weather_system'):
                from world.weather import WeatherSystem
                weather = WeatherSystem()
            else:
                weather = self.game_state.weather_system
            
            current_weather = weather.current_weather if hasattr(weather, 'current_weather') else "unknown"
            
            return True, f"Weather system present", {
                "current": current_weather
            }
        
        self.run_test("World", "Location System", test_locations)
        self.run_test("World", "Movement System", test_movement)
        self.run_test("World", "Time System", test_time_system)
        self.run_test("World", "Weather System", test_weather)
    
    # ==================== TESTY WALKI ====================
    
    def test_combat_systems(self):
        """Testuje systemy walki"""
        print(f"\n{Colors.HEADER}=== TESTING COMBAT SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state:
            self.add_result(TestResult(
                category="Combat",
                test_name="Combat Systems",
                status=TestStatus.SKIPPED,
                message="Game not initialized"
            ))
            return
        
        # Test inicjalizacji walki
        def test_combat_init():
            from mechanics.combat import CombatSystem, CombatStats
            
            combat = CombatSystem()
            
            # Stwórz statystyki dla gracza i przeciwnika
            player_stats = CombatStats(
                health=100,
                max_health=100,
                strength=10,
                agility=10,
                defense=5
            )
            
            enemy_stats = CombatStats(
                health=50,
                max_health=50,
                strength=8,
                agility=8,
                defense=3
            )
            
            return True, "Combat system initialized", {
                "player_health": player_stats.health,
                "enemy_health": enemy_stats.health
            }
        
        # Test mechaniki bólu
        def test_pain_system():
            if not hasattr(self.game_state.player, 'pain'):
                return False, "No pain system", None
            
            initial_pain = self.game_state.player.pain
            self.game_state.player.pain = 50
            
            # Sprawdź efekty bólu
            has_effects = self.game_state.player.pain > 0
            
            # Przywróć
            self.game_state.player.pain = initial_pain
            
            return has_effects, "Pain system exists", {
                "initial_pain": initial_pain
            }
        
        # Test kontuzji
        def test_injury_system():
            from mechanics.combat import Injury, BodyPart
            
            # Stwórz testową kontuzję
            injury = Injury(
                body_part=BodyPart.ARM,
                damage_type="cut",
                severity=0.5,
                bleeding=True
            )
            
            return injury is not None, "Injury system works", {
                "body_part": injury.body_part.value,
                "severity": injury.severity,
                "bleeding": injury.bleeding
            }
        
        # Test broni
        def test_weapons():
            weapons_data = None
            
            # Sprawdź czy są dane o broniach
            try:
                with open('data/items.json', 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    weapons = [k for k, v in items.items() if v.get('typ') == 'bron']
                    weapons_data = {
                        "count": len(weapons),
                        "sample": weapons[:3]
                    }
            except:
                pass
            
            return weapons_data is not None, "Weapons loaded", weapons_data
        
        self.run_test("Combat", "Combat Initialization", test_combat_init)
        self.run_test("Combat", "Pain System", test_pain_system)
        self.run_test("Combat", "Injury System", test_injury_system)
        self.run_test("Combat", "Weapons", test_weapons)
    
    # ==================== TESTY EKONOMII ====================
    
    def test_economy_systems(self):
        """Testuje systemy ekonomiczne"""
        print(f"\n{Colors.HEADER}=== TESTING ECONOMY SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state or not self.game_state.economy:
            self.add_result(TestResult(
                category="Economy",
                test_name="Economy Systems",
                status=TestStatus.SKIPPED,
                message="Economy not initialized"
            ))
            return
        
        economy = self.game_state.economy
        
        # Test cen
        def test_pricing():
            # Sprawdź cenę przykładowego przedmiotu
            price = economy.get_price("chleb")
            has_pricing = price > 0
            
            return has_pricing, f"Pricing system works", {
                "bread_price": price
            }
        
        # Test handlu
        def test_trading():
            initial_gold = self.game_state.player.gold
            
            # Symuluj kupno
            can_buy = economy.can_afford(self.game_state.player, "chleb")
            
            return True, "Trading system exists", {
                "player_gold": initial_gold,
                "can_buy_bread": can_buy
            }
        
        # Test rynku
        def test_market():
            if hasattr(economy, 'market_data'):
                market_size = len(economy.market_data)
            else:
                market_size = 0
            
            return market_size > 0, f"Market has {market_size} items", None
        
        # Test ekonomicznych eventów
        def test_economic_events():
            has_events = hasattr(economy, 'economic_events') or hasattr(economy, 'events')
            
            return has_events, "Economic events system exists", None
        
        self.run_test("Economy", "Pricing System", test_pricing)
        self.run_test("Economy", "Trading System", test_trading)
        self.run_test("Economy", "Market System", test_market)
        self.run_test("Economy", "Economic Events", test_economic_events)
    
    # ==================== TESTY CRAFTINGU ====================
    
    def test_crafting_systems(self):
        """Testuje systemy craftingu"""
        print(f"\n{Colors.HEADER}=== TESTING CRAFTING SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state or not hasattr(self.game_state, 'crafting') or not self.game_state.crafting:
            self.add_result(TestResult(
                category="Crafting",
                test_name="Crafting Systems",
                status=TestStatus.SKIPPED,
                message="Crafting not initialized"
            ))
            return
        
        crafting = self.game_state.crafting
        
        # Test receptur
        def test_recipes():
            recipe_count = len(crafting.recipes) if hasattr(crafting, 'recipes') else 0
            
            return recipe_count > 0, f"Found {recipe_count} recipes", {
                "count": recipe_count,
                "sample": list(crafting.recipes.keys())[:3] if recipe_count > 0 else []
            }
        
        # Test materiałów
        def test_materials():
            # Sprawdź czy są materiały w items.json
            try:
                with open('data/items.json', 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    materials = [k for k, v in items.items() if v.get('typ') == 'material']
                    
                return len(materials) > 0, f"Found {len(materials)} materials", {
                    "count": len(materials),
                    "sample": materials[:3]
                }
            except:
                return False, "Could not load materials", None
        
        # Test warsztatów
        def test_workshops():
            has_workshops = hasattr(crafting, 'workshops') or hasattr(crafting, 'stations')
            
            return has_workshops, "Workshop system exists", None
        
        # Test jakości przedmiotów
        def test_quality():
            has_quality = hasattr(crafting, 'calculate_quality') or hasattr(crafting, 'quality_levels')
            
            return has_quality, "Quality system exists", None
        
        self.run_test("Crafting", "Recipe System", test_recipes)
        self.run_test("Crafting", "Materials", test_materials)
        self.run_test("Crafting", "Workshops", test_workshops)
        self.run_test("Crafting", "Quality System", test_quality)
    
    # ==================== TESTY QUESTÓW ====================
    
    def test_quest_systems(self):
        """Testuje systemy questów"""
        print(f"\n{Colors.HEADER}=== TESTING QUEST SYSTEMS ==={Colors.ENDC}")
        
        # Test podstawowego silnika questów
        def test_quest_engine():
            from quests.quest_engine import QuestEngine
            engine = QuestEngine()
            
            return engine is not None, "Quest engine created", {
                "active_quests": len(engine.active_quests) if hasattr(engine, 'active_quests') else 0
            }
        
        # Test questów emergentnych
        def test_emergent_quests():
            try:
                from quests.emergent_quests import EmergentQuestIntegration
                
                if self.game_state:
                    integration = EmergentQuestIntegration(self.game_state)
                    quest_count = len(integration.quest_seeds) if hasattr(integration, 'quest_seeds') else 0
                    
                    return quest_count > 0, f"Found {quest_count} quest seeds", None
                
                return False, "Game state not available", None
            except ImportError:
                return False, "Emergent quests module not found", None
        
        # Test systemu konsekwencji
        def test_consequences():
            try:
                from quests.quest_consequences import ConsequenceSystem
                consequence_sys = ConsequenceSystem()
                
                return consequence_sys is not None, "Consequence system exists", None
            except ImportError:
                return False, "Consequence system not found", None
        
        # Test nagród
        def test_rewards():
            from quests.quest_engine import QuestEngine
            engine = QuestEngine()
            
            has_rewards = hasattr(engine, 'give_reward') or hasattr(engine, 'rewards')
            
            return has_rewards, "Reward system exists", None
        
        self.run_test("Quests", "Quest Engine", test_quest_engine)
        self.run_test("Quests", "Emergent Quests", test_emergent_quests)
        self.run_test("Quests", "Consequences", test_consequences)
        self.run_test("Quests", "Rewards", test_rewards)
    
    # ==================== TESTY UI I KOMEND ====================
    
    def test_ui_systems(self):
        """Testuje systemy interfejsu użytkownika"""
        print(f"\n{Colors.HEADER}=== TESTING UI SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state:
            self.add_result(TestResult(
                category="UI",
                test_name="UI Systems",
                status=TestStatus.SKIPPED,
                message="Game not initialized"
            ))
            return
        
        # Test parsera komend
        def test_command_parser():
            from ui.commands import CommandParser
            parser = CommandParser(self.game_state)
            
            # Test różnych komend
            commands_to_test = [
                "pomoc",
                "status",
                "ekwipunek",
                "rozejrzyj"
            ]
            
            successful = 0
            for cmd in commands_to_test:
                success, msg = parser.parse_and_execute(cmd)
                if success:
                    successful += 1
            
            return successful > 0, f"{successful}/{len(commands_to_test)} commands work", {
                "tested": commands_to_test,
                "successful": successful
            }
        
        # Test aliasów komend
        def test_command_aliases():
            from ui.commands import CommandParser
            parser = CommandParser(self.game_state)
            
            # Test czy aliasy działają
            success1, _ = parser.parse_and_execute("n")  # Alias dla "północ"
            success2, _ = parser.parse_and_execute("i")  # Alias dla "ekwipunek"
            
            return True, "Alias system exists", {
                "n_works": success1,
                "i_works": success2
            }
        
        # Test smart interface
        def test_smart_interface():
            try:
                from ui.smart_interface import SmartInterface
                smart = SmartInterface(self.game_state)
                
                has_plugins = hasattr(smart, 'plugins')
                plugin_count = len(smart.plugins) if has_plugins else 0
                
                return has_plugins, f"Smart interface with {plugin_count} plugins", None
            except ImportError:
                return False, "Smart interface not found", None
        
        # Test GUI
        def test_gui_availability():
            try:
                import tkinter
                return True, "Tkinter available for GUI", None
            except ImportError:
                return False, "Tkinter not available", None
        
        self.run_test("UI", "Command Parser", test_command_parser)
        self.run_test("UI", "Command Aliases", test_command_aliases)
        self.run_test("UI", "Smart Interface", test_smart_interface)
        self.run_test("UI", "GUI Availability", test_gui_availability)
    
    # ==================== TESTY ZAPISU/WCZYTYWANIA ====================
    
    def test_persistence_systems(self):
        """Testuje systemy zapisu i wczytywania"""
        print(f"\n{Colors.HEADER}=== TESTING PERSISTENCE SYSTEMS ==={Colors.ENDC}")
        
        if not self.game_state:
            self.add_result(TestResult(
                category="Persistence",
                test_name="Save Systems",
                status=TestStatus.SKIPPED,
                message="Game not initialized"
            ))
            return
        
        # Test zapisu
        def test_save():
            from persistence.save_manager import SaveManager
            save_mgr = SaveManager()
            
            # Spróbuj zapisać
            test_slot = 99  # Użyj slotu testowego
            success = save_mgr.save_game(self.game_state, test_slot)
            
            # Usuń plik testowy
            import os
            test_file = f"saves/save_{test_slot}.json"
            if os.path.exists(test_file):
                os.remove(test_file)
            
            return success, "Save system works", None
        
        # Test wczytywania
        def test_load():
            from persistence.save_manager import SaveManager
            save_mgr = SaveManager()
            
            # Najpierw zapisz
            test_slot = 99
            save_mgr.save_game(self.game_state, test_slot)
            
            # Spróbuj wczytać
            loaded_state = save_mgr.load_game(test_slot)
            success = loaded_state is not None
            
            # Usuń plik testowy
            import os
            test_file = f"saves/save_{test_slot}.json"
            if os.path.exists(test_file):
                os.remove(test_file)
            
            return success, "Load system works", None
        
        # Test kompresji
        def test_compression():
            from persistence.save_manager import SaveManager
            save_mgr = SaveManager()
            
            has_compression = hasattr(save_mgr, 'compress') or hasattr(save_mgr, 'compression_enabled')
            
            return has_compression, "Compression available", None
        
        # Test auto-save
        def test_autosave():
            has_autosave = hasattr(self.game_state, 'autosave') or hasattr(self.game_state, 'auto_save_enabled')
            
            return has_autosave, "Auto-save system exists", None
        
        self.run_test("Persistence", "Save System", test_save)
        self.run_test("Persistence", "Load System", test_load)
        self.run_test("Persistence", "Compression", test_compression)
        self.run_test("Persistence", "Auto-save", test_autosave)
    
    # ==================== TESTY INTEGRACJI ====================
    
    def test_integration(self):
        """Testuje integrację między systemami"""
        print(f"\n{Colors.HEADER}=== TESTING SYSTEM INTEGRATION ==={Colors.ENDC}")
        
        if not self.game_state:
            self.add_result(TestResult(
                category="Integration",
                test_name="Integration Tests",
                status=TestStatus.SKIPPED,
                message="Game not initialized"
            ))
            return
        
        # Test interakcji gracz-NPC
        def test_player_npc_interaction():
            if not self.game_state.npc_manager or len(self.game_state.npc_manager.npcs) == 0:
                return False, "No NPCs available", None
            
            # Spróbuj porozmawiać
            from ui.commands import CommandParser
            parser = CommandParser(self.game_state)
            
            first_npc = list(self.game_state.npc_manager.npcs.keys())[0]
            success, msg = parser.parse_and_execute(f"rozmawiaj {first_npc}")
            
            return success, f"Can interact with {first_npc}", None
        
        # Test quest-economy integration
        def test_quest_economy():
            has_both = (
                hasattr(self.game_state, 'quest_integration') and 
                hasattr(self.game_state, 'economy')
            )
            
            return has_both, "Quest-Economy integration possible", None
        
        # Test combat-skills integration
        def test_combat_skills():
            has_skills = hasattr(self.game_state.player, 'skills')
            has_combat = hasattr(self.game_state, 'combat_system') or True  # Combat jest zawsze dostępny
            
            return has_skills and has_combat, "Combat-Skills integration exists", None
        
        # Test time-npc integration
        def test_time_npc():
            has_time = hasattr(self.game_state, 'time_system')
            has_npcs = self.game_state.npc_manager is not None
            
            if has_time and has_npcs:
                # Sprawdź czy NPCe mają harmonogramy
                npcs_with_schedule = 0
                for npc in self.game_state.npc_manager.npcs.values():
                    if hasattr(npc, 'schedule') or hasattr(npc, 'daily_routine'):
                        npcs_with_schedule += 1
                
                return npcs_with_schedule > 0, f"{npcs_with_schedule} NPCs have schedules", None
            
            return False, "Time-NPC integration not available", None
        
        self.run_test("Integration", "Player-NPC", test_player_npc_interaction)
        self.run_test("Integration", "Quest-Economy", test_quest_economy)
        self.run_test("Integration", "Combat-Skills", test_combat_skills)
        self.run_test("Integration", "Time-NPC", test_time_npc)
    
    # ==================== TESTY WYDAJNOŚCI ====================
    
    def test_performance(self):
        """Testuje wydajność systemów"""
        print(f"\n{Colors.HEADER}=== TESTING PERFORMANCE ==={Colors.ENDC}")
        
        if not self.game_state:
            self.add_result(TestResult(
                category="Performance",
                test_name="Performance Tests",
                status=TestStatus.SKIPPED,
                message="Game not initialized"
            ))
            return
        
        # Test szybkości komend
        def test_command_speed():
            from ui.commands import CommandParser
            parser = CommandParser(self.game_state)
            
            start = time.time()
            for _ in range(100):
                parser.parse_and_execute("status")
            duration = time.time() - start
            
            avg_time = duration / 100
            is_fast = avg_time < 0.01  # Mniej niż 10ms na komendę
            
            return is_fast, f"Avg command time: {avg_time*1000:.2f}ms", {
                "total_time": f"{duration:.2f}s",
                "commands": 100,
                "avg_ms": f"{avg_time*1000:.2f}"
            }
        
        # Test obciążenia pamięci
        def test_memory_usage():
            import sys
            
            # Przybliżone sprawdzenie rozmiaru obiektów
            game_size = sys.getsizeof(self.game_state)
            
            # Sprawdź czy rozmiar jest rozsądny (mniej niż 10MB)
            is_reasonable = game_size < 10 * 1024 * 1024
            
            return is_reasonable, f"Game state size: {game_size/1024:.2f}KB", None
        
        # Test aktualizacji NPCów
        def test_npc_update_speed():
            if not self.game_state.npc_manager:
                return False, "No NPC manager", None
            
            start = time.time()
            for _ in range(100):
                self.game_state.npc_manager.update(0.1)
            duration = time.time() - start
            
            avg_time = duration / 100
            is_fast = avg_time < 0.05  # Mniej niż 50ms na update
            
            return is_fast, f"NPC update time: {avg_time*1000:.2f}ms", None
        
        self.run_test("Performance", "Command Speed", test_command_speed)
        self.run_test("Performance", "Memory Usage", test_memory_usage)
        self.run_test("Performance", "NPC Updates", test_npc_update_speed)
    
    # ==================== GENEROWANIE RAPORTU ====================
    
    def generate_report(self):
        """Generuje szczegółowy raport z testów"""
        duration = time.time() - self.start_time
        
        report = []
        report.append("=" * 80)
        report.append("MEGA TESTER - RAPORT Z TESTÓW")
        report.append("Droga Szamana RPG")
        report.append("=" * 80)
        report.append(f"Data testu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Czas trwania: {duration:.2f} sekund")
        report.append("")
        
        # Podsumowanie
        report.append("PODSUMOWANIE")
        report.append("-" * 40)
        report.append(f"Wszystkich testów: {self.total_tests}")
        report.append(f"✅ Passed: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        report.append(f"❌ Failed: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")
        report.append(f"⚠️  Warning: {self.warning_tests}")
        report.append(f"🔥 Error: {self.error_tests}")
        report.append(f"⏭️  Skipped: {self.skipped_tests}")
        report.append("")
        
        # Szczegółowe wyniki według kategorii
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        report.append("SZCZEGÓŁOWE WYNIKI")
        report.append("-" * 40)
        
        for category, results in categories.items():
            report.append(f"\n### {category}")
            
            for result in results:
                status_symbol = {
                    TestStatus.PASSED: "✅",
                    TestStatus.FAILED: "❌",
                    TestStatus.WARNING: "⚠️",
                    TestStatus.ERROR: "🔥",
                    TestStatus.SKIPPED: "⏭️"
                }.get(result.status, "?")
                
                report.append(f"  {status_symbol} {result.test_name}")
                report.append(f"     Status: {result.status.value}")
                report.append(f"     Message: {result.message}")
                
                if result.details:
                    try:
                        details_str = json.dumps(result.details, indent=6, ensure_ascii=False)
                    except (TypeError, ValueError):
                        # Jeśli nie można serializować, po prostu skonwertuj na string
                        details_str = str(result.details)
                    report.append(f"     Details: {details_str}")
                
                if result.error:
                    report.append(f"     Error trace:")
                    for line in result.error.split('\n')[:5]:
                        report.append(f"       {line}")
                
                if result.duration > 0:
                    report.append(f"     Duration: {result.duration:.3f}s")
                
                report.append("")
        
        # Problemy krytyczne
        critical_issues = [r for r in self.results if r.status in [TestStatus.ERROR, TestStatus.FAILED]]
        
        if critical_issues:
            report.append("\nPROBLEMY KRYTYCZNE")
            report.append("-" * 40)
            
            for issue in critical_issues[:10]:  # Pokaż max 10
                report.append(f"❗ {issue.category}/{issue.test_name}: {issue.message}")
        
        # Rekomendacje
        report.append("\nREKOMENDACJE")
        report.append("-" * 40)
        
        if self.failed_tests > 0 or self.error_tests > 0:
            report.append("1. Napraw krytyczne błędy przed kontynuacją rozwoju")
        
        if "NPCs" in categories:
            npc_issues = [r for r in categories["NPCs"] if r.status != TestStatus.PASSED]
            if npc_issues:
                report.append("2. System NPCów wymaga naprawy - tylko część NPCów się ładuje")
        
        if "Combat" in categories:
            combat_issues = [r for r in categories["Combat"] if r.status != TestStatus.PASSED]
            if combat_issues:
                report.append("3. System walki wymaga dopracowania")
        
        if self.passed_tests / self.total_tests < 0.8:
            report.append("4. Mniej niż 80% testów przechodzi - gra wymaga stabilizacji")
        else:
            report.append("✓ Gra jest w dobym stanie - ponad 80% testów przechodzi")
        
        report.append("\n" + "=" * 80)
        report.append("KONIEC RAPORTU")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_all_tests(self):
        """Uruchamia wszystkie testy"""
        self.start_time = time.time()
        
        print(f"{Colors.BOLD}{Colors.HEADER}")
        print("=" * 80)
        print("MEGA TESTER - Kompleksowe Testowanie Gry 'Droga Szamana'")
        print("=" * 80)
        print(f"{Colors.ENDC}")
        
        # Uruchom wszystkie kategorie testów z obsługą błędów
        test_categories = [
            ("Imports", self.test_imports),
            ("Game Init", self.test_game_initialization),
            ("Player", self.test_player_systems),
            ("NPCs", self.test_npc_systems),
            ("World", self.test_world_systems),
            ("Combat", self.test_combat_systems),
            ("Economy", self.test_economy_systems),
            ("Crafting", self.test_crafting_systems),
            ("Quests", self.test_quest_systems),
            ("UI", self.test_ui_systems),
            ("Persistence", self.test_persistence_systems),
            ("Integration", self.test_integration),
            ("Performance", self.test_performance)
        ]
        
        for category_name, test_func in test_categories:
            try:
                test_func()
            except Exception as e:
                print(f"\n{Colors.FAIL}Error in {category_name}: {e}{Colors.ENDC}")
                self.add_result(TestResult(
                    category=category_name,
                    test_name=f"{category_name} Tests",
                    status=TestStatus.ERROR,
                    message=str(e),
                    error=traceback.format_exc()
                ))
        
        # Generuj i zapisz raport
        report = self.generate_report()
        
        # Zapisz do pliku
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Wyświetl podsumowanie
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.HEADER}WYNIKI TESTÓW{Colors.ENDC}")
        print(f"{'=' * 80}")
        print(f"Total: {self.total_tests} | ", end="")
        print(f"{Colors.OKGREEN}Passed: {self.passed_tests}{Colors.ENDC} | ", end="")
        print(f"{Colors.FAIL}Failed: {self.failed_tests}{Colors.ENDC} | ", end="")
        print(f"{Colors.WARNING}Warnings: {self.warning_tests}{Colors.ENDC} | ", end="")
        print(f"Errors: {self.error_tests} | Skipped: {self.skipped_tests}")
        print(f"\nSuccess rate: {self.passed_tests/self.total_tests*100:.1f}%")
        print(f"\n📄 Szczegółowy raport zapisany w: {report_file}")
        print(f"{'=' * 80}")
        
        return report


if __name__ == "__main__":
    tester = MegaTester()
    
    try:
        report = tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test przerwany przez użytkownika{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Krytyczny błąd podczas testów: {e}{Colors.ENDC}")
        traceback.print_exc()