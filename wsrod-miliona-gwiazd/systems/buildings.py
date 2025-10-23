"""
System budynków planetarnych
Różne typy budynków: produkcyjne, badawcze, militarne
"""

from dataclasses import dataclass
from typing import Optional
from systems.resources import ResourcePool


@dataclass
class Building:
    """Klasa bazowa dla budynku"""

    name: str
    description: str
    level: int = 1
    max_level: int = 10
    operational: bool = True
    construction_time: int = 0  # Pozostałe tury do ukończenia (0 = gotowe)

    def get_cost(self) -> ResourcePool:
        """Zwraca koszt budowy/ulepszenia na obecny poziom"""
        raise NotImplementedError

    def get_production(self) -> ResourcePool:
        """Zwraca produkcję zasobów na turę"""
        return ResourcePool()

    def upgrade(self) -> ResourcePool:
        """Zwraca koszt ulepszenia do następnego poziomu"""
        if self.level >= self.max_level:
            return None

        base_cost = self.get_cost()
        # Koszt rośnie wykładniczo z poziomem
        multiplier = 1.5 ** self.level

        return ResourcePool(
            metale=int(base_cost.metale * multiplier),
            krysztaly=int(base_cost.krysztaly * multiplier),
            kredyty=int(base_cost.kredyty * multiplier)
        )

    def complete_construction(self):
        """Kończy budowę/upgrade"""
        if self.construction_time > 0:
            self.construction_time -= 1

        if self.construction_time == 0:
            self.operational = True

    def to_dict(self) -> dict:
        """Konwertuje do słownika"""
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "operational": self.operational,
            "construction_time": self.construction_time
        }


class Kopalnia(Building):
    """Kopalnia metali - produkuje metale"""

    def __init__(self, level: int = 1):
        super().__init__(
            name="Kopalnia Metali",
            description="Wydobywa metale z wnętrza planety",
            level=level,
            max_level=15
        )

    def get_cost(self) -> ResourcePool:
        return ResourcePool(metale=100, energia=50, kredyty=200)

    def get_production(self) -> ResourcePool:
        base_production = 50
        return ResourcePool(metale=int(base_production * (1.2 ** (self.level - 1))))


class Rafineria(Building):
    """Rafineria kryształów - produkuje kryształy"""

    def __init__(self, level: int = 1):
        super().__init__(
            name="Rafineria Kryształów",
            description="Przetwarza surowe kryształy na komponenty technologiczne",
            level=level,
            max_level=15
        )

    def get_cost(self) -> ResourcePool:
        return ResourcePool(metale=150, krysztaly=50, kredyty=300)

    def get_production(self) -> ResourcePool:
        base_production = 30
        return ResourcePool(krysztaly=int(base_production * (1.2 ** (self.level - 1))))


class Elektrownia(Building):
    """Elektrownia - produkuje energię"""

    def __init__(self, level: int = 1):
        super().__init__(
            name="Elektrownia Fuzji",
            description="Dostarcza energię dla całej planety",
            level=level,
            max_level=20
        )

    def get_cost(self) -> ResourcePool:
        return ResourcePool(metale=200, krysztaly=100, kredyty=400)

    def get_production(self) -> ResourcePool:
        base_production = 100
        return ResourcePool(energia=int(base_production * (1.3 ** (self.level - 1))))


class Laboratorium(Building):
    """Laboratorium badawcze - przyspiesza badania"""

    def __init__(self, level: int = 1):
        super().__init__(
            name="Laboratorium Badawcze",
            description="Prowadzi badania nad nowymi technologiami",
            level=level,
            max_level=12
        )

    def get_cost(self) -> ResourcePool:
        return ResourcePool(metale=300, krysztaly=200, energia=100, kredyty=600)

    def get_research_bonus(self) -> int:
        """Zwraca bonus do punktów badawczych na turę"""
        return 10 * self.level


class Stocznia(Building):
    """Stocznia kosmiczna - buduje statki"""

    def __init__(self, level: int = 1):
        super().__init__(
            name="Stocznia Kosmiczna",
            description="Konstruuje i naprawia statki kosmiczne",
            level=level,
            max_level=10
        )

    def get_cost(self) -> ResourcePool:
        return ResourcePool(metale=500, krysztaly=200, energia=200, kredyty=1000)

    def get_build_speed_bonus(self) -> float:
        """Zwraca mnożnik szybkości budowy statków"""
        return 1.0 + (0.15 * self.level)


class Tarcza(Building):
    """Generator tarczy planetarnej - obrona"""

    def __init__(self, level: int = 1):
        super().__init__(
            name="Generator Tarczy",
            description="Chroni planetę przed atakami z orbity",
            level=level,
            max_level=8
        )

    def get_cost(self) -> ResourcePool:
        return ResourcePool(metale=400, krysztaly=300, energia=250, kredyty=800)

    def get_defense_value(self) -> int:
        """Zwraca wartość obronną tarczy"""
        return 100 * self.level


class Farma(Building):
    """Farma hydroponiczna - zwiększa populację"""

    def __init__(self, level: int = 1):
        super().__init__(
            name="Farma Hydroponiczna",
            description="Produkuje żywność dla rosnącej populacji",
            level=level,
            max_level=12
        )

    def get_cost(self) -> ResourcePool:
        return ResourcePool(metale=100, energia=50, kredyty=250)

    def get_population_capacity(self) -> int:
        """Zwraca ile populacji może utrzymać"""
        return 1000 * self.level


# Słownik dostępnych budynków
BUILDING_TYPES = {
    "kopalnia": Kopalnia,
    "rafineria": Rafineria,
    "elektrownia": Elektrownia,
    "laboratorium": Laboratorium,
    "stocznia": Stocznia,
    "tarcza": Tarcza,
    "farma": Farma
}


def create_building(building_type: str, level: int = 1) -> Optional[Building]:
    """Tworzy budynek danego typu"""
    building_class = BUILDING_TYPES.get(building_type.lower())

    if building_class:
        return building_class(level)

    return None
