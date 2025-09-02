"""
System umiejętności dla Droga Szamana RPG.
Każda umiejętność rozwija się TYLKO przez praktykę, bez wydawania punktów doświadczenia.
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
    GEOGRAFIA = "geografia"
    RELIGIA = "religia"
    ARCHITEKTURA = "architektura"
    INŻYNIERIA = "inżynieria"
    MATEMATYKA = "matematyka"
    LITERATURA = "literatura"
    
    # Atletyczne
    WYTRZYMALOSC = "wytrzymalosc"
    SILA = "siła"
    ZWROTNOSC = "zwinność"
    GIMNASTYKA = "gimnastyka"
    PLYWANIE = "pływanie"
    WDRAPYWANIE = "wdrapywanie"
    AKROBACJA = "akrobacja"
    
    # Stare nazwy dla kompatybilności
    MEDYCYNA = "pierwsza_pomoc"  # Alias


@dataclass
class SkillSynergy:
    """Synergia między umiejętnościami."""
    target_skill: SkillName
    bonus_multiplier: float
    max_level: int  # Maksymalny poziom synergii


@dataclass  
class MuscleMemoryEntry:
    """Wpis pamięci mięśniowej dla konkretnej akcji."""
    action_signature: str  # Hash akcji (typ + kontekst)
    repetitions: int = 0
    success_rate: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)
    muscle_memory_bonus: float = 0.0


@dataclass
class Skill:
    """Rozszerzona reprezentacja umiejętności z pamięcią mięśniową i synergiami."""
    name: str
    polish_name: str
    category: SkillCategory
    level: int = 0
    progress: float = 0.0  # Postęp do następnego poziomu (0.0 - 100.0)
    uses_today: int = 0  # Liczba użyć dzisiaj (do limitowania nauki)
    total_uses: int = 0  # Całkowita liczba użyć
    last_difficulty_practiced: int = 0  # Ostatnia trudność ćwiczona
    
    # Enhanced features
    muscle_memory: Dict[str, MuscleMemoryEntry] = field(default_factory=dict)
    synergies: List[SkillSynergy] = field(default_factory=list)
    degradation_rate: float = 0.001  # Jak szybko umiejętność się pogarsza bez użycia
    last_used: datetime = field(default_factory=datetime.now)
    natural_talent: float = 1.0  # Naturalny talent (0.5 - 2.0)
    learning_fatigue: float = 0.0  # Zmęczenie uczeniem (0.0 - 1.0)
    specializations: Set[str] = field(default_factory=set)  # Specjalizacje w umiejętności
    teacher_bonus: float = 0.0  # Bonus od nauczyciela
    practice_quality: float = 1.0  # Jakość ostatniej praktyki
    
    def get_effective_level(self, pain_penalty: float = 0.0, injury_penalty: float = 0.0) -> int:
        """
        Zwraca efektywny poziom umiejętności po uwzględnieniu kar.
        
        Args:
            pain_penalty: Kara za ból (0.0 - 1.0)
            injury_penalty: Kara za kontuzje (0.0 - 1.0)
        
        Returns:
            Efektywny poziom umiejętności
        """
        base_level = self.level
        total_penalty = pain_penalty + injury_penalty
        effective = int(base_level * (1.0 - min(total_penalty, 0.9)))  # Max 90% kary
        return max(0, effective)
    
    def get_success_chance(self, difficulty: int, modifiers: float = 0.0) -> float:
        """
        Oblicza szansę sukcesu dla danej trudności.
        
        Args:
            difficulty: Trudność zadania (0-100)
            modifiers: Dodatkowe modyfikatory (-1.0 do 1.0)
        
        Returns:
            Szansa sukcesu (0.0 - 1.0)
        """
        skill_diff = self.level - difficulty
        base_chance = 0.5 + (skill_diff / 100.0)
        
        # Dodaj modyfikatory
        final_chance = base_chance + modifiers
        
        # Ogranicz do zakresu 0.05 - 0.95 (zawsze jest szansa na sukces/porażkę)
        return max(0.05, min(0.95, final_chance))
    
    def can_improve(self, difficulty: int) -> bool:
        """
        Sprawdza czy umiejętność może się poprawić przy danej trudności.
        
        Args:
            difficulty: Trudność zadania
        
        Returns:
            True jeśli może się uczyć
        """
        # Nie można się uczyć z zadań zbyt łatwych lub zbyt trudnych
        skill_diff = abs(self.level - difficulty)
        
        # Optymalna różnica to 5-15 poziomów
        if skill_diff < 5:
            return self.uses_today < 100  # Łatwe zadania - limit użyć
        elif skill_diff <= 30:
            return True  # Optymalna trudność
        else:
            return skill_diff <= 50  # Bardzo trudne - mała szansa
    
    def get_muscle_memory_bonus(self, action_signature: str) -> float:
        """Pobiera bonus pamięci mięśniowej dla konkretnej akcji."""
        if action_signature in self.muscle_memory:
            entry = self.muscle_memory[action_signature]
            # Bonus rośnie z powtórzeniami, ale z malejącymi przyrostami
            bonus = min(0.3, entry.repetitions * 0.01)  # Max 30% bonusu
            # Zmniejsza się z czasem nieużywania
            days_unused = (datetime.now() - entry.last_used).days
            decay = max(0.5, 1.0 - (days_unused * 0.02))
            return bonus * decay
        return 0.0
    
    def update_muscle_memory(self, action_signature: str, success: bool):
        """Aktualizuje pamięć mięśniową po wykonaniu akcji."""
        if action_signature not in self.muscle_memory:
            self.muscle_memory[action_signature] = MuscleMemoryEntry(action_signature)
        
        entry = self.muscle_memory[action_signature]
        entry.repetitions += 1
        entry.last_used = datetime.now()
        
        # Aktualizuj współczynnik sukcesu (średnia ważona)
        weight = min(0.1, 1.0 / entry.repetitions)
        if success:
            entry.success_rate = entry.success_rate * (1 - weight) + 1.0 * weight
        else:
            entry.success_rate = entry.success_rate * (1 - weight)
            
        entry.muscle_memory_bonus = min(0.3, entry.repetitions * 0.005)
    
    def get_synergy_bonus(self, skill_system: 'SkillSystem') -> float:
        """Oblicza bonus z synergii między umiejętnościami."""
        total_bonus = 0.0
        
        for synergy in self.synergies:
            other_skill = skill_system.get_skill(synergy.target_skill)
            if other_skill:
                # Bonus to procent od poziomu synergetycznej umiejętności
                bonus_level = min(synergy.max_level, other_skill.level)
                bonus = bonus_level * synergy.bonus_multiplier * 0.01
                total_bonus += bonus
        
        return min(0.5, total_bonus)  # Maksymalny bonus 50%
    
    def apply_degradation(self, days_passed: int):
        """Stosuje degradację umiejętności przez nieużywanie."""
        if days_passed == 0:
            return
            
        days_unused = (datetime.now() - self.last_used).days
        if days_unused > 7:  # Zaczyna się po tygodniu
            degradation = self.degradation_rate * days_unused * days_passed
            
            # Wyższe umiejętności degradują wolniej
            resistance = 1.0 - (self.level * 0.01)  # 1% redukcji na poziom
            degradation *= resistance
            
            self.progress -= degradation * 100
            if self.progress < 0 and self.level > 0:
                self.level -= 1
                self.progress = max(0, 100 + self.progress)
    
    def get_learning_efficiency(self) -> float:
        """Oblicza efektywność uczenia się uwzględniającą zmęczenie i talent."""
        base_efficiency = self.natural_talent
        
        # Zmęczenie uczeniem się
        fatigue_penalty = self.learning_fatigue * 0.5
        
        # Bonus od nauczyciela
        teacher_bonus = self.teacher_bonus
        
        # Jakość praktyki
        practice_modifier = self.practice_quality
        
        total_efficiency = base_efficiency * (1 - fatigue_penalty + teacher_bonus) * practice_modifier
        return max(0.1, min(3.0, total_efficiency))  # Zakres 10% - 300%
    
    def add_specialization(self, specialization: str):
        """Dodaje specjalizację do umiejętności."""
        self.specializations.add(specialization)
    
    def has_specialization(self, specialization: str) -> bool:
        """Sprawdza czy posiada daną specjalizację."""
        return specialization in self.specializations
    
    def get_specialization_bonus(self, context: str) -> float:
        """Pobiera bonus specjalizacji dla danego kontekstu."""
        for spec in self.specializations:
            if spec.lower() in context.lower():
                return 0.2  # 20% bonus dla specjalizacji
        return 0.0


class SkillSystem:
    """System zarządzania umiejętnościami gracza."""
    
    # Definicje umiejętności z kategoriami
    SKILL_DEFINITIONS = {
        # Bojowe
        SkillName.WALKA_WRECZ: ("Walka wręcz", "Umiejętność walki bez broni", SkillCategory.BOJOWE),
        SkillName.MIECZE: ("Miecze", "Władanie mieczami", SkillCategory.BOJOWE),
        SkillName.MIECZE_DWURECZNE: ("Miecze dwuręczne", "Władanie mieczami dwuręcznymi", SkillCategory.BOJOWE),
        SkillName.SZTYLETY: ("Sztylety", "Walka sztyletami", SkillCategory.BOJOWE),
        SkillName.TOPORY: ("Topory", "Władanie toporami", SkillCategory.BOJOWE),
        SkillName.TOPORY_DWURECZNE: ("Topory dwuręczne", "Władanie toporami dwuręcznymi", SkillCategory.BOJOWE),
        SkillName.MLOTY: ("Młoty", "Władanie młotami", SkillCategory.BOJOWE),
        SkillName.MLOTY_BOJOWE: ("Młoty bojowe", "Władanie młotami bojowymi", SkillCategory.BOJOWE),
        SkillName.WLÓCZNIE: ("Włócznie", "Walka włóczniami", SkillCategory.BOJOWE),
        SkillName.MACZUGI: ("Maczugi", "Walka maczugami", SkillCategory.BOJOWE),
        SkillName.KIJE_BOJOWE: ("Kije bojowe", "Walka kijami bojowymi", SkillCategory.BOJOWE),
        
        # Obronne
        SkillName.OBRONA: ("Obrona", "Techniki obronne", SkillCategory.OBRONNE),
        SkillName.UNIKI: ("Uniki", "Unikanie ataków", SkillCategory.OBRONNE),
        SkillName.PAROWANIE: ("Parowanie", "Parowanie ciosów", SkillCategory.OBRONNE),
        SkillName.TARCZE: ("Tarcze", "Walka z tarczą", SkillCategory.OBRONNE),
        SkillName.PANCERZ_LEKKI: ("Pancerz lekki", "Noszenie lekkiego pancerza", SkillCategory.OBRONNE),
        SkillName.PANCERZ_CIEZKI: ("Pancerz ciężki", "Noszenie ciężkiego pancerza", SkillCategory.OBRONNE),
        
        # Dystansowe
        SkillName.LUCZNICTWO: ("Łucznictwo", "Strzelanie z łuku", SkillCategory.DYSTANSOWE),
        SkillName.KUSZE: ("Kusze", "Strzelanie z kuszy", SkillCategory.DYSTANSOWE),
        SkillName.PROCE: ("Proce", "Strzelanie z procy", SkillCategory.DYSTANSOWE),
        SkillName.RZUCANIE: ("Rzucanie", "Rzucanie broni", SkillCategory.DYSTANSOWE),
        
        # Magiczne (Void Walker)
        SkillName.MANIPULACJA_PUSTKI: ("Manipulacja Pustki", "Kontrola energii pustki", SkillCategory.MAGICZNE),
        SkillName.ODPORNOSC_NA_BOL: ("Odporność na ból", "Tolerancja bólu", SkillCategory.MAGICZNE),
        SkillName.MEDYTACJA: ("Medytacja", "Kontrola umysłu", SkillCategory.MAGICZNE),
        SkillName.KONTROLA_ENERGII: ("Kontrola energii", "Zarządzanie energią magiczną", SkillCategory.MAGICZNE),
        
        # Społeczne
        SkillName.PERSWAZJA: ("Perswazja", "Przekonywanie", SkillCategory.SPOLECZNE),
        SkillName.HANDEL: ("Handel", "Negocjacje handlowe", SkillCategory.SPOLECZNE),
        SkillName.OSZUSTWO: ("Oszustwo", "Kłamstwo i blef", SkillCategory.SPOLECZNE),
        SkillName.ZASTRASZANIE: ("Zastraszanie", "Wymuszanie strachu", SkillCategory.SPOLECZNE),
        SkillName.PRZYWODZTWO: ("Przywództwo", "Kierowanie ludźmi", SkillCategory.SPOLECZNE),
        SkillName.ETYKIETA: ("Etykieta", "Znajomość protokołu", SkillCategory.SPOLECZNE),
        SkillName.WYSTEPY: ("Występy", "Publiczne wystąpienia", SkillCategory.SPOLECZNE),
        
        # Złodziejskie
        SkillName.SKRADANIE: ("Skradanie", "Cichy ruch", SkillCategory.ZLODZIEJSKIE),
        SkillName.KRADZIEŻ_KIESZONKOWA: ("Kradzież kieszonkowa", "Kradzież z osób", SkillCategory.ZLODZIEJSKIE),
        SkillName.WLAMYWANIE: ("Włamywanie", "Otwieranie zamków", SkillCategory.ZLODZIEJSKIE),
        SkillName.UKRYWANIE: ("Ukrywanie", "Ukrywanie się", SkillCategory.ZLODZIEJSKIE),
        SkillName.FALSYFIKATY: ("Fałszyfikaty", "Podrabianie dokumentów", SkillCategory.ZLODZIEJSKIE),
        SkillName.PULAPKI: ("Pułapki", "Budowanie i rozbrajanie pułapek", SkillCategory.ZLODZIEJSKIE),
        
        # Rzemieślnicze
        SkillName.KOWALSTWO: ("Kowalstwo", "Tworzenie metalowych przedmiotów", SkillCategory.RZEMIESLNICZE),
        SkillName.ALCHEMIA: ("Alchemia", "Warzenie mikstur", SkillCategory.RZEMIESLNICZE),
        SkillName.ZBROJMISTRZOSTWO: ("Zbrojmistrzostwo", "Tworzenie zbroi", SkillCategory.RZEMIESLNICZE),
        SkillName.LUCZARSTWO: ("Łuczarstwo", "Tworzenie łuków", SkillCategory.RZEMIESLNICZE),
        SkillName.JUBILERSTWO: ("Jubilerstwo", "Tworzenie biżuterii", SkillCategory.RZEMIESLNICZE),
        SkillName.KRAWIECTWO: ("Krawiectwo", "Szycie ubrań", SkillCategory.RZEMIESLNICZE),
        SkillName.GARBARSTWO: ("Garbarstwo", "Obróbka skór", SkillCategory.RZEMIESLNICZE),
        SkillName.STOLARSTWO: ("Stolarstwo", "Obróbka drewna", SkillCategory.RZEMIESLNICZE),
        SkillName.GOTOWANIE: ("Gotowanie", "Przygotowywanie posiłków", SkillCategory.RZEMIESLNICZE),
        
        # Przetrwanie
        SkillName.PIERWSZA_POMOC: ("Pierwsza pomoc", "Leczenie ran", SkillCategory.PRZETRWANIE),
        SkillName.TROPIENIE: ("Tropienie", "Śledzenie śladów", SkillCategory.PRZETRWANIE),
        SkillName.ZIELARSTWO: ("Zielarstwo", "Znajomość roślin", SkillCategory.PRZETRWANIE),
        SkillName.OBOZOWANIE: ("Obozowanie", "Przetrwanie w terenie", SkillCategory.PRZETRWANIE),
        SkillName.POLOWANIE: ("Polowanie", "Łowienie zwierząt", SkillCategory.PRZETRWANIE),
        SkillName.LOWIENIE_RYB: ("Łowienie ryb", "Łowienie ryb", SkillCategory.PRZETRWANIE),
        SkillName.ORIENTACJA: ("Orientacja", "Znajdowanie drogi", SkillCategory.PRZETRWANIE),
        
        # Atletyczne
        SkillName.WYTRZYMALOSC: ("Wytrzymałość", "Odporność na zmęczenie", SkillCategory.ATLETYCZNE),
        SkillName.SILA: ("Siła", "Siła fizyczna", SkillCategory.ATLETYCZNE),
        SkillName.ZWROTNOSC: ("Zwinność", "Zręczność i szybkość", SkillCategory.ATLETYCZNE),
        SkillName.AKROBACJA: ("Akrobacja", "Kontrola ciała", SkillCategory.ATLETYCZNE),
        SkillName.PLYWANIE: ("Pływanie", "Poruszanie się w wodzie", SkillCategory.ATLETYCZNE),
        SkillName.GIMNASTYKA: ("Gimnastyka", "Sprawność fizyczna", SkillCategory.ATLETYCZNE),
        SkillName.WDRAPYWANIE: ("Wdrapywanie", "Wspinaczka", SkillCategory.ATLETYCZNE),
        
        # Wiedza
        SkillName.HISTORIA: ("Historia", "Znajomość historii", SkillCategory.WIEDZA),
        SkillName.GEOGRAFIA: ("Geografia", "Znajomość terenu", SkillCategory.WIEDZA),
        SkillName.RELIGIA: ("Religia", "Znajomość wierzeń", SkillCategory.WIEDZA),
        SkillName.ARCHITEKTURA: ("Architektura", "Znajomość budownictwa", SkillCategory.WIEDZA),
        SkillName.INŻYNIERIA: ("Inżynieria", "Wiedza techniczna", SkillCategory.WIEDZA),
        SkillName.MATEMATYKA: ("Matematyka", "Znajomość liczb", SkillCategory.WIEDZA),
        SkillName.LITERATURA: ("Literatura", "Znajomość pisma", SkillCategory.WIEDZA),
        
        # Backward compatibility
        SkillName.MEDYCYNA: ("Medycyna", "Leczenie ran i chorób", SkillCategory.PRZETRWANIE)
    }
    
    def __init__(self):
        """Inicjalizacja systemu umiejętności."""
        self.skills: Dict[SkillName, Skill] = {}
        self._initialize_skills()
        self.learning_multiplier = 1.0  # Mnożnik szybkości nauki
        self.practice_sessions: Dict[SkillName, List[int]] = {
            skill: [] for skill in SkillName
        }
    
    def _initialize_skills(self):
        """Tworzy początkowe umiejętności gracza."""
        for skill_enum, (polish_name, description, category) in self.SKILL_DEFINITIONS.items():
            skill = Skill(
                name=skill_enum.value,
                polish_name=polish_name,
                category=category,
                level=random.randint(0, 5),  # Losowy początkowy poziom 0-5
                natural_talent=random.uniform(0.8, 1.2)  # Losowy talent
            )
            
            # Dodaj podstawowe synergię dla podobnych umiejętności
            self._initialize_skill_synergies(skill, skill_enum)
            self.skills[skill_enum] = skill
    
    def _initialize_skill_synergies(self, skill: Skill, skill_enum: SkillName):
        """Inicjalizuje synergię między umiejętnościami."""
        synergies_map = {
            # Bojowe umiejętności wzajemnie się wspierają
            SkillName.WALKA_WRECZ: [(SkillName.SILA, 0.5, 20), (SkillName.ZWROTNOSC, 0.3, 20)],
            SkillName.MIECZE: [(SkillName.WALKA_WRECZ, 0.3, 15), (SkillName.SILA, 0.4, 20)],
            SkillName.SZTYLETY: [(SkillName.ZWROTNOSC, 0.5, 20), (SkillName.SKRADANIE, 0.3, 15)],
            SkillName.LUCZNICTWO: [(SkillName.ZWROTNOSC, 0.4, 20), (SkillName.TROPIENIE, 0.2, 15)],
            
            # Społeczne
            SkillName.PERSWAZJA: [(SkillName.OSZUSTWO, 0.3, 15), (SkillName.ETYKIETA, 0.2, 15)],
            SkillName.HANDEL: [(SkillName.PERSWAZJA, 0.4, 20), (SkillName.MATEMATYKA, 0.3, 15)],
            
            # Rzemieślnicze
            SkillName.KOWALSTWO: [(SkillName.SILA, 0.3, 20), (SkillName.INŻYNIERIA, 0.2, 15)],
            SkillName.ALCHEMIA: [(SkillName.ZIELARSTWO, 0.4, 20), (SkillName.MATEMATYKA, 0.2, 15)],
            
            # Przetrwanie
            SkillName.PIERWSZA_POMOC: [(SkillName.ZIELARSTWO, 0.3, 15), (SkillName.ALCHEMIA, 0.2, 10)],
            SkillName.TROPIENIE: [(SkillName.LUCZNICTWO, 0.2, 15), (SkillName.GEOGRAFIA, 0.3, 15)],
        }
        
        if skill_enum in synergies_map:
            for target_skill, multiplier, max_level in synergies_map[skill_enum]:
                synergy = SkillSynergy(
                    target_skill=target_skill,
                    bonus_multiplier=multiplier,
                    max_level=max_level
                )
                skill.synergies.append(synergy)
    
    def get_skill(self, skill_name: SkillName) -> Optional[Skill]:
        """
        Pobiera umiejętność po nazwie.
        
        Args:
            skill_name: Nazwa umiejętności
        
        Returns:
            Obiekt umiejętności lub None
        """
        return self.skills.get(skill_name)
    
    def get_skill_level(self, skill_name) -> int:
        """
        Pobiera poziom umiejętności.
        
        Args:
            skill_name: Nazwa umiejętności (str lub SkillName)
        
        Returns:
            Poziom umiejętności (0 jeśli nieznana)
        """
        # Obsługa obu typów - string i enum
        if isinstance(skill_name, str):
            # Konwersja string na SkillName
            try:
                skill_enum = SkillName(skill_name)
            except ValueError:
                return 0  # Nieznana umiejętność
        else:
            skill_enum = skill_name
        
        skill = self.get_skill(skill_enum)
        return skill.level if skill else 0
    
    def use_skill(self, skill_name: SkillName, difficulty: int, 
                  pain_level: float = 0.0, injuries: Dict[str, float] = None) -> Tuple[bool, str]:
        """
        Używa umiejętności i sprawdza sukces.
        
        Args:
            skill_name: Nazwa używanej umiejętności
            difficulty: Trudność zadania (0-100)
            pain_level: Poziom bólu (0-100)
            injuries: Słownik kontuzji {część_ciała: poziom}
        
        Returns:
            (sukces, opis wyniku)
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return False, f"Nie posiadasz umiejętności {skill_name.value}!"
        
        # Oblicz kary
        pain_penalty = self._calculate_pain_penalty(pain_level)
        injury_penalty = self._calculate_injury_penalty(skill_name, injuries or {})
        
        # Oblicz efektywny poziom umiejętności
        effective_level = skill.get_effective_level(pain_penalty, injury_penalty)
        
        # Oblicz szansę sukcesu
        base_chance = skill.get_success_chance(difficulty)
        
        # Uwzględnij kary w szansie
        final_chance = base_chance * (1.0 - pain_penalty) * (1.0 - injury_penalty)
        
        # Rzut na sukces
        roll = random.random()
        success = roll < final_chance
        
        # Aktualizuj statystyki
        skill.uses_today += 1
        skill.total_uses += 1
        skill.last_difficulty_practiced = difficulty
        
        # Sprawdź możliwość nauki
        if skill.can_improve(difficulty):
            improvement = self._try_improve_skill(skill, difficulty, success)
            if improvement:
                result_msg = f"{'Sukces' if success else 'Porażka'}! {skill.polish_name} wzrasta!"
            else:
                result_msg = f"{'Sukces' if success else 'Porażka'} w {skill.polish_name}."
        else:
            result_msg = f"{'Sukces' if success else 'Porażka'} w {skill.polish_name} (zbyt {'łatwe' if difficulty < skill.level - 30 else 'trudne'} aby się uczyć)."
        
        # Dodaj informacje o karach
        if pain_penalty > 0 or injury_penalty > 0:
            penalties = []
            if pain_penalty > 0:
                penalties.append(f"ból: -{int(pain_penalty*100)}%")
            if injury_penalty > 0:
                penalties.append(f"rany: -{int(injury_penalty*100)}%")
            result_msg += f" [Kary: {', '.join(penalties)}]"
        
        return success, result_msg
    
    def _calculate_pain_penalty(self, pain_level: float) -> float:
        """
        Oblicza karę do umiejętności z powodu bólu.
        
        Args:
            pain_level: Poziom bólu (0-100)
        
        Returns:
            Kara (0.0 - 0.75)
        """
        if pain_level < 30:
            return 0.0  # Brak kary poniżej 30
        elif pain_level < 50:
            return (pain_level - 30) / 100.0  # 0.0 - 0.2
        elif pain_level < 70:
            return 0.2 + (pain_level - 50) / 50.0  # 0.2 - 0.6
        else:
            return min(0.75, 0.6 + (pain_level - 70) / 40.0)  # 0.6 - 0.75
    
    def _calculate_injury_penalty(self, skill_name: SkillName, injuries: Dict[str, float]) -> float:
        """
        Oblicza karę do umiejętności z powodu kontuzji.
        
        Args:
            skill_name: Nazwa umiejętności
            injuries: Słownik kontuzji {część_ciała: poziom}
        
        Returns:
            Kara (0.0 - 0.9)
        """
        if not injuries:
            return 0.0
        
        # Mapowanie umiejętności na istotne części ciała
        skill_body_parts = {
            SkillName.WALKA_WRECZ: ['prawa_reka', 'lewa_reka', 'tulow', 'prawa_noga', 'lewa_noga'],
            SkillName.MIECZE: ['prawa_reka', 'tulow', 'prawa_noga', 'lewa_noga'],
            SkillName.LUCZNICTWO: ['prawa_reka', 'lewa_reka', 'tulow', 'glowa'],
            SkillName.SKRADANIE: ['prawa_noga', 'lewa_noga', 'tulow'],
            SkillName.PERSWAZJA: ['glowa'],
            SkillName.HANDEL: ['glowa'],
            SkillName.KOWALSTWO: ['prawa_reka', 'lewa_reka', 'tulow'],
            SkillName.ALCHEMIA: ['prawa_reka', 'lewa_reka', 'glowa'],
            SkillName.MEDYCYNA: ['prawa_reka', 'lewa_reka', 'glowa'],
            SkillName.WYTRZYMALOSC: ['tulow', 'glowa']
        }
        
        relevant_parts = skill_body_parts.get(skill_name, [])
        total_penalty = 0.0
        
        for part in relevant_parts:
            if part in injuries:
                injury_level = injuries[part]
                if injury_level > 0:
                    # Kara zależna od poziomu kontuzji
                    part_penalty = (injury_level / 100.0) * 0.3  # Max 0.3 na część
                    total_penalty += part_penalty
        
        return min(0.9, total_penalty)  # Max 90% kary
    
    def _try_improve_skill(self, skill: Skill, difficulty: int, success: bool) -> bool:
        """
        Próbuje poprawić umiejętność po użyciu.
        
        Args:
            skill: Umiejętność do poprawy
            difficulty: Trudność zadania
            success: Czy akcja się powiodła
        
        Returns:
            True jeśli umiejętność wzrosła
        """
        # Oblicz szansę na naukę
        skill_diff = abs(skill.level - difficulty)
        
        if skill_diff < 5:
            # Zbyt łatwe - minimalna szansa
            learn_chance = 0.01 * self.learning_multiplier
        elif skill_diff <= 15:
            # Optymalna trudność
            learn_chance = 0.10 * self.learning_multiplier
            if not success:
                learn_chance *= 1.5  # Bonus za porażkę przy optymalnej trudności
        elif skill_diff <= 30:
            # Trudne ale wykonalne
            learn_chance = 0.05 * self.learning_multiplier
        else:
            # Bardzo trudne
            learn_chance = 0.02 * self.learning_multiplier
        
        # Logarytmiczny spadek szansy przy wyższych poziomach
        level_penalty = math.log10(skill.level + 10) / 2.0
        learn_chance /= level_penalty
        
        # Rzut na naukę
        if random.random() < learn_chance:
            # Oblicz postęp
            progress_gain = random.uniform(5, 15) * self.learning_multiplier
            
            # Dodaj postęp
            skill.progress += progress_gain
            
            # Sprawdź czy poziom wzrósł
            if skill.progress >= 100.0:
                skill.level += 1
                skill.progress -= 100.0
                
                # Zapisz sesję treningową
                self.practice_sessions[SkillName(skill.name)].append(difficulty)
                
                return True
        
        return False
    
    def train_skill(self, skill_name: SkillName, training_quality: float = 1.0) -> Tuple[bool, str]:
        """
        Specjalny trening umiejętności (np. z nauczycielem).
        
        Args:
            skill_name: Nazwa umiejętności
            training_quality: Jakość treningu (0.5 - 2.0)
        
        Returns:
            (czy wzrosła, opis)
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return False, f"Nie posiadasz umiejętności {skill_name.value}!"
        
        # Trening jest zawsze na optymalnym poziomie trudności
        optimal_difficulty = skill.level + 10
        
        # Zwiększ mnożnik nauki tymczasowo
        old_multiplier = self.learning_multiplier
        self.learning_multiplier *= training_quality
        
        # Symuluj intensywny trening
        successes = 0
        attempts = 5  # 5 prób podczas sesji treningowej
        
        for _ in range(attempts):
            success, _ = self.use_skill(skill_name, optimal_difficulty)
            if success:
                successes += 1
        
        # Przywróć mnożnik
        self.learning_multiplier = old_multiplier
        
        result = f"Trening {skill.polish_name}: {successes}/{attempts} sukcesów."
        if skill.progress > 75:
            result += f" Blisko awansu! ({skill.progress:.1f}%)"
        
        return successes > 0, result
    
    def reset_daily_limits(self):
        """Resetuje dzienne limity użyć umiejętności."""
        for skill in self.skills.values():
            skill.uses_today = 0
    
    def get_skill_summary(self) -> str:
        """
        Zwraca podsumowanie wszystkich umiejętności.
        
        Returns:
            Sformatowany tekst z umiejętnościami
        """
        lines = ["=== UMIEJĘTNOŚCI ==="]
        
        for skill_enum in SkillName:
            skill = self.skills[skill_enum]
            progress_bar = self._create_progress_bar(skill.progress)
            lines.append(
                f"{skill.polish_name:15} Poziom: {skill.level:3} "
                f"[{progress_bar}] {skill.progress:.1f}% "
                f"(użyć: {skill.total_uses})"
            )
        
        return "\n".join(lines)
    
    def _create_progress_bar(self, progress: float, width: int = 10) -> str:
        """
        Tworzy pasek postępu.
        
        Args:
            progress: Postęp (0-100)
            width: Szerokość paska
        
        Returns:
            Tekstowy pasek postępu
        """
        filled = int(progress / 100 * width)
        empty = width - filled
        return "█" * filled + "░" * empty
    
    def get_combat_skills(self) -> List[SkillName]:
        """Zwraca listę umiejętności bojowych."""
        return [SkillName.WALKA_WRECZ, SkillName.MIECZE, SkillName.LUCZNICTWO]
    
    def get_social_skills(self) -> List[SkillName]:
        """Zwraca listę umiejętności społecznych."""
        return [SkillName.PERSWAZJA, SkillName.HANDEL]
    
    def get_crafting_skills(self) -> List[SkillName]:
        """Zwraca listę umiejętności rzemieślniczych."""
        return [SkillName.KOWALSTWO, SkillName.ALCHEMIA, SkillName.MEDYCYNA]