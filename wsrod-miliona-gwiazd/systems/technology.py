"""
System technologii i badań naukowych
Drzewo technologiczne z różnymi gałęziami
"""

from dataclasses import dataclass, field
from typing import List, Optional
from systems.resources import ResourcePool


@dataclass
class Technology:
    """Klasa reprezentująca technologię"""

    id: str
    name: str
    description: str
    category: str  # "militarna", "ekonomiczna", "naukowa", "eksploracyjna"
    cost: ResourcePool
    research_time: int  # Liczba tur potrzebnych do zbadania
    prerequisites: List[str] = field(default_factory=list)  # ID technologii wymaganych
    researched: bool = False
    current_progress: int = 0

    def can_research(self, player) -> bool:
        """Sprawdza czy można rozpocząć badania"""
        # Sprawdź wymagania
        for prereq_id in self.prerequisites:
            if not player.is_technology_researched(prereq_id):
                return False

        # Sprawdź zasoby
        if not player.resources.can_afford(self.cost):
            return False

        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "cost": self.cost.to_dict(),
            "research_time": self.research_time,
            "prerequisites": self.prerequisites,
            "researched": self.researched,
            "current_progress": self.current_progress
        }

    @classmethod
    def from_dict(cls, data: dict):
        cost = ResourcePool.from_dict(data["cost"])
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            cost=cost,
            research_time=data["research_time"],
            prerequisites=data.get("prerequisites", []),
            researched=data.get("researched", False),
            current_progress=data.get("current_progress", 0)
        )


class TechnologyTree:
    """Drzewo technologiczne"""

    def __init__(self):
        self.technologies = self._initialize_technologies()

    def _initialize_technologies(self) -> dict:
        """Inicjalizuje wszystkie dostępne technologie"""

        techs = {}

        # GAŁĄŹ MILITARNA
        techs["lasery_1"] = Technology(
            id="lasery_1",
            name="Działa Laserowe I",
            description="Podstawowe uzbrojenie energetyczne dla statków",
            category="militarna",
            cost=ResourcePool(krysztaly=200, kredyty=500),
            research_time=3,
            prerequisites=[]
        )

        techs["lasery_2"] = Technology(
            id="lasery_2",
            name="Działa Laserowe II",
            description="Ulepszone lasery o większej mocy",
            category="militarna",
            cost=ResourcePool(krysztaly=500, kredyty=1200),
            research_time=5,
            prerequisites=["lasery_1"]
        )

        techs["pancerz_1"] = Technology(
            id="pancerz_1",
            name="Pancerz Reaktywny",
            description="Lepsza ochrona kadłuba statków",
            category="militarna",
            cost=ResourcePool(metale=300, krysztaly=150, kredyty=600),
            research_time=4,
            prerequisites=[]
        )

        techs["tarcze_1"] = Technology(
            id="tarcze_1",
            name="Tarcze Energetyczne",
            description="Pierwsze tarcze dla statków",
            category="militarna",
            cost=ResourcePool(krysztaly=400, energia=200, kredyty=800),
            research_time=6,
            prerequisites=["lasery_1"]
        )

        # GAŁĄŹ EKONOMICZNA
        techs["wydobycie_1"] = Technology(
            id="wydobycie_1",
            name="Zaawansowane Wydobycie",
            description="+25% produkcji metali ze wszystkich kopalń",
            category="ekonomiczna",
            cost=ResourcePool(metale=150, kredyty=400),
            research_time=3,
            prerequisites=[]
        )

        techs["rafinacja_1"] = Technology(
            id="rafinacja_1",
            name="Efektywna Rafinacja",
            description="+25% produkcji kryształów",
            category="ekonomiczna",
            cost=ResourcePool(krysztaly=200, kredyty=500),
            research_time=4,
            prerequisites=[]
        )

        techs["fuzja_1"] = Technology(
            id="fuzja_1",
            name="Ulepszona Fuzja",
            description="+30% produkcji energii z elektrowni",
            category="ekonomiczna",
            cost=ResourcePool(krysztaly=250, energia=100, kredyty=600),
            research_time=5,
            prerequisites=[]
        )

        # GAŁĄŹ NAUKOWA
        techs["komputery_1"] = Technology(
            id="komputery_1",
            name="Komputery Kwantowe",
            description="+20% szybkości badań",
            category="naukowa",
            cost=ResourcePool(krysztaly=300, kredyty=700),
            research_time=4,
            prerequisites=[]
        )

        techs["ai_1"] = Technology(
            id="ai_1",
            name="Sztuczna Inteligencja",
            description="Umożliwia automatyzację produkcji",
            category="naukowa",
            cost=ResourcePool(krysztaly=500, energia=200, kredyty=1000),
            research_time=7,
            prerequisites=["komputery_1"]
        )

        # GAŁĄŹ EKSPLORACYJNA
        techs["silniki_1"] = Technology(
            id="silniki_1",
            name="Napęd Jonowy",
            description="+1 do zasięgu ruchu flot",
            category="eksploracyjna",
            cost=ResourcePool(metale=200, krysztaly=150, kredyty=500),
            research_time=3,
            prerequisites=[]
        )

        techs["silniki_2"] = Technology(
            id="silniki_2",
            name="Napęd Warpowy",
            description="+2 do zasięgu ruchu flot",
            category="eksploracyjna",
            cost=ResourcePool(metale=400, krysztaly=400, antymateria=50, kredyty=1200),
            research_time=8,
            prerequisites=["silniki_1"]
        )

        techs["skanery_1"] = Technology(
            id="skanery_1",
            name="Skanery Długozasięgowe",
            description="Umożliwia skanowanie sąsiednich systemów",
            category="eksploracyjna",
            cost=ResourcePool(krysztaly=250, energia=100, kredyty=600),
            research_time=4,
            prerequisites=[]
        )

        techs["kolonizacja_1"] = Technology(
            id="kolonizacja_1",
            name="Technologia Kolonizacyjna",
            description="Umożliwia kolonizację nowych planet",
            category="eksploracyjna",
            cost=ResourcePool(metale=500, krysztaly=300, kredyty=1500),
            research_time=10,
            prerequisites=["silniki_1"]
        )

        return techs

    def get_technology(self, tech_id: str) -> Optional[Technology]:
        """Pobiera technologię po ID"""
        return self.technologies.get(tech_id)

    def get_available_technologies(self, player) -> List[Technology]:
        """Zwraca listę technologii dostępnych do zbadania"""
        available = []

        for tech in self.technologies.values():
            if not tech.researched and tech.can_research(player):
                available.append(tech)

        return available

    def get_by_category(self, category: str) -> List[Technology]:
        """Zwraca technologie z danej kategorii"""
        return [tech for tech in self.technologies.values() if tech.category == category]

    def to_dict(self) -> dict:
        return {
            tech_id: tech.to_dict()
            for tech_id, tech in self.technologies.items()
        }

    @classmethod
    def from_dict(cls, data: dict):
        tree = cls()
        for tech_id, tech_data in data.items():
            tree.technologies[tech_id] = Technology.from_dict(tech_data)
        return tree
