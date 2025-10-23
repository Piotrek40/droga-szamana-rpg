"""
System zasobów w grze
Zarządza surowcami, energią i kredytami
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ResourcePool:
    """Pula zasobów gracza lub planety"""

    # Podstawowe zasoby
    metale: int = 0          # Metale przemysłowe
    krysztaly: int = 0       # Kryształy (technologia zaawansowana)
    energia: int = 0         # Energia (produkcja/konsumpcja na turę)
    kredyty: int = 1000      # Waluta galaktyczna
    populacja: int = 0       # Populacja (na planetach)

    # Strategiczne zasoby
    antymateria: int = 0     # Rzadki zasób do napędu FTL
    deuterium: int = 0       # Paliwo do statków

    def __add__(self, other):
        """Dodaje zasoby z innej puli"""
        if not isinstance(other, ResourcePool):
            return NotImplemented

        return ResourcePool(
            metale=self.metale + other.metale,
            krysztaly=self.krysztaly + other.krysztaly,
            energia=self.energia + other.energia,
            kredyty=self.kredyty + other.kredyty,
            populacja=self.populacja + other.populacja,
            antymateria=self.antymateria + other.antymateria,
            deuterium=self.deuterium + other.deuterium
        )

    def __sub__(self, other):
        """Odejmuje zasoby"""
        if not isinstance(other, ResourcePool):
            return NotImplemented

        return ResourcePool(
            metale=self.metale - other.metale,
            krysztaly=self.krysztaly - other.krysztaly,
            energia=self.energia - other.energia,
            kredyty=self.kredyty - other.kredyty,
            populacja=self.populacja - other.populacja,
            antymateria=self.antymateria - other.antymateria,
            deuterium=self.deuterium - other.deuterium
        )

    def can_afford(self, cost: 'ResourcePool') -> bool:
        """Sprawdza czy stać na dany koszt"""
        return (
            self.metale >= cost.metale and
            self.krysztaly >= cost.krysztaly and
            self.energia >= cost.energia and
            self.kredyty >= cost.kredyty and
            self.populacja >= cost.populacja and
            self.antymateria >= cost.antymateria and
            self.deuterium >= cost.deuterium
        )

    def to_dict(self) -> dict:
        """Konwertuje do słownika"""
        return {
            "metale": self.metale,
            "krysztaly": self.krysztaly,
            "energia": self.energia,
            "kredyty": self.kredyty,
            "populacja": self.populacja,
            "antymateria": self.antymateria,
            "deuterium": self.deuterium
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Tworzy z słownika"""
        return cls(**data)

    def __str__(self) -> str:
        """Tekstowa reprezentacja zasobów"""
        return (
            f"Metale: {self.metale} | Kryształy: {self.krysztaly} | "
            f"Energia: {self.energia} | Kredyty: {self.kredyty}"
        )


class ResourceManager:
    """Zarządza zasobami w całej grze"""

    # Nazwy zasobów po polsku
    RESOURCE_NAMES = {
        "metale": "Metale",
        "krysztaly": "Kryształy",
        "energia": "Energia",
        "kredyty": "Kredyty",
        "populacja": "Populacja",
        "antymateria": "Antymateria",
        "deuterium": "Deuterium"
    }

    # Ikony zasobów (dla lepszego UI)
    RESOURCE_ICONS = {
        "metale": "⚙️",
        "krysztaly": "💎",
        "energia": "⚡",
        "kredyty": "💰",
        "populacja": "👥",
        "antymateria": "⚛️",
        "deuterium": "🛢️"
    }

    @staticmethod
    def format_resources(resources: ResourcePool) -> str:
        """Formatuje zasoby do czytelnego tekstu"""
        lines = []
        for key, value in resources.to_dict().items():
            if value != 0:  # Pokazuj tylko niezerowe
                icon = ResourceManager.RESOURCE_ICONS.get(key, "")
                name = ResourceManager.RESOURCE_NAMES.get(key, key)
                lines.append(f"  {icon} {name}: {value}")

        return "\n".join(lines) if lines else "  Brak zasobów"

    @staticmethod
    def calculate_income(planet) -> ResourcePool:
        """Oblicza przychód zasobów z planety"""
        income = ResourcePool()

        # Podstawowa produkcja z budynków
        for building in planet.buildings:
            if building.operational:
                building_income = building.get_production()
                income = income + building_income

        # Bonusy z typu planety
        if planet.planet_type == "przemysłowa":
            income.metale = int(income.metale * 1.25)
        elif planet.planet_type == "badawcza":
            income.krysztaly = int(income.krysztaly * 1.25)

        return income
