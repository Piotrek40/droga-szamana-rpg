"""
Enhanced Skill Progression System for Droga Szamana RPG.
Pure use-based learning with muscle memory, synergies, and degradation.
"""

import random
import math
import json
from typing import Dict, Optional, Tuple, List, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import copy


class SkillCategory(Enum):
    """Kategorie umiejętności."""
    BOJOWE = "bojowe"
    OBRONNE = "obronne"
    DYSTANSOWE = "dystansowe"
    MAGICZNE = "magiczne"
    RZEMIESLNICZE = "rzemieślnicze"
    SPOLECZNE = "społeczne"
    ZLODZIEJSKIE = "złodziejskie"
    PRZETRWANIE = "przetrwanie"
    WIEDZA = "wiedza"
    ATLETYCZNE = "atletyczne"


class SkillName(Enum):
    """Rozszerzona lista umiejętności."""
    # Bojowe
    WALKA_WRECZ = "walka_wręcz"
    SZTYLETY = "sztylety"
    MIECZE = "miecze"
    MIECZE_DWURECZNE = "miecze_dwuręczne"
    TOPORY = "topory"
    TOPORY_DWURECZNE = "topory_dwuręczne"
    MLOTY = "młoty"
    MLOTY_BOJOWE = "młoty_bojowe"
    WLÓCZNIE = "włócznie"
    MACZUGI = "maczugi"
    KIJE_BOJOWE = "kije_bojowe"
    
    # Obronne
    OBRONA = "obrona"
    UNIKI = "uniki"
    PAROWANIE = "parowanie"
    TARCZE = "tarcze"
    PANCERZ_LEKKI = "pancerz_lekki"
    PANCERZ_CIEZKI = "pancerz_ciężki"
    
    # Dystansowe
    LUCZNICTWO = "łucznictwo"
    KUSZE = "kusze"
    PROCE = "proce"
    RZUCANIE = "rzucanie"
    
    # Magiczne (Void Walker)
    MANIPULACJA_PUSTKI = "manipulacja_pustki"
    ODPORNOSC_NA_BOL = "odporność_na_ból"
    MEDYTACJA = "medytacja"
    KONTROLA_ENERGII = "kontrola_energii"
    
    # Rzemieślnicze
    KOWALSTWO = "kowalstwo"
    ZBROJMISTRZOSTWO = "zbrojmistrzostwo"
    LUCZARSTWO = "łuczarstwo"
    ALCHEMIA = "alchemia"
    JUBILERSTWO = "jubilerstwo"
    KRAWIECTWO = "krawiectwo"
    GARBARSTWO = "garbarstwo"
    STOLARSTWO = "stolarstwo"
    GOTOWANIE = "gotowanie"
    
    # Społeczne
    PERSWAZJA = "perswazja"
    OSZUSTWO = "oszustwo"
    ZASTRASZANIE = "zastraszanie"
    HANDEL = "handel"
    PRZYWODZTWO = "przywództwo"
    ETYKIETA = "etykieta"
    WYSTEPY = "występy"
    
    # Złodziejskie
    SKRADANIE = "skradanie"
    KRADZIEŻ_KIESZONKOWA = "kradzież_kieszonkowa"
    WLAMYWANIE = "włamywanie"
    UKRYWANIE = "ukrywanie"
    FALSYFIKATY = "fałszyfikaty"
    PULAPKI = "pułapki"
    
    # Przetrwanie
    TROPIENIE = "tropienie"
    POLOWANIE = "polowanie"
    LOWIENIE_RYB = "łowienie_ryb"
    ZIELARSTWO = "zielarstwo"
    PIERWSZA_POMOC = "pierwsza_pomoc"
    OBOZOWANIE = "obozowanie"
    ORIENTACJA = "orientacja"
    
    # Wiedza
    HISTORIA = "historia"
    RELIGIA = "religia"
    MAGIA = "magia"
    PRZYRODA = "przyroda"
    LOKALNA_WIEDZA = "lokalna_wiedza"
    JĘZYKI = "języki"
    
    # Atletyczne
    WYTRZYMALOSC = "wytrzymałość"
    SILA = "siła"
    ZWINNOSC = "zwinność"
    PLYWANIE = "pływanie"
    WSPINACZKA = "wspinaczka"
    AKROBATYKA = "akrobatyka"
    JEZDZIECTWO = "jeździectwo"


@dataclass
class SkillMemory:
    """Pamięć mięśniowa i doświadczenie w umiejętności."""
    muscle_memory: float = 0.0  # 0-100, jak dobrze ciało pamięta ruchy
    theoretical_knowledge: float = 0.0  # 0-100, wiedza teoretyczna
    practical_experience: float = 0.0  # 0-100, doświadczenie praktyczne
    last_used: Optional[datetime] = None
    degradation_rate: float = 0.01  # Szybkość zapominania
    peak_level: int = 0  # Najwyższy osiągnięty poziom
    
    def apply_degradation(self, days_passed: int):
        """Aplikuje degradację umiejętności z czasem."""
        if days_passed <= 7:
            return  # Brak degradacji w pierwszym tygodniu
        
        degradation = self.degradation_rate * (days_passed - 7)
        
        # Pamięć mięśniowa degraduje wolniej
        self.muscle_memory = max(0, self.muscle_memory - degradation * 0.5)
        
        # Wiedza teoretyczna degraduje średnio
        self.theoretical_knowledge = max(0, self.theoretical_knowledge - degradation)
        
        # Praktyczne doświadczenie degraduje najszybciej
        self.practical_experience = max(0, self.practical_experience - degradation * 1.5)
    
    def get_effective_bonus(self) -> float:
        """Oblicza efektywny bonus z pamięci."""
        return (self.muscle_memory * 0.5 + 
                self.theoretical_knowledge * 0.2 + 
                self.practical_experience * 0.3) / 100.0


@dataclass
class SkillTechnique:
    """Odkryta technika w ramach umiejętności."""
    name: str
    description: str
    discovered: bool = False
    mastery: float = 0.0  # 0-100
    requirements: Dict[str, int] = field(default_factory=dict)  # Wymagane poziomy
    bonuses: Dict[str, float] = field(default_factory=dict)  # Bonusy gdy opanowana


@dataclass
class EnhancedSkill:
    """Rozszerzona reprezentacja umiejętności."""
    name: str
    polish_name: str
    category: SkillCategory
    level: int = 0
    progress: float = 0.0
    memory: SkillMemory = field(default_factory=SkillMemory)
    synergies: Dict[str, float] = field(default_factory=dict)  # Synergie z innymi umiejętnościami
    techniques: Dict[str, SkillTechnique] = field(default_factory=dict)  # Odkryte techniki
    specialization: Optional[str] = None  # Specjalizacja w ramach umiejętności
    uses_today: int = 0
    total_uses: int = 0
    learning_events: List[Dict[str, Any]] = field(default_factory=list)  # Historia nauki
    
    def get_effective_level(self, modifiers: Dict[str, float] = None) -> int:
        """Oblicza efektywny poziom z wszystkimi modyfikatorami."""
        base_level = self.level
        
        # Bonus z pamięci
        memory_bonus = self.memory.get_effective_bonus() * 10
        
        # Bonus ze specjalizacji
        spec_bonus = 5 if self.specialization else 0
        
        # Bonus z technik
        technique_bonus = sum(
            tech.mastery / 20 for tech in self.techniques.values() 
            if tech.discovered
        )
        
        # Modyfikatory zewnętrzne
        external_mods = sum(modifiers.values()) if modifiers else 0
        
        return int(base_level + memory_bonus + spec_bonus + technique_bonus + external_mods)
    
    def can_discover_technique(self, technique_name: str) -> bool:
        """Sprawdza czy można odkryć technikę."""
        if technique_name not in self.techniques:
            return False
        
        technique = self.techniques[technique_name]
        if technique.discovered:
            return False
        
        # Sprawdź wymagania
        for req_skill, req_level in technique.requirements.items():
            if req_skill == "self" and self.level < req_level:
                return False
        
        return True
    
    def try_discover_technique(self) -> Optional[str]:
        """Próbuje odkryć nową technikę."""
        for tech_name, technique in self.techniques.items():
            if self.can_discover_technique(tech_name):
                # Szansa na odkrycie
                discovery_chance = 0.01 * (self.level / max(technique.requirements.get("self", 10), 1))
                if random.random() < discovery_chance:
                    technique.discovered = True
                    return tech_name
        return None


class EnhancedSkillSystem:
    """Rozszerzony system umiejętności z pełną funkcjonalnością."""
    
    def __init__(self):
        """Inicjalizacja systemu."""
        self.skills: Dict[SkillName, EnhancedSkill] = {}
        self.skill_synergies = self._initialize_synergies()
        self.skill_techniques = self._initialize_techniques()
        self.learning_conditions: Dict[str, float] = {}  # Warunki wpływające na naukę
        self.current_date = datetime.now()  # Śledzenie czasu dla degradacji
        
        self._initialize_skills()
    
    def _initialize_skills(self):
        """Tworzy wszystkie umiejętności."""
        skill_definitions = {
            # Bojowe
            SkillName.WALKA_WRECZ: ("Walka wręcz", SkillCategory.BOJOWE),
            SkillName.SZTYLETY: ("Sztylety", SkillCategory.BOJOWE),
            SkillName.MIECZE: ("Miecze", SkillCategory.BOJOWE),
            SkillName.MIECZE_DWURECZNE: ("Miecze dwuręczne", SkillCategory.BOJOWE),
            SkillName.TOPORY: ("Topory", SkillCategory.BOJOWE),
            SkillName.TOPORY_DWURECZNE: ("Topory dwuręczne", SkillCategory.BOJOWE),
            SkillName.MLOTY: ("Młoty", SkillCategory.BOJOWE),
            SkillName.MLOTY_BOJOWE: ("Młoty bojowe", SkillCategory.BOJOWE),
            SkillName.WLÓCZNIE: ("Włócznie", SkillCategory.BOJOWE),
            SkillName.MACZUGI: ("Maczugi", SkillCategory.BOJOWE),
            SkillName.KIJE_BOJOWE: ("Kije bojowe", SkillCategory.BOJOWE),
            
            # Obronne
            SkillName.OBRONA: ("Obrona", SkillCategory.OBRONNE),
            SkillName.UNIKI: ("Uniki", SkillCategory.OBRONNE),
            SkillName.PAROWANIE: ("Parowanie", SkillCategory.OBRONNE),
            SkillName.TARCZE: ("Tarcze", SkillCategory.OBRONNE),
            SkillName.PANCERZ_LEKKI: ("Pancerz lekki", SkillCategory.OBRONNE),
            SkillName.PANCERZ_CIEZKI: ("Pancerz ciężki", SkillCategory.OBRONNE),
            
            # Dystansowe
            SkillName.LUCZNICTWO: ("Łucznictwo", SkillCategory.DYSTANSOWE),
            SkillName.KUSZE: ("Kusze", SkillCategory.DYSTANSOWE),
            SkillName.PROCE: ("Proce", SkillCategory.DYSTANSOWE),
            SkillName.RZUCANIE: ("Rzucanie", SkillCategory.DYSTANSOWE),
            
            # Magiczne
            SkillName.MANIPULACJA_PUSTKI: ("Manipulacja Pustki", SkillCategory.MAGICZNE),
            SkillName.ODPORNOSC_NA_BOL: ("Odporność na ból", SkillCategory.MAGICZNE),
            SkillName.MEDYTACJA: ("Medytacja", SkillCategory.MAGICZNE),
            SkillName.KONTROLA_ENERGII: ("Kontrola energii", SkillCategory.MAGICZNE),
            
            # Rzemieślnicze
            SkillName.KOWALSTWO: ("Kowalstwo", SkillCategory.RZEMIESLNICZE),
            SkillName.ZBROJMISTRZOSTWO: ("Zbrojmistrzostwo", SkillCategory.RZEMIESLNICZE),
            SkillName.LUCZARSTWO: ("Łuczarstwo", SkillCategory.RZEMIESLNICZE),
            SkillName.ALCHEMIA: ("Alchemia", SkillCategory.RZEMIESLNICZE),
            SkillName.JUBILERSTWO: ("Jubilerstwo", SkillCategory.RZEMIESLNICZE),
            SkillName.KRAWIECTWO: ("Krawiectwo", SkillCategory.RZEMIESLNICZE),
            SkillName.GARBARSTWO: ("Garbarstwo", SkillCategory.RZEMIESLNICZE),
            SkillName.STOLARSTWO: ("Stolarstwo", SkillCategory.RZEMIESLNICZE),
            SkillName.GOTOWANIE: ("Gotowanie", SkillCategory.RZEMIESLNICZE),
            
            # Społeczne
            SkillName.PERSWAZJA: ("Perswazja", SkillCategory.SPOLECZNE),
            SkillName.OSZUSTWO: ("Oszustwo", SkillCategory.SPOLECZNE),
            SkillName.ZASTRASZANIE: ("Zastraszanie", SkillCategory.SPOLECZNE),
            SkillName.HANDEL: ("Handel", SkillCategory.SPOLECZNE),
            SkillName.PRZYWODZTWO: ("Przywództwo", SkillCategory.SPOLECZNE),
            SkillName.ETYKIETA: ("Etykieta", SkillCategory.SPOLECZNE),
            SkillName.WYSTEPY: ("Występy", SkillCategory.SPOLECZNE),
            
            # Złodziejskie
            SkillName.SKRADANIE: ("Skradanie", SkillCategory.ZLODZIEJSKIE),
            SkillName.KRADZIEŻ_KIESZONKOWA: ("Kradzież kieszonkowa", SkillCategory.ZLODZIEJSKIE),
            SkillName.WLAMYWANIE: ("Włamywanie", SkillCategory.ZLODZIEJSKIE),
            SkillName.UKRYWANIE: ("Ukrywanie", SkillCategory.ZLODZIEJSKIE),
            SkillName.FALSYFIKATY: ("Fałszyfikaty", SkillCategory.ZLODZIEJSKIE),
            SkillName.PULAPKI: ("Pułapki", SkillCategory.ZLODZIEJSKIE),
            
            # Przetrwanie
            SkillName.TROPIENIE: ("Tropienie", SkillCategory.PRZETRWANIE),
            SkillName.POLOWANIE: ("Polowanie", SkillCategory.PRZETRWANIE),
            SkillName.LOWIENIE_RYB: ("Łowienie ryb", SkillCategory.PRZETRWANIE),
            SkillName.ZIELARSTWO: ("Zielarstwo", SkillCategory.PRZETRWANIE),
            SkillName.PIERWSZA_POMOC: ("Pierwsza pomoc", SkillCategory.PRZETRWANIE),
            SkillName.OBOZOWANIE: ("Obozowanie", SkillCategory.PRZETRWANIE),
            SkillName.ORIENTACJA: ("Orientacja", SkillCategory.PRZETRWANIE),
            
            # Wiedza
            SkillName.HISTORIA: ("Historia", SkillCategory.WIEDZA),
            SkillName.RELIGIA: ("Religia", SkillCategory.WIEDZA),
            SkillName.MAGIA: ("Magia", SkillCategory.WIEDZA),
            SkillName.PRZYRODA: ("Przyroda", SkillCategory.WIEDZA),
            SkillName.LOKALNA_WIEDZA: ("Lokalna wiedza", SkillCategory.WIEDZA),
            SkillName.JĘZYKI: ("Języki", SkillCategory.WIEDZA),
            
            # Atletyczne
            SkillName.WYTRZYMALOSC: ("Wytrzymałość", SkillCategory.ATLETYCZNE),
            SkillName.SILA: ("Siła", SkillCategory.ATLETYCZNE),
            SkillName.ZWINNOSC: ("Zwinność", SkillCategory.ATLETYCZNE),
            SkillName.PLYWANIE: ("Pływanie", SkillCategory.ATLETYCZNE),
            SkillName.WSPINACZKA: ("Wspinaczka", SkillCategory.ATLETYCZNE),
            SkillName.AKROBATYKA: ("Akrobatyka", SkillCategory.ATLETYCZNE),
            SkillName.JEZDZIECTWO: ("Jeździectwo", SkillCategory.ATLETYCZNE),
        }
        
        for skill_name, (polish_name, category) in skill_definitions.items():
            skill = EnhancedSkill(
                name=skill_name.value,
                polish_name=polish_name,
                category=category,
                level=random.randint(0, 3),  # Losowy początkowy poziom
                synergies=self.skill_synergies.get(skill_name, {}),
                techniques=copy.deepcopy(self.skill_techniques.get(skill_name, {}))
            )
            self.skills[skill_name] = skill
    
    def _initialize_synergies(self) -> Dict[SkillName, Dict[SkillName, float]]:
        """Definiuje synergie między umiejętnościami."""
        synergies = {
            # Synergie broni jednoręcznych
            SkillName.MIECZE: {
                SkillName.SZTYLETY: 0.3,
                SkillName.PAROWANIE: 0.2,
                SkillName.MIECZE_DWURECZNE: 0.4
            },
            SkillName.SZTYLETY: {
                SkillName.ZWINNOSC: 0.3,
                SkillName.SKRADANIE: 0.2,
                SkillName.MIECZE: 0.2
            },
            
            # Synergie broni dwuręcznych
            SkillName.MIECZE_DWURECZNE: {
                SkillName.MIECZE: 0.4,
                SkillName.SILA: 0.3,
                SkillName.TOPORY_DWURECZNE: 0.2
            },
            SkillName.TOPORY_DWURECZNE: {
                SkillName.TOPORY: 0.5,
                SkillName.SILA: 0.4,
                SkillName.MIECZE_DWURECZNE: 0.2
            },
            
            # Synergie obronne
            SkillName.OBRONA: {
                SkillName.TARCZE: 0.4,
                SkillName.PAROWANIE: 0.3,
                SkillName.UNIKI: 0.3
            },
            SkillName.UNIKI: {
                SkillName.ZWINNOSC: 0.5,
                SkillName.AKROBATYKA: 0.3,
                SkillName.OBRONA: 0.2
            },
            SkillName.PAROWANIE: {
                SkillName.MIECZE: 0.3,
                SkillName.OBRONA: 0.3,
                SkillName.TARCZE: 0.2
            },
            
            # Synergie łucznicze
            SkillName.LUCZNICTWO: {
                SkillName.KUSZE: 0.4,
                SkillName.RZUCANIE: 0.2,
                SkillName.POLOWANIE: 0.3
            },
            
            # Synergie rzemieślnicze
            SkillName.KOWALSTWO: {
                SkillName.ZBROJMISTRZOSTWO: 0.5,
                SkillName.SILA: 0.2,
                SkillName.WYTRZYMALOSC: 0.1
            },
            SkillName.ZBROJMISTRZOSTWO: {
                SkillName.KOWALSTWO: 0.5,
                SkillName.PANCERZ_LEKKI: 0.2,
                SkillName.PANCERZ_CIEZKI: 0.2
            },
            
            # Synergie społeczne
            SkillName.PERSWAZJA: {
                SkillName.OSZUSTWO: 0.3,
                SkillName.HANDEL: 0.4,
                SkillName.PRZYWODZTWO: 0.3
            },
            SkillName.HANDEL: {
                SkillName.PERSWAZJA: 0.4,
                SkillName.OSZUSTWO: 0.2,
                SkillName.LOKALNA_WIEDZA: 0.2
            },
            
            # Synergie złodziejskie
            SkillName.SKRADANIE: {
                SkillName.UKRYWANIE: 0.5,
                SkillName.KRADZIEŻ_KIESZONKOWA: 0.3,
                SkillName.ZWINNOSC: 0.3
            },
            SkillName.KRADZIEŻ_KIESZONKOWA: {
                SkillName.SKRADANIE: 0.3,
                SkillName.ZWINNOSC: 0.4,
                SkillName.OSZUSTWO: 0.2
            },
            
            # Synergie Void Walker
            SkillName.MANIPULACJA_PUSTKI: {
                SkillName.MEDYTACJA: 0.4,
                SkillName.KONTROLA_ENERGII: 0.5,
                SkillName.ODPORNOSC_NA_BOL: 0.3
            },
            SkillName.ODPORNOSC_NA_BOL: {
                SkillName.WYTRZYMALOSC: 0.3,
                SkillName.MEDYTACJA: 0.3,
                SkillName.MANIPULACJA_PUSTKI: 0.2
            },
        }
        
        return synergies
    
    def _initialize_techniques(self) -> Dict[SkillName, Dict[str, SkillTechnique]]:
        """Definiuje techniki dla umiejętności."""
        techniques = {
            SkillName.MIECZE: {
                'perfekcyjne_ciecie': SkillTechnique(
                    name='Perfekcyjne Cięcie',
                    description='Idealne cięcie trafiające w słaby punkt',
                    requirements={'self': 20},
                    bonuses={'critical': 0.15, 'damage': 1.2}
                ),
                'taniec_ostrzy': SkillTechnique(
                    name='Taniec Ostrzy',
                    description='Seria płynnych cięć',
                    requirements={'self': 35, SkillName.ZWINNOSC.value: 20},
                    bonuses={'attack_speed': 1.3, 'dodge': 0.1}
                ),
                'riposta_mistrza': SkillTechnique(
                    name='Riposta Mistrza',
                    description='Kontratak po udanym parowaniu',
                    requirements={'self': 50, SkillName.PAROWANIE.value: 30},
                    bonuses={'counter': 0.5, 'damage': 1.5}
                ),
            },
            SkillName.LUCZNICTWO: {
                'strzal_snajpera': SkillTechnique(
                    name='Strzał Snajpera',
                    description='Precyzyjny strzał na daleką odległość',
                    requirements={'self': 25},
                    bonuses={'range': 1.5, 'accuracy': 0.3}
                ),
                'szybkie_naciagniecie': SkillTechnique(
                    name='Szybkie Naciągnięcie',
                    description='Technika szybkiego strzelania',
                    requirements={'self': 15, SkillName.SILA.value: 10},
                    bonuses={'attack_speed': 1.4}
                ),
                'strzal_w_ruch': SkillTechnique(
                    name='Strzał w Ruch',
                    description='Celny strzał podczas ruchu',
                    requirements={'self': 40, SkillName.ZWINNOSC.value: 25},
                    bonuses={'mobile_accuracy': 0.8}
                ),
            },
            SkillName.SKRADANIE: {
                'cien_w_cieniu': SkillTechnique(
                    name='Cień w Cieniu',
                    description='Perfekcyjne wtopienie się w cienie',
                    requirements={'self': 30},
                    bonuses={'stealth': 1.5}
                ),
                'cichy_krok': SkillTechnique(
                    name='Cichy Krok',
                    description='Bezgłośne poruszanie się',
                    requirements={'self': 20},
                    bonuses={'noise': -0.8}
                ),
            },
            SkillName.KOWALSTWO: {
                'hartowanie_mistrzowskie': SkillTechnique(
                    name='Hartowanie Mistrzowskie',
                    description='Technika tworzenia wyjątkowo twardej stali',
                    requirements={'self': 40},
                    bonuses={'durability': 1.5, 'sharpness': 1.2}
                ),
                'damascenska_stal': SkillTechnique(
                    name='Damasceńska Stal',
                    description='Sztuka tworzenia wzorzystej stali',
                    requirements={'self': 60},
                    bonuses={'quality': 2.0, 'value': 3.0}
                ),
            },
            SkillName.MANIPULACJA_PUSTKI: {
                'dotyk_nicosci': SkillTechnique(
                    name='Dotyk Nicości',
                    description='Kanalizowanie czystej energii Pustki',
                    requirements={'self': 30, SkillName.MEDYTACJA.value: 20},
                    bonuses={'void_damage': 1.5, 'void_cost': -0.2}
                ),
                'brama_cieni': SkillTechnique(
                    name='Brama Cieni',
                    description='Tworzenie portali przez Pustkę',
                    requirements={'self': 50, SkillName.KONTROLA_ENERGII.value: 40},
                    bonuses={'teleport_range': 2.0, 'void_cost': -0.3}
                ),
            },
        }
        
        return techniques
    
    def use_skill(self, skill_name: SkillName, difficulty: int, 
                  conditions: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Używa umiejętności z pełnym systemem progresji.
        
        Args:
            skill_name: Nazwa umiejętności
            difficulty: Trudność zadania
            conditions: Warunki użycia (ból, kontuzje, środowisko, etc.)
        
        Returns:
            (sukces, opis, dodatkowe_efekty)
        """
        skill = self.skills.get(skill_name)
        if not skill:
            return False, f"Nieznana umiejętność: {skill_name.value}", {}
        
        conditions = conditions or {}
        
        # Oblicz modyfikatory
        modifiers = self._calculate_modifiers(skill, conditions)
        
        # Efektywny poziom umiejętności
        effective_level = skill.get_effective_level(modifiers)
        
        # Oblicz szansę sukcesu
        base_chance = self._calculate_success_chance(effective_level, difficulty)
        
        # Uwzględnij synergie
        synergy_bonus = self._calculate_synergy_bonus(skill)
        final_chance = min(0.95, base_chance + synergy_bonus)
        
        # Rzut na sukces
        roll = random.random()
        success = roll < final_chance
        
        # Aktualizuj statystyki
        skill.uses_today += 1
        skill.total_uses += 1
        skill.memory.last_used = self.current_date
        
        # Sprawdź możliwość nauki
        learning_result = self._try_learn(skill, difficulty, success, conditions)
        
        # Sprawdź odkrycie techniki
        discovered_technique = skill.try_discover_technique()
        
        # Buduj opis wyniku
        result_msg = self._build_result_message(skill, success, learning_result, discovered_technique)
        
        # Dodatkowe efekty
        effects = {
            'effective_level': effective_level,
            'success_chance': final_chance,
            'roll': roll,
            'learning': learning_result,
            'discovered_technique': discovered_technique,
            'synergy_bonus': synergy_bonus
        }
        
        # Zapisz wydarzenie
        skill.learning_events.append({
            'date': self.current_date,
            'difficulty': difficulty,
            'success': success,
            'learned': learning_result.get('improved', False)
        })
        
        return success, result_msg, effects
    
    def _calculate_modifiers(self, skill: EnhancedSkill, conditions: Dict[str, Any]) -> Dict[str, float]:
        """Oblicza modyfikatory do umiejętności."""
        modifiers = {}
        
        # Kara za ból
        if 'pain' in conditions:
            pain_level = conditions['pain']
            if pain_level > 30:
                modifiers['pain'] = -(pain_level - 30) / 100.0 * 20
        
        # Kara za kontuzje
        if 'injuries' in conditions:
            injury_penalty = 0
            for injury in conditions['injuries']:
                if skill.category in [SkillCategory.BOJOWE, SkillCategory.ATLETYCZNE]:
                    injury_penalty += injury.get('severity', 0) / 200.0 * 10
            modifiers['injuries'] = -injury_penalty
        
        # Kara za zmęczenie
        if 'exhaustion' in conditions:
            exhaustion = conditions['exhaustion']
            if exhaustion > 50:
                modifiers['exhaustion'] = -(exhaustion - 50) / 100.0 * 15
        
        # Bonus za sprzęt
        if 'equipment_quality' in conditions:
            quality = conditions['equipment_quality']
            quality_bonuses = {
                'słaba': -5,
                'zwykła': 0,
                'dobra': 3,
                'mistrzowska': 7,
                'legendarna': 12
            }
            modifiers['equipment'] = quality_bonuses.get(quality, 0)
        
        # Modyfikatory środowiskowe
        if 'environment' in conditions:
            env_penalty = 0
            for factor in conditions['environment']:
                if factor == 'darkness' and skill.category == SkillCategory.DYSTANSOWE:
                    env_penalty += 10
                elif factor == 'rain' and skill.name == SkillName.LUCZNICTWO.value:
                    env_penalty += 5
            modifiers['environment'] = -env_penalty
        
        return modifiers
    
    def _calculate_success_chance(self, effective_level: int, difficulty: int) -> float:
        """Oblicza szansę sukcesu z krzywą logarytmiczną."""
        level_diff = effective_level - difficulty
        
        # Krzywa logarytmiczna dla bardziej realistycznego rozkładu
        if level_diff >= 0:
            # Łatwiejsze zadanie
            base_chance = 0.5 + (1 - math.exp(-level_diff / 20)) * 0.45
        else:
            # Trudniejsze zadanie
            base_chance = 0.5 * math.exp(level_diff / 30)
        
        return max(0.05, min(0.95, base_chance))
    
    def _calculate_synergy_bonus(self, skill: EnhancedSkill) -> float:
        """Oblicza bonus z synergii."""
        total_bonus = 0.0
        
        for synergy_skill_name, synergy_strength in skill.synergies.items():
            if isinstance(synergy_skill_name, str):
                # Konwertuj string na SkillName jeśli potrzeba
                try:
                    synergy_enum = SkillName(synergy_skill_name)
                except ValueError:
                    continue
            else:
                synergy_enum = synergy_skill_name
            
            if synergy_enum in self.skills:
                synergy_skill = self.skills[synergy_enum]
                # Bonus proporcjonalny do poziomu umiejętności synergicznej
                total_bonus += (synergy_skill.level / 100.0) * synergy_strength * 0.1
        
        return min(0.2, total_bonus)  # Max 20% bonus z synergii
    
    def _try_learn(self, skill: EnhancedSkill, difficulty: int, success: bool, 
                   conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Próbuje nauczyć się z doświadczenia."""
        result = {
            'improved': False,
            'progress_gained': 0,
            'muscle_memory_gained': 0,
            'theory_gained': 0,
            'practice_gained': 0
        }
        
        # Oblicz optymalność trudności
        level_diff = abs(skill.level - difficulty)
        
        if level_diff > 50:
            # Zbyt trudne lub zbyt łatwe
            return result
        
        # Szansa na naukę
        if level_diff < 5:
            # Zbyt łatwe
            learn_chance = 0.02
        elif level_diff <= 15:
            # Optymalne
            learn_chance = 0.15
            if not success:
                learn_chance *= 1.5  # Uczymy się na błędach
        elif level_diff <= 30:
            # Trudne ale wykonalne
            learn_chance = 0.08
        else:
            # Bardzo trudne
            learn_chance = 0.04
        
        # Modyfikatory warunków nauki
        if conditions.get('has_teacher'):
            learn_chance *= 2.0
        if conditions.get('perfect_conditions'):
            learn_chance *= 1.5
        if conditions.get('distracted'):
            learn_chance *= 0.5
        
        # Logarytmiczny spadek przy wyższych poziomach
        level_penalty = math.log10(skill.level + 10) / 2.0
        learn_chance /= level_penalty
        
        # Rzut na naukę
        if random.random() < learn_chance:
            # Oblicz postęp
            base_progress = random.uniform(3, 10)
            
            # Różne aspekty nauki
            if success:
                # Sukces - więcej pamięci mięśniowej
                skill.memory.muscle_memory = min(100, skill.memory.muscle_memory + base_progress * 0.5)
                skill.memory.practical_experience = min(100, skill.memory.practical_experience + base_progress * 0.3)
                result['muscle_memory_gained'] = base_progress * 0.5
                result['practice_gained'] = base_progress * 0.3
            else:
                # Porażka - więcej wiedzy teoretycznej
                skill.memory.theoretical_knowledge = min(100, skill.memory.theoretical_knowledge + base_progress * 0.4)
                result['theory_gained'] = base_progress * 0.4
            
            # Dodaj postęp
            progress_gain = base_progress * (1 + skill.memory.get_effective_bonus())
            skill.progress += progress_gain
            result['progress_gained'] = progress_gain
            
            # Sprawdź awans poziomu
            if skill.progress >= 100:
                skill.level += 1
                skill.progress -= 100
                skill.memory.peak_level = max(skill.memory.peak_level, skill.level)
                result['improved'] = True
                
                # Przy awansie zwiększ też pamięć
                skill.memory.muscle_memory = min(100, skill.memory.muscle_memory + 10)
                skill.memory.theoretical_knowledge = min(100, skill.memory.theoretical_knowledge + 10)
                skill.memory.practical_experience = min(100, skill.memory.practical_experience + 10)
        
        return result
    
    def _build_result_message(self, skill: EnhancedSkill, success: bool, 
                              learning_result: Dict[str, Any], 
                              discovered_technique: Optional[str]) -> str:
        """Buduje komunikat wyniku."""
        if success:
            msg = f"✓ Sukces w {skill.polish_name}!"
        else:
            msg = f"✗ Porażka w {skill.polish_name}."
        
        if learning_result['improved']:
            msg += f" 📈 UMIEJĘTNOŚĆ WZROSŁA DO POZIOMU {skill.level}!"
        elif learning_result['progress_gained'] > 0:
            msg += f" (postęp: +{learning_result['progress_gained']:.1f}%)"
        
        if discovered_technique:
            technique = skill.techniques[discovered_technique]
            msg += f" 🎯 ODKRYTO TECHNIKĘ: {technique.name}!"
        
        return msg
    
    def apply_time_degradation(self, days_passed: int):
        """Aplikuje degradację umiejętności z czasem."""
        for skill in self.skills.values():
            if skill.memory.last_used:
                days_since_use = (self.current_date - skill.memory.last_used).days
                if days_since_use > days_passed:
                    skill.memory.apply_degradation(days_since_use)
                    
                    # Jeśli pamięć bardzo słaba, może spaść poziom
                    if skill.memory.get_effective_bonus() < 0.1 and skill.level > 0:
                        if random.random() < 0.1:  # 10% szans na utratę poziomu
                            skill.level -= 1
                            skill.progress = 50  # Zaczynamy od połowy
    
    def get_skill_recommendations(self, skill_name: SkillName) -> List[str]:
        """Zwraca rekomendacje treningowe dla umiejętności."""
        skill = self.skills.get(skill_name)
        if not skill:
            return []
        
        recommendations = []
        
        # Rekomenduj optymalne trudności
        optimal_min = skill.level + 5
        optimal_max = skill.level + 15
        recommendations.append(f"Trenuj z trudnością {optimal_min}-{optimal_max} dla najlepszych efektów")
        
        # Rekomenduj synergiczne umiejętności
        for synergy_skill in skill.synergies.keys():
            recommendations.append(f"Rozwijaj {synergy_skill} dla bonusu synergii")
        
        # Rekomenduj techniki do odkrycia
        for tech_name, technique in skill.techniques.items():
            if not technique.discovered and skill.level >= technique.requirements.get('self', 999) - 5:
                recommendations.append(f"Blisko odkrycia techniki: {technique.name}")
        
        return recommendations
    
    def get_mastery_level(self, skill_name: SkillName) -> str:
        """Zwraca słowny poziom mistrzostwa."""
        skill = self.skills.get(skill_name)
        if not skill:
            return "nieznany"
        
        level = skill.level
        if level == 0:
            return "niewprawny"
        elif level < 10:
            return "nowicjusz"
        elif level < 25:
            return "uczeń"
        elif level < 40:
            return "czeladnik"
        elif level < 60:
            return "rzemieślnik"
        elif level < 80:
            return "mistrz"
        elif level < 95:
            return "arcymistrz"
        else:
            return "legenda"