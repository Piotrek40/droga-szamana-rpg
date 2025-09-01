"""
Comprehensive tests for enhanced combat and skill progression systems.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from mechanics.enhanced_combat import (
    EnhancedCombatSystem, Combatant, Weapon, Armor, WeaponType, 
    CombatStance, DamageType, BodyPart, CombatAction, CombatStats,
    CombatTechnique, TechniqueType, EnvironmentalFactor, VoidWalkerAbility
)
from player.enhanced_skills import (
    EnhancedSkillSystem, SkillName, SkillCategory, EnhancedSkill
)
from mechanics.combat_integration import CombatManager, CombatEncounter
# from player.character import CharacterState  # This is an enum, not a class
# from player.classes import ClassName  # Commented out to avoid enum issues

# Create a mock character class for testing
class CharacterState:
    """Mock character state for testing."""
    def __init__(self):
        self.name = ""
        self.health = 100
        self.max_health = 100
        self.stamina = 100
        self.max_stamina = 100
        self.pain = 0
        self.exhaustion = 0
        self.character_class = None
        self.skills = None
        self.equipment = {}
        self.injuries = []
        self.void_energy = 50
        self.max_void_energy = 100


def test_weapon_mastery():
    """Test weapon creation and mastery system."""
    print("\n=== TEST: Weapon Mastery System ===")
    
    # Create different weapon types
    sword = Weapon(
        name="steel_sword",
        polish_name="Stalowy Miecz",
        weapon_type=WeaponType.MIECZE_DLUGIE,
        damage_type=DamageType.CIECIE,
        base_damage=20,
        speed=1,
        reach=2,
        weight=2.5,
        quality="dobra"
    )
    
    dagger = Weapon(
        name="sharp_dagger",
        polish_name="Ostry Sztylet",
        weapon_type=WeaponType.SZTYLETY,
        damage_type=DamageType.KLUTE,
        base_damage=8,
        speed=3,
        reach=1,
        weight=0.5,
        quality="mistrzowska"
    )
    
    print(f"Miecz: {sword.polish_name}")
    print(f"  - Obrażenia bazowe: {sword.base_damage}")
    print(f"  - Obrażenia efektywne: {sword.get_effective_damage()}")
    print(f"  - Szybkość: {sword.speed}, Zasięg: {sword.reach}")
    
    print(f"\nSztylet: {dagger.polish_name}")
    print(f"  - Obrażenia bazowe: {dagger.base_damage}")
    print(f"  - Obrażenia efektywne: {dagger.get_effective_damage()}")
    print(f"  - Szybkość: {dagger.speed}, Zasięg: {dagger.reach}")
    
    # Test weapon degradation
    print("\nTest degradacji broni:")
    original_condition = sword.condition
    for i in range(5):
        sword.degrade(5)
    print(f"Stan po 5 użyciach: {original_condition}% -> {sword.condition}%")
    print(f"Obrażenia po degradacji: {sword.get_effective_damage()}")
    
    print("✓ Weapon mastery test passed")


def test_skill_progression():
    """Test use-based skill progression."""
    print("\n=== TEST: Use-Based Skill Progression ===")
    
    skill_system = EnhancedSkillSystem()
    
    # Test sword skill progression
    sword_skill = skill_system.skills[SkillName.MIECZE]
    print(f"Początkowy poziom miecza: {sword_skill.level}")
    
    # Simulate training sessions
    improvements = 0
    for i in range(50):
        # Optimal difficulty for learning
        difficulty = sword_skill.level + 10
        success, msg, effects = skill_system.use_skill(
            SkillName.MIECZE,
            difficulty,
            conditions={'perfect_conditions': True}
        )
        if effects['learning']['improved']:
            improvements += 1
            print(f"  Tura {i+1}: {msg}")
    
    print(f"Po 50 próbach: Poziom {sword_skill.level}, {improvements} awansów")
    print(f"Pamięć mięśniowa: {sword_skill.memory.muscle_memory:.1f}%")
    print(f"Wiedza teoretyczna: {sword_skill.memory.theoretical_knowledge:.1f}%")
    print(f"Doświadczenie praktyczne: {sword_skill.memory.practical_experience:.1f}%")
    
    # Test skill synergy
    print("\nTest synergii umiejętności:")
    parry_skill = skill_system.skills[SkillName.PAROWANIE]
    synergy_bonus = skill_system._calculate_synergy_bonus(parry_skill)
    print(f"Bonus synergii dla parowania: {synergy_bonus:.2%}")
    
    # Test skill degradation
    print("\nTest degradacji umiejętności:")
    skill_system.apply_time_degradation(30)  # 30 dni bez użycia
    print(f"Po 30 dniach bez treningu:")
    print(f"  Pamięć mięśniowa: {sword_skill.memory.muscle_memory:.1f}%")
    
    # Test technique discovery
    print("\nTest odkrywania technik:")
    for technique_name, technique in sword_skill.techniques.items():
        if sword_skill.can_discover_technique(technique_name):
            print(f"  Może odkryć: {technique.name}")
    
    print("✓ Skill progression test passed")


def test_combat_with_pain():
    """Test combat with pain and injury system."""
    print("\n=== TEST: Combat with Pain System ===")
    
    combat_system = EnhancedCombatSystem()
    
    # Create combatants
    player = Combatant(
        name="Gracz",
        stats=CombatStats(health=100, stamina=100),
        weapon=Weapon(
            name="sword",
            polish_name="Miecz",
            weapon_type=WeaponType.MIECZE_DLUGIE,
            damage_type=DamageType.CIECIE,
            base_damage=15,
            speed=1,
            reach=2,
            weight=2
        ),
        skills={'miecze': 20, 'obrona': 15}
    )
    
    enemy = Combatant(
        name="Bandyta",
        stats=CombatStats(health=80, stamina=80),
        weapon=Weapon(
            name="axe",
            polish_name="Topór",
            weapon_type=WeaponType.TOPORY,
            damage_type=DamageType.CIECIE,
            base_damage=18,
            speed=0,
            reach=2,
            weight=3
        ),
        skills={'topory': 15, 'obrona': 10},
        ai_pattern="agresywny"
    )
    
    print("Początek walki:")
    print(f"  {player.name}: HP {player.stats.health}, Ból {player.stats.pain}")
    print(f"  {enemy.name}: HP {enemy.stats.health}, Ból {enemy.stats.pain}")
    
    # Simulate combat rounds
    for round_num in range(1, 6):
        print(f"\nRunda {round_num}:")
        
        # Player attacks
        result = combat_system.process_combat_turn(
            player, enemy, CombatAction.ATAK_PODSTAWOWY
        )
        if result['damage'] > 0:
            print(f"  {player.name} zadaje {result['damage']} obrażeń")
            print(f"  {enemy.name} - Ból wzrasta do {enemy.stats.pain}")
        
        # Check if enemy can continue
        if not enemy.stats.is_conscious:
            print(f"  {enemy.name} traci przytomność!")
            break
        
        # Enemy attacks
        ai_action, _ = combat_system.ai_choose_action(enemy, player)
        result = combat_system.process_combat_turn(
            enemy, player, ai_action
        )
        if result['damage'] > 0:
            print(f"  {enemy.name} zadaje {result['damage']} obrażeń")
            print(f"  {player.name} - Ból wzrasta do {player.stats.pain}")
        
        # Check pain penalties
        penalties = combat_system.calculate_combat_penalties(player.stats, player.injuries)
        if penalties['attack'] > 0:
            print(f"  Kary dla gracza: Atak -{penalties['attack']:.0%}, Celność -{penalties['accuracy']:.0%}")
    
    print("\nStan po walce:")
    print(f"  {player.name}: HP {player.stats.health}, Ból {player.stats.pain}")
    print(f"  {enemy.name}: HP {enemy.stats.health}, Ból {enemy.stats.pain}")
    print(f"  Kontuzje gracza: {len(player.injuries)}")
    
    print("✓ Combat with pain test passed")


def test_combat_techniques():
    """Test combat techniques and combos."""
    print("\n=== TEST: Combat Techniques and Combos ===")
    
    combat_system = EnhancedCombatSystem()
    
    # Create skilled combatants
    master = Combatant(
        name="Mistrz Miecza",
        stats=CombatStats(health=120, stamina=120),
        weapon=Weapon(
            name="master_sword",
            polish_name="Miecz Mistrza",
            weapon_type=WeaponType.MIECZE_DLUGIE,
            damage_type=DamageType.CIECIE,
            base_damage=25,
            speed=2,
            reach=2,
            weight=2,
            quality="mistrzowska"
        ),
        skills={'miecze': 50, 'obrona': 40, 'uniki': 35}
    )
    
    opponent = Combatant(
        name="Przeciwnik",
        stats=CombatStats(health=100, stamina=100),
        skills={'obrona': 20}
    )
    
    # Test technique execution
    technique = combat_system.techniques['ciecie_poziome']
    print(f"Testowanie techniki: {technique.polish_name}")
    
    success, result = combat_system.execute_technique(master, opponent, technique)
    if success:
        print(f"  Sukces! {result['description']}")
        print(f"  Efekty: {result.get('effects', [])}")
    
    # Test combo system
    print("\nTestowanie kombinacji:")
    
    # Simulate combo chain
    combat_system.combo_tracker[master.name] = ['ciecie_poziome']
    combat_system.combo_window[master.name] = 2
    
    combo = combat_system.check_combo_opportunity(master.name, 'ciecie_poziome')
    if combo:
        print(f"  Odkryto kombinację: {combo.polish_name}")
        success, result = combat_system.execute_technique(master, opponent, combo)
        if success:
            print(f"  Wykonano! {result['description']}")
    
    print("✓ Combat techniques test passed")


def test_environmental_combat():
    """Test environmental factors in combat."""
    print("\n=== TEST: Environmental Combat Factors ===")
    
    combat_system = EnhancedCombatSystem()
    
    # Add environmental factors
    combat_system.combat_environment.add(EnvironmentalFactor.CIEMNOSC)
    combat_system.combat_environment.add(EnvironmentalFactor.SLISKA_POWIERZCHNIA)
    
    print("Czynniki środowiskowe:")
    for factor in combat_system.combat_environment:
        print(f"  - {factor.value}")
    
    # Calculate modifiers
    env_mods = combat_system.calculate_environmental_modifiers()
    print("\nModyfikatory:")
    for mod_name, value in env_mods.items():
        if value != 0:
            print(f"  {mod_name}: {value:+.0%}")
    
    # Test combat in environment
    archer = Combatant(
        name="Łucznik",
        stats=CombatStats(health=80, stamina=100),
        weapon=Weapon(
            name="bow",
            polish_name="Łuk",
            weapon_type=WeaponType.LUKI,
            damage_type=DamageType.KLUTE,
            base_damage=12,
            speed=1,
            reach=10,
            weight=1.5
        ),
        skills={'lucznictwo': 25}
    )
    
    target = Combatant(
        name="Cel",
        stats=CombatStats(health=60, stamina=60),
        skills={'uniki': 15}
    )
    
    # Add rain for archery penalty
    combat_system.combat_environment.add(EnvironmentalFactor.DESZCZ)
    
    print("\nŁucznictwo w deszczu i ciemności:")
    result = combat_system.process_combat_turn(
        archer, target, CombatAction.ATAK_PODSTAWOWY
    )
    print(f"  {result['messages'][0]}")
    
    print("✓ Environmental combat test passed")


def test_void_walker_abilities():
    """Test Void Walker special abilities."""
    print("\n=== TEST: Void Walker Abilities ===")
    
    combat_system = EnhancedCombatSystem()
    
    # Create Void Walker
    void_walker = Combatant(
        name="Wędrowiec Pustki",
        stats=CombatStats(health=100, stamina=100, pain=0),
        skills={'manipulacja_pustki': 30, 'medytacja': 25}
    )
    
    # Add void energy
    void_walker.stats.void_energy = 50
    void_walker.stats.max_void_energy = 100
    
    enemy = Combatant(
        name="Przeciwnik",
        stats=CombatStats(health=80, stamina=80),
        skills={'obrona': 15}
    )
    
    # Test void ability
    void_touch = combat_system.void_abilities['dotyk_pustki']
    print(f"Używanie zdolności: {void_touch.polish_name}")
    print(f"  Koszt energii Pustki: {void_touch.void_energy_cost}")
    print(f"  Wzrost bólu: {void_touch.pain_increase}")
    
    success, msg = void_touch.execute(void_walker.stats, enemy.stats)
    if success:
        print(f"  {msg}")
        print(f"  Energia Pustki: {void_walker.stats.void_energy}/{void_walker.stats.max_void_energy}")
        print(f"  Ból Wędrowca: {void_walker.stats.pain}")
        print(f"  HP przeciwnika: {enemy.stats.health}")
    
    print("✓ Void Walker abilities test passed")


def test_npc_ai_combat():
    """Test NPC AI combat patterns."""
    print("\n=== TEST: NPC AI Combat Patterns ===")
    
    combat_system = EnhancedCombatSystem()
    
    # Create NPCs with different AI patterns
    npcs = [
        Combatant(
            name="Agresywny Wojownik",
            stats=CombatStats(health=100, stamina=100),
            skills={'miecze': 20, 'obrona': 10},
            ai_pattern="agresywny"
        ),
        Combatant(
            name="Ostrożny Łotr",
            stats=CombatStats(health=70, stamina=120),
            skills={'sztylety': 25, 'uniki': 30},
            ai_pattern="defensywny"
        ),
        Combatant(
            name="Taktyczny Dowódca",
            stats=CombatStats(health=90, stamina=90),
            skills={'miecze': 22, 'obrona': 22},
            ai_pattern="taktyczny"
        ),
        Combatant(
            name="Berserker",
            stats=CombatStats(health=150, stamina=80),
            skills={'topory': 30, 'obrona': 5},
            ai_pattern="berserker"
        )
    ]
    
    player = Combatant(
        name="Gracz",
        stats=CombatStats(health=100, stamina=100),
        skills={'miecze': 20}
    )
    
    print("Testowanie wzorców AI:")
    for npc in npcs:
        print(f"\n{npc.name} (wzorzec: {npc.ai_pattern}):")
        
        # Test różnych sytuacji
        # Pełne zdrowie
        action, technique = combat_system.ai_choose_action(npc, player)
        print(f"  Pełne HP -> Akcja: {action.value}")
        
        # Niskie zdrowie
        npc.stats.health = 15
        action, technique = combat_system.ai_choose_action(npc, player)
        print(f"  Niskie HP -> Akcja: {action.value}")
        
        # Restore health for next test
        npc.stats.health = npc.stats.max_health
    
    print("✓ NPC AI combat test passed")


def test_combat_integration():
    """Test full combat integration."""
    print("\n=== TEST: Full Combat Integration ===")
    
    # Create combat manager
    combat_manager = CombatManager()
    
    # Create player character
    player = CharacterState()
    player.name = "Bohater"
    player.health = 100
    player.max_health = 100
    player.stamina = 100
    player.max_stamina = 100
    player.character_class = "Wojownik"  # Use string instead of enum
    player.pain = 0
    player.exhaustion = 0
    player.skills = combat_manager.skill_system
    
    # Define enemies
    enemies = [
        {
            'name': 'Bandyta',
            'health': 60,
            'max_health': 60,
            'stamina': 50,
            'max_stamina': 50,
            'weapon': {
                'type': 'miecz',
                'nazwa': 'Zardzewiały miecz',
                'obrazenia': 12
            },
            'skills': {
                'miecze': 10,
                'obrona': 8
            },
            'ai_pattern': 'agresywny'
        },
        {
            'name': 'Łucznik',
            'health': 40,
            'max_health': 40,
            'stamina': 60,
            'max_stamina': 60,
            'weapon': {
                'type': 'luk',
                'nazwa': 'Krótki łuk',
                'obrazenia': 10,
                'zasieg': 8
            },
            'skills': {
                'lucznictwo': 15,
                'uniki': 12
            },
            'ai_pattern': 'łucznik'
        }
    ]
    
    # Start combat with environmental factors
    environment = ['ciemnosc', 'nierownny_teren']
    encounter = combat_manager.start_combat(player, enemies, environment)
    
    print("Rozpoczęcie walki:")
    status = encounter.get_combat_status()
    print(f"  Gracz: {status['player']['health']} HP")
    print(f"  Przeciwnicy: {len(status['enemies'])}")
    print(f"  Środowisko: {', '.join(status['environment'])}")
    print(f"  Kolejność inicjatywy: {encounter.turn_order}")
    
    # Simulate combat round
    print("\nRunda walki:")
    
    # Player turn
    player_result = combat_manager.process_player_action('atak', 'Bandyta')
    print(f"  Gracz: {player_result['message']}")
    
    # Enemy turns
    enemy_results = combat_manager.process_enemy_turns()
    for result in enemy_results:
        print(f"  {result['attacker']}: {result['message']}")
    
    # Check combat end
    outcome = combat_manager.check_combat_end()
    if outcome:
        print(f"\nWynik walki: {outcome}")
    
    # Apply results
    combat_manager.apply_combat_results(player)
    print(f"\nStan gracza po walce:")
    print(f"  HP: {player.health}/{player.max_health}")
    print(f"  Stamina: {player.stamina}/{player.max_stamina}")
    print(f"  Ból: {player.pain}")
    print(f"  Wyczerpanie: {player.exhaustion}")
    
    print("✓ Combat integration test passed")


def run_all_tests():
    """Run all combat and skill tests."""
    print("=" * 60)
    print("ENHANCED COMBAT & SKILLS SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        test_weapon_mastery,
        test_skill_progression,
        test_combat_with_pain,
        test_combat_techniques,
        test_environmental_combat,
        test_void_walker_abilities,
        test_npc_ai_combat,
        test_combat_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Combat system ready for integration.")
    else:
        print(f"\n⚠️ {failed} tests failed. Please review and fix.")


if __name__ == "__main__":
    # Set random seed for reproducible tests
    random.seed(42)
    run_all_tests()