"""
System galaktyki - generacja i zarządzanie gwiazdami i planetami
"""

import random
from typing import List, Optional, Tuple
from game.planet import Planet, PlanetGenerator


class Galaxy:
    """Klasa reprezentująca galaktykę"""

    def __init__(self, width: int = 20, height: int = 20, num_planets: int = 30):
        self.width = width
        self.height = height
        self.num_planets = num_planets
        self.planets: List[Planet] = []

    def generate(self):
        """Generuje galaktykę z planetami"""
        self.planets = []

        for i in range(self.num_planets):
            # Generuj losową pozycję
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)

            # Sprawdź czy pozycja nie jest zajęta
            while self.get_planet_at(x, y) is not None:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

            planet = PlanetGenerator.generate_planet(f"planet_{i}", x, y)
            self.planets.append(planet)

        # Posortuj planety po pozycji (dla lepszej czytelności)
        self.planets.sort(key=lambda p: (p.y, p.x))

    def get_planet_at(self, x: int, y: int) -> Optional[Planet]:
        """Zwraca planetę na danej pozycji"""
        for planet in self.planets:
            if planet.x == x and planet.y == y:
                return planet
        return None

    def get_planet_by_id(self, planet_id: str) -> Optional[Planet]:
        """Zwraca planetę po ID"""
        for planet in self.planets:
            if planet.id == planet_id:
                return planet
        return None

    def get_planet_by_name(self, name: str) -> Optional[Planet]:
        """Zwraca planetę po nazwie (case-insensitive)"""
        name_lower = name.lower()
        for planet in self.planets:
            if planet.name.lower() == name_lower:
                return planet
        return None

    def get_starting_planet(self) -> Planet:
        """Zwraca najlepszą planetę startową (duża, ziemska, bogate zasoby)"""
        # Znajdź planety ziemskie
        earth_like = [p for p in self.planets if p.planet_type == "ziemska"]

        if not earth_like:
            # Jeśli brak ziemskich, weź dowolną dużą
            return max(self.planets, key=lambda p: p.size * p.resources_richness)

        # Wybierz najlepszą ziemską
        return max(earth_like, key=lambda p: p.size * p.resources_richness)

    def get_nearby_planets(self, x: int, y: int, radius: int = 3) -> List[Planet]:
        """Zwraca planety w promieniu od danej pozycji"""
        nearby = []

        for planet in self.planets:
            distance = ((planet.x - x) ** 2 + (planet.y - y) ** 2) ** 0.5
            if distance <= radius:
                nearby.append(planet)

        return nearby

    def get_distance(self, planet1: Planet, planet2: Planet) -> float:
        """Oblicza dystans między planetami"""
        dx = planet1.x - planet2.x
        dy = planet1.y - planet2.y
        return (dx ** 2 + dy ** 2) ** 0.5

    def get_map_view(self, center_x: int = 10, center_y: int = 10, view_range: int = 10) -> str:
        """
        Zwraca tekstową mapę galaktyki
        Pokazuje planety jako symbole w siatce współrzędnych
        """
        lines = ["\n=== MAPA GALAKTYKI ===\n"]

        # Określ zakres widoku
        min_x = max(0, center_x - view_range)
        max_x = min(self.width, center_x + view_range)
        min_y = max(0, center_y - view_range)
        max_y = min(self.height, center_y + view_range)

        # Nagłówek z numerami kolumn
        header = "    "
        for x in range(min_x, max_x):
            header += f"{x % 10}"
        lines.append(header)
        lines.append("    " + "-" * (max_x - min_x))

        # Rysuj mapę
        for y in range(min_y, max_y):
            row = f"{y:2d} |"

            for x in range(min_x, max_x):
                planet = self.get_planet_at(x, y)

                if planet:
                    if planet.owner:
                        symbol = "●"  # Planeta gracza
                    else:
                        symbol = "○"  # Planeta neutralna
                else:
                    symbol = "·"

                row += symbol

            lines.append(row)

        lines.append("\nLegenda: ● = Twoja planeta | ○ = Planeta neutralna | · = Pusta przestrzeń")

        return "\n".join(lines)

    def get_planets_list(self, owned_only: bool = False, owner=None) -> str:
        """Zwraca listę planet"""
        lines = ["\n=== LISTA PLANET ===\n"]

        filtered_planets = self.planets
        if owned_only and owner:
            filtered_planets = [p for p in self.planets if p.owner == owner]

        if not filtered_planets:
            lines.append("Brak planet do wyświetlenia.")
            return "\n".join(lines)

        for i, planet in enumerate(filtered_planets, 1):
            owner_text = planet.owner.name if planet.owner else "Neutralna"
            lines.append(
                f"{i}. {planet.name} ({planet.x},{planet.y}) - "
                f"{planet.planet_type.capitalize()} - "
                f"Rozmiar: {planet.size} - "
                f"Właściciel: {owner_text}"
            )

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "num_planets": self.num_planets,
            "planets": [p.to_dict() for p in self.planets]
        }

    @classmethod
    def from_dict(cls, data: dict):
        galaxy = cls(data["width"], data["height"], data["num_planets"])
        # Planety zostaną odtworzone przez Player.from_dict
        # ponieważ potrzebujemy referencji do właściciela
        return galaxy
