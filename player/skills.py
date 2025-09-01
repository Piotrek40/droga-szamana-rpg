"""
System umiejętności dla Droga Szamana RPG.
Każda umiejętność rozwija się TYLKO przez praktykę, bez wydawania punktów doświadczenia.
"""

import random
import math
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum


class SkillName(Enum):
    """Nazwy wszystkich umiejętności w grze."""
    WALKA_WRECZ = "walka_wrecz"
    MIECZE = "miecze"
    LUCZNICTWO = "lucznictwo"
    SKRADANIE = "skradanie"
    PERSWAZJA = "perswazja"
    HANDEL = "handel"
    KOWALSTWO = "kowalstwo"
    ALCHEMIA = "alchemia"
    MEDYCYNA = "medycyna"
    WYTRZYMALOSC = "wytrzymalosc"


@dataclass
class Skill:
    """Reprezentacja pojedynczej umiejętności."""
    name: str
    polish_name: str
    level: int = 0
    progress: float = 0.0  # Postęp do następnego poziomu (0.0 - 100.0)
    uses_today: int = 0  # Liczba użyć dzisiaj (do limitowania nauki)
    total_uses: int = 0  # Całkowita liczba użyć
    last_difficulty_practiced: int = 0  # Ostatnia trudność ćwiczona
    
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


class SkillSystem:
    """System zarządzania umiejętnościami gracza."""
    
    # Definicje umiejętności
    SKILL_DEFINITIONS = {
        SkillName.WALKA_WRECZ: ("Walka wręcz", "Umiejętność walki bez broni"),
        SkillName.MIECZE: ("Miecze", "Władanie mieczami jedno i dwuręcznymi"),
        SkillName.LUCZNICTWO: ("Łucznictwo", "Strzelanie z łuku i kuszy"),
        SkillName.SKRADANIE: ("Skradanie", "Cichy ruch i ukrywanie się"),
        SkillName.PERSWAZJA: ("Perswazja", "Przekonywanie i manipulacja"),
        SkillName.HANDEL: ("Handel", "Negocjacje cenowe i ocena wartości"),
        SkillName.KOWALSTWO: ("Kowalstwo", "Tworzenie i naprawa metalowych przedmiotów"),
        SkillName.ALCHEMIA: ("Alchemia", "Warzenie mikstur i eliksirów"),
        SkillName.MEDYCYNA: ("Medycyna", "Leczenie ran i chorób"),
        SkillName.WYTRZYMALOSC: ("Wytrzymałość", "Odporność na zmęczenie i ból")
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
        for skill_enum, (polish_name, _) in self.SKILL_DEFINITIONS.items():
            self.skills[skill_enum] = Skill(
                name=skill_enum.value,
                polish_name=polish_name,
                level=random.randint(0, 5)  # Losowy początkowy poziom 0-5
            )
    
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