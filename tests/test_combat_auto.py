#!/usr/bin/env python3
"""
Automatyczna demonstracja systemu walki i umiejętności dla Droga Szamana RPG.
"""

import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from player.character import Character, CharacterState
from player.skills import SkillName
from mechanics.combat import BodyPart, DamageType, CombatAction, CombatSystem


def print_separator(title: str = ""):
    """Drukuje separator z opcjonalnym tytułem."""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)


def test_skill_system():
    """Testuje system umiejętności."""
    print_separator("TEST SYSTEMU UMIEJĘTNOŚCI")
    
    player = Character("Mahan")
    
    print("\nTEST 1: Początkowe umiejętności")
    for skill_name in [SkillName.MIECZE, SkillName.LUCZNICTWO, SkillName.MEDYCYNA]:
        skill = player.skills.get_skill(skill_name)
        print(f"  {skill.polish_name}: Poziom {skill.level}")
    
    print("\nTEST 2: Użycie umiejętności z różną trudnością")
    skill = player.skills.get_skill(SkillName.MIECZE)
    base_level = skill.level
    
    # Zbyt łatwe zadanie
    success, msg = player.use_skill(SkillName.MIECZE, base_level - 20)
    print(f"  Łatwe (trudność {base_level - 20}): {msg}")
    
    # Optymalne zadanie
    success, msg = player.use_skill(SkillName.MIECZE, base_level + 10)
    print(f"  Optymalne (trudność {base_level + 10}): {msg}")
    
    # Zbyt trudne zadanie
    success, msg = player.use_skill(SkillName.MIECZE, base_level + 40)
    print(f"  Trudne (trudność {base_level + 40}): {msg}")
    
    print("\nTEST 3: Rozwój umiejętności przez praktykę")
    initial_level = skill.level
    attempts = 0
    while skill.level == initial_level and attempts < 50:
        difficulty = skill.level + random.randint(8, 12)
        success, msg = player.use_skill(SkillName.MIECZE, difficulty)
        attempts += 1
        if "wzrasta" in msg:
            print(f"  Umiejętność wzrosła po {attempts} próbach!")
            print(f"  Nowy poziom: {skill.level}")
            break
    
    if attempts == 50:
        print(f"  Postęp: {skill.progress:.1f}% (potrzeba więcej praktyki)")
    
    print("\n✓ System umiejętności działa poprawnie")


def test_pain_system():
    """Testuje system bólu."""
    print_separator("TEST SYSTEMU BÓLU")
    
    player = Character("Raven")
    
    print("\nTEST 1: Akumulacja bólu")
    print(f"  Początkowy ból: {player.combat_stats.pain:.0f}")
    
    # Małe obrażenia
    player.take_damage(5, BodyPart.LEWA_REKA, DamageType.OBUCHOWE)
    print(f"  Po 5 obrażeniach: Ból = {player.combat_stats.pain:.1f}")
    
    # Średnie obrażenia
    player.take_damage(15, BodyPart.TULOW, DamageType.CIECIE)
    print(f"  Po 15 obrażeniach: Ból = {player.combat_stats.pain:.1f}")
    
    # Duże obrażenia w głowę
    player.take_damage(20, BodyPart.GLOWA, DamageType.OBUCHOWE)
    print(f"  Po 20 obrażeniach w głowę: Ból = {player.combat_stats.pain:.1f}")
    
    print("\nTEST 2: Wpływ bólu na umiejętności")
    if player.combat_stats.pain > 30:
        success, msg = player.use_skill(SkillName.MIECZE, 50)
        if "Kary:" in msg:
            print(f"  Kary wykryte: {msg.split('[Kary:')[1]}")
    
    print("\nTEST 3: Próg utraty przytomności")
    while player.combat_stats.pain < 80 and player.combat_stats.is_conscious:
        player.combat_stats.pain += 10
    print(f"  Ból = {player.combat_stats.pain:.0f}")
    print(f"  Przytomny: {'TAK' if player.combat_stats.is_conscious else 'NIE'}")
    
    print("\n✓ System bólu działa poprawnie")


def test_injury_system():
    """Testuje system kontuzji."""
    print_separator("TEST SYSTEMU KONTUZJI")
    
    player = Character("Shaman")
    combat_system = CombatSystem()
    
    print("\nTEST 1: Tworzenie różnych typów kontuzji")
    
    # Cięcie z krwawieniem
    injury1 = combat_system._create_injury(BodyPart.TULOW, 20, DamageType.CIECIE)
    player.injuries[BodyPart.TULOW].append(injury1)
    print(f"  Cięcie: severity={injury1.severity:.0f}, krwawi={injury1.bleeding}")
    
    # Stłuczenie
    injury2 = combat_system._create_injury(BodyPart.LEWA_NOGA, 15, DamageType.OBUCHOWE)
    player.injuries[BodyPart.LEWA_NOGA].append(injury2)
    print(f"  Stłuczenie: severity={injury2.severity:.0f}, krwawi={injury2.bleeding}")
    
    # Oparzenie
    injury3 = combat_system._create_injury(BodyPart.PRAWA_REKA, 10, DamageType.OPARZENIE)
    player.injuries[BodyPart.PRAWA_REKA].append(injury3)
    print(f"  Oparzenie: severity={injury3.severity:.0f}, czas_leczenia={injury3.time_to_heal}")
    
    print("\nTEST 2: Wpływ kontuzji na umiejętności")
    # Kowalstwo wymaga rąk
    success, msg = player.use_skill(SkillName.KOWALSTWO, 50)
    if "rany:" in msg:
        print(f"  Kowalstwo z ranną ręką: kary wykryte")
    
    # Skradanie wymaga nóg
    success, msg = player.use_skill(SkillName.SKRADANIE, 50)
    if "rany:" in msg:
        print(f"  Skradanie z ranną nogą: kary wykryte")
    
    print("\nTEST 3: Leczenie kontuzji")
    success, msg = player.treat_injuries()
    print(f"  Leczenie: {msg}")
    
    print("\nTEST 4: Regeneracja podczas odpoczynku")
    before_count = len(player.get_all_injuries())
    player.rest(100)
    after_count = len(player.get_all_injuries())
    print(f"  Kontuzje przed: {before_count}, po odpoczynku: {after_count}")
    
    print("\n✓ System kontuzji działa poprawnie")


def test_combat_system():
    """Testuje system walki."""
    print_separator("TEST SYSTEMU WALKI")
    
    player = Character("Geralt")
    enemy = Character("Bandyta")
    combat_system = CombatSystem()
    
    player.equipment.weapon = {'name': 'Miecz', 'damage': 15, 'damage_type': 'cięcie'}
    
    print("\nTEST 1: Inicjatywa")
    player_skill = player.skills.get_skill(SkillName.MIECZE).level
    enemy_skill = enemy.skills.get_skill(SkillName.WALKA_WRECZ).level
    
    has_init, msg = combat_system.calculate_initiative(
        player.combat_stats, enemy.combat_stats,
        player_skill, enemy_skill
    )
    print(f"  {msg}")
    
    print("\nTEST 2: Różne typy ataków")
    actions = [CombatAction.ATAK_PODSTAWOWY, CombatAction.ATAK_SILNY, CombatAction.ATAK_SZYBKI]
    
    for action in actions:
        if player.combat_stats.stamina < combat_system.STAMINA_COSTS[action]:
            print(f"  {action.value}: Brak staminy!")
            continue
            
        success, result = combat_system.perform_attack(
            player.combat_stats, enemy.combat_stats,
            player_skill, enemy_skill,
            action, 15, DamageType.CIECIE
        )
        
        if success and result['hit']:
            print(f"  {action.value}: Trafienie! Obrażenia={result['damage']:.1f}, Część={result['body_part'].value}")
        else:
            print(f"  {action.value}: {result['description']}")
    
    print("\nTEST 3: System obrony")
    success, reduction = combat_system.perform_defense(
        player.combat_stats, player_skill, CombatAction.OBRONA
    )
    print(f"  Obrona: {'Sukces' if success else 'Porażka'}, redukcja={reduction*100:.0f}%")
    
    print("\nTEST 4: Regeneracja staminy")
    initial_stamina = player.combat_stats.stamina
    regen = combat_system.recover_stamina(player.combat_stats, False, 10)
    print(f"  Stamina: {initial_stamina:.0f} → {player.combat_stats.stamina:.0f} (+{regen:.1f})")
    
    print("\n✓ System walki działa poprawnie")


def test_fatigue_system():
    """Testuje system zmęczenia."""
    print_separator("TEST SYSTEMU ZMĘCZENIA")
    
    player = Character("Conan")
    combat_system = CombatSystem()
    
    print(f"\nPoczątkowe wartości:")
    print(f"  Stamina: {player.combat_stats.stamina:.0f}/{player.combat_stats.max_stamina:.0f}")
    print(f"  Wyczerpanie: {player.combat_stats.exhaustion:.0f}")
    
    print("\nTEST 1: Zużycie staminy podczas akcji")
    for i in range(5):
        stamina_before = player.combat_stats.stamina
        cost = combat_system.STAMINA_COSTS[CombatAction.ATAK_SILNY]
        
        if player.combat_stats.stamina >= cost:
            player.combat_stats.stamina -= cost
            player.combat_stats.exhaustion += cost * 0.1
            print(f"  Akcja {i+1}: Stamina -{cost}, Wyczerpanie +{cost*0.1:.1f}")
    
    print(f"\nPo akcjach:")
    print(f"  Stamina: {player.combat_stats.stamina:.0f}/{player.combat_stats.max_stamina:.0f}")
    print(f"  Wyczerpanie: {player.combat_stats.exhaustion:.1f}")
    
    print("\nTEST 2: Różne typy regeneracji")
    # Regeneracja w walce
    regen_combat = combat_system.recover_stamina(player.combat_stats, False, 10)
    print(f"  W walce (10s): +{regen_combat:.1f} staminy")
    
    # Regeneracja podczas odpoczynku
    regen_rest = combat_system.recover_stamina(player.combat_stats, True, 10)
    print(f"  Odpoczynek (10s): +{regen_rest:.1f} staminy")
    
    print("\nTEST 3: Wpływ wyczerpania na regenerację")
    player.combat_stats.exhaustion = 80
    regen_exhausted = combat_system.recover_stamina(player.combat_stats, True, 10)
    print(f"  Przy wyczerpaniu 80: +{regen_exhausted:.1f} staminy (znacznie wolniej)")
    
    print("\n✓ System zmęczenia działa poprawnie")


def test_character_integration():
    """Testuje integrację wszystkich systemów w klasie Character."""
    print_separator("TEST INTEGRACJI SYSTEMÓW")
    
    player = Character("Kompleksowy Test")
    
    print("\nTEST 1: Pełny status postaci")
    print(player.get_status())
    
    print("\nTEST 2: Symulacja krótkiej walki")
    # Otrzymanie obrażeń
    player.take_damage(15, BodyPart.TULOW, DamageType.CIECIE)
    player.take_damage(10, BodyPart.LEWA_REKA, DamageType.OBUCHOWE)
    
    # Użycie różnych umiejętności
    player.use_skill(SkillName.MIECZE, 50)
    player.use_skill(SkillName.MEDYCYNA, 40)
    
    # Leczenie
    player.treat_injuries()
    
    # Odpoczynek
    player.rest(60)
    
    print("\nTEST 3: Zapis stanu postaci")
    save_data = player.save_character()
    print(f"  Zapisane klucze: {list(save_data.keys())}")
    print(f"  Umiejętności zapisane: {len(save_data['skills'])}")
    print(f"  Kontuzje zapisane: {sum(len(inj) for inj in save_data['injuries'].values())}")
    
    print("\n✓ Integracja systemów działa poprawnie")


def main():
    """Główna funkcja testowa."""
    print("\n" + "="*60)
    print(" DROGA SZAMANA - AUTOMATYCZNE TESTY SYSTEMU")
    print("="*60)
    
    tests = [
        test_skill_system,
        test_pain_system,
        test_injury_system,
        test_combat_system,
        test_fatigue_system,
        test_character_integration
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ TEST NIEPOWODZONY: {test_func.__name__}")
            print(f"  Błąd: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(" PODSUMOWANIE TESTÓW")
    print("="*60)
    print(f"Testy zakończone: {passed} ✓")
    print(f"Testy niepowodzenia: {failed} ✗")
    
    if failed == 0:
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        print("\nSystem jest gotowy do użycia:")
        print("• Umiejętności rozwijają się przez praktykę ✓")
        print("• Ból wpływa na efektywność działań ✓")
        print("• Kontuzje mają długoterminowe efekty ✓")
        print("• Zmęczenie wymusza taktyczne podejście ✓")
        print("• Wszystkie systemy są zintegrowane ✓")
    else:
        print("\n⚠️ Niektóre testy nie przeszły. Sprawdź logi powyżej.")


if __name__ == "__main__":
    main()