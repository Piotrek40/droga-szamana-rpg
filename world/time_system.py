"""
System czasu dla gry Droga Szamana RPG.
Zarządza porą dnia, wpływa na opisy lokacji i wydarzenia.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import random


class TimeSystem:
    """System zarządzania czasem w grze."""
    
    def __init__(self):
        """Inicjalizacja systemu czasu."""
        self.current_time = datetime(1000, 1, 1, 6, 0)  # Start o 6:00 rano
        self.time_speed = 1  # Mnożnik prędkości czasu (1 = normalny)
        self.is_paused = False
        
        # Definicje pór dnia
        self.time_periods = {
            'świt': (5, 7),      # 5:00 - 7:00
            'ranek': (7, 10),    # 7:00 - 10:00
            'przedpołudnie': (10, 12),  # 10:00 - 12:00
            'południe': (12, 14),  # 12:00 - 14:00
            'popołudnie': (14, 17),  # 14:00 - 17:00
            'wieczór': (17, 20),  # 17:00 - 20:00
            'zmierzch': (20, 22),  # 20:00 - 22:00
            'noc': (22, 5)  # 22:00 - 5:00
        }
        
        # Modyfikatory jasności dla różnych pór
        self.light_levels = {
            'świt': 0.3,
            'ranek': 0.7,
            'przedpołudnie': 0.9,
            'południe': 1.0,
            'popołudnie': 0.9,
            'wieczór': 0.6,
            'zmierzch': 0.3,
            'noc': 0.1
        }
    
    @property
    def aktualny_czas(self):
        """Alias dla current_time dla kompatybilności"""
        return self.current_time
    
    @property
    def day(self) -> int:
        """Zwraca aktualny dzień miesiąca."""
        return self.current_time.day
    
    @property
    def hour(self) -> int:
        """Zwraca aktualną godzinę (0-23)."""
        return self.current_time.hour
    
    @property
    def minute(self) -> int:
        """Zwraca aktualną minutę (0-59)."""
        return self.current_time.minute
        
    def advance_time(self, minutes: int = 1):
        """Przesuwa czas o określoną liczbę minut."""
        if not self.is_paused:
            self.current_time += timedelta(minutes=minutes * self.time_speed)
    
    def get_hour(self) -> int:
        """Zwraca aktualną godzinę (0-23)."""
        return self.current_time.hour
    
    def get_minute(self) -> int:
        """Zwraca aktualną minutę (0-59)."""
        return self.current_time.minute
    
    def get_time_string(self) -> str:
        """Zwraca czas w formacie tekstowym."""
        return self.current_time.strftime("%H:%M")
    
    def get_date_string(self) -> str:
        """Zwraca datę w formacie tekstowym."""
        day = self.current_time.day
        month = self.get_month_name(self.current_time.month)
        year = self.current_time.year
        return f"{day} {month}, rok {year}"
    
    def get_month_name(self, month: int) -> str:
        """Zwraca polską nazwę miesiąca."""
        months = {
            1: "Stycznia", 2: "Lutego", 3: "Marca", 4: "Kwietnia",
            5: "Maja", 6: "Czerwca", 7: "Lipca", 8: "Sierpnia",
            9: "Września", 10: "Października", 11: "Listopada", 12: "Grudnia"
        }
        return months.get(month, "Nieznany")
    
    def is_day(self) -> bool:
        """Sprawdza czy jest dzień (6:00 - 18:00)."""
        hour = self.get_hour()
        return 6 <= hour < 18
    
    def is_night(self) -> bool:
        """Sprawdza czy jest noc (18:00 - 6:00)."""
        return not self.is_day()
    
    def get_time_period(self) -> str:
        """Zwraca aktualną porę dnia."""
        hour = self.get_hour()
        
        for period, (start, end) in self.time_periods.items():
            if period == 'noc':
                if hour >= start or hour < end:
                    return period
            else:
                if start <= hour < end:
                    return period
        
        return 'noc'  # Domyślnie
    
    def get_light_level(self) -> float:
        """Zwraca poziom oświetlenia (0.0 - 1.0)."""
        period = self.get_time_period()
        return self.light_levels.get(period, 0.5)
    
    def get_time_description(self) -> str:
        """Zwraca opisowy tekst aktualnej pory."""
        period = self.get_time_period()
        hour = self.get_hour()
        
        descriptions = {
            'świt': [
                "Pierwsze promienie słońca przebijają się przez ciemność.",
                "Niebo na wschodzie zaczyna się rozjaśniać.",
                "Świt powoli rozprasza nocne cienie."
            ],
            'ranek': [
                "Poranne słońce oświetla świat złotym blaskiem.",
                "Ranek przynosi ze sobą świeżość i nową energię.",
                "Jasne poranne światło wypełnia przestrzeń."
            ],
            'przedpołudnie': [
                "Słońce wspina się coraz wyżej po niebie.",
                "Przedpołudniowe światło jest jasne i ostre.",
                "Dzień nabiera rozpędu."
            ],
            'południe': [
                "Słońce świeci z zenitu, rzucając krótkie cienie.",
                "Południowy żar wypełnia powietrze.",
                "Jest najjaśniejsza pora dnia."
            ],
            'popołudnie': [
                "Słońce powoli zaczyna schodzić ku zachodowi.",
                "Popołudniowe światło staje się cieplejsze.",
                "Cienie wydłużają się z każdą chwilą."
            ],
            'wieczór': [
                "Słońce chyli się ku horyzontowi.",
                "Wieczorne światło maluje wszystko w złotych barwach.",
                "Dzień powoli ustępuje miejsca nocy."
            ],
            'zmierzch': [
                "Ostatnie promienie słońca gasną na niebie.",
                "Zmierzch otula świat półmrokiem.",
                "Gwiazdy zaczynają pojawiać się na niebie."
            ],
            'noc': [
                "Ciemność nocy spowijа wszystko wokół.",
                "Księżyc i gwiazdy są jedynym źródłem światła.",
                "Noc przynosi ciszę i tajemnicę."
            ]
        }
        
        period_descs = descriptions.get(period, ["Jest teraz."])
        return random.choice(period_descs)
    
    def get_guard_shift(self) -> str:
        """Zwraca aktualną zmianę straży."""
        hour = self.get_hour()
        
        if 6 <= hour < 14:
            return "poranna"
        elif 14 <= hour < 22:
            return "popołudniowa"
        else:
            return "nocna"
    
    def get_activity_level(self) -> str:
        """Zwraca poziom aktywności w więzieniu."""
        hour = self.get_hour()
        
        if 23 <= hour or hour < 5:
            return "bardzo_niski"  # Większość śpi
        elif 5 <= hour < 7:
            return "niski"  # Pobudka
        elif 7 <= hour < 8:
            return "średni"  # Śniadanie
        elif 8 <= hour < 12:
            return "wysoki"  # Praca/aktywności
        elif 12 <= hour < 13:
            return "średni"  # Obiad
        elif 13 <= hour < 17:
            return "wysoki"  # Praca/aktywności
        elif 17 <= hour < 18:
            return "średni"  # Kolacja
        elif 18 <= hour < 21:
            return "niski"  # Czas wolny
        else:
            return "bardzo_niski"  # Przygotowanie do snu
    
    def should_guards_patrol(self) -> bool:
        """Określa czy strażnicy powinni patrolować."""
        minute = self.get_minute()
        # Patrol co 15 minut
        return minute % 15 == 0
    
    def get_meal_time(self) -> Optional[str]:
        """Zwraca nazwę posiłku jeśli jest pora posiłku."""
        hour = self.get_hour()
        minute = self.get_minute()
        
        if hour == 7 and minute < 30:
            return "śniadanie"
        elif hour == 12 and minute < 30:
            return "obiad"
        elif hour == 17 and minute < 30:
            return "kolacja"
        else:
            return None
    
    def set_time(self, hour: int, minute: int = 0):
        """Ustawia konkretną godzinę."""
        self.current_time = self.current_time.replace(hour=hour, minute=minute)
    
    def pause(self):
        """Pauzuje upływ czasu."""
        self.is_paused = True
    
    def resume(self):
        """Wznawia upływ czasu."""
        self.is_paused = False
    
    def set_speed(self, speed: float):
        """Ustawia prędkość upływu czasu."""
        self.time_speed = max(0.1, min(10.0, speed))  # Ograniczenie 0.1x - 10x
    
    def update(self, current_game_time: int):
        """Aktualizuje system czasu na podstawie czasu gry w minutach.
        
        Args:
            current_game_time: Aktualny czas gry w minutach od początku
        """
        # Konwertuj minuty gry na czas dnia
        hours = (current_game_time // 60) % 24
        minutes = current_game_time % 60
        
        # Ustaw czas
        self.current_time = self.current_time.replace(hour=int(hours), minute=int(minutes))