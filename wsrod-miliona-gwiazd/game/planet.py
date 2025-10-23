"""
System planet i ich zarządzania
"""

from dataclasses import dataclass, field
from typing import List, Optional
import random

from systems.resources import ResourcePool, ResourceManager
from systems.buildings import Building, BUILDING_TYPES, create_building


@dataclass
class Planet:
    """Klasa reprezentująca planetę"""

    id: str
    name: str
    x: int  # Pozycja w galaktyce
    y: int
    planet_type: str  # "ziemska", "pustynna", "lodowa", "wulkaniczna", "gazowy olbrzym"
    size: int  # 1-10, wpływa na maksymalną liczbę budynków
    resources_richness: float  # 0.5-2.0, modyfikator produkcji
    owner: Optional[object] = None  # Referencja do gracza
    buildings: List[Building] = field(default_factory=list)
    population: int = 1000
    max_population: int = 5000

    def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        self.max_population = self.size * 1000

    def get_available_building_slots(self) -> int:
        """Zwraca ile jeszcze budynków można zbudować"""
        max_buildings = self.size * 2  # Rozmiar * 2 = max budynków
        return max(0, max_buildings - len(self.buildings))

    def can_build(self, building_type: str) -> bool:
        """Sprawdza czy można zbudować budynek"""
        if self.get_available_building_slots() <= 0:
            return False

        # Sprawdź czy typ budynku jest dozwolony
        if building_type not in BUILDING_TYPES:
            return False

        return True

    def add_building(self, building: Building):
        """Dodaje budynek do planety"""
        if self.get_available_building_slots() > 0:
            self.buildings.append(building)
            return True
        return False

    def produce_resources(self, player) -> ResourcePool:
        """Produkuje zasoby na podstawie budynków"""
        total_production = ResourcePool()

        for building in self.buildings:
            if building.operational and building.construction_time == 0:
                production = building.get_production()

                # Zastosuj modyfikator bogactwa planety
                production.metale = int(production.metale * self.resources_richness)
                production.krysztaly = int(production.krysztaly * self.resources_richness)

                total_production = total_production + production

        # Dodaj produkcję do zasobów gracza
        if player:
            player.resources = player.resources + total_production

        return total_production

    def update_construction(self):
        """Aktualizuje stan budów"""
        for building in self.buildings:
            if building.construction_time > 0:
                building.complete_construction()

    def get_total_population_capacity(self) -> int:
        """Zwraca maksymalną populację z uwzględnieniem farm"""
        base_capacity = self.max_population

        for building in self.buildings:
            if building.__class__.__name__ == "Farma":
                base_capacity += building.get_population_capacity()

        return base_capacity

    def get_description(self) -> str:
        """Zwraca opis planety"""
        owner_text = self.owner.name if self.owner else "Brak właściciela"

        lines = [
            f"\n=== {self.name} ===",
            f"Typ: {self.planet_type.capitalize()}",
            f"Rozmiar: {self.size}/10",
            f"Pozycja: ({self.x}, {self.y})",
            f"Właściciel: {owner_text}",
            f"Populacja: {self.population:,} / {self.get_total_population_capacity():,}",
            f"Bogactwo zasobów: {self.resources_richness:.1%}",
            f"\nBudynki ({len(self.buildings)}/{self.size * 2}):"
        ]

        if self.buildings:
            for i, building in enumerate(self.buildings, 1):
                status = "✓" if building.operational and building.construction_time == 0 else f"🔨 ({building.construction_time} tur)"
                lines.append(f"  {i}. {building.name} (poz. {building.level}) {status}")
        else:
            lines.append("  Brak budynków")

        lines.append(f"\nDostępne sloty budowlane: {self.get_available_building_slots()}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "planet_type": self.planet_type,
            "size": self.size,
            "resources_richness": self.resources_richness,
            "owner_id": self.owner.id if self.owner else None,
            "buildings": [b.to_dict() for b in self.buildings],
            "population": self.population,
            "max_population": self.max_population
        }

    @classmethod
    def from_dict(cls, data: dict, owner=None):
        # Rekonstruuj budynki
        buildings = []
        for b_data in data.get("buildings", []):
            building_type = b_data["type"].lower().replace("class", "")
            building = create_building(building_type, b_data.get("level", 1))
            if building:
                building.operational = b_data.get("operational", True)
                building.construction_time = b_data.get("construction_time", 0)
                buildings.append(building)

        return cls(
            id=data["id"],
            name=data["name"],
            x=data["x"],
            y=data["y"],
            planet_type=data["planet_type"],
            size=data["size"],
            resources_richness=data["resources_richness"],
            owner=owner,
            buildings=buildings,
            population=data["population"],
            max_population=data["max_population"]
        )


class PlanetGenerator:
    """Generator nazw i właściwości planet"""

    PLANET_TYPES = ["ziemska", "pustynna", "lodowa", "wulkaniczna", "gazowy olbrzym"]

    # Prefiksy i sufiksy do nazw planet
    PREFIXES = [
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Nova", "Proxima",
        "Kepler", "Gliese", "Trappist", "HD", "Ross", "Wolf", "Sirius"
    ]

    SUFFIXES = [
        "Prime", "Secundus", "Tertius", "Major", "Minor", "I", "II", "III", "IV", "V",
        "A", "B", "C", "Majoris", "Minoris"
    ]

    @staticmethod
    def generate_planet_name() -> str:
        """Generuje losową nazwę planety"""
        prefix = random.choice(PlanetGenerator.PREFIXES)
        number = random.randint(100, 999)
        suffix = random.choice(PlanetGenerator.SUFFIXES)

        # Czasem dodaj numer, czasem sufiks
        if random.random() > 0.5:
            return f"{prefix}-{number}"
        else:
            return f"{prefix} {suffix}"

    @staticmethod
    def generate_planet(planet_id: str, x: int, y: int) -> Planet:
        """Generuje losową planetę"""
        name = PlanetGenerator.generate_planet_name()
        planet_type = random.choice(PlanetGenerator.PLANET_TYPES)
        size = random.randint(3, 10)
        richness = random.uniform(0.7, 1.5)

        return Planet(
            id=planet_id,
            name=name,
            x=x,
            y=y,
            planet_type=planet_type,
            size=size,
            resources_richness=richness
        )
