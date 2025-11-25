"""
Klasa gracza dla Droga Szamana RPG.
Integruje wszystkie systemy: umiejętności, walkę, kontuzje, ekwipunek.
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from player.skills import SkillSystem, SkillName
from player.classes import CharacterClass, ClassName, ClassManager
from mechanics.combat import CombatStats, Injury, BodyPart, DamageType, CombatAction, CombatSystem


class CharacterState(Enum):
    """Stan postaci."""
    NORMALNY = "normalny"
    ZMECZONY = "zmęczony"
    WYCZERPANY = "wyczerpany"
    RANNY = "ranny"
    CIEZKO_RANNY = "ciężko_ranny"
    NIEPRZYTOMNY = "nieprzytomny"
    UMIERAJACY = "umierający"
    MARTWY = "martwy"


@dataclass
class Equipment:
    """Ekwipunek postaci."""
    weapon: Optional[Dict[str, Any]] = None
    armor: Dict[str, Optional[Dict[str, Any]]] = field(default_factory=lambda: {
        'glowa': None,
        'tulow': None,
        'rece': None,
        'nogi': None
    })
    items: List[Dict[str, Any]] = field(default_factory=list)  # Lista wszystkich przedmiotów w inventory
    equipped: Dict[str, Any] = field(default_factory=dict)  # Założone przedmioty (oprócz broni i pancerza)
    gold: int = 0
    
    def has_item(self, item_name: str) -> bool:
        """Sprawdź czy jest przedmiot w ekwipunku."""
        for item in self.items:
            if item.get('name', '').lower() == item_name.lower():
                return True
        return False
    
    def get_weapon_damage(self) -> Tuple[int, DamageType]:
        """
        Zwraca obrażenia broni.
        
        Returns:
            (obrażenia, typ)
        """
        if not self.weapon:
            return 5, DamageType.OBUCHOWE  # Pięści
        
        return self.weapon.get('damage', 10), DamageType(self.weapon.get('damage_type', 'obuchowe'))
    
    def get_armor_protection(self, body_part: BodyPart) -> float:
        """
        Zwraca ochronę pancerza dla części ciała.
        
        Args:
            body_part: Część ciała
        
        Returns:
            Redukcja obrażeń (0.0 - 0.8)
        """
        part_mapping = {
            BodyPart.GLOWA: 'glowa',
            BodyPart.TULOW: 'tulow',
            BodyPart.LEWA_REKA: 'rece',
            BodyPart.PRAWA_REKA: 'rece',
            BodyPart.LEWA_NOGA: 'nogi',
            BodyPart.PRAWA_NOGA: 'nogi'
        }
        
        armor_slot = part_mapping.get(body_part, 'tulow')
        armor = self.armor.get(armor_slot)
        
        if not armor:
            return 0.0
        
        base_protection = armor.get('protection', 0.0)
        condition = armor.get('condition', 100) / 100.0
        
        return min(0.8, base_protection * condition)
    
    def damage_armor(self, body_part: BodyPart, damage: float):
        """
        Uszkadza pancerz w danej lokacji.
        
        Args:
            body_part: Część ciała
            damage: Obrażenia
        """
        part_mapping = {
            BodyPart.GLOWA: 'glowa',
            BodyPart.TULOW: 'tulow',
            BodyPart.LEWA_REKA: 'rece',
            BodyPart.PRAWA_REKA: 'rece',
            BodyPart.LEWA_NOGA: 'nogi',
            BodyPart.PRAWA_NOGA: 'nogi'
        }
        
        armor_slot = part_mapping.get(body_part, 'tulow')
        armor = self.armor.get(armor_slot)
        
        if armor:
            condition_loss = min(5, damage / 10.0)
            armor['condition'] = max(0, armor.get('condition', 100) - condition_loss)
            
            if armor['condition'] <= 0:
                armor['broken'] = True


class Character:
    """Klasa reprezentująca postać gracza."""
    
    def __init__(self, name: str = "Bezimienny", character_class: Optional[ClassName] = None):
        """
        Inicjalizacja postaci.
        
        Args:
            name: Imię postaci
            character_class: Klasa postaci
        """
        self.name = name
        self.level = 1  # Poziom postaci (nie wpływa na umiejętności!)
        
        # System klas
        self.character_class: Optional[CharacterClass] = None
        self.class_name: Optional[ClassName] = character_class
        if character_class:
            class_manager = ClassManager()
            self.character_class = class_manager.get_class(character_class)
        
        # Podstawowe atrybuty (modyfikowane przez klasę)
        base_strength = random.randint(8, 15)
        base_agility = random.randint(8, 15)
        base_endurance = random.randint(8, 15)
        base_intelligence = random.randint(8, 15)
        base_willpower = random.randint(8, 15)
        
        if self.character_class:
            self.strength = max(1, base_strength + self.character_class.attribute_modifiers['strength'])
            self.agility = max(1, base_agility + self.character_class.attribute_modifiers['agility'])
            self.endurance = max(1, base_endurance + self.character_class.attribute_modifiers['endurance'])
            self.intelligence = max(1, base_intelligence + self.character_class.attribute_modifiers['intelligence'])
            self.willpower = max(1, base_willpower + self.character_class.attribute_modifiers['willpower'])
        else:
            self.strength = base_strength
            self.agility = base_agility
            self.endurance = base_endurance
            self.intelligence = base_intelligence
            self.willpower = base_willpower
        
        # Mana dla magów
        if character_class == ClassName.MAG:
            self.mana = 50 + self.intelligence * 5
            self.max_mana = self.mana
        
        # Cooldowny zdolności
        self.ability_cooldowns: Dict[str, int] = {}
        
        # Buffy i debuffy
        self.active_buffs: Dict[str, Dict] = {}
        self.active_debuffs: Dict[str, Dict] = {}
        
        # Systemy
        self.skills = SkillSystem()
        self.combat_stats = self._initialize_combat_stats()
        self.injuries: Dict[BodyPart, List[Injury]] = {part: [] for part in BodyPart}
        self.equipment = Equipment(gold=random.randint(10, 50))
        
        # Stan
        self.state = CharacterState.NORMALNY
        self.location = "Karczma"
        self.time_played = 0  # Minuty gry
        
        # Historia
        self.combat_history: List[str] = []
        self.death_count = 0
        self.scars: List[str] = []

        # Crafting
        self._known_recipes: set = set()  # Zbiór znanych receptur (wewnętrzny)
    
    def _initialize_combat_stats(self) -> CombatStats:
        """
        Inicjalizuje statystyki bojowe na podstawie atrybutów.
        
        Returns:
            Statystyki bojowe
        """
        max_health = 50 + self.endurance * 5
        max_stamina = 50 + self.endurance * 3 + self.strength * 2
        
        stats = CombatStats(
            health=max_health,
            max_health=max_health,
            stamina=max_stamina,
            max_stamina=max_stamina,
            pain=0.0,
            exhaustion=0.0,
            attack_speed=1.0 + (self.agility - 10) * 0.05,
            damage_multiplier=1.0 + (self.strength - 10) * 0.05,
            defense_multiplier=0.1 + (self.agility - 10) * 0.02
        )
        
        return stats
    
    @property
    def health(self) -> float:
        """Zwraca aktualne zdrowie."""
        return self.combat_stats.health
    
    @health.setter
    def health(self, value: float):
        """Ustawia zdrowie."""
        self.combat_stats.health = max(0, value)
    
    @property
    def max_health(self) -> float:
        """Zwraca maksymalne zdrowie."""
        return self.combat_stats.max_health
    
    @property
    def stamina(self) -> float:
        """Zwraca aktualną staminę."""
        return self.combat_stats.stamina
    
    @stamina.setter
    def stamina(self, value: float):
        """Ustawia staminę."""
        self.combat_stats.stamina = max(0, value)
    
    @property
    def max_stamina(self) -> float:
        """Zwraca maksymalną staminę."""
        return self.combat_stats.max_stamina
    
    @property
    def pain(self) -> float:
        """Zwraca poziom bólu."""
        return self.combat_stats.pain
    
    @pain.setter
    def pain(self, value: float):
        """Ustawia poziom bólu."""
        self.combat_stats.pain = max(0, min(100, value))
    
    def update_buffs_and_cooldowns(self):
        """Aktualizuje buffy, debuffy i cooldowny (wywoływane co turę)."""
        # Aktualizuj cooldowny zdolności
        for ability_name in list(self.ability_cooldowns.keys()):
            self.ability_cooldowns[ability_name] -= 1
            if self.ability_cooldowns[ability_name] <= 0:
                del self.ability_cooldowns[ability_name]
        
        # Aktualizuj buffy
        from player.ability_effects import BuffType
        for buff_type in list(self.active_buffs.keys()):
            buff = self.active_buffs[buff_type]
            if buff['duration'] > 0:  # -1 oznacza buff permanentny
                buff['duration'] -= 1
                if buff['duration'] <= 0:
                    # Usuń buff i przywróć oryginalne wartości jeśli trzeba
                    if buff_type == BuffType.BERSERK:
                        self.combat_stats.damage_multiplier /= buff['damage_multiplier']
                        self.combat_stats.defense_multiplier /= buff['defense_multiplier']
                    elif buff_type == BuffType.PAIN_IMMUNITY:
                        self.pain = buff.get('old_pain', 0)
                        if hasattr(self, 'combat_stats'):
                            self.combat_stats.pain = buff.get('old_pain', 0)
                    
                    del self.active_buffs[buff_type]
        
        # Aktualizuj debuffy
        for debuff_name in list(self.active_debuffs.keys()):
            debuff = self.active_debuffs[debuff_name]
            if debuff['duration'] > 0:
                debuff['duration'] -= 1
                
                # Aplikuj efekty debuffu (np. podpalenie)
                if debuff_name == 'burning' and 'damage_per_turn' in debuff:
                    self.health -= debuff['damage_per_turn']
                
                if debuff['duration'] <= 0:
                    del self.active_debuffs[debuff_name]
    
    def update_state(self):
        """Aktualizuje stan postaci na podstawie statystyk."""
        if not self.combat_stats.is_conscious:
            self.state = CharacterState.NIEPRZYTOMNY
        elif self.combat_stats.health <= 0:
            self.state = CharacterState.MARTWY
        elif self.combat_stats.health < self.combat_stats.max_health * 0.2:
            self.state = CharacterState.UMIERAJACY
        elif self.combat_stats.health < self.combat_stats.max_health * 0.5:
            self.state = CharacterState.CIEZKO_RANNY
        elif self.get_total_injury_severity() > 50:
            self.state = CharacterState.RANNY
        elif self.combat_stats.exhaustion > 70:
            self.state = CharacterState.WYCZERPANY
        elif self.combat_stats.stamina < self.combat_stats.max_stamina * 0.3:
            self.state = CharacterState.ZMECZONY
        else:
            self.state = CharacterState.NORMALNY
    
    def perform_action(self, action: str, target: Optional[Any] = None, 
                      context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Wykonuje akcję.
        
        Args:
            action: Nazwa akcji
            target: Cel akcji
            context: Dodatkowy kontekst
        
        Returns:
            (sukces, opis)
        """
        # Sprawdź stan świadomości
        if not self.combat_stats.is_conscious:
            return False, "Jesteś nieprzytomny!"
        
        # Sprawdź oszołomienie
        if self.combat_stats.is_stunned:
            self.combat_stats.stun_duration -= 1
            if self.combat_stats.stun_duration <= 0:
                self.combat_stats.is_stunned = False
            return False, "Jesteś oszołomiony!"
        
        # Akcje bojowe
        if action.startswith("atak_"):
            return self._perform_combat_action(action, target, context)
        
        # Użycie umiejętności
        if action in [skill.value for skill in SkillName]:
            skill_name = SkillName(action)
            difficulty = context.get('difficulty', 50) if context else 50
            return self.use_skill(skill_name, difficulty)
        
        # Odpoczynek
        if action == "odpoczynek":
            return self.rest(context.get('duration', 60) if context else 60)
        
        # Leczenie
        if action == "leczenie":
            return self.treat_injuries()
        
        return False, f"Nieznana akcja: {action}"
    
    def _perform_combat_action(self, action: str, target: Any, 
                              context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Wykonuje akcję bojową.
        
        Args:
            action: Typ akcji bojowej
            target: Cel ataku
            context: Kontekst walki
        
        Returns:
            (sukces, opis)
        """
        combat_system = CombatSystem()
        
        # Mapuj akcję
        action_mapping = {
            'atak_podstawowy': CombatAction.ATAK_PODSTAWOWY,
            'atak_silny': CombatAction.ATAK_SILNY,
            'atak_szybki': CombatAction.ATAK_SZYBKI,
            'obrona': CombatAction.OBRONA,
            'unik': CombatAction.UNIK,
            'parowanie': CombatAction.PAROWANIE
        }
        
        combat_action = action_mapping.get(action, CombatAction.ATAK_PODSTAWOWY)
        
        # Pobierz umiejętność walki
        weapon_skill = SkillName.MIECZE if self.equipment.weapon else SkillName.WALKA_WRECZ
        skill_level = self.skills.get_skill(weapon_skill).level
        
        # Pobierz obrażenia broni
        weapon_damage, damage_type = self.equipment.get_weapon_damage()
        
        # Wykonaj atak
        if combat_action in [CombatAction.ATAK_PODSTAWOWY, CombatAction.ATAK_SILNY, 
                             CombatAction.ATAK_SZYBKI]:
            
            # Oblicz kary
            injury_dict = self.get_injuries_by_part()
            pain_level = self.combat_stats.pain
            
            # Użyj umiejętności z karami
            skill_success, skill_msg = self.skills.use_skill(
                weapon_skill, 
                target.combat_stats.defense_multiplier * 100 if hasattr(target, 'combat_stats') else 50,
                pain_level,
                injury_dict
            )
            
            # Wykonaj atak
            success, result = combat_system.perform_attack(
                self.combat_stats,
                target.combat_stats if hasattr(target, 'combat_stats') else CombatStats(),
                skill_level,
                target.skills.get_skill(SkillName.WALKA_WRECZ).level if hasattr(target, 'skills') else 10,
                combat_action,
                weapon_damage,
                damage_type
            )
            
            if success:
                # Atak był wykonany pomyślnie
                if result['hit']:
                    # Trafienie!
                    if hasattr(target, 'take_damage'):
                        target.take_damage(result['damage'], result['body_part'], 
                                          damage_type, result.get('injury'))
                    
                    return True, f"{result['description']} {skill_msg}"
                else:
                    # Chybienie
                    return True, f"{result['description']} {skill_msg}"
            else:
                # Nie udało się wykonać ataku (brak staminy, oszołomienie itp.)
                return False, f"{result['description']} {skill_msg}"
        
        # Akcje obronne
        else:
            success, reduction = combat_system.perform_defense(
                self.combat_stats,
                skill_level,
                combat_action
            )
            
            if success:
                self.combat_stats.defense_multiplier = reduction
                return True, f"Przyjąłeś postawę obronną (redukcja: {int(reduction*100)}%)"
            else:
                return False, "Nie udało się przyjąć postawy obronnej"
    
    def use_ability(self, ability_name: str, target=None) -> Tuple[bool, str]:
        """
        Używa zdolności klasowej.
        
        Args:
            ability_name: Nazwa zdolności
            target: Opcjonalny cel
        
        Returns:
            (sukces, opis)
        """
        if not self.character_class:
            return False, "Nie masz klasy postaci!"
        
        # Sprawdź czy postać może użyć zdolności
        can_use, msg = self.character_class.can_use_ability(ability_name, self)
        if not can_use:
            return False, msg
        
        # Importuj system efektów
        from player.ability_effects import execute_ability
        
        # Wykonaj zdolność
        success, effect_msg, data = execute_ability(ability_name, self, target)
        
        if success:
            # Ustaw cooldown
            ability = self.character_class.abilities.get(ability_name)
            if ability and ability.cooldown > 0:
                self.ability_cooldowns[ability_name] = ability.cooldown
            
            # Zwiększ mistrzostwo klasy
            self.character_class.mastery_level = min(100, 
                self.character_class.mastery_level + 0.5)
        
        return success, effect_msg
    
    def use_skill(self, skill_name: SkillName, difficulty: int) -> Tuple[bool, str]:
        """
        Używa umiejętności.
        
        Args:
            skill_name: Nazwa umiejętności
            difficulty: Trudność zadania
        
        Returns:
            (sukces, opis)
        """
        # Pobierz kontuzje
        injury_dict = self.get_injuries_by_part()
        
        # Użyj umiejętności
        success, msg = self.skills.use_skill(
            skill_name,
            difficulty,
            self.combat_stats.pain,
            injury_dict
        )
        
        # Zużyj staminę w zależności od umiejętności
        stamina_costs = {
            SkillName.WALKA_WRECZ: 5,
            SkillName.MIECZE: 6,
            SkillName.LUCZNICTWO: 4,
            SkillName.SKRADANIE: 3,
            SkillName.PERSWAZJA: 2,
            SkillName.HANDEL: 1,
            SkillName.KOWALSTWO: 8,
            SkillName.ALCHEMIA: 4,
            SkillName.MEDYCYNA: 3,
            SkillName.WYTRZYMALOSC: 10
        }
        
        stamina_cost = stamina_costs.get(skill_name, 5)
        self.combat_stats.stamina = max(0, self.combat_stats.stamina - stamina_cost)
        self.combat_stats.exhaustion += stamina_cost * 0.1
        
        return success, msg
    
    def take_damage(self, damage: float, body_part: Optional[BodyPart] = None, 
                   damage_type: Optional[DamageType] = None, injury: Optional[Injury] = None) -> str:
        """
        Przyjmuje obrażenia.
        
        Args:
            damage: Ilość obrażeń
            body_part: Trafiona część ciała
            damage_type: Typ obrażeń
            injury: Kontuzja do dodania
        
        Returns:
            Opis efektu
        """
        # Domyślne wartości jeśli nie podano
        if body_part is None:
            body_part = BodyPart.TULOW
        if damage_type is None:
            damage_type = DamageType.IMPACT
        
        # Redukcja przez pancerz
        armor_protection = self.equipment.get_armor_protection(body_part)
        final_damage = damage * (1.0 - armor_protection)
        
        # Uszkodzenie pancerza
        if armor_protection > 0:
            self.equipment.damage_armor(body_part, damage)
        
        # Aplikuj obrażenia
        combat_system = CombatSystem()
        effect = combat_system.apply_damage(
            self.combat_stats,
            final_damage,
            body_part,
            damage_type,
            injury
        )
        
        # Dodaj kontuzję
        if injury:
            self.injuries[body_part].append(injury)
            
            # Sprawdź czy to pozostawi bliznę
            if injury.severity > 70:
                scar_desc = f"Blizna na {body_part.value} od {damage_type.value}"
                if scar_desc not in self.scars:
                    self.scars.append(scar_desc)
        
        # Aktualizuj stan
        self.update_state()
        
        # Sprawdź śmierć
        if self.state == CharacterState.MARTWY:
            self.death_count += 1
            return f"{effect} ŚMIERĆ! (Zgon nr {self.death_count})"
        
        return effect
    
    def heal(self, amount: float) -> str:
        """
        Leczy postać o podaną ilość punktów zdrowia.
        
        Args:
            amount: Ilość punktów zdrowia do wyleczenia
        
        Returns:
            Opis efektu leczenia
        """
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        actual_healed = self.health - old_health
        
        # Redukcja bólu przy leczeniu
        if actual_healed > 0:
            self.pain = max(0, self.pain - actual_healed * 0.5)
        
        if actual_healed > 0:
            return f"Wyleczono {actual_healed:.0f} punktów zdrowia."
        else:
            return "Jesteś już w pełni zdrowy."
    
    def rest(self, duration: int) -> Tuple[bool, str]:
        """
        Odpoczywa przez określony czas.
        
        Args:
            duration: Czas odpoczynku w minutach gry
        
        Returns:
            (zawsze True, opis efektów)
        """
        # Regeneracja staminy
        combat_system = CombatSystem()
        stamina_recovered = combat_system.recover_stamina(
            self.combat_stats,
            is_resting=True,
            time_passed=duration * 60
        )
        
        # Redukcja bólu
        pain_reduction = duration * 0.5
        pain_reduced = combat_system.reduce_pain(
            self.combat_stats,
            pain_reduction,
            is_medical=False
        )
        
        # Leczenie kontuzji
        healed_injuries = []
        for body_part, injuries in self.injuries.items():
            for injury in injuries[:]:  # Kopia listy
                blood_loss, healed = injury.update(duration)
                
                if blood_loss > 0:
                    self.combat_stats.health -= blood_loss
                
                if healed:
                    injuries.remove(injury)
                    healed_injuries.append(f"{body_part.value}")
        
        # Regeneracja zdrowia (bardzo wolna)
        if self.combat_stats.health < self.combat_stats.max_health:
            health_regen = duration * 0.1
            self.combat_stats.health = min(
                self.combat_stats.max_health,
                self.combat_stats.health + health_regen
            )
        
        # Aktualizuj stan
        self.update_state()
        
        # Przygotuj raport
        effects = []
        if stamina_recovered > 0:
            effects.append(f"stamina +{stamina_recovered:.1f}")
        if pain_reduced > 0:
            effects.append(f"ból -{pain_reduced:.1f}")
        if healed_injuries:
            effects.append(f"wyleczone: {', '.join(healed_injuries)}")
        
        self.time_played += duration
        
        return True, f"Odpoczywałeś {duration} minut. Efekty: {', '.join(effects) if effects else 'brak'}"
    
    def treat_injuries(self) -> Tuple[bool, str]:
        """
        Leczy kontuzje używając umiejętności medycyny.
        
        Returns:
            (sukces, opis)
        """
        # Użyj umiejętności medycyny
        medicine_skill = self.skills.get_skill(SkillName.MEDYCYNA)
        
        if not self.get_all_injuries():
            return False, "Nie masz żadnych ran do opatrzenia"
        
        # Znajdź najpoważniejszą ranę
        most_severe = None
        most_severe_part = None
        
        for body_part, injuries in self.injuries.items():
            for injury in injuries:
                if not injury.treated:
                    if not most_severe or injury.severity > most_severe.severity:
                        most_severe = injury
                        most_severe_part = body_part
        
        if not most_severe:
            return False, "Wszystkie rany są już opatrzone"
        
        # Sprawdź sukces leczenia
        difficulty = int(most_severe.severity)
        success, msg = self.skills.use_skill(SkillName.MEDYCYNA, difficulty, 
                                            self.combat_stats.pain,
                                            self.get_injuries_by_part())
        
        if success:
            most_severe.treated = True
            most_severe.bleeding = False
            most_severe.bleeding_rate = 0
            most_severe.time_to_heal = int(most_severe.time_to_heal * 0.7)
            
            # Redukcja bólu
            combat_system = CombatSystem()
            pain_reduced = combat_system.reduce_pain(
                self.combat_stats,
                most_severe.severity * 0.3,
                is_medical=True
            )
            
            return True, f"Opatrzyłeś ranę {most_severe_part.value} (severity: {most_severe.severity:.0f}). {msg}"
        else:
            return False, f"Nie udało się opatrzyć rany. {msg}"
    
    def get_injuries_by_part(self) -> Dict[str, float]:
        """
        Zwraca słownik kontuzji według części ciała.
        
        Returns:
            {część_ciała: suma severity}
        """
        injury_dict = {}
        
        for body_part, injuries in self.injuries.items():
            if injuries:
                total_severity = sum(inj.severity for inj in injuries)
                # Mapuj enum na string używany w systemie umiejętności
                part_name = body_part.value.replace('ł', 'l').replace('ę', 'e').replace(' ', '_')
                injury_dict[part_name] = total_severity
        
        return injury_dict
    
    def get_all_injuries(self) -> List[Injury]:
        """
        Zwraca listę wszystkich kontuzji.
        
        Returns:
            Lista kontuzji
        """
        all_injuries = []
        for injuries in self.injuries.values():
            all_injuries.extend(injuries)
        return all_injuries
    
    def get_total_injury_severity(self) -> float:
        """
        Zwraca sumaryczną dotkliwość wszystkich kontuzji.
        
        Returns:
            Suma severity
        """
        return sum(inj.severity for inj in self.get_all_injuries())

    def get_pain_penalty(self) -> float:
        """
        Zwraca karę od bólu zgodnie z systemem z README.

        Returns:
            Kara jako wartość 0.0-1.0 (np. 0.15 = -15%)

        Pain thresholds:
            30-50: -15% do testów
            50-70: -30% do testów
            70-80: -45% do testów
            80+: utrata przytomności
        """
        pain = self.pain

        if pain >= 80:
            return 1.0  # Utrata przytomności = 100% kara
        elif pain >= 70:
            return 0.45  # -45%
        elif pain >= 50:
            return 0.30  # -30%
        elif pain >= 30:
            return 0.15  # -15%
        else:
            return 0.0  # Brak kary

    def get_status(self) -> str:
        """
        Zwraca pełny status postaci.
        
        Returns:
            Sformatowany status
        """
        lines = [
            f"=== {self.name.upper()} ===",
            f"Stan: {self.state.value}",
            f"Lokacja: {self.location}",
            "",
            "--- STATYSTYKI ---",
            f"Zdrowie: {self.combat_stats.health:.1f}/{self.combat_stats.max_health:.0f}",
            f"Stamina: {self.combat_stats.stamina:.1f}/{self.combat_stats.max_stamina:.0f}",
            f"Ból: {self.combat_stats.pain:.1f}/100",
            f"Wyczerpanie: {self.combat_stats.exhaustion:.1f}/100",
            ""
        ]
        
        # Atrybuty
        lines.extend([
            "--- ATRYBUTY ---",
            f"Siła: {self.strength}  Zręczność: {self.agility}",
            f"Wytrzymałość: {self.endurance}  Inteligencja: {self.intelligence}",
            f"Siła woli: {self.willpower}",
            ""
        ])
        
        # Kontuzje
        if self.get_all_injuries():
            lines.append("--- KONTUZJE ---")
            for body_part, injuries in self.injuries.items():
                if injuries:
                    for injury in injuries:
                        status = []
                        if injury.bleeding:
                            status.append("krwawi")
                        if injury.infected:
                            status.append("zainfekowana")
                        if injury.treated:
                            status.append("opatrzona")
                        
                        lines.append(
                            f"{body_part.value}: {injury.damage_type.value} "
                            f"(severity: {injury.severity:.0f}) "
                            f"[{', '.join(status) if status else 'nieleczona'}]"
                        )
            lines.append("")
        
        # Blizny
        if self.scars:
            lines.append("--- BLIZNY ---")
            for scar in self.scars:
                lines.append(f"• {scar}")
            lines.append("")
        
        # Ekwipunek
        lines.append("--- EKWIPUNEK ---")
        if self.equipment.weapon:
            lines.append(f"Broń: {self.equipment.weapon.get('name', 'Nieznana')}")
        else:
            lines.append("Broń: Pięści")
        
        armor_worn = []
        for slot, armor in self.equipment.armor.items():
            if armor:
                armor_worn.append(f"{slot}: {armor.get('name', 'Nieznany')} ({armor.get('condition', 100)}%)")
        
        if armor_worn:
            lines.extend(armor_worn)
        else:
            lines.append("Pancerz: Brak")
        
        lines.append(f"Złoto: {self.equipment.gold}")
        lines.append("")
        
        # Umiejętności (skrócone)
        lines.append("--- TOP UMIEJĘTNOŚCI ---")
        sorted_skills = sorted(
            self.skills.skills.items(),
            key=lambda x: x[1].level,
            reverse=True
        )[:5]
        
        for skill_enum, skill in sorted_skills:
            lines.append(f"{skill.polish_name}: {skill.level}")
        
        return "\n".join(lines)
    
    def save_character(self) -> Dict[str, Any]:
        """
        Zapisuje stan postaci do słownika.
        
        Returns:
            Słownik z danymi postaci
        """
        return {
            'name': self.name,
            'level': self.level,
            'attributes': {
                'strength': self.strength,
                'agility': self.agility,
                'endurance': self.endurance,
                'intelligence': self.intelligence,
                'willpower': self.willpower
            },
            'combat_stats': {
                'health': self.combat_stats.health,
                'stamina': self.combat_stats.stamina,
                'pain': self.combat_stats.pain,
                'exhaustion': self.combat_stats.exhaustion
            },
            'skills': {
                skill.value: {
                    'level': self.skills.skills[skill].level,
                    'progress': self.skills.skills[skill].progress,
                    'total_uses': self.skills.skills[skill].total_uses
                }
                for skill in SkillName
                if skill in self.skills.skills  # Tylko zapisuj istniejące skille
            },
            'injuries': {
                part.value: [
                    {
                        'severity': inj.severity,
                        'damage_type': inj.damage_type.value,
                        'bleeding': inj.bleeding,
                        'infected': inj.infected,
                        'treated': inj.treated,
                        'time_to_heal': inj.time_to_heal
                    }
                    for inj in injuries
                ]
                for part, injuries in self.injuries.items()
            },
            'equipment': {
                'weapon': self.equipment.weapon,
                'armor': self.equipment.armor,
                'gold': self.equipment.gold
            },
            'state': self.state.value,
            'location': self.location,
            'time_played': self.time_played,
            'death_count': self.death_count,
            'scars': self.scars,
            'known_recipes': list(self.known_recipes)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Alias for save_character for compatibility."""
        return self.save_character()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """
        Wczytuje postać ze słownika.
        
        Args:
            data: Dane postaci
            
        Returns:
            Instancja postaci
        """
        character = cls(data['name'])
        
        # Poziom
        character.level = data.get('level', 1)
        
        # Atrybuty
        attrs = data.get('attributes', {})
        character.strength = attrs.get('strength', character.strength)
        character.agility = attrs.get('agility', character.agility)
        character.endurance = attrs.get('endurance', character.endurance)
        character.intelligence = attrs.get('intelligence', character.intelligence)
        character.willpower = attrs.get('willpower', character.willpower)
        
        # Statystyki bojowe
        combat_stats = data.get('combat_stats', {})
        character.combat_stats.health = combat_stats.get('health', character.combat_stats.health)
        character.combat_stats.stamina = combat_stats.get('stamina', character.combat_stats.stamina)
        character.combat_stats.pain = combat_stats.get('pain', 0)
        character.combat_stats.exhaustion = combat_stats.get('exhaustion', 0)
        
        # Umiejętności
        skills_data = data.get('skills', {})
        for skill_name, skill_info in skills_data.items():
            try:
                skill_enum = SkillName(skill_name)
                skill = character.skills.get_skill(skill_enum)
                skill.level = skill_info.get('level', skill.level)
                skill.progress = skill_info.get('progress', skill.progress)
                skill.total_uses = skill_info.get('total_uses', skill.total_uses)
            except ValueError:
                continue
        
        # Kontuzje
        injuries_data = data.get('injuries', {})
        for body_part_name, injury_list in injuries_data.items():
            try:
                from mechanics.combat import BodyPart, DamageType, Injury
                body_part = BodyPart(body_part_name)
                character.injuries[body_part] = []
                
                for injury_data in injury_list:
                    injury = Injury(
                        severity=injury_data['severity'],
                        damage_type=DamageType(injury_data['damage_type']),
                        bleeding=injury_data.get('bleeding', False),
                        time_to_heal=injury_data.get('time_to_heal', 1440)
                    )
                    injury.infected = injury_data.get('infected', False)
                    injury.treated = injury_data.get('treated', False)
                    character.injuries[body_part].append(injury)
            except (ValueError, KeyError):
                continue
        
        # Ekwipunek
        equipment_data = data.get('equipment', {})
        character.equipment.weapon = equipment_data.get('weapon')
        character.equipment.armor = equipment_data.get('armor', character.equipment.armor)
        character.equipment.gold = equipment_data.get('gold', 0)
        
        # Stan
        character.state = CharacterState(data.get('state', 'normalny'))
        character.location = data.get('location', 'Karczma')
        character.time_played = data.get('time_played', 0)
        character.death_count = data.get('death_count', 0)
        character.scars = data.get('scars', [])
        character.known_recipes = set(data.get('known_recipes', []))

        return character
    
    # ===== BRAKUJĄCE METODY INVENTORY I INTERAKCJI =====
    
    @property
    def inventory(self) -> List[Dict[str, Any]]:
        """Zwraca inventory gracza."""
        return self.equipment.items
    
    @property
    def gold(self) -> int:
        """Zwraca ilość złota."""
        return self.equipment.gold
    
    @gold.setter
    def gold(self, value: int):
        """Ustawia ilość złota."""
        self.equipment.gold = max(0, value)
    
    @property
    def current_location(self) -> str:
        """Zwraca aktualną lokację."""
        return self.location
    
    @current_location.setter
    def current_location(self, value: str):
        """Ustawia aktualną lokację."""
        self.location = value
    
    @property
    def hunger(self) -> float:
        """Zwraca poziom głodu (0-100)."""
        return getattr(self, '_hunger', 0.0)
    
    @hunger.setter 
    def hunger(self, value: float):
        """Ustawia poziom głodu."""
        self._hunger = max(0, min(100, value))
    
    @property
    def defending(self) -> bool:
        """Sprawdza czy gracz jest w postawie obronnej."""
        return getattr(self, '_defending', False)
    
    @defending.setter
    def defending(self, value: bool):
        """Ustawia postawę obronną."""
        self._defending = bool(value)
    
    @property
    def known_recipes(self) -> set:
        """Zwraca znane przepisy."""
        return getattr(self, '_known_recipes', set())

    @known_recipes.setter
    def known_recipes(self, value):
        """Ustawia znane przepisy."""
        if isinstance(value, (list, set)):
            self._known_recipes = set(value)
        else:
            self._known_recipes = set()
    
    def add_item(self, item: Dict[str, Any], amount: int = 1) -> bool:
        """
        Dodaje przedmiot do inventory.
        
        Args:
            item: Przedmiot do dodania
            amount: Ilość
        
        Returns:
            True jeśli udało się dodać
        """
        if not isinstance(item, dict) or 'name' not in item:
            return False
        
        # Sprawdź czy przedmiot już istnieje
        for inv_item in self.inventory:
            if inv_item.get('name') == item['name']:
                inv_item['quantity'] = inv_item.get('quantity', 1) + amount
                return True
        
        # Dodaj nowy przedmiot
        new_item = item.copy()
        new_item['quantity'] = amount
        self.inventory.append(new_item)
        return True
    
    def get_item(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Znajdź przedmiot w inventory.
        
        Args:
            item_name: Nazwa przedmiotu
        
        Returns:
            Przedmiot lub None
        """
        for item in self.inventory:
            if item.get('name', '').lower() == item_name.lower():
                return item
        return None
    
    def remove_item(self, item_name: str, amount: int = 1) -> bool:
        """
        Usuwa przedmiot z inventory.
        
        Args:
            item_name: Nazwa przedmiotu
            amount: Ilość do usunięcia
        
        Returns:
            True jeśli udało się usunąć
        """
        for item in self.inventory[:]:  # Kopia listy
            if item.get('name', '').lower() == item_name.lower():
                current_qty = item.get('quantity', 1)
                if current_qty <= amount:
                    self.inventory.remove(item)
                else:
                    item['quantity'] = current_qty - amount
                return True
        return False
    
    def show_inventory(self) -> str:
        """
        Zwraca opis inventory.
        
        Returns:
            Sformatowany opis inventory
        """
        if not self.inventory:
            return "Twój plecak jest pusty."
        
        lines = ["=== PLECAK ==="]
        for item in self.inventory:
            name = item.get('name', 'Nieznany')
            qty = item.get('quantity', 1)
            weight = item.get('weight', 0)
            
            line = f"• {name}"
            if qty > 1:
                line += f" x{qty}"
            if weight > 0:
                line += f" ({weight}kg)"
            lines.append(line)
        
        lines.append(f"\nZłoto: {self.gold}")
        return "\n".join(lines)
    
    def show_skills(self) -> str:
        """
        Zwraca opis umiejętności.
        
        Returns:
            Sformatowany opis umiejętności
        """
        lines = ["=== UMIEJĘTNOŚCI ==="]
        
        # Posortuj umiejętności według poziomu
        sorted_skills = sorted(
            self.skills.skills.items(),
            key=lambda x: x[1].level,
            reverse=True
        )
        
        for skill_enum, skill in sorted_skills:
            progress_percent = skill.progress
            lines.append(
                f"{skill.polish_name}: {skill.level} "
                f"({progress_percent:.0f}% do następnego, użyte {skill.total_uses}x)"
            )
        
        return "\n".join(lines)
    
    def get_skill(self, skill_name: str) -> Optional[Any]:
        """
        Znajdź umiejętność po nazwie.
        
        Args:
            skill_name: Nazwa umiejętności (polska lub angielska)
        
        Returns:
            Skill object lub None
        """
        # Sprawdź po nazwie angielskiej
        for skill_enum in self.skills.skills:
            if skill_enum.value.lower() == skill_name.lower():
                return self.skills.get_skill(skill_enum)
        
        # Sprawdź po nazwie polskiej
        for skill_enum, skill in self.skills.skills.items():
            if skill.polish_name.lower() == skill_name.lower():
                return skill
        
        return None
    
    def equip_item(self, item_name: str) -> Tuple[bool, str]:
        """
        Zakłada przedmiot.
        
        Args:
            item_name: Nazwa przedmiotu
        
        Returns:
            (sukces, wiadomość)
        """
        item = self.get_item(item_name)
        if not item:
            return False, f"Nie masz przedmiotu: {item_name}"
        
        item_type = item.get('type', 'misc')
        
        if item_type == 'weapon':
            # Zdejmij poprzednią broń
            if self.equipment.weapon:
                old_weapon = self.equipment.weapon.copy()
                self.add_item(old_weapon)
            
            self.equipment.weapon = item.copy()
            self.remove_item(item_name, 1)
            return True, f"Zakładasz: {item_name}"
            
        elif item_type == 'armor':
            slot = item.get('slot', 'tulow')
            
            # Zdejmij poprzedni pancerz z tego slotu
            if self.equipment.armor.get(slot):
                old_armor = self.equipment.armor[slot].copy()
                self.add_item(old_armor)
            
            self.equipment.armor[slot] = item.copy()
            self.remove_item(item_name, 1)
            return True, f"Zakładasz: {item_name}"
        
        else:
            return False, f"Nie można założyć: {item_name}"
    
    def unequip_item(self, slot_or_item: str) -> Tuple[bool, str]:
        """
        Zdejmuje przedmiot.
        
        Args:
            slot_or_item: Slot pancerza lub 'weapon'
        
        Returns:
            (sukces, wiadomość)
        """
        if slot_or_item == 'weapon':
            if not self.equipment.weapon:
                return False, "Nie masz założonej broni"
            
            weapon = self.equipment.weapon.copy()
            self.add_item(weapon)
            self.equipment.weapon = None
            return True, f"Zdejmujesz: {weapon['name']}"
        
        elif slot_or_item in self.equipment.armor:
            armor = self.equipment.armor.get(slot_or_item)
            if not armor:
                return False, f"Nie masz pancerza na: {slot_or_item}"
            
            self.add_item(armor.copy())
            self.equipment.armor[slot_or_item] = None
            return True, f"Zdejmujesz: {armor['name']}"
        
        else:
            return False, f"Nieznany slot: {slot_or_item}"
    
    def drop_item(self, item_name: str, amount: int = 1) -> Tuple[bool, str]:
        """
        Wyrzuca przedmiot.
        
        Args:
            item_name: Nazwa przedmiotu
            amount: Ilość
        
        Returns:
            (sukces, wiadomość)
        """
        if self.remove_item(item_name, amount):
            return True, f"Wyrzucasz: {item_name} x{amount}"
        else:
            return False, f"Nie masz przedmiotu: {item_name}"
    
    def use_item(self, item_name: str, target: Optional[Any] = None) -> Tuple[bool, str]:
        """
        Używa przedmiotu.
        
        Args:
            item_name: Nazwa przedmiotu
            target: Cel użycia
        
        Returns:
            (sukces, wiadomość)
        """
        item = self.get_item(item_name)
        if not item:
            return False, f"Nie masz przedmiotu: {item_name}"
        
        item_type = item.get('type', 'misc')
        
        if item_type == 'consumable':
            # Użyj consumable
            effect = item.get('effect', {})
            
            if 'heal' in effect:
                heal_amount = effect['heal']
                self.health = min(self.max_health, self.health + heal_amount)
                self.remove_item(item_name, 1)
                return True, f"Używasz {item_name} i odzyskujesz {heal_amount} zdrowia"
            
            elif 'stamina' in effect:
                stamina_amount = effect['stamina']
                self.stamina = min(self.max_stamina, self.stamina + stamina_amount)
                self.remove_item(item_name, 1)
                return True, f"Używasz {item_name} i odzyskujesz {stamina_amount} staminy"
            
            else:
                return False, f"Nie wiesz jak użyć: {item_name}"
        
        else:
            return False, f"Nie możesz użyć: {item_name}"
    
    def attack(self, target: Any) -> Tuple[bool, str]:
        """
        Atakuje cel.
        
        Args:
            target: Cel ataku
        
        Returns:
            (sukces, wiadomość)
        """
        return self.perform_action("atak_podstawowy", target)
    
    def is_incapacitated(self) -> bool:
        """
        Sprawdza czy postać jest niezdolna do działania.
        
        Returns:
            True jeśli postać nie może działać
        """
        return (self.combat_stats.health <= 0 or 
                self.combat_stats.pain > 90 or 
                not self.combat_stats.is_conscious or
                self.state in [CharacterState.NIEPRZYTOMNY, 
                              CharacterState.UMIERAJACY, 
                              CharacterState.MARTWY])
    
    def spend_stamina(self, amount: float):
        """
        Zużywa staminę.
        
        Args:
            amount: Ilość staminy do zużycia
        """
        self.stamina = max(0, self.stamina - amount)
        
        # Aktualizuj stan jeśli stamina jest bardzo niska
        if self.stamina < 10:
            self.combat_stats.exhaustion = min(100, self.combat_stats.exhaustion + amount)
    
    def regenerate(self, minutes: int = 1):
        """
        Regeneracja zdrowia, staminy i many.
        
        Args:
            minutes: Czas regeneracji w minutach
        """
        # Regeneracja staminy (szybsza)
        stamina_regen = minutes * (0.5 + self.endurance * 0.1)
        self.stamina = min(self.max_stamina, self.stamina + stamina_regen)
        
        # Regeneracja many (dla magów)
        if hasattr(self, 'mana') and hasattr(self, 'max_mana'):
            mana_regen_rate = 2.0  # Bazowa regeneracja
            
            # Bonus z klasy maga
            if self.character_class and hasattr(self.character_class, 'special_mechanics'):
                mana_regen_rate = self.character_class.special_mechanics.get('mana_regen', 2.0)
            
            # Bonus z medytacji
            if 'meditating' in self.active_buffs:
                mana_regen_rate += self.max_mana * self.active_buffs['meditating']['mana_regen']
            
            self.mana = min(self.max_mana, self.mana + mana_regen_rate * minutes)
        
        # Regeneracja zdrowia (wolniejsza, tylko gdy odpoczywamy)
        if self.state == CharacterState.NORMALNY and self.combat_stats.pain < 30:
            health_regen = minutes * 0.1 * (1 + self.endurance * 0.05)
            self.health = min(self.max_health, self.health + health_regen)
        
        # Redukcja bólu
        if self.combat_stats.pain > 0:
            pain_reduction = minutes * 0.2
            self.pain = max(0, self.pain - pain_reduction)
        
        # Redukcja wyczerpania
        if self.combat_stats.exhaustion > 0:
            exhaustion_reduction = minutes * 0.3
            self.combat_stats.exhaustion = max(0, self.combat_stats.exhaustion - exhaustion_reduction)
    
    def respawn(self):
        """
        Odradza postać po śmierci.
        
        Przywraca podstawowe statystyki i przenosi do punktu respawnu.
        """
        # Przywróć podstawowe HP/stamina
        self.health = self.max_health * 0.5  # 50% zdrowia
        self.stamina = self.max_stamina * 0.3  # 30% staminy
        self.pain = 0
        self.combat_stats.exhaustion = 50  # Zmęczenie po śmierci
        
        # Wyczyść kontuzje
        self.injuries = {part: [] for part in BodyPart}
        
        # Resetuj stan
        self.state = CharacterState.NORMALNY
        self.combat_stats.is_conscious = True
        self.combat_stats.is_stunned = False
        self.combat_stats.stun_duration = 0
        
        # Przenieś do celi startowej
        self.location = "cela_1"
        
        # Dodaj bliznę
        self.scars.append(f"Blizna po śmierci #{self.death_count + 1}")
        self.death_count += 1
        
        # Utrata części ekwipunku (opcjonalne)
        if self.equipment.gold > 0:
            lost_gold = int(self.equipment.gold * 0.5)
            self.equipment.gold -= lost_gold
            
        return f"Odradzasz się w celi. Straciłeś {lost_gold if 'lost_gold' in locals() else 0} złota."
    
    def has_item(self, item_name: str) -> bool:
        """Sprawdź czy gracz ma przedmiot."""
        return self.equipment.has_item(item_name)
    
    def get_skill_level(self, skill_name: str) -> int:
        """Pobierz poziom umiejętności."""
        return self.skills.get_skill_level(skill_name)
    
    def get_reputation(self, faction: str) -> int:
        """Pobierz reputację z frakcją."""
        if not hasattr(self, 'reputation'):
            self.reputation = {}
        return self.reputation.get(faction, 0)
    
    def add_knowledge(self, knowledge: str):
        """Dodaj wiedzę do gracza."""
        if not hasattr(self, 'knowledge'):
            self.knowledge = set()
        self.knowledge.add(knowledge)
    
    def change_reputation(self, faction: str, change: int):
        """Zmień reputację z frakcją."""
        if not hasattr(self, 'reputation'):
            self.reputation = {}
        self.reputation[faction] = self.reputation.get(faction, 0) + change
    
    def check_class_progression(self, action: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Sprawdza progresję klasy po wykonanej akcji.
        
        Args:
            action: Wykonana akcja
            context: Kontekst akcji
        
        Returns:
            Opis awansu lub None
        """
        if not self.character_class:
            return None
        
        messages = []
        
        # Sprawdź postęp w filozofii klasy
        if hasattr(self.character_class, 'philosophy'):
            philosophy = self.character_class.philosophy
            
            # Wojownik - chroni słabszych
            if self.character_class.name == "Wojownik":
                if action == "defend_weak" and context:
                    philosophy.training_progress += 5
                    if philosophy.training_progress >= 100:
                        messages.append("Osiągnąłeś nowy poziom zrozumienia Drogi Wojownika!")
                        self._unlock_new_ability("Tarcza Honoru")
            
            # Łotrzyk - wykorzystuje cienie
            elif self.character_class.name == "Łotrzyk":
                if action in ["stealth", "backstab", "pickpocket"]:
                    philosophy.training_progress += 3
                    if philosophy.training_progress >= 100:
                        messages.append("Cienie stają się twoim domem!")
                        self._unlock_new_ability("Taniec Cieni")
            
            # Łowca - harmonia z naturą
            elif self.character_class.name == "Łowca":
                if action in ["track", "hunt", "tame"]:
                    philosophy.training_progress += 4
                    if philosophy.training_progress >= 100:
                        messages.append("Natura przyjmuje cię jako swojego!")
                        self._unlock_new_ability("Więź z Bestią")
            
            # Rzemieślnik - doskonałość w tworzeniu
            elif self.character_class.name == "Rzemieślnik":
                if action == "craft" and context:
                    quality = context.get('quality', 0)
                    if quality >= 80:
                        philosophy.training_progress += 5
                    if philosophy.training_progress >= 100:
                        messages.append("Twoje ręce tworzą arcydzieła!")
                        self._unlock_new_ability("Mistrzowski Wyrób")
            
            # Mag - zrozumienie energii
            elif self.character_class.name == "Mag":
                if action == "meditate" or action.startswith("cast_"):
                    philosophy.training_progress += 2
                    if philosophy.training_progress >= 100:
                        messages.append("Energia świata odpowiada na twoje wezwanie!")
                        self._unlock_new_ability("Przebudzenie Mocy")
        
        # Zwiększ poziom klasy po osiągnięciu kamieni milowych
        if hasattr(self.character_class, 'level'):
            experience_gained = self._calculate_class_experience(action, context)
            self.character_class.experience += experience_gained
            
            # Sprawdź awans
            if self.character_class.experience >= self.character_class.level * 100:
                self.character_class.level += 1
                self.character_class.experience = 0
                messages.append(f"Twoja klasa {self.character_class.name} osiągnęła poziom {self.character_class.level}!")
                
                # Bonusy za poziom
                self._apply_level_bonuses()
        
        return '\n'.join(messages) if messages else None
    
    def _unlock_new_ability(self, ability_name: str):
        """
        Odblokowuje nową zdolność klasową.
        
        Args:
            ability_name: Nazwa zdolności do odblokowania
        """
        if not self.character_class:
            return
        
        # Tu można dodać logikę odblokowywania nowych zdolności
        # Na razie tylko logujemy
        print(f"[PROGRESJA] Odblokowano nową zdolność: {ability_name}")
    
    def _calculate_class_experience(self, action: str, context: Dict[str, Any]) -> int:
        """
        Oblicza doświadczenie klasowe za akcję.
        
        Args:
            action: Wykonana akcja
            context: Kontekst akcji
        
        Returns:
            Ilość doświadczenia
        """
        base_exp = 1
        
        if not self.character_class:
            return 0
        
        # Doświadczenie zależne od klasy i akcji
        class_actions = {
            "Wojownik": ["attack", "defend", "parry"],
            "Łotrzyk": ["stealth", "backstab", "pickpocket", "lockpick"],
            "Łowca": ["track", "hunt", "shoot", "trap"],
            "Rzemieślnik": ["craft", "repair", "enchant", "analyze"],
            "Mag": ["cast", "meditate", "dispel", "identify"]
        }
        
        # Bonus za akcje zgodne z klasą
        if self.character_class.name in class_actions:
            for class_action in class_actions[self.character_class.name]:
                if class_action in action:
                    base_exp *= 2
                    break
        
        # Bonus za trudność
        if context and 'difficulty' in context:
            difficulty = context['difficulty']
            if difficulty > 50:
                base_exp = int(base_exp * (1 + (difficulty - 50) / 100))
        
        return base_exp
    
    def _apply_level_bonuses(self):
        """Stosuje bonusy za awans klasowy."""
        if not self.character_class:
            return
        
        level = getattr(self.character_class, 'level', 1)
        
        # Co 5 poziomów - większy bonus
        if level % 5 == 0:
            self.max_health += 10
            self.max_stamina += 10
            if hasattr(self, 'max_mana'):
                self.max_mana += 20
        else:
            self.max_health += 5
            self.max_stamina += 5
            if hasattr(self, 'max_mana'):
                self.max_mana += 10
        
        # Pełne wyleczenie po awansie
        self.health = self.max_health
        self.stamina = self.max_stamina
        if hasattr(self, 'mana'):
            self.mana = self.max_mana


# Alias dla kompatybilności
Player = Character