"""
System gracza i frakcji
"""

from dataclasses import dataclass, field
from typing import List, Optional
import uuid

from systems.resources import ResourcePool
from systems.technology import TechnologyTree, Technology
from systems.fleet import Fleet
from game.planet import Planet


@dataclass
class Player:
    """Klasa reprezentująca gracza"""

    id: str
    name: str
    faction: str  # "Imperium", "Federacja", "Korporacja", "Piraci"
    resources: ResourcePool = field(default_factory=lambda: ResourcePool(kredyty=5000))
    planets: List[Planet] = field(default_factory=list)
    fleets: List[Fleet] = field(default_factory=list)
    technology_tree: TechnologyTree = field(default_factory=TechnologyTree)
    current_research: Optional[Technology] = None
    research_progress: int = 0

    def __init__(self, name: str, faction: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.faction = faction
        self.resources = ResourcePool(kredyty=5000, metale=1000, krysztaly=500, energia=500)
        self.planets = []
        self.fleets = []
        self.technology_tree = TechnologyTree()
        self.current_research = None
        self.research_progress = 0

    def add_planet(self, planet: Planet):
        """Dodaje planetę do listy posiadanych"""
        if planet not in self.planets:
            self.planets.append(planet)
            planet.owner = self

    def remove_planet(self, planet: Planet):
        """Usuwa planetę z listy posiadanych"""
        if planet in self.planets:
            self.planets.remove(planet)
            planet.owner = None

    def add_fleet(self, fleet: Fleet):
        """Dodaje flotę"""
        self.fleets.append(fleet)
        fleet.owner_id = self.id

    def get_planet_by_name(self, name: str) -> Optional[Planet]:
        """Znajduje planetę po nazwie"""
        name_lower = name.lower()
        for planet in self.planets:
            if planet.name.lower() == name_lower:
                return planet
        return None

    def get_total_income(self) -> ResourcePool:
        """Oblicza całkowite przychody ze wszystkich planet"""
        total = ResourcePool()

        for planet in self.planets:
            planet_income = planet.produce_resources(None)  # Nie dodajemy jeszcze do zasobów
            total = total + planet_income

        return total

    def collect_resources(self):
        """Zbiera zasoby ze wszystkich planet"""
        for planet in self.planets:
            planet.produce_resources(self)

    def is_technology_researched(self, tech_id: str) -> bool:
        """Sprawdza czy technologia została zbadana"""
        tech = self.technology_tree.get_technology(tech_id)
        return tech.researched if tech else False

    def start_research(self, tech_id: str) -> bool:
        """Rozpoczyna badanie technologii"""
        tech = self.technology_tree.get_technology(tech_id)

        if not tech:
            return False

        if not tech.can_research(self):
            return False

        # Odejmij koszt
        self.resources = self.resources - tech.cost

        # Ustaw jako obecne badanie
        self.current_research = tech
        self.research_progress = 0

        return True

    def advance_research(self):
        """Postęp w badaniach (wywoływane co turę)"""
        if not self.current_research:
            return

        # Oblicz punkty badawcze z laboratoriów
        research_points = 10  # Bazowe punkty

        for planet in self.planets:
            for building in planet.buildings:
                if building.__class__.__name__ == "Laboratorium" and building.operational:
                    research_points += building.get_research_bonus()

        self.research_progress += research_points

        # Sprawdź czy badanie ukończone
        if self.research_progress >= self.current_research.research_time * 100:
            self.current_research.researched = True
            self.current_research = None
            self.research_progress = 0

    def get_status(self) -> str:
        """Zwraca status gracza"""
        lines = [
            f"\n=== STATUS GRACZA: {self.name} ===",
            f"Frakcja: {self.faction}",
            f"\nZasoby:",
            f"  {self.resources}",
            f"\nPlanety: {len(self.planets)}",
            f"Floty: {len(self.fleets)}",
        ]

        if self.current_research:
            progress = (self.research_progress / (self.current_research.research_time * 100)) * 100
            lines.append(f"\nBadania: {self.current_research.name} ({progress:.1f}%)")

        # Pokaż przychody
        income = self.get_total_income()
        lines.append(f"\nPrzychód na turę:")
        lines.append(f"  {income}")

        return "\n".join(lines)

    def get_research_status(self) -> str:
        """Zwraca status badań"""
        lines = ["\n=== STATUS BADAŃ ==="]

        if self.current_research:
            progress = (self.research_progress / (self.current_research.research_time * 100)) * 100
            lines.append(f"\nObecne badanie: {self.current_research.name}")
            lines.append(f"Postęp: {progress:.1f}%")
            lines.append(f"Opis: {self.current_research.description}")
        else:
            lines.append("\nBrak aktywnych badań")

        # Pokaż dostępne technologie
        available = self.technology_tree.get_available_technologies(self)
        if available:
            lines.append(f"\nDostępne do zbadania ({len(available)}):")
            for tech in available[:5]:  # Pokaż max 5
                lines.append(f"  - {tech.name} (Koszt: {tech.cost.kredyty} kredytów, {tech.research_time} tur)")

        # Pokaż zbadane technologie
        researched = [t for t in self.technology_tree.technologies.values() if t.researched]
        if researched:
            lines.append(f"\nZbadane technologie ({len(researched)}):")
            for tech in researched:
                lines.append(f"  ✓ {tech.name}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "faction": self.faction,
            "resources": self.resources.to_dict(),
            "planets": [p.to_dict() for p in self.planets],
            "fleets": [f.to_dict() for f in self.fleets],
            "technology_tree": self.technology_tree.to_dict(),
            "current_research": self.current_research.id if self.current_research else None,
            "research_progress": self.research_progress
        }

    @classmethod
    def from_dict(cls, data: dict):
        player = cls.__new__(cls)
        player.id = data["id"]
        player.name = data["name"]
        player.faction = data["faction"]
        player.resources = ResourcePool.from_dict(data["resources"])

        # Odtwórz drzewo technologiczne
        player.technology_tree = TechnologyTree.from_dict(data["technology_tree"])

        # Odtwórz obecne badanie
        current_research_id = data.get("current_research")
        if current_research_id:
            player.current_research = player.technology_tree.get_technology(current_research_id)
        else:
            player.current_research = None

        player.research_progress = data.get("research_progress", 0)

        # Odtwórz planety
        from game.planet import Planet
        player.planets = []
        for p_data in data.get("planets", []):
            planet = Planet.from_dict(p_data, owner=player)
            player.planets.append(planet)

        # Odtwórz floty
        from systems.fleet import Fleet
        player.fleets = []
        for f_data in data.get("fleets", []):
            fleet = Fleet.from_dict(f_data)
            player.fleets.append(fleet)

        return player
