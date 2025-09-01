#!/usr/bin/env python3
"""
Demonstracja systemu walki i umiejętności dla Droga Szamana RPG.
Pokazuje realistyczną walkę z bólem, kontuzjami i uczeniem przez praktykę.
"""

import random
from player.character import Character, CharacterState
from player.skills import SkillName
from mechanics.combat import BodyPart, DamageType, CombatAction, CombatSystem


def print_separator(title: str = ""):
    """Drukuje separator z opcjonalnym tytułem."""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)


def demonstrate_skill_learning():
    """Demonstruje system uczenia umiejętności przez praktykę."""
    print_separator("DEMONSTRACJA SYSTEMU UMIEJĘTNOŚCI")
    
    player = Character("Mahan")
    
    print("\nPoczątkowe umiejętności:")
    print(player.skills.get_skill_summary())
    
    print("\n\n--- Trening miecza poprzez praktykę ---")
    print("Każde użycie umiejętności daje szansę na rozwój.")
    print("Optymalna trudność to poziom umiejętności + 5-15.\n")
    
    # Symulacja treningu
    sword_skill = player.skills.get_skill(SkillName.MIECZE)
    initial_level = sword_skill.level
    
    for i in range(20):
        # Optymalna trudność
        difficulty = sword_skill.level + random.randint(5, 15)
        success, msg = player.use_skill(SkillName.MIECZE, difficulty)
        
        if "wzrasta" in msg:
            print(f"Próba {i+1}: {msg}")
            print(f"  → Nowy poziom: {sword_skill.level}")
    
    print(f"\nPo 20 próbach: Miecze wzrosły z {initial_level} do {sword_skill.level}")
    print(f"Postęp do następnego poziomu: {sword_skill.progress:.1f}%")
    print(f"Całkowita liczba użyć: {sword_skill.total_uses}")


def demonstrate_pain_system():
    """Demonstruje system bólu i jego wpływ na akcje."""
    print_separator("DEMONSTRACJA SYSTEMU BÓLU")
    
    player = Character("Raven")
    
    print(f"\nPoczątkowy stan: Ból = {player.combat_stats.pain:.0f}")
    
    # Symulacja otrzymywania obrażeń
    injuries = [
        (15, BodyPart.TULOW, DamageType.CIECIE, "Cięcie mieczem w tułów"),
        (8, BodyPart.LEWA_REKA, DamageType.OBUCHOWE, "Uderzenie w lewą rękę"),
        (20, BodyPart.GLOWA, DamageType.OBUCHOWE, "Silne uderzenie w głowę")
    ]
    
    for damage, part, dtype, description in injuries:
        print(f"\n{description} ({damage} obrażeń):")
        effect = player.take_damage(damage, part, dtype)
        print(f"  Efekt: {effect}")
        print(f"  Ból: {player.combat_stats.pain:.1f}/100")
        print(f"  Zdrowie: {player.combat_stats.health:.1f}/{player.combat_stats.max_health:.0f}")
        print(f"  Stan: {player.state.value}")
        
        # Sprawdź kary do umiejętności
        if player.combat_stats.pain > 30:
            print(f"  KARY z powodu bólu:")
            # Próba użycia umiejętności z karami
            success, msg = player.use_skill(SkillName.MIECZE, 50)
            if "Kary:" in msg:
                print(f"    {msg.split('[Kary:')[1][:-1]}")
    
    # Pokazanie utraty przytomności
    if player.combat_stats.pain >= 80:
        print("\n!!! UTRATA PRZYTOMNOŚCI z powodu bólu !!!")


def demonstrate_injury_system():
    """Demonstruje system kontuzji i leczenia."""
    print_separator("DEMONSTRACJA SYSTEMU KONTUZJI")
    
    player = Character("Shaman")
    
    print("\nSymulacja ciężkiej walki...")
    
    # Zadaj różne kontuzje
    combat_system = CombatSystem()
    
    # Głębokie cięcie - krwawienie
    print("\n1. Głębokie cięcie mieczem w tułów:")
    injury1 = combat_system._create_injury(BodyPart.TULOW, 25, DamageType.CIECIE)
    player.injuries[BodyPart.TULOW].append(injury1)
    print(f"   - Severity: {injury1.severity:.0f}")
    print(f"   - Krwawienie: {'TAK' if injury1.bleeding else 'NIE'}")
    if injury1.bleeding:
        print(f"   - Tempo krwawienia: {injury1.bleeding_rate:.1f} HP/turę")
    print(f"   - Czas leczenia: {injury1.time_to_heal} minut gry")
    
    # Złamanie
    print("\n2. Złamanie lewej nogi od upadku:")
    injury2 = combat_system._create_injury(BodyPart.LEWA_NOGA, 30, DamageType.UPADEK)
    player.injuries[BodyPart.LEWA_NOGA].append(injury2)
    print(f"   - Severity: {injury2.severity:.0f}")
    print(f"   - Czas leczenia: {injury2.time_to_heal} minut gry")
    
    # Oparzenie
    print("\n3. Oparzenie prawej ręki:")
    injury3 = combat_system._create_injury(BodyPart.PRAWA_REKA, 15, DamageType.OPARZENIE)
    player.injuries[BodyPart.PRAWA_REKA].append(injury3)
    print(f"   - Severity: {injury3.severity:.0f}")
    print(f"   - Czas leczenia: {injury3.time_to_heal} minut gry (dłużej bo oparzenie)")
    
    # Wpływ kontuzji na umiejętności
    print("\n--- Wpływ kontuzji na różne umiejętności ---")
    
    skills_to_test = [
        (SkillName.MIECZE, "Miecze (wymaga sprawnej prawej ręki)"),
        (SkillName.SKRADANIE, "Skradanie (wymaga sprawnych nóg)"),
        (SkillName.KOWALSTWO, "Kowalstwo (wymaga obu rąk)")
    ]
    
    for skill, description in skills_to_test:
        success, msg = player.use_skill(skill, 50)
        print(f"\n{description}:")
        if "Kary:" in msg and "rany:" in msg:
            penalty_part = msg.split("rany: -")[1].split("%")[0]
            print(f"  Kara z powodu ran: -{penalty_part}%")
    
    # Leczenie
    print("\n\n--- Próba leczenia ran ---")
    success, msg = player.treat_injuries()
    print(f"Leczenie: {msg}")
    
    if success:
        print("\nStan po opatrzeniu:")
        for part, injuries in player.injuries.items():
            for injury in injuries:
                if injury.treated:
                    print(f"  {part.value}: OPATRZONA (przyspieszone leczenie)")
    
    # Odpoczynek i regeneracja
    print("\n\n--- Odpoczynek 120 minut ---")
    success, msg = player.rest(120)
    print(msg)
    
    print("\nStan kontuzji po odpoczynku:")
    remaining_injuries = player.get_all_injuries()
    if remaining_injuries:
        for injury in remaining_injuries:
            print(f"  Pozostały czas leczenia: {injury.time_to_heal} minut")
    else:
        print("  Wszystkie rany wyleczone!")


def demonstrate_combat_flow():
    """Demonstruje pełny przebieg walki."""
    print_separator("DEMONSTRACJA PEŁNEJ WALKI")
    
    player = Character("Geralt")
    enemy = Character("Bandyta")
    
    # Wyposażenie
    player.equipment.weapon = {'name': 'Stalowy miecz', 'damage': 15, 'damage_type': 'cięcie'}
    enemy.equipment.weapon = {'name': 'Maczuga', 'damage': 12, 'damage_type': 'obuchowe'}
    
    print(f"\n{player.name} (Zdrowie: {player.combat_stats.health:.0f}) VS {enemy.name} (Zdrowie: {enemy.combat_stats.health:.0f})")
    
    combat_system = CombatSystem()
    turn = 0
    
    while (player.combat_stats.is_conscious and enemy.combat_stats.is_conscious 
           and turn < 10):
        turn += 1
        print(f"\n--- TURA {turn} ---")
        
        # Stan przed turą
        print(f"{player.name}: HP={player.combat_stats.health:.1f}, "
              f"Stamina={player.combat_stats.stamina:.1f}, "
              f"Ból={player.combat_stats.pain:.1f}")
        print(f"{enemy.name}: HP={enemy.combat_stats.health:.1f}, "
              f"Stamina={enemy.combat_stats.stamina:.1f}, "
              f"Ból={enemy.combat_stats.pain:.1f}")
        
        # Inicjatywa
        player_skill = player.skills.get_skill(SkillName.MIECZE).level
        enemy_skill = enemy.skills.get_skill(SkillName.WALKA_WRECZ).level
        
        has_initiative, init_msg = combat_system.calculate_initiative(
            player.combat_stats, enemy.combat_stats,
            player_skill, enemy_skill
        )
        
        print(f"\nInicjatywa: {init_msg}")
        
        if has_initiative:
            # Gracz atakuje pierwszy
            action = random.choice([CombatAction.ATAK_PODSTAWOWY, 
                                   CombatAction.ATAK_SILNY,
                                   CombatAction.ATAK_SZYBKI])
            
            print(f"\n{player.name} wykonuje {action.value}!")
            
            weapon_damage, damage_type = player.equipment.get_weapon_damage()
            success, result = combat_system.perform_attack(
                player.combat_stats, enemy.combat_stats,
                player_skill, enemy_skill,
                action, weapon_damage, DamageType(damage_type)
            )
            
            if success and result['hit']:
                print(f"  {result['description']}")
                effect = enemy.take_damage(
                    result['damage'], 
                    result['body_part'],
                    DamageType(damage_type),
                    result.get('injury')
                )
                print(f"  {enemy.name}: {effect}")
            else:
                print(f"  {result['description']}")
            
            # Riposta wroga jeśli żyje
            if enemy.combat_stats.is_conscious and enemy.combat_stats.stamina > 10:
                print(f"\n{enemy.name} kontratakuje!")
                weapon_damage, damage_type = enemy.equipment.get_weapon_damage()
                success, result = combat_system.perform_attack(
                    enemy.combat_stats, player.combat_stats,
                    enemy_skill, player_skill,
                    CombatAction.ATAK_PODSTAWOWY, weapon_damage, DamageType(damage_type)
                )
                
                if success and result['hit']:
                    print(f"  {result['description']}")
                    effect = player.take_damage(
                        result['damage'],
                        result['body_part'],
                        DamageType(damage_type),
                        result.get('injury')
                    )
                    print(f"  {player.name}: {effect}")
        
        # Regeneracja staminy
        combat_system.recover_stamina(player.combat_stats, False, 5)
        combat_system.recover_stamina(enemy.combat_stats, False, 5)
        
        # Sprawdź zakończenie walki
        if not enemy.combat_stats.is_conscious:
            print(f"\n*** {enemy.name} POKONANY! ***")
            break
        if not player.combat_stats.is_conscious:
            print(f"\n*** {player.name} POKONANY! ***")
            break
    
    # Podsumowanie walki
    print("\n" + "="*60)
    print("PODSUMOWANIE WALKI:")
    print(f"\n{player.name}:")
    print(f"  Stan: {player.state.value}")
    print(f"  Kontuzje: {len(player.get_all_injuries())}")
    if player.get_all_injuries():
        for part, injuries in player.injuries.items():
            for injury in injuries:
                print(f"    - {part.value}: {injury.damage_type.value} (severity: {injury.severity:.0f})")
    
    print(f"\n{enemy.name}:")
    print(f"  Stan: {enemy.state.value}")
    print(f"  Kontuzje: {len(enemy.get_all_injuries())}")


def demonstrate_fatigue_system():
    """Demonstruje system zmęczenia i wyczerpania."""
    print_separator("DEMONSTRACJA SYSTEMU ZMĘCZENIA")
    
    player = Character("Conan")
    
    print(f"\nPoczątkowa stamina: {player.combat_stats.stamina:.0f}/{player.combat_stats.max_stamina:.0f}")
    print(f"Wyczerpanie: {player.combat_stats.exhaustion:.0f}")
    
    print("\n--- Intensywna seria ataków ---")
    
    for i in range(10):
        # Wykonaj ciężki atak
        stamina_before = player.combat_stats.stamina
        exhaustion_before = player.combat_stats.exhaustion
        
        # Symulacja ataku
        stamina_cost = CombatSystem.STAMINA_COSTS[CombatAction.ATAK_SILNY]
        player.combat_stats.stamina -= stamina_cost
        player.combat_stats.exhaustion += stamina_cost * 0.1
        
        print(f"\nAtak {i+1} (Silny atak - koszt {stamina_cost} staminy):")
        print(f"  Stamina: {stamina_before:.0f} → {player.combat_stats.stamina:.0f}")
        print(f"  Wyczerpanie: {exhaustion_before:.1f} → {player.combat_stats.exhaustion:.1f}")
        
        if player.combat_stats.stamina < stamina_cost:
            print("  !!! ZBYT ZMĘCZONY aby kontynuować walkę !!!")
            break
        
        if player.combat_stats.exhaustion > 70:
            print("  !!! SKRAJNE WYCZERPANIE - znaczne kary do wszystkich akcji !!!")
    
    # Pokazanie regeneracji
    print("\n\n--- Regeneracja podczas walki (5 sekund) ---")
    combat_system = CombatSystem()
    regen = combat_system.recover_stamina(player.combat_stats, False, 5)
    print(f"Odzyskano {regen:.1f} staminy (wolna regeneracja podczas walki)")
    print(f"Stamina: {player.combat_stats.stamina:.1f}/{player.combat_stats.max_stamina:.0f}")
    
    print("\n--- Odpoczynek (60 sekund) ---")
    regen = combat_system.recover_stamina(player.combat_stats, True, 60)
    print(f"Odzyskano {regen:.1f} staminy")
    print(f"Stamina: {player.combat_stats.stamina:.1f}/{player.combat_stats.max_stamina:.0f}")
    print(f"Wyczerpanie: {player.combat_stats.exhaustion:.1f} (powoli spada podczas odpoczynku)")


def main():
    """Główna funkcja demonstracyjna."""
    print("\n" + "="*60)
    print(" DROGA SZAMANA - DEMONSTRACJA SYSTEMU WALKI I UMIEJĘTNOŚCI")
    print("="*60)
    print("\nSystem oparty na realizmie:")
    print("• Umiejętności rosną TYLKO przez praktykę")
    print("• Ból wpływa na wszystkie akcje")
    print("• Kontuzje mają długoterminowe konsekwencje")
    print("• Zmęczenie wymusza taktyczne podejście")
    print("• Śmierć jest realna i ma konsekwencje")
    
    demos = [
        ("System umiejętności", demonstrate_skill_learning),
        ("System bólu", demonstrate_pain_system),
        ("System kontuzji", demonstrate_injury_system),
        ("System zmęczenia", demonstrate_fatigue_system),
        ("Pełna walka", demonstrate_combat_flow)
    ]
    
    while True:
        print("\n" + "="*60)
        print("Wybierz demonstrację:")
        for i, (name, _) in enumerate(demos, 1):
            print(f"{i}. {name}")
        print("0. Wyjście")
        
        try:
            choice = input("\nTwój wybór: ")
            if choice == "0":
                break
            
            idx = int(choice) - 1
            if 0 <= idx < len(demos):
                demos[idx][1]()
                input("\nNaciśnij Enter aby kontynuować...")
            else:
                print("Nieprawidłowy wybór!")
        except (ValueError, KeyboardInterrupt):
            break
    
    print("\nDziękujemy za przetestowanie systemu Droga Szamana!")


if __name__ == "__main__":
    main()