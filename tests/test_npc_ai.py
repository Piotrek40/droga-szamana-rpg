"""
Testy dla zaawansowanego systemu AI NPCów
Sprawdza behavior trees, pamięć, rutyny i interakcje społeczne
"""

import unittest
import time
import random
from unittest.mock import Mock, patch
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from npcs.npc_manager import NPC, NPCManager, NPCState, EmotionalState, Memory, Relationship, Goal
from npcs.ai_behaviors import (
    create_behavior_tree, NodeStatus, SelectorNode, SequenceNode,
    ConditionalNode, ActionNode, PriorityNode, ParallelNode,
    is_hungry, is_tired, is_under_attack, flee, eat_meal, sleep
)
from npcs.memory_system import (
    IntegratedMemorySystem, EpisodicMemory, SemanticMemory,
    ProceduralMemory, EmotionalMemory, MemoryTrace
)


class TestBehaviorTrees(unittest.TestCase):
    """Testy dla systemu Behavior Trees"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.npc_data = {
            "id": "test_npc",
            "name": "Test NPC",
            "role": "prisoner",
            "location": "cell_1",
            "personality": ["quiet", "planner", "intelligent"],
            "quirks": ["observant"],
            "inventory": {},
            "gold": 10,
            "health": 100,
            "max_health": 100,
            "energy": 80,
            "max_energy": 100
        }
        
        self.npc = NPC(self.npc_data)
        self.context = {
            "time": time.time(),
            "hour": 12,
            "npcs": {"test_npc": self.npc},
            "events": []
        }
    
    def test_behavior_tree_creation(self):
        """Test tworzenia behavior tree"""
        tree = create_behavior_tree("prisoner", ["quiet", "planner"])
        self.assertIsNotNone(tree)
        
        # Sprawdź czy tree ma dzieci
        self.assertTrue(hasattr(tree, 'children') or hasattr(tree, 'child'))
    
    def test_priority_node_execution(self):
        """Test węzła priorytetowego"""
        priority_node = PriorityNode("test_priority")
        
        # Dodaj dzieci z różnymi priorytetami
        high_priority = ActionNode("high", lambda n, c: NodeStatus.SUCCESS)
        low_priority = ActionNode("low", lambda n, c: NodeStatus.SUCCESS)
        
        priority_node.add_child_with_priority(high_priority, 10.0)
        priority_node.add_child_with_priority(low_priority, 5.0)
        
        # Wykonaj
        status = priority_node.execute(self.npc, self.context)
        self.assertEqual(status, NodeStatus.SUCCESS)
    
    def test_parallel_node_execution(self):
        """Test węzła równoległego"""
        parallel_node = ParallelNode("test_parallel", success_threshold=2)
        
        # Dodaj dzieci
        success1 = ActionNode("success1", lambda n, c: NodeStatus.SUCCESS)
        success2 = ActionNode("success2", lambda n, c: NodeStatus.SUCCESS)
        failure = ActionNode("failure", lambda n, c: NodeStatus.FAILURE)
        
        parallel_node.add_child(success1)
        parallel_node.add_child(success2)
        parallel_node.add_child(failure)
        
        # Wykonaj - powinno być SUCCESS bo 2 sukces >= threshold
        status = parallel_node.execute(self.npc, self.context)
        self.assertEqual(status, NodeStatus.SUCCESS)
    
    def test_conditional_node(self):
        """Test węzła warunkowego"""
        # Test głodu
        self.npc.hunger = 70
        hungry_condition = ConditionalNode("is_hungry", is_hungry)
        status = hungry_condition.execute(self.npc, self.context)
        self.assertEqual(status, NodeStatus.SUCCESS)
        
        # Test zmęczenia
        self.npc.energy = 20
        tired_condition = ConditionalNode("is_tired", is_tired)
        status = tired_condition.execute(self.npc, self.context)
        self.assertEqual(status, NodeStatus.SUCCESS)
    
    def test_behavior_tree_interruption(self):
        """Test przerwania sekwencji przez ważniejsze zadanie"""
        # Symuluj atak podczas jedzenia
        self.npc.hunger = 80
        self.context["events"] = [{"type": "attack", "participants": ["test_npc"]}]
        
        tree = create_behavior_tree("prisoner", ["quiet"])
        status = tree.execute(self.npc, self.context)
        
        # Powinien uciekać zamiast jeść
        self.assertEqual(self.npc.current_state, NPCState.FLEEING)


class TestMemorySystem(unittest.TestCase):
    """Testy dla systemu pamięci"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.memory_system = IntegratedMemorySystem("test_npc")
    
    def test_episodic_memory_storage(self):
        """Test przechowywania pamięci epizodycznej"""
        event = {
            "event_type": "attack",
            "description": "Został zaatakowany przez strażnika",
            "participants": ["test_npc", "guard_1"],
            "location": "corridor",
            "importance": 0.8,
            "emotional_impact": {"fear": 0.7, "angry": 0.5}
        }
        
        self.memory_system.process_event(event)
        
        # Sprawdź czy wydarzenie zostało zapisane
        recalled = self.memory_system.episodic.recall({"event_type": "attack"})
        self.assertTrue(len(recalled) > 0)
        self.assertEqual(recalled[0]["event_type"], "attack")
    
    def test_memory_associations(self):
        """Test tworzenia powiązań między wspomnieniami"""
        # Dodaj powiązane wydarzenia
        event1 = {
            "event_type": "threat",
            "participants": ["guard_1"],
            "location": "cell",
            "importance": 0.6,
            "timestamp": time.time()
        }
        
        event2 = {
            "event_type": "attack",
            "participants": ["guard_1"],
            "location": "cell",
            "importance": 0.8,
            "timestamp": time.time() + 10
        }
        
        self.memory_system.episodic.add_memory(event1)
        self.memory_system.episodic.add_memory(event2)
        
        # Sprawdź powiązania
        self.assertTrue(len(event2.get("associations", [])) > 0)
    
    def test_semantic_memory(self):
        """Test pamięci semantycznej"""
        # Dodaj wiedzę
        self.memory_system.semantic.add_knowledge(
            "tunnel_location",
            {"location": "behind_kitchen", "discovered": time.time()},
            "escape_routes"
        )
        
        # Pobierz wiedzę
        knowledge = self.memory_system.semantic.retrieve("tunnel_location")
        self.assertIsNotNone(knowledge)
        self.assertEqual(knowledge["location"], "behind_kitchen")
        
        # Sprawdź powiązane koncepty
        related = self.memory_system.semantic.get_related("tunnel_location")
        self.assertIsInstance(related, list)
    
    def test_procedural_memory(self):
        """Test pamięci proceduralnej"""
        # Naucz umiejętności
        self.memory_system.procedural.learn_skill(
            "lockpicking",
            ["insert_pick", "apply_tension", "feel_pins", "turn_lock"],
            {"difficulty": "medium"}
        )
        
        # Wykonaj umiejętność
        success, steps = self.memory_system.procedural.execute_skill(
            "lockpicking",
            {"lock_type": "standard"}
        )
        
        self.assertIsInstance(success, bool)
        self.assertIsInstance(steps, list)
        self.assertTrue(len(steps) > 0)
    
    def test_emotional_memory(self):
        """Test pamięci emocjonalnej"""
        # Oznacz emocje związane z miejscem
        self.memory_system.emotional.tag_emotion("cell_1", "fear", 0.8)
        self.memory_system.emotional.tag_emotion("cell_1", "disgust", 0.5)
        
        # Pobierz reakcję emocjonalną
        response = self.memory_system.emotional.get_emotional_response("cell_1")
        self.assertIn("fear", response)
        self.assertTrue(response["fear"] > 0)
    
    def test_trauma_processing(self):
        """Test przetwarzania traumy"""
        trauma_event = {
            "event_type": "torture",
            "intensity": 0.9,
            "elements": ["guard_1", "torture_room", "whip"],
            "location": "torture_room",
            "participants": ["test_npc", "guard_1"]
        }
        
        result = self.memory_system.emotional.process_trauma(trauma_event)
        
        self.assertTrue(result["trauma_recorded"])
        self.assertTrue(result["triggers_identified"] > 0)
        
        # Sprawdź wyzwalacze
        trigger_intensity = self.memory_system.emotional.check_triggers({
            "location": "torture_room"
        })
        self.assertTrue(trigger_intensity > 0)
    
    def test_memory_consolidation(self):
        """Test konsolidacji pamięci"""
        # Dodaj wiele wspomnień
        for i in range(20):
            self.memory_system.episodic.add_memory({
                "event_type": "routine",
                "description": f"Routine event {i}",
                "participants": ["test_npc"],
                "location": "cell",
                "importance": random.uniform(0.1, 0.5),
                "timestamp": time.time() - i * 3600
            })
        
        # Konsoliduj
        initial_count = len(self.memory_system.episodic.memories)
        self.memory_system.consolidate_all()
        
        # Sprawdź czy słabe wspomnienia zostały osłabione
        for memory in self.memory_system.episodic.memories:
            if memory["importance"] < 0.2:
                self.assertTrue(memory["strength"] < 0.8)


class TestNPCInteractions(unittest.TestCase):
    """Testy interakcji między NPCami"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.manager = NPCManager("data/npc_complete.json")
        self.context = {
            "time": time.time(),
            "hour": 14,
            "npcs": self.manager.npcs,
            "events": []
        }
    
    def test_relationship_building(self):
        """Test budowania relacji"""
        if len(self.manager.npcs) < 2:
            self.skipTest("Niewystarczająca liczba NPCów do testu")
        
        npc_ids = list(self.manager.npcs.keys())
        npc1 = self.manager.npcs[npc_ids[0]]
        npc2 = self.manager.npcs[npc_ids[1]]
        
        # Początkowa relacja
        initial_trust = npc1.get_relationship(npc2.id).trust
        
        # Pozytywna interakcja
        npc1.interact_with(npc2.id, "help", 1.0)
        
        # Sprawdź zmianę relacji
        new_trust = npc1.get_relationship(npc2.id).trust
        self.assertTrue(new_trust > initial_trust)
    
    def test_gossip_spreading(self):
        """Test rozprzestrzeniania plotek"""
        if len(self.manager.npcs) < 3:
            self.skipTest("Niewystarczająca liczba NPCów do testu")
        
        npc_ids = list(self.manager.npcs.keys())
        source = self.manager.npcs[npc_ids[0]]
        recipient = self.manager.npcs[npc_ids[1]]
        
        # Utwórz plotkę
        gossip = {
            "type": "escape_attempt",
            "participants": [npc_ids[2]],
            "location": "tunnel",
            "credibility": 0.7
        }
        
        # Podziel się plotką
        from npcs.ai_behaviors import share_gossip
        share_gossip(source, recipient, gossip)
        
        # Sprawdź czy plotka została przekazana
        self.assertTrue(any("gossip" in key for key in recipient.semantic_memory.keys()))
    
    def test_group_dynamics(self):
        """Test dynamiki grupowej"""
        # Symuluj spotkanie grupowe
        location = "mess_hall"
        for npc in list(self.manager.npcs.values())[:3]:
            npc.location = location
            npc.current_state = NPCState.SOCIALIZING
        
        # Przetwórz interakcje
        self.manager._process_npc_interactions()
        
        # Sprawdź czy nastąpiły interakcje
        self.assertTrue(len(self.manager.world_events) > 0)
    
    def test_conflict_resolution(self):
        """Test rozwiązywania konfliktów"""
        if len(self.manager.npcs) < 2:
            self.skipTest("Niewystarczająca liczba NPCów do testu")
        
        npc_ids = list(self.manager.npcs.keys())
        npc1 = self.manager.npcs[npc_ids[0]]
        npc2 = self.manager.npcs[npc_ids[1]]
        
        # Utwórz konflikt
        npc1.interact_with(npc2.id, "threat", 2.0)
        npc2.interact_with(npc1.id, "threat", 2.0)
        
        # Sprawdź relacje
        self.assertTrue(npc1.get_relationship(npc2.id).fear > 0)
        self.assertTrue(npc1.get_relationship(npc2.id).trust < 0)


class TestDailyRoutines(unittest.TestCase):
    """Testy codziennych rutyn NPCów"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.npc_data = {
            "id": "routine_test",
            "name": "Routine Test",
            "role": "prisoner",
            "location": "cell_1",
            "personality": ["organized"],
            "quirks": [],
            "inventory": {},
            "gold": 10,
            "health": 100,
            "max_health": 100,
            "energy": 100,
            "max_energy": 100,
            "schedule": {}
        }
        
        self.npc = NPC(self.npc_data)
    
    def test_schedule_adherence(self):
        """Test przestrzegania harmonogramu"""
        # Ustaw harmonogram
        self.npc.schedule = {
            6: "waking_routine",
            7: "eating",
            8: "working",
            12: "eating",
            18: "eating",
            19: "socializing",
            22: "sleeping"
        }
        
        # Test różnych godzin
        test_hours = [7, 8, 12, 19, 22]
        expected_activities = ["eating", "working", "eating", "socializing", "sleeping"]
        
        for hour, expected in zip(test_hours, expected_activities):
            context = {"hour": hour, "npcs": {}, "events": []}
            self.npc._check_schedule(time.time())
            
            # Sprawdź czy stan odpowiada harmonogramowi
            if expected == "eating":
                self.assertIn(self.npc.current_state, [NPCState.EATING, NPCState.IDLE])
            elif expected == "working":
                self.assertIn(self.npc.current_state, [NPCState.WORKING, NPCState.IDLE])
            elif expected == "sleeping":
                self.assertIn(self.npc.current_state, [NPCState.SLEEPING, NPCState.IDLE])
    
    def test_schedule_variation(self):
        """Test wariacji w harmonogramie"""
        self.npc.schedule_variation = 0.5  # 50% szans na ignorowanie harmonogramu
        
        variations_count = 0
        for _ in range(100):
            old_state = self.npc.current_state
            self.npc._check_schedule(time.time())
            if self.npc.current_state == old_state:
                variations_count += 1
        
        # Powinno być około 50 wariacji
        self.assertTrue(30 < variations_count < 70)
    
    def test_emergency_interruption(self):
        """Test przerwania rutyny przez sytuację kryzysową"""
        self.npc.schedule[12] = "eating"
        self.npc.current_state = NPCState.EATING
        
        # Symuluj atak
        context = {
            "hour": 12,
            "events": [{"type": "attack", "participants": ["routine_test"]}],
            "npcs": {}
        }
        
        tree = create_behavior_tree("prisoner", [])
        tree.execute(self.npc, context)
        
        # Powinien przestać jeść i uciekać
        self.assertEqual(self.npc.current_state, NPCState.FLEEING)


class TestEmotionalStates(unittest.TestCase):
    """Testy stanów emocjonalnych"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.npc_data = {
            "id": "emotional_test",
            "name": "Emotional Test",
            "role": "prisoner",
            "location": "cell_1",
            "personality": ["emotional"],
            "quirks": [],
            "inventory": {},
            "gold": 10,
            "health": 100,
            "max_health": 100,
            "energy": 100,
            "max_energy": 100
        }
        
        self.npc = NPC(self.npc_data)
    
    def test_emotion_modification(self):
        """Test modyfikacji emocji"""
        initial_happy = self.npc.emotional_states[EmotionalState.HAPPY]
        
        self.npc.modify_emotion(EmotionalState.HAPPY, 0.3)
        
        new_happy = self.npc.emotional_states[EmotionalState.HAPPY]
        self.assertTrue(new_happy > initial_happy)
        
        # Sprawdź normalizację
        total = sum(self.npc.emotional_states.values())
        self.assertAlmostEqual(total, 1.0, places=5)
    
    def test_emotion_decay(self):
        """Test wygasania emocji"""
        self.npc.modify_emotion(EmotionalState.ANGRY, 0.5)
        initial_anger = self.npc.emotional_states[EmotionalState.ANGRY]
        
        # Symuluj upływ czasu
        self.npc._decay_emotions(10.0)
        
        new_anger = self.npc.emotional_states[EmotionalState.ANGRY]
        self.assertTrue(new_anger < initial_anger)
    
    def test_dominant_emotion(self):
        """Test dominującej emocji"""
        self.npc.modify_emotion(EmotionalState.FEAR, 0.6)
        self.npc.modify_emotion(EmotionalState.ANGRY, 0.3)
        
        dominant = self.npc.get_dominant_emotion()
        self.assertEqual(dominant, EmotionalState.FEAR)
    
    def test_emotional_impact_on_behavior(self):
        """Test wpływu emocji na zachowanie"""
        # Ustaw wysokie zmęczenie i złość
        self.npc.energy = 10
        self.npc.modify_emotion(EmotionalState.ANGRY, 0.7)
        
        context = {"hour": 14, "npcs": {}, "events": []}
        
        # Zły i zmęczony NPC powinien być bardziej agresywny
        tree = create_behavior_tree("prisoner", ["aggressive"])
        status = tree.execute(self.npc, context)
        
        # Sprawdź czy emocje wpłynęły na decyzje
        self.assertIsNotNone(status)


class TestGoalSystem(unittest.TestCase):
    """Testy systemu celów"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.npc_data = {
            "id": "goal_test",
            "name": "Goal Test",
            "role": "prisoner",
            "location": "cell_1",
            "personality": ["determined"],
            "quirks": [],
            "inventory": {},
            "gold": 10,
            "health": 100,
            "max_health": 100,
            "energy": 100,
            "max_energy": 100,
            "goals": []
        }
        
        self.npc = NPC(self.npc_data)
    
    def test_goal_creation(self):
        """Test tworzenia celów"""
        goal = Goal(
            name="escape_prison",
            priority=0.9,
            prerequisites=["find_tunnel", "get_tools"]
        )
        
        self.npc.goals.append(goal)
        
        self.assertEqual(len(self.npc.goals), 1)
        self.assertEqual(self.npc.goals[0].name, "escape_prison")
    
    def test_goal_urgency(self):
        """Test pilności celów"""
        current_time = time.time()
        
        urgent_goal = Goal(
            name="urgent_task",
            priority=0.8,
            deadline=current_time + 1800  # Za 30 minut
        )
        
        non_urgent_goal = Goal(
            name="long_term",
            priority=0.5,
            deadline=current_time + 86400  # Za dzień
        )
        
        self.assertTrue(urgent_goal.is_urgent(current_time))
        self.assertFalse(non_urgent_goal.is_urgent(current_time))
    
    def test_goal_completion(self):
        """Test ukończenia celu"""
        goal = Goal(name="test_goal", priority=0.7)
        self.npc.goals.append(goal)
        
        # Symuluj postęp
        for _ in range(10):
            goal.completion = min(1.0, goal.completion + 0.1)
        
        self.assertEqual(goal.completion, 1.0)
        
        # Sprawdź czy cel jest oznaczony jako nieaktywny
        self.npc._update_goals(time.time())
        self.assertFalse(goal.active)
    
    def test_goal_prioritization(self):
        """Test priorytetyzacji celów"""
        goals = [
            Goal(name="low_priority", priority=0.3),
            Goal(name="high_priority", priority=0.9),
            Goal(name="medium_priority", priority=0.5)
        ]
        
        self.npc.goals = goals
        self.npc._update_goals(time.time())
        
        # Cele powinny być posortowane według priorytetu
        self.assertEqual(self.npc.goals[0].name, "high_priority")
        self.assertEqual(self.npc.goals[-1].name, "low_priority")


class TestCombatIntegration(unittest.TestCase):
    """Testy integracji z systemem walki"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.attacker_data = {
            "id": "attacker",
            "name": "Attacker",
            "role": "guard",
            "location": "corridor",
            "personality": ["aggressive"],
            "quirks": [],
            "inventory": {"baton": 1},
            "gold": 50,
            "health": 100,
            "max_health": 100,
            "energy": 100,
            "max_energy": 100,
            "strength": 15
        }
        
        self.defender_data = {
            "id": "defender",
            "name": "Defender",
            "role": "prisoner",
            "location": "corridor",
            "personality": ["peaceful"],
            "quirks": [],
            "inventory": {},
            "gold": 5,
            "health": 80,
            "max_health": 80,
            "energy": 80,
            "max_energy": 80,
            "strength": 10
        }
        
        self.attacker = NPC(self.attacker_data)
        self.defender = NPC(self.defender_data)
    
    def test_combat_initiation(self):
        """Test inicjacji walki"""
        initial_health = self.defender.health
        
        # Atak
        success, message = self.attacker.attack(self.defender)
        
        if success:
            # Sprawdź czy obrażenia zostały zadane
            self.assertTrue(self.defender.health <= initial_health)
            
            # Sprawdź stany emocjonalne
            self.assertTrue(self.defender.emotional_states[EmotionalState.FEAR] > 0)
    
    def test_flee_response(self):
        """Test reakcji ucieczki"""
        # Symuluj atak
        self.defender.health = 30  # Niskie zdrowie
        
        context = {
            "events": [{"type": "attack", "participants": ["defender", "attacker"]}],
            "npcs": {"attacker": self.attacker, "defender": self.defender}
        }
        
        # Wykonaj behavior tree
        tree = create_behavior_tree("prisoner", ["peaceful"])
        tree.execute(self.defender, context)
        
        # Powinien uciekać
        self.assertEqual(self.defender.current_state, NPCState.FLEEING)
    
    def test_injury_memory(self):
        """Test zapamiętywania obrażeń"""
        from mechanics.combat import BodyPart, DamageType, Injury
        
        # Zadaj obrażenia
        injury = Injury(
            severity=0.5,
            injury_type="cut",
            bleeding_rate=0.1
        )
        
        self.defender.take_damage(
            damage=20,
            body_part=BodyPart.TULOW,
            damage_type=DamageType.CIECIE,
            injury=injury
        )
        
        # Sprawdź pamięć o ataku
        attack_memories = self.defender.recall_memories(
            query_type="attacked",
            limit=1
        )
        
        self.assertTrue(len(attack_memories) > 0)
        self.assertIn("attacked", attack_memories[0]["event_type"])


def run_tests():
    """Uruchom wszystkie testy"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Dodaj wszystkie testy
    suite.addTests(loader.loadTestsFromTestCase(TestBehaviorTrees))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorySystem))
    suite.addTests(loader.loadTestsFromTestCase(TestNPCInteractions))
    suite.addTests(loader.loadTestsFromTestCase(TestDailyRoutines))
    suite.addTests(loader.loadTestsFromTestCase(TestEmotionalStates))
    suite.addTests(loader.loadTestsFromTestCase(TestGoalSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestCombatIntegration))
    
    # Uruchom testy
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Podsumowanie
    print("\n" + "="*60)
    print("PODSUMOWANIE TESTÓW SYSTEMU AI NPCów")
    print("="*60)
    print(f"Testy uruchomione: {result.testsRun}")
    print(f"Sukcesy: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Niepowodzenia: {len(result.failures)}")
    print(f"Błędy: {len(result.errors)}")
    
    if result.failures:
        print("\nNiepowodzenia:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split(chr(10))[0]}")
    
    if result.errors:
        print("\nBłędy:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[0]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)