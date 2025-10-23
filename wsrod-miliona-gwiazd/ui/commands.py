"""
Parser i obsługa komend gracza
"""

import re
from typing import List, Optional, Tuple


class CommandParser:
    """Parser komend gracza"""

    @staticmethod
    def parse(command_text: str) -> Tuple[str, List[str]]:
        """
        Parsuje tekst komendy na komendę i argumenty
        Obsługuje cudzysłowy dla argumentów z spacjami

        Przykłady:
            "buduj kopalnia Alpha" -> ("buduj", ["kopalnia", "Alpha"])
            'planeta "Alpha Prime"' -> ("planeta", ["Alpha Prime"])
        """
        # Usuń zbędne białe znaki
        command_text = command_text.strip()

        if not command_text:
            return ("", [])

        # Regex do wyciągnięcia słów i fraz w cudzysłowach
        pattern = r'"([^"]+)"|\'([^\']+)\'|(\S+)'
        matches = re.findall(pattern, command_text)

        # Spłaszcz wyniki (regex zwraca tuple)
        tokens = []
        for match in matches:
            # Weź pierwszą niepustą grupę
            token = match[0] or match[1] or match[2]
            tokens.append(token)

        if not tokens:
            return ("", [])

        command = tokens[0].lower()
        args = tokens[1:]

        return (command, args)

    @staticmethod
    def normalize_planet_name(name: str) -> str:
        """Normalizuje nazwę planety (usuwa cudzysłowy, case insensitive)"""
        return name.strip().strip('"').strip("'")


class CommandHandler:
    """Obsługuje wykonywanie komend"""

    def __init__(self, game_engine):
        self.engine = game_engine

    def execute(self, command: str, args: List[str]) -> bool:
        """
        Wykonuje komendę
        Zwraca True jeśli gra powinna kontynuować, False jeśli zakończyć
        """
        from ui.interface import GameInterface
        from systems.buildings import create_building

        # Komendy menu
        if command == "koniec" or command == "quit" or command == "exit":
            if GameInterface.confirm("Czy na pewno chcesz zakończyć?"):
                return False

        elif command == "pomoc" or command == "help" or command == "?":
            GameInterface.show_help()

        # Komendy informacyjne
        elif command == "status":
            print(self.engine.player.get_status())

        elif command == "planety":
            if not self.engine.player.planets:
                GameInterface.show_error("Nie posiadasz żadnych planet!")
            else:
                print("\n=== TWOJE PLANETY ===\n")
                for i, planet in enumerate(self.engine.player.planets, 1):
                    print(f"{i}. {planet.name} ({planet.x},{planet.y}) - "
                          f"{planet.planet_type.capitalize()} - "
                          f"Rozmiar: {planet.size}")

        elif command == "planeta":
            if not args:
                GameInterface.show_error("Podaj nazwę planety: planeta <nazwa>")
            else:
                planet_name = CommandParser.normalize_planet_name(" ".join(args))
                planet = self.engine.player.get_planet_by_name(planet_name)

                if not planet:
                    # Spróbuj też w całej galaktyce
                    planet = self.engine.galaxy.get_planet_by_name(planet_name)

                if planet:
                    print(planet.get_description())
                else:
                    GameInterface.show_error(f"Nie znaleziono planety: {planet_name}")

        elif command == "mapa":
            # Centrum na pierwszej planecie gracza
            if self.engine.player.planets:
                center_planet = self.engine.player.planets[0]
                print(self.engine.galaxy.get_map_view(center_planet.x, center_planet.y, 10))
            else:
                print(self.engine.galaxy.get_map_view())

        elif command == "wszystkie_planety":
            print(self.engine.galaxy.get_planets_list())

        # Komendy budowy
        elif command == "buduj":
            if len(args) < 2:
                GameInterface.show_error("Użycie: buduj <typ_budynku> <nazwa_planety>")
                GameInterface.show_building_types()
            else:
                building_type = args[0].lower()
                planet_name = CommandParser.normalize_planet_name(" ".join(args[1:]))

                planet = self.engine.player.get_planet_by_name(planet_name)

                if not planet:
                    GameInterface.show_error(f"Nie posiadasz planety: {planet_name}")
                else:
                    # Sprawdź czy można zbudować
                    if not planet.can_build(building_type):
                        GameInterface.show_error(f"Nie można zbudować {building_type} na {planet.name}")
                        GameInterface.show_error(f"Brak dostępnych slotów budowlanych!")
                    else:
                        # Utwórz budynek
                        building = create_building(building_type)

                        if not building:
                            GameInterface.show_error(f"Nieznany typ budynku: {building_type}")
                            GameInterface.show_building_types()
                        else:
                            cost = building.get_cost()

                            if not self.engine.player.resources.can_afford(cost):
                                GameInterface.show_error(f"Niewystarczające zasoby! Potrzeba:")
                                print(f"  {cost}")
                            else:
                                # Zbuduj
                                self.engine.player.resources = self.engine.player.resources - cost
                                building.construction_time = 2  # 2 tury budowy
                                building.operational = False
                                planet.add_building(building)

                                GameInterface.show_success(
                                    f"Rozpoczęto budowę: {building.name} na planecie {planet.name}"
                                )

        # Komendy badań
        elif command == "badania":
            print(self.engine.player.get_research_status())

        elif command == "badaj":
            if not args:
                GameInterface.show_error("Użycie: badaj <id_technologii>")
                # Pokaż dostępne
                available = self.engine.player.technology_tree.get_available_technologies(
                    self.engine.player
                )
                if available:
                    print("\nDostępne technologie:")
                    for tech in available[:10]:
                        print(f"  {tech.id} - {tech.name}")
            else:
                tech_id = args[0]

                if self.engine.player.current_research:
                    GameInterface.show_error("Już prowadzisz badania! Poczekaj aż się skończą.")
                else:
                    if self.engine.player.start_research(tech_id):
                        GameInterface.show_success(f"Rozpoczęto badanie: {tech_id}")
                    else:
                        GameInterface.show_error(f"Nie można rozpocząć badania: {tech_id}")
                        GameInterface.show_error("Sprawdź wymagania i zasoby")

        # Komendy floty
        elif command == "floty":
            if not self.engine.player.fleets:
                print("\nNie posiadasz żadnych flot.")
            else:
                print("\n=== TWOJE FLOTY ===\n")
                for i, fleet in enumerate(self.engine.player.fleets, 1):
                    print(f"{i}. {fleet.name} - {len(fleet.ships)} statków - "
                          f"Pozycja: ({fleet.location[0]}, {fleet.location[1]})")

        # Następna tura
        elif command == "następna" or command == "next" or command == "n":
            self.engine.next_turn()
            GameInterface.show_success(f"Przeszedłeś do tury {self.engine.current_turn}")

            # Pokaż automatycznie przychody
            income = self.engine.player.get_total_income()
            if income:
                print(f"\nPrzychód tej tury:")
                print(f"  {income}")

            # Sprawdź koniec gry
            if self.engine.game_over:
                GameInterface.show_game_over(self.engine.victory)
                return False

        # Zapis/odczyt
        elif command == "zapisz" or command == "save":
            slot = args[0] if args else "autosave"
            if self.engine.save_game(slot):
                GameInterface.show_success(f"Gra zapisana: {slot}")
            else:
                GameInterface.show_error("Nie udało się zapisać gry")

        elif command == "wczytaj" or command == "load":
            if not args:
                GameInterface.show_error("Użycie: wczytaj <nazwa_slotu>")
            else:
                slot = args[0]
                if self.engine.load_game(slot):
                    GameInterface.show_success(f"Gra wczytana: {slot}")
                else:
                    GameInterface.show_error(f"Nie udało się wczytać gry: {slot}")

        # Nieznana komenda
        else:
            GameInterface.show_error(f"Nieznana komenda: {command}")
            GameInterface.show_info("Wpisz 'pomoc' aby zobaczyć dostępne komendy")

        return True
