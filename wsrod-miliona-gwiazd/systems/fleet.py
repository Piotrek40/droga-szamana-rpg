"""
System floty i statków kosmicznych
Różne typy statków, formacje i ruchy
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from systems.resources import ResourcePool


@dataclass
class Ship:
    """Klasa reprezentująca pojedynczy statek"""

    ship_type: str
    name: str
    hull: int  # Wytrzymałość
    max_hull: int
    attack: int
    defense: int
    speed: int  # Zasięg ruchu na turę

    def is_destroyed(self) -> bool:
        """Sprawdza czy statek został zniszczony"""
        return self.hull <= 0

    def take_damage(self, damage: int):
        """Otrzymuje obrażenia"""
        actual_damage = max(0, damage - self.defense)
        self.hull = max(0, self.hull - actual_damage)

    def repair(self, amount: int):
        """Naprawia statek"""
        self.hull = min(self.max_hull, self.hull + amount)

    def to_dict(self) -> dict:
        return {
            "ship_type": self.ship_type,
            "name": self.name,
            "hull": self.hull,
            "max_hull": self.max_hull,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class ShipBlueprint:
    """Szablon statku z kosztami budowy"""

    def __init__(self, ship_type: str, name: str, cost: ResourcePool,
                 hull: int, attack: int, defense: int, speed: int,
                 build_time: int, required_tech: Optional[str] = None):
        self.ship_type = ship_type
        self.name = name
        self.cost = cost
        self.hull = hull
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.build_time = build_time
        self.required_tech = required_tech

    def build_ship(self) -> Ship:
        """Tworzy nowy statek z blueprintu"""
        return Ship(
            ship_type=self.ship_type,
            name=self.name,
            hull=self.hull,
            max_hull=self.hull,
            attack=self.attack,
            defense=self.defense,
            speed=self.speed
        )


# Definicje typów statków
SHIP_BLUEPRINTS = {
    "zwiadowca": ShipBlueprint(
        ship_type="zwiadowca",
        name="Zwiadowca",
        cost=ResourcePool(metale=100, kredyty=200),
        hull=50,
        attack=10,
        defense=5,
        speed=3,
        build_time=2
    ),

    "niszczyciel": ShipBlueprint(
        ship_type="niszczyciel",
        name="Niszczyciel",
        cost=ResourcePool(metale=300, krysztaly=100, kredyty=600),
        hull=150,
        attack=40,
        defense=20,
        speed=2,
        build_time=4,
        required_tech="lasery_1"
    ),

    "krazownik": ShipBlueprint(
        ship_type="krazownik",
        name="Krążownik",
        cost=ResourcePool(metale=600, krysztaly=300, kredyty=1200),
        hull=300,
        attack=70,
        defense=40,
        speed=2,
        build_time=6,
        required_tech="lasery_2"
    ),

    "pancernik": ShipBlueprint(
        ship_type="pancernik",
        name="Pancernik",
        cost=ResourcePool(metale=1200, krysztaly=600, antymateria=50, kredyty=2500),
        hull=600,
        attack=120,
        defense=80,
        speed=1,
        build_time=10,
        required_tech="tarcze_1"
    ),

    "transportowiec": ShipBlueprint(
        ship_type="transportowiec",
        name="Transportowiec",
        cost=ResourcePool(metale=200, kredyty=400),
        hull=100,
        attack=5,
        defense=10,
        speed=2,
        build_time=3
    ),

    "kolonizator": ShipBlueprint(
        ship_type="kolonizator",
        name="Statek Kolonizacyjny",
        cost=ResourcePool(metale=500, krysztaly=200, populacja=1000, kredyty=1500),
        hull=150,
        attack=0,
        defense=15,
        speed=1,
        build_time=8,
        required_tech="kolonizacja_1"
    )
}


@dataclass
class Fleet:
    """Flota statków"""

    id: str
    name: str
    ships: List[Ship] = field(default_factory=list)
    location: Tuple[int, int] = (0, 0)  # Koordynaty w galaktyce
    destination: Optional[Tuple[int, int]] = None
    owner_id: str = ""

    def add_ship(self, ship: Ship):
        """Dodaje statek do floty"""
        self.ships.append(ship)

    def remove_destroyed_ships(self):
        """Usuwa zniszczone statki z floty"""
        self.ships = [ship for ship in self.ships if not ship.is_destroyed()]

    def get_total_firepower(self) -> int:
        """Zwraca łączną siłę ognia floty"""
        return sum(ship.attack for ship in self.ships)

    def get_total_defense(self) -> int:
        """Zwraca łączną obronę floty"""
        return sum(ship.defense for ship in self.ships)

    def get_fleet_speed(self) -> int:
        """Zwraca prędkość floty (najwolniejszy statek)"""
        if not self.ships:
            return 0
        return min(ship.speed for ship in self.ships)

    def is_empty(self) -> bool:
        """Sprawdza czy flota jest pusta"""
        return len(self.ships) == 0

    def move(self):
        """Porusza flotę w kierunku celu"""
        if self.destination is None:
            return

        # Oblicz dystans
        dx = self.destination[0] - self.location[0]
        dy = self.destination[1] - self.location[1]
        distance = (dx**2 + dy**2) ** 0.5

        speed = self.get_fleet_speed()

        if distance <= speed:
            # Dotarła do celu
            self.location = self.destination
            self.destination = None
        else:
            # Przesuń w kierunku celu
            ratio = speed / distance
            new_x = self.location[0] + int(dx * ratio)
            new_y = self.location[1] + int(dy * ratio)
            self.location = (new_x, new_y)

    def update_status(self):
        """Aktualizuje stan floty (usuwa zniszczone statki)"""
        self.remove_destroyed_ships()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ships": [ship.to_dict() for ship in self.ships],
            "location": self.location,
            "destination": self.destination,
            "owner_id": self.owner_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        ships = [Ship.from_dict(s) for s in data["ships"]]
        return cls(
            id=data["id"],
            name=data["name"],
            ships=ships,
            location=tuple(data["location"]),
            destination=tuple(data["destination"]) if data.get("destination") else None,
            owner_id=data.get("owner_id", "")
        )


class CombatResolver:
    """Rozwiązuje walkę między flotami"""

    @staticmethod
    def resolve_combat(attacker: Fleet, defender: Fleet) -> dict:
        """
        Rozwiązuje walkę między dwiema flotami
        Zwraca raport z walki
        """
        rounds = 0
        max_rounds = 10

        initial_attacker_ships = len(attacker.ships)
        initial_defender_ships = len(defender.ships)

        while rounds < max_rounds and not attacker.is_empty() and not defender.is_empty():
            rounds += 1

            # Atak z obu stron jednocześnie
            attacker_damage = attacker.get_total_firepower()
            defender_damage = defender.get_total_firepower()

            # Rozdziel obrażenia równomiernie między statki
            CombatResolver._distribute_damage(defender.ships, attacker_damage)
            CombatResolver._distribute_damage(attacker.ships, defender_damage)

            # Usuń zniszczone statki
            attacker.remove_destroyed_ships()
            defender.remove_destroyed_ships()

        # Ustal zwycięzcę
        if attacker.is_empty() and defender.is_empty():
            winner = "remis"
        elif attacker.is_empty():
            winner = "defender"
        elif defender.is_empty():
            winner = "attacker"
        else:
            winner = "nierozstrzygnięte"

        return {
            "rounds": rounds,
            "winner": winner,
            "attacker_losses": initial_attacker_ships - len(attacker.ships),
            "defender_losses": initial_defender_ships - len(defender.ships),
            "attacker_remaining": len(attacker.ships),
            "defender_remaining": len(defender.ships)
        }

    @staticmethod
    def _distribute_damage(ships: List[Ship], total_damage: int):
        """Rozdziela obrażenia równomiernie między statki"""
        if not ships:
            return

        damage_per_ship = total_damage // len(ships)

        for ship in ships:
            ship.take_damage(damage_per_ship)
