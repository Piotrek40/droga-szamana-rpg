"""
System walki dla Droga Szamana RPG.
Realistyczna walka z bólem, kontuzjami, zmęczeniem i taktyką.
"""

import random
import math
import json
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import copy


class DamageType(Enum):
    """Typy obrażeń."""
    CIECIE = "cięcie"
    KLUTE = "kłucie"
    OBUCHOWE = "obuchowe"
    IMPACT = "uderzenie"  # Alias dla obuchowe
    MAGICZNE = "magiczne"
    UPADEK = "upadek"
    TRUCIZNA = "trucizna"
    OPARZENIE = "oparzenie"


class BodyPart(Enum):
    """Części ciała które mogą zostać trafione."""
    GLOWA = "głowa"
    TULOW = "tułów"
    LEWA_REKA = "lewa_ręka"
    PRAWA_REKA = "prawa_ręka"
    ARM = "ręka"  # Alias ogólny dla ręki
    LEWA_NOGA = "lewa_noga"
    PRAWA_NOGA = "prawa_noga"


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


class CombatAction(Enum):
    """Dostępne akcje bojowe."""
    ATAK_PODSTAWOWY = "atak_podstawowy"
    ATAK_SILNY = "atak_silny"
    ATAK_SZYBKI = "atak_szybki"
    OBRONA = "obrona"
    UNIK = "unik"
    PAROWANIE = "parowanie"
    RIPOSTA = "riposta"
    FINTA = "finta"
    KOPNIECIE = "kopnięcie"
    PCHNIECIE = "pchnięcie"


@dataclass
class Injury:
    """Reprezentacja kontuzji."""
    body_part: BodyPart
    severity: float  # 0-100
    damage_type: DamageType
    bleeding: bool = False
    bleeding_rate: float = 0.0  # Punkty życia na turę
    infected: bool = False
    treated: bool = False
    time_to_heal: int = 0  # Czas do wyleczenia w minutach gry
    permanent_scar: bool = False
    
    def update(self, delta_time: int) -> Tuple[float, bool]:
        """
        Aktualizuje stan kontuzji.
        
        Args:
            delta_time: Czas który minął (minuty gry)
        
        Returns:
            (utrata krwi, czy wyleczona)
        """
        blood_loss = 0.0
        
        if self.bleeding and not self.treated:
            blood_loss = self.bleeding_rate * (delta_time / 60.0)
            
            # Krwawienie może się zatrzymać samo
            if random.random() < 0.05:
                self.bleeding = False
                self.bleeding_rate = 0.0
        
        if self.time_to_heal > 0:
            healing_rate = 1.0
            if self.treated:
                healing_rate = 2.0  # Szybsze leczenie gdy opatrzona
            if self.infected:
                healing_rate = 0.3  # Wolniejsze gdy zainfekowana
            
            self.time_to_heal -= int(delta_time * healing_rate)
            
            if self.time_to_heal <= 0:
                # Rana wyleczona
                if self.severity > 50 and random.random() < 0.3:
                    self.permanent_scar = True
                return blood_loss, True
        
        # Ryzyko infekcji
        if not self.treated and not self.infected:
            infection_chance = 0.001 * delta_time
            if self.severity > 30:
                infection_chance *= 2
            if random.random() < infection_chance:
                self.infected = True
                self.time_to_heal = int(self.time_to_heal * 1.5)
        
        return blood_loss, False


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
        """Analizuje wzorce przeciwnika na podstawie obserwacji."""
        if not self.observed_actions:
            return {}
        
        patterns = {}
        actions = list(self.observed_actions)
        
        # Analiza częstotliwości akcji
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        total_actions = len(actions)
        patterns['action_probabilities'] = {
            action: count / total_actions 
            for action, count in action_counts.items()
        }
        
        # Szukanie sekwencji
        if len(actions) >= 3:
            sequences = []
            for i in range(len(actions) - 2):
                seq = (actions[i], actions[i+1], actions[i+2])
                sequences.append(seq)
            
            patterns['common_sequences'] = self._find_common_sequences(sequences)
        
        return patterns
    
    def _find_common_sequences(self, sequences: List[Tuple]) -> List[Tuple]:
        """Znajduje najczęstsze sekwencje akcji."""
        seq_counts = {}
        for seq in sequences:
            seq_counts[seq] = seq_counts.get(seq, 0) + 1
        
        return sorted(seq_counts.keys(), key=lambda x: seq_counts[x], reverse=True)[:3]


@dataclass
class VoidWalkerAbility:
    """Zdolność Wędrowca Pustki."""
    name: str
    polish_name: str
    void_energy_cost: int
    pain_increase: int  # Ile bólu zwiększa użycie
    cooldown: int  # Tury
    level_requirement: int
    description: str
    effects: Dict[str, Any] = field(default_factory=dict)
    
    def execute(self, caster_stats: 'CombatStats', target_stats: Optional['CombatStats'] = None) -> Tuple[bool, str]:
        """Wykonuje zdolność Pustki."""
        # Sprawdź poziom bólu - przy wysokim bólu zdolności są mniej skuteczne
        pain_modifier = 1.0 - (caster_stats.pain / 200.0)  # Max 50% redukcji
        
        # Zwiększ ból kastera
        caster_stats.pain = min(100, caster_stats.pain + self.pain_increase)
        
        result_message = f"Używasz zdolności: {self.polish_name}"
        
        # Zastosuj efekty
        if 'damage' in self.effects:
            base_damage = self.effects['damage'] * pain_modifier
            if target_stats:
                target_stats.health -= base_damage
                result_message += f" - zadajesz {base_damage:.1f} obrażeń"
        
        if 'heal' in self.effects:
            heal_amount = self.effects['heal'] * pain_modifier
            caster_stats.health = min(caster_stats.max_health, caster_stats.health + heal_amount)
            result_message += f" - odzyskujesz {heal_amount:.1f} zdrowia"
        
        if 'slow' in self.effects and target_stats:
            # Efekt spowolnienia - implementacja zależna od systemu
            result_message += " - cel jest spowolniony"
        
        return True, result_message


@dataclass
class CombatStats:
    """Statystyki bojowe postaci."""
    health: float = 100.0
    max_health: float = 100.0
    stamina: float = 100.0
    max_stamina: float = 100.0
    pain: float = 0.0  # 0-100
    exhaustion: float = 0.0  # 0-100, długoterminowe zmęczenie
    strength: float = 50.0  # Siła fizyczna, wpływa na obrażenia
    agility: float = 50.0  # Zręczność, wpływa na uniki
    
    # Modyfikatory
    attack_speed: float = 1.0
    damage_multiplier: float = 1.0
    defense_multiplier: float = 1.0
    speed_multiplier: float = 1.0  # Modyfikator prędkości ruchu
    accuracy_multiplier: float = 1.0  # Modyfikator celności
    critical_chance: float = 0.05  # Szansa na trafienie krytyczne (5%)

    # Stan
    is_conscious: bool = True
    is_stunned: bool = False
    stun_duration: int = 0
    is_bleeding: bool = False
    total_bleeding_rate: float = 0.0
    
    # Nowe pola z enhanced combat
    void_energy: float = 0.0  # Energia pustki dla Void Walker
    max_void_energy: float = 100.0
    fatigue: float = 0.0  # Zmęczenie wpływające na regenerację
    combat_stance: CombatStance = CombatStance.NEUTRALNA
    current_weapon: Optional[Weapon] = None
    current_armor: Optional[Armor] = None
    memory: CombatantMemory = field(default_factory=CombatantMemory)


class CombatSystem:
    """System zarządzania walką."""
    
    def __init__(self, combat_data_path: str = "data/combat_mechanics.json"):
        """Inicjalizacja systemu walki z danymi z JSON."""
        # Inicjalizacja podstawowych atrybutów
        self.combat_log: List[str] = []
        self.turn_count: int = 0
        self.last_actions: Dict[str, CombatAction] = {}
        
        # Wczytaj dane z JSON
        self.combat_data = self._load_combat_data(combat_data_path)
        self.pain_thresholds = self.combat_data.get('pain_system', {}).get('thresholds', {})
        self.body_parts_data = self.combat_data.get('injury_system', {}).get('body_parts', {})
        self.weapon_types = self.combat_data.get('weapon_types', {})
        self.combat_formulas = self.combat_data.get('combat_formulas', {})
        
        # Enhanced combat features
        self.combat_techniques: Dict[str, CombatTechnique] = self._initialize_techniques()
        self.void_abilities: Dict[str, VoidWalkerAbility] = self._initialize_void_abilities()
        self.ai_patterns: Dict[str, Dict[str, Any]] = self._initialize_ai_patterns()
        self.combat_environment: List[EnvironmentalFactor] = []
        
        # Ensure pain_thresholds is available as class attribute for compatibility
        if hasattr(self, 'pain_thresholds'):
            CombatSystem.pain_thresholds = self.pain_thresholds
    
    def _load_combat_data(self, path: str) -> Dict:
        """Wczytaj dane systemu walki z JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Ostrzeżenie: Nie znaleziono pliku {path}")
            return {}
    
    def get_pain_effects(self, pain_level: int) -> Dict[str, Any]:
        """Zwraca efekty bólu na podstawie danych z JSON."""
        for threshold_name, threshold_data in self.pain_thresholds.items():
            min_pain = threshold_data.get('min', 0)
            max_pain = threshold_data.get('max', 100)
            if min_pain <= pain_level < max_pain:
                return threshold_data.get('effects', {})
        return {}
    
    # Szanse trafienia części ciała
    HIT_CHANCES = {
        BodyPart.GLOWA: 0.10,
        BodyPart.TULOW: 0.40,
        BodyPart.LEWA_REKA: 0.15,
        BodyPart.PRAWA_REKA: 0.15,
        BodyPart.LEWA_NOGA: 0.10,
        BodyPart.PRAWA_NOGA: 0.10
    }
    
    # Mnożniki obrażeń dla części ciała
    DAMAGE_MULTIPLIERS = {
        BodyPart.GLOWA: 2.0,
        BodyPart.TULOW: 1.0,
        BodyPart.LEWA_REKA: 0.8,
        BodyPart.PRAWA_REKA: 0.8,
        BodyPart.LEWA_NOGA: 0.7,
        BodyPart.PRAWA_NOGA: 0.7
    }
    
    # Koszty staminy dla akcji
    STAMINA_COSTS = {
        CombatAction.ATAK_PODSTAWOWY: 5,
        CombatAction.ATAK_SILNY: 15,
        CombatAction.ATAK_SZYBKI: 3,
        CombatAction.OBRONA: 2,
        CombatAction.UNIK: 8,
        CombatAction.PAROWANIE: 6,
        CombatAction.RIPOSTA: 10,
        CombatAction.FINTA: 4,
        CombatAction.KOPNIECIE: 7,
        CombatAction.PCHNIECIE: 5
    }
    
    def calculate_initiative(self, attacker_stats: CombatStats, defender_stats: CombatStats,
                           attacker_skill: int, defender_skill: int) -> Tuple[bool, str]:
        """
        Oblicza kto atakuje pierwszy.
        
        Args:
            attacker_stats: Statystyki atakującego
            defender_stats: Statystyki obrońcy
            attacker_skill: Poziom umiejętności atakującego
            defender_skill: Poziom umiejętności obrońcy
        
        Returns:
            (czy atakujący ma inicjatywę, opis)
        """
        # Bazowa inicjatywa
        attacker_init = attacker_skill + random.randint(1, 20)
        defender_init = defender_skill + random.randint(1, 20)
        
        # Modyfikatory za stan
        if attacker_stats.pain > 50:
            attacker_init -= 5
        if attacker_stats.exhaustion > 70:
            attacker_init -= 10
            
        if defender_stats.pain > 50:
            defender_init -= 5
        if defender_stats.exhaustion > 70:
            defender_init -= 10
        
        if attacker_init > defender_init:
            return True, "Atakujący wyprzedza przeciwnika!"
        else:
            return False, "Obrońca reaguje szybciej!"
    
    def perform_attack(self, attacker_stats: CombatStats, defender_stats: CombatStats,
                      attacker_skill: int, defender_skill: int,
                      action: CombatAction, weapon_damage: int = 10,
                      damage_type: DamageType = DamageType.OBUCHOWE) -> Tuple[bool, Dict[str, Any]]:
        """
        Wykonuje atak.
        
        Args:
            attacker_stats: Statystyki atakującego
            defender_stats: Statystyki obrońcy
            attacker_skill: Poziom umiejętności atakującego
            defender_skill: Poziom umiejętności obrońcy
            action: Rodzaj ataku
            weapon_damage: Bazowe obrażenia broni
            damage_type: Typ obrażeń
        
        Returns:
            (sukces, szczegóły ataku)
        """
        result = {
            'hit': False,
            'damage': 0,
            'body_part': None,
            'injury': None,
            'pain_caused': 0,
            'critical': False,
            'description': ""
        }
        
        # Sprawdź czy atakujący ma wystarczająco staminy
        stamina_cost = self.STAMINA_COSTS.get(action, 5)
        if attacker_stats.stamina < stamina_cost:
            result['description'] = "Zbyt zmęczony aby wykonać atak!"
            return False, result
        
        # Zużyj staminę
        attacker_stats.stamina -= stamina_cost
        attacker_stats.exhaustion += stamina_cost * 0.1  # Długoterminowe zmęczenie
        
        # Oblicz szansę trafienia
        base_hit_chance = 0.5 + (attacker_skill - defender_skill) / 100.0
        
        # Modyfikatory za akcję
        action_modifiers = {
            CombatAction.ATAK_PODSTAWOWY: 0.0,
            CombatAction.ATAK_SILNY: -0.15,  # Trudniej trafić
            CombatAction.ATAK_SZYBKI: 0.10,  # Łatwiej trafić
            CombatAction.FINTA: 0.20  # Bonus za zmylenie
        }
        
        hit_chance = base_hit_chance + action_modifiers.get(action, 0.0)
        
        # Kary za ból i zmęczenie
        pain_penalty = attacker_stats.pain / 200.0
        exhaustion_penalty = attacker_stats.exhaustion / 300.0
        hit_chance -= (pain_penalty + exhaustion_penalty)
        
        # Rzut na trafienie
        hit_roll = random.random()
        
        if hit_roll > hit_chance:
            result['description'] = "Atak chybił!"
            result['hit'] = False
            return True, result  # Zwracamy True bo atak był wykonany, tylko chybił
        
        # Określ trafioną część ciała
        body_part = self._determine_hit_location()
        result['body_part'] = body_part
        result['hit'] = True  # Trafienie!
        
        # Oblicz obrażenia
        base_damage = weapon_damage
        
        # Modyfikatory za akcję
        if action == CombatAction.ATAK_SILNY:
            base_damage *= 1.5
        elif action == CombatAction.ATAK_SZYBKI:
            base_damage *= 0.7
        
        # Mnożnik za część ciała
        base_damage *= self.DAMAGE_MULTIPLIERS[body_part]
        
        # Losowy element
        damage_roll = random.uniform(0.8, 1.2)
        final_damage = base_damage * damage_roll * attacker_stats.damage_multiplier
        
        # Sprawdź krytyczne trafienie
        crit_chance = 0.05 + (attacker_skill - defender_skill) / 500.0
        if random.random() < crit_chance:
            final_damage *= 2.0
            result['critical'] = True
        
        # Redukcja przez obronę
        if defender_stats.defense_multiplier > 0:
            final_damage *= (1.0 - min(0.8, defender_stats.defense_multiplier))
        
        result['damage'] = round(final_damage, 1)
        
        # Oblicz ból
        pain_spike = self._calculate_pain_from_damage(final_damage, body_part, damage_type)
        result['pain_caused'] = pain_spike
        
        # Stwórz kontuzję jeśli obrażenia znaczące
        if final_damage > 5:
            injury = self._create_injury(body_part, final_damage, damage_type)
            result['injury'] = injury
        
        # Opis ataku
        descriptions = {
            BodyPart.GLOWA: "w głowę",
            BodyPart.TULOW: "w tułów",
            BodyPart.LEWA_REKA: "w lewą rękę",
            BodyPart.PRAWA_REKA: "w prawą rękę",
            BodyPart.LEWA_NOGA: "w lewą nogę",
            BodyPart.PRAWA_NOGA: "w prawą nogę"
        }
        
        hit_desc = descriptions[body_part]
        if result['critical']:
            result['description'] = f"KRYTYCZNE trafienie {hit_desc}! Zadano {final_damage:.1f} obrażeń!"
        else:
            result['description'] = f"Trafienie {hit_desc}. Zadano {final_damage:.1f} obrażeń."
        
        return True, result
    
    def perform_defense(self, defender_stats: CombatStats, defender_skill: int,
                       action: CombatAction) -> Tuple[bool, float]:
        """
        Wykonuje akcję obronną.
        
        Args:
            defender_stats: Statystyki broniącego
            defender_skill: Poziom umiejętności
            action: Typ obrony
        
        Returns:
            (sukces, mnożnik redukcji obrażeń)
        """
        # Sprawdź staminę
        stamina_cost = self.STAMINA_COSTS.get(action, 5)
        if defender_stats.stamina < stamina_cost:
            return False, 0.0
        
        defender_stats.stamina -= stamina_cost
        
        # Bazowa szansa obrony
        base_chance = 0.3 + defender_skill / 200.0
        
        # Modyfikatory za akcję
        if action == CombatAction.OBRONA:
            defense_chance = base_chance + 0.2
            reduction = 0.5
        elif action == CombatAction.UNIK:
            defense_chance = base_chance + 0.1
            reduction = 1.0  # Pełne uniknięcie
        elif action == CombatAction.PAROWANIE:
            defense_chance = base_chance + 0.15
            reduction = 0.7
        else:
            defense_chance = base_chance
            reduction = 0.3
        
        # Kary za stan
        pain_penalty = defender_stats.pain / 300.0
        exhaustion_penalty = defender_stats.exhaustion / 400.0
        defense_chance -= (pain_penalty + exhaustion_penalty)
        
        if random.random() < defense_chance:
            return True, reduction
        
        return False, 0.0
    
    def apply_damage(self, stats: CombatStats, damage: float, body_part: BodyPart,
                    damage_type: DamageType, injury: Optional[Injury] = None) -> str:
        """
        Aplikuje obrażenia do postaci.
        
        Args:
            stats: Statystyki postaci
            damage: Ilość obrażeń
            body_part: Trafiona część ciała
            damage_type: Typ obrażeń
            injury: Kontuzja do dodania
        
        Returns:
            Opis efektu
        """
        # Zmniejsz zdrowie
        stats.health -= damage
        
        # Dodaj ból
        pain_increase = self._calculate_pain_from_damage(damage, body_part, damage_type)
        stats.pain = min(100, stats.pain + pain_increase)
        
        # Sprawdź utratę przytomności
        if stats.pain >= 80 or stats.health <= 0:
            stats.is_conscious = False
            return "Postać traci przytomność!"
        
        # Sprawdź oszołomienie
        if body_part == BodyPart.GLOWA and damage > 15:
            stats.is_stunned = True
            stats.stun_duration = random.randint(1, 3)
            return "Postać jest oszołomiona!"
        
        # Efekty w zależności od części ciała
        effects = []
        
        if body_part == BodyPart.GLOWA:
            if damage > 10:
                effects.append("zawroty głowy")
        elif body_part == BodyPart.TULOW:
            if damage > 20:
                effects.append("trudności z oddychaniem")
        elif body_part in [BodyPart.LEWA_REKA, BodyPart.PRAWA_REKA]:
            if damage > 15:
                effects.append("osłabiona ręka")
        elif body_part in [BodyPart.LEWA_NOGA, BodyPart.PRAWA_NOGA]:
            if damage > 15:
                effects.append("utykanie")
        
        if injury and injury.bleeding:
            stats.is_bleeding = True
            stats.total_bleeding_rate += injury.bleeding_rate
            effects.append("krwawienie")
        
        if effects:
            return f"Efekty: {', '.join(effects)}"
        
        return "Postać odczuwa ból."
    
    def _determine_hit_location(self) -> BodyPart:
        """
        Losuje trafioną część ciała.
        
        Returns:
            Trafiona część ciała
        """
        roll = random.random()
        cumulative = 0.0
        
        for part, chance in self.HIT_CHANCES.items():
            cumulative += chance
            if roll < cumulative:
                return part
        
        return BodyPart.TULOW  # Domyślnie tułów
    
    def _calculate_pain_from_damage(self, damage: float, body_part: BodyPart,
                                   damage_type: DamageType) -> float:
        """
        Oblicza wzrost bólu na podstawie obrażeń.
        
        Args:
            damage: Ilość obrażeń
            body_part: Trafiona część ciała
            damage_type: Typ obrażeń
        
        Returns:
            Wzrost poziomu bólu
        """
        # Bazowy ból
        base_pain = damage * 2.0
        
        # Mnożniki za część ciała
        part_multipliers = {
            BodyPart.GLOWA: 1.5,
            BodyPart.TULOW: 1.0,
            BodyPart.LEWA_REKA: 0.9,
            BodyPart.PRAWA_REKA: 0.9,
            BodyPart.LEWA_NOGA: 0.8,
            BodyPart.PRAWA_NOGA: 0.8
        }
        
        # Mnożniki za typ obrażeń
        type_multipliers = {
            DamageType.CIECIE: 1.2,
            DamageType.KLUTE: 1.3,
            DamageType.OBUCHOWE: 0.9,
            DamageType.MAGICZNE: 1.0,
            DamageType.OPARZENIE: 1.5,
            DamageType.TRUCIZNA: 0.7,
            DamageType.UPADEK: 0.8
        }
        
        pain = base_pain * part_multipliers.get(body_part, 1.0) * type_multipliers.get(damage_type, 1.0)
        
        # Losowy element
        pain *= random.uniform(0.8, 1.2)
        
        return min(40, pain)  # Max 40 bólu z jednego ataku
    
    def _create_injury(self, body_part: BodyPart, damage: float, 
                      damage_type: DamageType) -> Injury:
        """
        Tworzy kontuzję na podstawie obrażeń.
        
        Args:
            body_part: Część ciała
            damage: Ilość obrażeń
            damage_type: Typ obrażeń
        
        Returns:
            Nowa kontuzja
        """
        severity = min(100, damage * 3)
        
        # Szansa na krwawienie
        bleeding = False
        bleeding_rate = 0.0
        
        if damage_type in [DamageType.CIECIE, DamageType.KLUTE]:
            if damage > 10:
                bleeding = True
                bleeding_rate = damage / 20.0  # 0.5 HP/turę na 10 obrażeń
        
        # Czas leczenia
        base_heal_time = int(severity * 10)  # 10 minut na punkt severity
        
        # Modyfikatory za typ
        if damage_type == DamageType.OPARZENIE:
            base_heal_time *= 1.5
        elif damage_type == DamageType.TRUCIZNA:
            base_heal_time *= 2.0
        
        injury = Injury(
            body_part=body_part,
            severity=severity,
            damage_type=damage_type,
            bleeding=bleeding,
            bleeding_rate=bleeding_rate,
            time_to_heal=base_heal_time
        )
        
        return injury
    
    def recover_stamina(self, stats: CombatStats, is_resting: bool, 
                       time_passed: int) -> float:
        """
        Regeneruje staminę.
        
        Args:
            stats: Statystyki postaci
            is_resting: Czy postać odpoczywa
            time_passed: Czas który minął (sekundy)
        
        Returns:
            Ilość zregenerowanej staminy
        """
        # Bazowa regeneracja
        base_regen = 1.0 if is_resting else 0.3
        
        # Kary za wyczerpanie
        if stats.exhaustion > 50:
            base_regen *= 0.5
        if stats.exhaustion > 80:
            base_regen *= 0.5
        
        # Kara za ból
        if stats.pain > 30:
            base_regen *= (1.0 - stats.pain / 200.0)
        
        regen_amount = base_regen * time_passed
        
        # Aktualizuj staminę
        old_stamina = stats.stamina
        stats.stamina = min(stats.max_stamina, stats.stamina + regen_amount)
        
        # Zmniejsz wyczerpanie podczas odpoczynku
        if is_resting and stats.exhaustion > 0:
            stats.exhaustion = max(0, stats.exhaustion - time_passed * 0.1)
        
        return stats.stamina - old_stamina
    
    def reduce_pain(self, stats: CombatStats, amount: float, is_medical: bool = False) -> float:
        """
        Zmniejsza poziom bólu.
        
        Args:
            stats: Statystyki postaci
            amount: Bazowa ilość redukcji
            is_medical: Czy to leczenie medyczne
        
        Returns:
            Rzeczywista redukcja bólu
        """
        if is_medical:
            # Leczenie medyczne jest bardziej efektywne
            actual_reduction = amount * random.uniform(0.8, 1.2)
        else:
            # Naturalny spadek bólu
            actual_reduction = amount * random.uniform(0.5, 1.0)
        
        old_pain = stats.pain
        stats.pain = max(0, stats.pain - actual_reduction)
        
        # Sprawdź czy postać odzyskuje przytomność
        if not stats.is_conscious and stats.pain < 60 and stats.health > 0:
            if random.random() < 0.3:  # 30% szans
                stats.is_conscious = True
        
        return old_pain - stats.pain
    
    def calculate_combat_penalties(self, stats: CombatStats, 
                                  injuries: List[Injury]) -> Dict[str, float]:
        """
        Oblicza kary do walki na podstawie stanu postaci.
        
        Args:
            stats: Statystyki postaci
            injuries: Lista kontuzji
        
        Returns:
            Słownik z karami
        """
        penalties = {
            'attack': 0.0,
            'defense': 0.0,
            'speed': 0.0,
            'accuracy': 0.0
        }
        
        # Kary za ból
        if stats.pain > 30:
            pain_penalty = (stats.pain - 30) / 100.0
            penalties['attack'] += pain_penalty * 0.3
            penalties['accuracy'] += pain_penalty * 0.5
            penalties['defense'] += pain_penalty * 0.2
        
        # Kary za wyczerpanie
        if stats.exhaustion > 50:
            exhaustion_penalty = (stats.exhaustion - 50) / 100.0
            penalties['speed'] += exhaustion_penalty * 0.4
            penalties['attack'] += exhaustion_penalty * 0.2
            penalties['defense'] += exhaustion_penalty * 0.3
        
        # Kary za kontuzje
        for injury in injuries:
            if injury.body_part == BodyPart.GLOWA:
                penalties['accuracy'] += injury.severity / 200.0
            elif injury.body_part == BodyPart.TULOW:
                penalties['defense'] += injury.severity / 300.0
            elif injury.body_part in [BodyPart.LEWA_REKA, BodyPart.PRAWA_REKA]:
                penalties['attack'] += injury.severity / 250.0
            elif injury.body_part in [BodyPart.LEWA_NOGA, BodyPart.PRAWA_NOGA]:
                penalties['speed'] += injury.severity / 200.0
        
        # Ogranicz kary do maksimum 90%
        for key in penalties:
            penalties[key] = min(0.9, penalties[key])
        
        return penalties
    
    def apply_character_buffs(self, character, stats: CombatStats) -> None:
        """
        Stosuje buffy i debuffy postaci do statystyk bojowych.
        
        Args:
            character: Postać z buffami/debuffami
            stats: Statystyki bojowe do modyfikacji
        """
        # Zastosuj buffy
        if hasattr(character, 'active_buffs'):
            for buff_name, buff_data in character.active_buffs.items():
                # Szał Bitewny (Wojownik)
                if buff_name == 'BERSERK':
                    stats.damage_multiplier *= buff_data.get('damage_multiplier', 1.0)
                    stats.defense_multiplier *= buff_data.get('defense_multiplier', 1.0)
                
                # Kamienne Ciało (Wojownik)
                elif buff_name == 'STONE_BODY':
                    stats.defense_multiplier *= buff_data.get('defense_multiplier', 1.0)
                    stats.speed_multiplier *= buff_data.get('speed_multiplier', 1.0)
                
                # Mglisty Płaszcz (Łotrzyk)
                elif buff_name == 'MIST_CLOAK':
                    stats.defense_multiplier *= buff_data.get('evasion_multiplier', 1.0)
                
                # Ostry Wzrok (Myśliwy)
                elif buff_name == 'SHARP_SIGHT':
                    stats.accuracy_multiplier *= buff_data.get('accuracy_multiplier', 1.0)
                    stats.critical_chance += buff_data.get('crit_bonus', 0.0)
                
                # Skupienie Rzemieślnika (Rzemieślnik)
                elif buff_name == 'CRAFTING_FOCUS':
                    stats.accuracy_multiplier *= buff_data.get('precision_multiplier', 1.0)
                
                # Tarcza Energii (Mag)
                elif buff_name == 'ENERGY_SHIELD':
                    stats.defense_multiplier *= buff_data.get('damage_reduction', 1.0)
        
        # Zastosuj debuffy
        if hasattr(character, 'active_debuffs'):
            for debuff_name, debuff_data in character.active_debuffs.items():
                # Trucizna (Łotrzyk)
                if debuff_name == 'POISON':
                    stats.health -= debuff_data.get('damage', 0)
                    stats.speed_multiplier *= 0.8
                
                # Pułapka (Myśliwy)
                elif debuff_name == 'TRAPPED':
                    stats.speed_multiplier *= 0.3
                    stats.defense_multiplier *= 0.7
                
                # Rozproszone Zmysły (Mag)
                elif debuff_name == 'DISPERSED_SENSES':
                    stats.accuracy_multiplier *= debuff_data.get('accuracy_penalty', 1.0)
                    stats.defense_multiplier *= debuff_data.get('defense_penalty', 1.0)
    
    def _initialize_techniques(self) -> Dict[str, CombatTechnique]:
        """Inicjalizuje techniki bojowe."""
        techniques = {}
        
        # Techniki dla mieczy
        techniques['ripost'] = CombatTechnique(
            name='riposte',
            polish_name='Riposta',
            type=TechniqueType.PODSTAWOWA,
            weapon_types=[WeaponType.MIECZE_KROTKIE, WeaponType.MIECZE_DLUGIE],
            skill_requirement=5,
            stamina_cost=10,
            damage_multiplier=1.3,
            critical_chance_bonus=0.2,
            special_effects={'counter_attack': True},
            description="Szybki kontratak po udanym parowaniu"
        )
        
        techniques['feint_strike'] = CombatTechnique(
            name='feint_strike',
            polish_name='Finta i Cios',
            type=TechniqueType.KOMBINACJA,
            weapon_types=[WeaponType.MIECZE_KROTKIE, WeaponType.SZTYLETY],
            skill_requirement=12,
            stamina_cost=15,
            combo_chain=['finta', 'atak_podstawowy'],
            damage_multiplier=1.6,
            accuracy_modifier=0.3,
            description="Finta wprowadzając w błąd, po której następuje precyzyjny cios"
        )
        
        techniques['whirlwind'] = CombatTechnique(
            name='whirlwind',
            polish_name='Wirujące Ostrza',
            type=TechniqueType.SPECJALNA,
            weapon_types=[WeaponType.MIECZE_DLUGIE, WeaponType.MIECZE_DWURECZNE],
            skill_requirement=20,
            stamina_cost=25,
            combo_chain=['ciecie_poziome', 'ciecie_poziome'],
            damage_multiplier=2.0,
            special_effects={'area_damage': True, 'dizzy_chance': 0.3},
            description="Seria wirujących cięć"
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
                modifiers['accuracy'] -= 0.1
        
        return modifiers
    
    def execute_technique(self, attacker_stats: 'CombatStats', defender_stats: 'CombatStats',
                         technique_name: str, attacker_skill: int) -> Tuple[bool, str, float]:
        """Wykonuje technikę bojową."""
        if technique_name not in self.combat_techniques:
            return False, "Nieznana technika", 0.0
        
        technique = self.combat_techniques[technique_name]
        
        # Sprawdź czy technika może być wykonana
        if not technique.can_execute(attacker_skill, attacker_stats.stamina, attacker_stats.current_weapon):
            return False, f"Nie można wykonać techniki: {technique.polish_name}", 0.0
        
        # Zużyj stamina
        attacker_stats.stamina -= technique.stamina_cost
        
        # Oblicz obrażenia
        base_damage = attacker_stats.strength * technique.damage_multiplier
        
        # Zastosuj efekty specjalne
        special_message = ""
        for effect, value in technique.special_effects.items():
            if effect == 'bleeding_chance' and random.random() < value:
                special_message += " - cel krwawi"
            elif effect == 'stun_duration' and value > 0:
                defender_stats.is_stunned = True
                defender_stats.stun_duration = value
                special_message += f" - cel ogłuszony na {value} tur"
        
        # Zastosuj obrażenia
        final_damage = base_damage
        defender_stats.health -= final_damage
        
        message = f"Wykonujesz {technique.polish_name} zadając {final_damage:.1f} obrażeń{special_message}"
        
        return True, message, final_damage