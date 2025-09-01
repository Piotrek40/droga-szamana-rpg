"""
Enhanced Combat System for Droga Szamana RPG.
Comprehensive realistic combat with pain, injuries, fatigue, weapon mastery, and tactical depth.
"""

import random
import math
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import copy

from mechanics.combat import (
    DamageType, BodyPart, CombatAction, Injury, CombatStats,
    CombatSystem as BaseCombatSystem
)


class WeaponType(Enum):
    """Rozszerzone typy broni."""
    PIESCI = "pięści"
    SZTYLETY = "sztylety"
    MIECZE_KROTKIE = "miecze_krótkie"
    MIECZE_DLUGIE = "miecze_długie"
    MIECZE_DWURECZNE = "miecze_dwuręczne"
    TOPORY = "topory"
    TOPORY_DWURECZNE = "topory_dwuręczne"
    MLOTY = "młoty"
    MLOTY_BOJOWE = "młoty_bojowe"
    WLÓCZNIE = "włócznie"
    HALABARD = "halabardy"
    MACZUGI = "maczugi"
    KIJE = "kije"
    LUKI = "łuki"
    KUSZE = "kusze"
    TARCZE = "tarcze"


class CombatStance(Enum):
    """Postawy bojowe."""
    NEUTRALNA = "neutralna"
    DEFENSYWNA = "defensywna"
    AGRESYWNA = "agresywna"
    WYWAŻONA = "wyważona"
    BERSERKER = "berserker"
    UNIKOWA = "unikowa"
    KONTRATAK = "kontratak"


class TechniqueType(Enum):
    """Typy technik bojowych."""
    PODSTAWOWA = "podstawowa"
    KOMBINACJA = "kombinacja"
    SPECJALNA = "specjalna"
    MISTRZOWSKA = "mistrzowska"
    LEGENDARNA = "legendarna"


class EnvironmentalFactor(Enum):
    """Czynniki środowiskowe wpływające na walkę."""
    WASKA_PRZESTRZEN = "wąska_przestrzeń"
    CIEMNOSC = "ciemność"
    SLISKA_POWIERZCHNIA = "śliska_powierzchnia"
    NIEROWNNY_TEREN = "nierówny_teren"
    MGLA = "mgła"
    DESZCZ = "deszcz"
    WIATR = "wiatr"
    WYSOKOSC = "wysokość"
    WODA = "woda"


@dataclass
class CombatTechnique:
    """Technika bojowa."""
    name: str
    polish_name: str
    type: TechniqueType
    weapon_types: List[WeaponType]
    skill_requirement: int
    stamina_cost: float
    combo_chain: List[str] = field(default_factory=list)
    damage_multiplier: float = 1.0
    accuracy_modifier: float = 0.0
    critical_chance_bonus: float = 0.0
    special_effects: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def can_execute(self, skill_level: int, current_stamina: float, weapon: Optional['Weapon']) -> bool:
        """Sprawdza czy technika może być wykonana."""
        if skill_level < self.skill_requirement:
            return False
        if current_stamina < self.stamina_cost:
            return False
        if weapon and weapon.weapon_type not in self.weapon_types:
            return False
        return True


@dataclass
class Weapon:
    """Rozszerzona reprezentacja broni."""
    name: str
    polish_name: str
    weapon_type: WeaponType
    damage_type: DamageType
    base_damage: float
    speed: int  # Szybkość ataku (-3 do +3)
    reach: int  # Zasięg w jednostkach
    weight: float
    condition: float = 100.0  # Stan broni (0-100)
    quality: str = "zwykła"  # zwykła, dobra, mistrzowska, legendarna
    techniques: List[str] = field(default_factory=list)
    special_properties: Dict[str, Any] = field(default_factory=dict)
    
    def get_effective_damage(self) -> float:
        """Oblicza efektywne obrażenia uwzględniając stan broni."""
        quality_multipliers = {
            "zepsuta": 0.5,
            "słaba": 0.7,
            "zwykła": 1.0,
            "dobra": 1.2,
            "mistrzowska": 1.5,
            "legendarna": 2.0
        }
        condition_multiplier = self.condition / 100.0
        return self.base_damage * quality_multipliers.get(self.quality, 1.0) * condition_multiplier
    
    def degrade(self, amount: float = 1.0):
        """Degraduje stan broni."""
        self.condition = max(0, self.condition - amount)
        if self.condition < 20:
            self.quality = "zepsuta"


@dataclass
class Armor:
    """Rozszerzona reprezentacja zbroi."""
    name: str
    polish_name: str
    protection: Dict[BodyPart, float]  # Ochrona dla każdej części ciała
    weight: float
    movement_penalty: float
    condition: float = 100.0
    quality: str = "zwykła"
    special_resistances: Dict[DamageType, float] = field(default_factory=dict)
    
    def get_protection(self, body_part: BodyPart, damage_type: DamageType) -> float:
        """Oblicza ochronę dla danej części ciała i typu obrażeń."""
        base_protection = self.protection.get(body_part, 0)
        condition_modifier = self.condition / 100.0
        type_resistance = self.special_resistances.get(damage_type, 1.0)
        return base_protection * condition_modifier * type_resistance
    
    def degrade(self, amount: float = 1.0):
        """Degraduje stan zbroi."""
        self.condition = max(0, self.condition - amount)


@dataclass
class CombatantMemory:
    """Pamięć kombatanta o przeciwnikach."""
    observed_actions: deque = field(default_factory=lambda: deque(maxlen=20))
    preferred_attacks: Dict[str, int] = field(default_factory=dict)
    defensive_patterns: List[str] = field(default_factory=list)
    weaknesses_discovered: Set[str] = field(default_factory=set)
    last_damage_taken: float = 0.0
    last_damage_dealt: float = 0.0
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analizuje zapamiętane wzorce walki."""
        if not self.observed_actions:
            return {}
        
        # Analiza najczęstszych ataków
        action_counts = {}
        for action in self.observed_actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        most_common = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None
        
        return {
            'most_common_action': most_common,
            'action_variety': len(set(self.observed_actions)),
            'defensive_tendency': sum(1 for a in self.observed_actions if 'obrona' in str(a).lower()) / max(len(self.observed_actions), 1),
            'discovered_weaknesses': list(self.weaknesses_discovered)
        }


@dataclass
class VoidWalkerAbility:
    """Specjalna zdolność Wędrowca Pustki."""
    name: str
    polish_name: str
    void_energy_cost: float
    pain_increase: float  # Ból przy użyciu
    cooldown: int  # Tury odnowienia
    level_requirement: int
    description: str
    effects: Dict[str, Any]
    
    def execute(self, caster_stats: CombatStats, target_stats: Optional[CombatStats] = None) -> Tuple[bool, str]:
        """Wykonuje zdolność Pustki."""
        # Sprawdź czy może być użyta
        if hasattr(caster_stats, 'void_energy') and caster_stats.void_energy < self.void_energy_cost:
            return False, f"Niewystarczająca energia Pustki! (potrzeba {self.void_energy_cost})"
        
        # Aplikuj ból
        caster_stats.pain = min(100, caster_stats.pain + self.pain_increase)
        
        # Zużyj energię
        if hasattr(caster_stats, 'void_energy'):
            caster_stats.void_energy -= self.void_energy_cost
        
        # Aplikuj efekty
        result_messages = []
        
        if 'damage' in self.effects and target_stats:
            damage = self.effects['damage']
            target_stats.health -= damage
            result_messages.append(f"Zadano {damage} obrażeń z Pustki!")
        
        if 'heal' in self.effects:
            heal = self.effects['heal']
            caster_stats.health = min(caster_stats.max_health, caster_stats.health + heal)
            result_messages.append(f"Uleczono {heal} punktów życia!")
        
        if 'teleport' in self.effects:
            result_messages.append("Teleportacja przez Pustkę!")
        
        if 'reality_tear' in self.effects:
            result_messages.append("Rozerwanie rzeczywistości! Przeciwnicy są zdezorientowani!")
        
        return True, f"{self.polish_name}: {' '.join(result_messages)}"


class EnhancedCombatSystem(BaseCombatSystem):
    """Rozszerzony system walki z pełną funkcjonalnością."""
    
    def __init__(self):
        """Inicjalizacja rozszerzonego systemu walki."""
        super().__init__()
        
        # Dodatkowe komponenty
        self.combatants: Dict[str, 'Combatant'] = {}
        self.combat_environment: Set[EnvironmentalFactor] = set()
        self.turn_order: List[str] = []
        self.combat_round: int = 0
        
        # Techniki bojowe
        self.techniques = self._initialize_techniques()
        
        # Zdolności Pustki
        self.void_abilities = self._initialize_void_abilities()
        
        # System kombinacji
        self.combo_tracker: Dict[str, List[str]] = {}
        self.combo_window: Dict[str, int] = {}
        
        # AI patterns dla NPCów
        self.ai_patterns = self._initialize_ai_patterns()
    
    def _initialize_techniques(self) -> Dict[str, CombatTechnique]:
        """Inicjalizuje techniki bojowe."""
        techniques = {}
        
        # Techniki dla mieczy
        techniques['ciecie_poziome'] = CombatTechnique(
            name='horizontal_slash',
            polish_name='Cięcie Poziome',
            type=TechniqueType.PODSTAWOWA,
            weapon_types=[WeaponType.MIECZE_KROTKIE, WeaponType.MIECZE_DLUGIE],
            skill_requirement=5,
            stamina_cost=8,
            damage_multiplier=1.2,
            description="Szerokie cięcie poziome"
        )
        
        techniques['pchnięcie_precyzyjne'] = CombatTechnique(
            name='precise_thrust',
            polish_name='Pchnięcie Precyzyjne',
            type=TechniqueType.PODSTAWOWA,
            weapon_types=[WeaponType.MIECZE_KROTKIE, WeaponType.MIECZE_DLUGIE, WeaponType.SZTYLETY],
            skill_requirement=10,
            stamina_cost=10,
            damage_multiplier=1.5,
            accuracy_modifier=0.15,
            critical_chance_bonus=0.2,
            description="Precyzyjne pchnięcie w słaby punkt"
        )
        
        techniques['wirujacy_taniec'] = CombatTechnique(
            name='spinning_dance',
            polish_name='Wirujący Taniec',
            type=TechniqueType.KOMBINACJA,
            weapon_types=[WeaponType.MIECZE_DLUGIE, WeaponType.MIECZE_DWURECZNE],
            skill_requirement=25,
            stamina_cost=20,
            combo_chain=['ciecie_poziome', 'ciecie_poziome'],
            damage_multiplier=2.0,
            special_effects={'area_damage': True, 'dizzy_chance': 0.3},
            description="Seria wirujących cięć"
        )
        
        techniques['cios_mistrza'] = CombatTechnique(
            name='master_strike',
            polish_name='Cios Mistrza',
            type=TechniqueType.MISTRZOWSKA,
            weapon_types=[WeaponType.MIECZE_DLUGIE],
            skill_requirement=50,
            stamina_cost=30,
            damage_multiplier=3.0,
            critical_chance_bonus=0.5,
            special_effects={'ignore_armor': 0.5, 'fear': 0.3},
            description="Perfekcyjny cios ignorujący część pancerza"
        )
        
        # Techniki dla toporów
        techniques['rozpłatanie'] = CombatTechnique(
            name='cleave',
            polish_name='Rozpłatanie',
            type=TechniqueType.PODSTAWOWA,
            weapon_types=[WeaponType.TOPORY, WeaponType.TOPORY_DWURECZNE],
            skill_requirement=8,
            stamina_cost=15,
            damage_multiplier=1.8,
            special_effects={'bleeding_chance': 0.7},
            description="Potężne cięcie powodujące krwawienie"
        )
        
        # Techniki dla łuków
        techniques['strzał_przebijający'] = CombatTechnique(
            name='piercing_shot',
            polish_name='Strzał Przebijający',
            type=TechniqueType.SPECJALNA,
            weapon_types=[WeaponType.LUKI, WeaponType.KUSZE],
            skill_requirement=15,
            stamina_cost=12,
            damage_multiplier=1.5,
            special_effects={'armor_penetration': 0.7},
            description="Strzał przebijający pancerz"
        )
        
        # Techniki walki wręcz
        techniques['nokaut'] = CombatTechnique(
            name='knockout',
            polish_name='Nokaut',
            type=TechniqueType.SPECJALNA,
            weapon_types=[WeaponType.PIESCI, WeaponType.MACZUGI],
            skill_requirement=20,
            stamina_cost=25,
            damage_multiplier=2.0,
            special_effects={'stun_duration': 2, 'target_head': True},
            description="Potężny cios w głowę"
        )
        
        return techniques
    
    def _initialize_void_abilities(self) -> Dict[str, VoidWalkerAbility]:
        """Inicjalizuje zdolności Wędrowca Pustki."""
        abilities = {}
        
        abilities['dotyk_pustki'] = VoidWalkerAbility(
            name='void_touch',
            polish_name='Dotyk Pustki',
            void_energy_cost=10,
            pain_increase=15,
            cooldown=2,
            level_requirement=10,
            description="Dotyk nasyca cel energią Pustki",
            effects={'damage': 25, 'slow': 2}
        )
        
        abilities['krok_cienia'] = VoidWalkerAbility(
            name='shadow_step',
            polish_name='Krok Cienia',
            void_energy_cost=15,
            pain_increase=10,
            cooldown=3,
            level_requirement=15,
            description="Teleportacja przez cienie",
            effects={'teleport': True, 'dodge_bonus': 0.5}
        )
        
        abilities['rozerwanie_rzeczywistości'] = VoidWalkerAbility(
            name='reality_tear',
            polish_name='Rozerwanie Rzeczywistości',
            void_energy_cost=30,
            pain_increase=25,
            cooldown=5,
            level_requirement=30,
            description="Tworzy rozerwanie w tkance rzeczywistości",
            effects={'reality_tear': True, 'area_damage': 40, 'confusion': 3}
        )
        
        abilities['pochłonięcie_pustki'] = VoidWalkerAbility(
            name='void_absorption',
            polish_name='Pochłonięcie Pustki',
            void_energy_cost=20,
            pain_increase=20,
            cooldown=4,
            level_requirement=25,
            description="Pochłania życie przeciwnika",
            effects={'damage': 30, 'heal': 15}
        )
        
        return abilities
    
    def _initialize_ai_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Inicjalizuje wzorce AI dla różnych typów przeciwników."""
        patterns = {
            'agresywny': {
                'stance_preference': CombatStance.AGRESYWNA,
                'attack_probability': 0.7,
                'defense_probability': 0.2,
                'retreat_threshold': 20,
                'technique_usage': 0.3,
                'target_priority': 'weakest'
            },
            'defensywny': {
                'stance_preference': CombatStance.DEFENSYWNA,
                'attack_probability': 0.3,
                'defense_probability': 0.6,
                'retreat_threshold': 40,
                'technique_usage': 0.1,
                'target_priority': 'closest'
            },
            'taktyczny': {
                'stance_preference': CombatStance.WYWAŻONA,
                'attack_probability': 0.5,
                'defense_probability': 0.4,
                'retreat_threshold': 30,
                'technique_usage': 0.4,
                'target_priority': 'most_dangerous',
                'adapts_to_player': True
            },
            'berserker': {
                'stance_preference': CombatStance.BERSERKER,
                'attack_probability': 0.9,
                'defense_probability': 0.05,
                'retreat_threshold': 5,
                'technique_usage': 0.5,
                'target_priority': 'random',
                'ignores_pain': True
            },
            'łucznik': {
                'stance_preference': CombatStance.UNIKOWA,
                'attack_probability': 0.6,
                'defense_probability': 0.3,
                'retreat_threshold': 50,
                'technique_usage': 0.3,
                'target_priority': 'furthest',
                'maintains_distance': True
            }
        }
        return patterns
    
    def calculate_weapon_reach_advantage(self, attacker_weapon: Optional[Weapon], 
                                        defender_weapon: Optional[Weapon]) -> float:
        """Oblicza przewagę zasięgu broni."""
        attacker_reach = attacker_weapon.reach if attacker_weapon else 1
        defender_reach = defender_weapon.reach if defender_weapon else 1
        
        reach_diff = attacker_reach - defender_reach
        if reach_diff > 0:
            return 0.1 * reach_diff  # Bonus do trafienia
        elif reach_diff < 0:
            return 0.05 * reach_diff  # Kara do trafienia
        return 0.0
    
    def calculate_environmental_modifiers(self) -> Dict[str, float]:
        """Oblicza modyfikatory środowiskowe."""
        modifiers = {
            'accuracy': 0.0,
            'damage': 0.0,
            'defense': 0.0,
            'movement': 0.0
        }
        
        for factor in self.combat_environment:
            if factor == EnvironmentalFactor.CIEMNOSC:
                modifiers['accuracy'] -= 0.3
                modifiers['defense'] -= 0.2
            elif factor == EnvironmentalFactor.SLISKA_POWIERZCHNIA:
                modifiers['movement'] -= 0.3
                modifiers['defense'] -= 0.15
            elif factor == EnvironmentalFactor.WASKA_PRZESTRZEN:
                modifiers['movement'] -= 0.2
                # Utrudnia długie bronie
                modifiers['accuracy'] -= 0.1
            elif factor == EnvironmentalFactor.MGLA:
                modifiers['accuracy'] -= 0.2
            elif factor == EnvironmentalFactor.DESZCZ:
                modifiers['accuracy'] -= 0.1
                # Utrudnia łucznictwo
                modifiers['damage'] -= 0.1
            elif factor == EnvironmentalFactor.WIATR:
                modifiers['accuracy'] -= 0.15  # Głównie dla łuczników
            elif factor == EnvironmentalFactor.WYSOKOSC:
                # Przewaga dla wyższego
                modifiers['damage'] += 0.1
                modifiers['defense'] += 0.1
        
        return modifiers
    
    def execute_technique(self, attacker: 'Combatant', defender: 'Combatant', 
                         technique: CombatTechnique) -> Tuple[bool, Dict[str, Any]]:
        """Wykonuje technikę bojową."""
        result = {
            'success': False,
            'damage': 0,
            'effects': [],
            'description': ""
        }
        
        # Sprawdź czy technika może być wykonana
        if not technique.can_execute(attacker.get_weapon_skill(), 
                                    attacker.stats.stamina, 
                                    attacker.weapon):
            result['description'] = f"Nie można wykonać {technique.polish_name}!"
            return False, result
        
        # Zużyj staminę
        attacker.stats.stamina -= technique.stamina_cost
        
        # Oblicz szansę trafienia z modyfikatorami techniki
        base_hit_chance = 0.5 + (attacker.get_weapon_skill() - defender.get_defense_skill()) / 100.0
        hit_chance = base_hit_chance + technique.accuracy_modifier
        
        # Modyfikatory środowiskowe
        env_mods = self.calculate_environmental_modifiers()
        hit_chance += env_mods['accuracy']
        
        if random.random() > hit_chance:
            result['description'] = f"{technique.polish_name} chybił!"
            return True, result
        
        # Oblicz obrażenia
        base_damage = attacker.weapon.get_effective_damage() if attacker.weapon else 5
        damage = base_damage * technique.damage_multiplier
        
        # Sprawdź krytyczne trafienie
        crit_chance = 0.05 + technique.critical_chance_bonus
        if random.random() < crit_chance:
            damage *= 2.0
            result['effects'].append('critical')
        
        # Aplikuj specjalne efekty
        if technique.special_effects:
            for effect, value in technique.special_effects.items():
                if effect == 'bleeding_chance' and random.random() < value:
                    result['effects'].append('bleeding')
                elif effect == 'stun_duration':
                    defender.stats.is_stunned = True
                    defender.stats.stun_duration = value
                    result['effects'].append(f'stun_{value}')
                elif effect == 'armor_penetration':
                    # Ignoruj część pancerza
                    pass  # Obsłużone w redukcji obrażeń
                elif effect == 'area_damage':
                    result['effects'].append('area')
        
        result['success'] = True
        result['damage'] = damage
        result['description'] = f"{technique.polish_name} trafia za {damage:.1f} obrażeń!"
        
        return True, result
    
    def check_combo_opportunity(self, combatant_id: str, action: str) -> Optional[CombatTechnique]:
        """Sprawdza czy można wykonać kombinację."""
        if combatant_id not in self.combo_tracker:
            self.combo_tracker[combatant_id] = []
            self.combo_window[combatant_id] = 0
        
        # Dodaj akcję do trackera
        self.combo_tracker[combatant_id].append(action)
        
        # Sprawdź czy okno kombinacji jest aktywne
        if self.combo_window[combatant_id] <= 0:
            self.combo_tracker[combatant_id] = [action]
            self.combo_window[combatant_id] = 2  # 2 tury na kombinację
        
        # Szukaj pasujących kombinacji
        for tech_name, technique in self.techniques.items():
            if technique.type == TechniqueType.KOMBINACJA:
                if technique.combo_chain == self.combo_tracker[combatant_id][-len(technique.combo_chain):]:
                    return technique
        
        return None
    
    def update_combo_windows(self):
        """Aktualizuje okna czasowe kombinacji."""
        for combatant_id in list(self.combo_window.keys()):
            self.combo_window[combatant_id] -= 1
            if self.combo_window[combatant_id] <= 0:
                self.combo_tracker[combatant_id] = []
    
    def apply_weapon_degradation(self, weapon: Weapon, action: CombatAction):
        """Aplikuje degradację broni."""
        degradation_rates = {
            CombatAction.ATAK_PODSTAWOWY: 0.5,
            CombatAction.ATAK_SILNY: 1.0,
            CombatAction.ATAK_SZYBKI: 0.3,
            CombatAction.PAROWANIE: 0.7
        }
        
        degradation = degradation_rates.get(action, 0.5)
        
        # Modyfikatory jakości
        if weapon.quality == "słaba":
            degradation *= 2.0
        elif weapon.quality == "mistrzowska":
            degradation *= 0.5
        elif weapon.quality == "legendarna":
            degradation *= 0.3
        
        weapon.degrade(degradation)
    
    def calculate_fatigue_penalties(self, stats: CombatStats) -> Dict[str, float]:
        """Oblicza kary za zmęczenie."""
        penalties = {
            'attack_speed': 0.0,
            'damage': 0.0,
            'defense': 0.0,
            'accuracy': 0.0
        }
        
        # Zmęczenie krótkoterminowe (stamina)
        stamina_percent = stats.stamina / stats.max_stamina
        if stamina_percent < 0.3:
            penalties['attack_speed'] += 0.3
            penalties['damage'] += 0.2
            penalties['accuracy'] += 0.2
        elif stamina_percent < 0.5:
            penalties['attack_speed'] += 0.15
            penalties['damage'] += 0.1
            penalties['accuracy'] += 0.1
        
        # Zmęczenie długoterminowe (exhaustion)
        if stats.exhaustion > 50:
            exhaustion_penalty = (stats.exhaustion - 50) / 100.0
            penalties['attack_speed'] += exhaustion_penalty * 0.4
            penalties['damage'] += exhaustion_penalty * 0.3
            penalties['defense'] += exhaustion_penalty * 0.3
            penalties['accuracy'] += exhaustion_penalty * 0.25
        
        return penalties
    
    def ai_choose_action(self, npc: 'Combatant', player: 'Combatant') -> Tuple[CombatAction, Optional[CombatTechnique]]:
        """AI wybiera akcję dla NPC."""
        pattern = self.ai_patterns.get(npc.ai_pattern, self.ai_patterns['taktyczny'])
        
        # Analiza sytuacji
        health_percent = npc.stats.health / npc.stats.max_health
        enemy_health_percent = player.stats.health / player.stats.max_health
        
        # Sprawdź czy należy się wycofać
        if health_percent * 100 < pattern['retreat_threshold']:
            if random.random() < 0.7:
                return CombatAction.UNIK, None
        
        # Adaptacja do gracza
        if pattern.get('adapts_to_player'):
            player_patterns = npc.memory.analyze_patterns()
            if player_patterns.get('defensive_tendency', 0) > 0.5:
                # Gracz jest defensywny - bądź bardziej agresywny
                pattern = copy.deepcopy(pattern)
                pattern['attack_probability'] *= 1.3
        
        # Wybór akcji
        roll = random.random()
        
        if roll < pattern['attack_probability']:
            # Atak
            if random.random() < pattern['technique_usage'] and npc.weapon:
                # Spróbuj użyć techniki
                available_techniques = [
                    tech for name, tech in self.techniques.items()
                    if tech.can_execute(npc.get_weapon_skill(), npc.stats.stamina, npc.weapon)
                ]
                if available_techniques:
                    return CombatAction.ATAK_PODSTAWOWY, random.choice(available_techniques)
            
            # Wybierz typ ataku
            if npc.stats.stamina > 20:
                return random.choice([CombatAction.ATAK_PODSTAWOWY, CombatAction.ATAK_SILNY]), None
            else:
                return CombatAction.ATAK_SZYBKI, None
        
        elif roll < pattern['attack_probability'] + pattern['defense_probability']:
            # Obrona
            return random.choice([CombatAction.OBRONA, CombatAction.PAROWANIE, CombatAction.UNIK]), None
        
        else:
            # Inne akcje
            return random.choice([CombatAction.FINTA, CombatAction.KOPNIECIE]), None
    
    def process_combat_turn(self, attacker: 'Combatant', defender: 'Combatant', 
                           action: CombatAction, technique: Optional[CombatTechnique] = None) -> Dict[str, Any]:
        """Przetwarza pełną turę walki."""
        result = {
            'attacker': attacker.name,
            'defender': defender.name,
            'action': action.value,
            'success': False,
            'damage': 0,
            'effects': [],
            'messages': []
        }
        
        # Sprawdź oszołomienie
        if attacker.stats.is_stunned:
            if attacker.stats.stun_duration > 0:
                attacker.stats.stun_duration -= 1
                result['messages'].append(f"{attacker.name} jest oszołomiony!")
                if attacker.stats.stun_duration == 0:
                    attacker.stats.is_stunned = False
                return result
        
        # Sprawdź przytomność
        if not attacker.stats.is_conscious:
            result['messages'].append(f"{attacker.name} jest nieprzytomny!")
            return result
        
        # Wykonaj akcję
        if technique:
            # Wykonaj technikę
            success, tech_result = self.execute_technique(attacker, defender, technique)
            result['success'] = tech_result['success']
            result['damage'] = tech_result.get('damage', 0)
            result['effects'] = tech_result.get('effects', [])
            result['messages'].append(tech_result['description'])
        else:
            # Standardowa akcja
            if action in [CombatAction.ATAK_PODSTAWOWY, CombatAction.ATAK_SILNY, CombatAction.ATAK_SZYBKI]:
                weapon_damage = attacker.weapon.get_effective_damage() if attacker.weapon else 5
                damage_type = attacker.weapon.damage_type if attacker.weapon else DamageType.OBUCHOWE
                
                success, attack_result = self.perform_attack(
                    attacker.stats, defender.stats,
                    attacker.get_weapon_skill(), defender.get_defense_skill(),
                    action, weapon_damage, damage_type
                )
                
                if success and attack_result['hit']:
                    # Aplikuj obrażenia
                    self.apply_damage(
                        defender.stats, attack_result['damage'],
                        attack_result['body_part'], damage_type,
                        attack_result.get('injury')
                    )
                    
                    # Degraduj broń
                    if attacker.weapon:
                        self.apply_weapon_degradation(attacker.weapon, action)
                    
                    # Degraduj zbroję obrońcy
                    if defender.armor and attack_result['hit']:
                        defender.armor.degrade(0.5)
                
                result['success'] = success
                result['damage'] = attack_result.get('damage', 0)
                result['messages'].append(attack_result['description'])
                
            elif action in [CombatAction.OBRONA, CombatAction.UNIK, CombatAction.PAROWANIE]:
                # Akcja defensywna - ustaw flagę
                defender.defensive_action = action
                result['messages'].append(f"{attacker.name} przyjmuje postawę obronną.")
        
        # Aktualizuj pamięć
        if hasattr(defender, 'memory'):
            defender.memory.observed_actions.append(action)
            if result['damage'] > 0:
                defender.memory.last_damage_taken = result['damage']
        
        # Sprawdź kombinacje
        combo = self.check_combo_opportunity(attacker.name, action.value)
        if combo:
            result['messages'].append(f"Możliwa kombinacja: {combo.polish_name}!")
        
        # Aktualizuj okna kombinacji
        self.update_combo_windows()
        
        return result
    
    def calculate_combat_outcome(self, combatant: 'Combatant') -> str:
        """Określa wynik walki dla kombatanta."""
        if not combatant.stats.is_conscious:
            if combatant.stats.health <= 0:
                return "martwy"
            else:
                return "nieprzytomny"
        elif combatant.stats.health <= 10:
            return "ciężko_ranny"
        elif combatant.stats.health <= 30:
            return "ranny"
        elif combatant.stats.exhaustion > 80:
            return "wyczerpany"
        else:
            return "walczy"


@dataclass
class Combatant:
    """Rozszerzona reprezentacja uczestnika walki."""
    name: str
    stats: CombatStats
    weapon: Optional[Weapon] = None
    armor: Optional[Armor] = None
    skills: Dict[str, int] = field(default_factory=dict)
    stance: CombatStance = CombatStance.NEUTRALNA
    memory: CombatantMemory = field(default_factory=CombatantMemory)
    ai_pattern: str = "taktyczny"
    defensive_action: Optional[CombatAction] = None
    injuries: List[Injury] = field(default_factory=list)
    
    def get_weapon_skill(self) -> int:
        """Zwraca poziom umiejętności dla aktualnej broni."""
        if not self.weapon:
            return self.skills.get('walka_wrecz', 0)
        
        weapon_skill_map = {
            WeaponType.SZTYLETY: 'sztylety',
            WeaponType.MIECZE_KROTKIE: 'miecze',
            WeaponType.MIECZE_DLUGIE: 'miecze',
            WeaponType.MIECZE_DWURECZNE: 'miecze_dwureczne',
            WeaponType.TOPORY: 'topory',
            WeaponType.LUKI: 'lucznictwo',
            WeaponType.KUSZE: 'lucznictwo'
        }
        
        skill_name = weapon_skill_map.get(self.weapon.weapon_type, 'walka_wrecz')
        return self.skills.get(skill_name, 0)
    
    def get_defense_skill(self) -> int:
        """Zwraca poziom umiejętności obronnych."""
        base_defense = self.skills.get('obrona', 0)
        
        # Bonus za tarczę
        if self.weapon and self.weapon.weapon_type == WeaponType.TARCZE:
            base_defense += 10
        
        # Modyfikator za postawę
        if self.stance == CombatStance.DEFENSYWNA:
            base_defense += 15
        elif self.stance == CombatStance.AGRESYWNA:
            base_defense -= 10
        
        return base_defense
    
    def calculate_initiative(self) -> int:
        """Oblicza inicjatywę w walce."""
        base_initiative = 10 + self.skills.get('zwinnosc', 0)
        
        # Modyfikatory za broń
        if self.weapon:
            base_initiative += self.weapon.speed * 2
        
        # Kary za zbroję
        if self.armor:
            base_initiative -= self.armor.movement_penalty
        
        # Kary za stan
        if self.stats.pain > 30:
            base_initiative -= (self.stats.pain - 30) // 10
        
        if self.stats.exhaustion > 50:
            base_initiative -= (self.stats.exhaustion - 50) // 10
        
        # Losowy element
        base_initiative += random.randint(-5, 5)
        
        return max(1, base_initiative)