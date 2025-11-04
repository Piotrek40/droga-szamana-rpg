"""
Contextual Action Menu - Inteligentne menu pokazujące dostępne akcje w kontekście
Automatycznie skanuje lokację i generuje numbered menu z możliwymi akcjami
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ActionOption:
    """Pojedyncza opcja akcji w menu."""
    number: int
    command: str  # Pełna komenda do wykonania
    display: str  # Tekst do wyświetlenia
    category: str  # people, objects, directions, items, other
    icon: str = ""  # Emoji/ikona


class ContextualActionMenu:
    """
    System generujący inteligentne menu kontekstowe.
    Automatycznie wykrywa co gracz może zrobić w danej lokacji.
    """

    def __init__(self, game_state):
        """
        Args:
            game_state: Referencja do stanu gry
        """
        self.game_state = game_state
        self.last_menu: List[ActionOption] = []
        self.last_menu_location: Optional[str] = None  # Track location when menu was generated

        # Ikony dla kategorii
        self.category_icons = {
            'people': '👥',
            'objects': '🔍',
            'directions': '🚪',
            'items': '📦',
            'combat': '⚔️',
            'other': '✨'
        }

    def generate_menu(self) -> List[ActionOption]:
        """
        Generuj menu akcji na podstawie obecnej lokacji i stanu gry.

        Returns:
            Lista dostępnych akcji
        """
        actions = []
        counter = 1

        # 1. LUDZIE w lokacji
        people_actions = self._get_people_actions()
        for action in people_actions:
            action.number = counter
            actions.append(action)
            counter += 1

        # 2. OBIEKTY do zbadania (interaktywne elementy lokacji)
        object_actions = self._get_object_actions()
        for action in object_actions:
            action.number = counter
            actions.append(action)
            counter += 1

        # 3. PRZEDMIOTY do wzięcia
        item_actions = self._get_item_actions()
        for action in item_actions:
            action.number = counter
            actions.append(action)
            counter += 1

        # 4. KIERUNKI (wyjścia)
        direction_actions = self._get_direction_actions()
        for action in direction_actions:
            action.number = counter
            actions.append(action)
            counter += 1

        # 5. WALKA (jeśli są wrogowie)
        combat_actions = self._get_combat_actions()
        for action in combat_actions:
            action.number = counter
            actions.append(action)
            counter += 1

        self.last_menu = actions
        self.last_menu_location = self.game_state.current_location  # Zapisz lokację
        return actions

    def _get_people_actions(self) -> List[ActionOption]:
        """Pobierz akcje związane z ludźmi w lokacji."""
        actions = []

        if not self.game_state.npc_manager:
            return actions

        current_location = self.game_state.current_location

        for npc_id, npc in self.game_state.npc_manager.npcs.items():
            # Sprawdź czy NPC jest w tej lokacji
            if hasattr(npc, 'current_location') and npc.current_location == current_location:
                # Sprawdź czy NPC żyje
                is_alive = True
                if hasattr(npc, 'combat_stats'):
                    is_alive = npc.combat_stats.health > 0

                # Nie pokazuj stworzeń jako ludzi (są w combat)
                if is_alive and npc.role != "creature":
                    # Akcja: Rozmawiaj
                    actions.append(ActionOption(
                        number=0,  # Zostanie ustawiony później
                        command=f"rozmawiaj {npc.name.lower()}",
                        display=f"Rozmawiaj z {npc.name}",
                        category='people',
                        icon='💬'
                    ))

                    # Akcja: Zbadaj
                    actions.append(ActionOption(
                        number=0,
                        command=f"zbadaj {npc.name.lower()}",
                        display=f"Zbadaj {npc.name}",
                        category='people',
                        icon='🔍'
                    ))

        return actions

    def _get_object_actions(self) -> List[ActionOption]:
        """Pobierz akcje związane z obiektami w lokacji."""
        actions = []

        if not self.game_state.prison:
            return actions

        location = self.game_state.prison.get_current_location()
        if not location:
            return actions

        # Obiekty interaktywne (zdefiniowane w lokacji)
        # Dla każdej lokacji mamy pewne standardowe obiekty do zbadania
        searchable_objects = {
            'cela_1': ['łóżko', 'prycza', 'krata', 'ściana'],
            'cela_2': ['łóżko', 'krata', 'podłoga'],
            'cela_3': ['łóżko', 'krata', 'okno'],
            'cela_4': ['łóżko', 'krata'],
            'cela_5': ['łóżko', 'krata'],
            'korytarz_centralny': ['pochodnia', 'ściana', 'drzwi'],
            'korytarz_północny': ['pochodnia', 'drzwi'],
            'korytarz_południowy': ['pochodnia', 'okno'],
            'korytarz_wschodni': ['pochodnia'],
            'korytarz_zachodni': ['pochodnia', 'drzwi'],
            'kuchnia': ['stół', 'piec', 'półka'],
            'dziedziniec': ['drzewo', 'ławka', 'studnia'],
            'zbrojownia': ['stojak', 'skrzynia', 'ściana'],
            'wartownia': ['stół', 'krzesło', 'okno']
        }

        loc_id = self.game_state.current_location
        if loc_id in searchable_objects:
            # Ogranicz do 3-4 najważniejszych obiektów
            for obj in searchable_objects[loc_id][:4]:
                actions.append(ActionOption(
                    number=0,
                    command=f"zbadaj {obj}",
                    display=f"Zbadaj {obj}",
                    category='objects',
                    icon='🔍'
                ))

        # Dodaj akcję "przeszukaj" jeśli lokacja ma ukryte przedmioty
        if hasattr(location, 'hidden_items') or True:  # Zawsze oferuj przeszukanie
            actions.append(ActionOption(
                number=0,
                command="szukaj",
                display="Przeszukaj lokację dokładnie",
                category='objects',
                icon='🔎'
            ))

        return actions

    def _get_item_actions(self) -> List[ActionOption]:
        """Pobierz akcje związane z przedmiotami na ziemi."""
        actions = []

        if not self.game_state.prison:
            return actions

        location = self.game_state.prison.get_current_location()
        if not location or not hasattr(location, 'items'):
            return actions

        # Przedmioty w lokacji
        for item in location.items:
            item_name = ""
            if hasattr(item, 'name'):
                item_name = item.name
            elif isinstance(item, dict):
                item_name = item.get('name', 'nieznany')
            elif isinstance(item, str):
                item_name = item

            if item_name:
                actions.append(ActionOption(
                    number=0,
                    command=f"weź {item_name.lower()}",
                    display=f"Weź {item_name}",
                    category='items',
                    icon='📦'
                ))

        return actions

    def _get_direction_actions(self) -> List[ActionOption]:
        """Pobierz akcje ruchu (wyjścia z lokacji)."""
        actions = []

        if not self.game_state.prison:
            return actions

        location = self.game_state.prison.get_current_location()
        if not location or not hasattr(location, 'connections'):
            return actions

        # Mapowanie kierunków na polskie nazwy i ikony
        direction_names = {
            'north': ('północ', '⬆️'),
            'south': ('południe', '⬇️'),
            'east': ('wschód', '➡️'),
            'west': ('zachód', '⬅️'),
            'up': ('góra', '🔼'),
            'down': ('dół', '🔽'),
            # Polskie nazwy
            'północ': ('północ', '⬆️'),
            'południe': ('południe', '⬇️'),
            'wschód': ('wschód', '➡️'),
            'zachód': ('zachód', '⬅️'),
            'góra': ('góra', '🔼'),
            'dół': ('dół', '🔽')
        }

        for direction, destination in location.connections.items():
            direction_lower = direction.lower()
            display_name, icon = direction_names.get(direction_lower, (direction, '🚪'))

            # Pobierz nazwę lokacji docelowej
            dest_location = self.game_state.prison.locations.get(destination)
            dest_name = dest_location.name if dest_location else destination

            actions.append(ActionOption(
                number=0,
                command=f"idź {display_name}",
                display=f"Idź {display_name} → {dest_name}",
                category='directions',
                icon=icon
            ))

        return actions

    def _get_combat_actions(self) -> List[ActionOption]:
        """Pobierz akcje walki (jeśli są wrogowie)."""
        actions = []

        if not self.game_state.npc_manager:
            return actions

        current_location = self.game_state.current_location

        # Znajdź wrogów (stworzenia lub wrogie NPCe)
        for npc_id, npc in self.game_state.npc_manager.npcs.items():
            if hasattr(npc, 'current_location') and npc.current_location == current_location:
                # Sprawdź czy NPC żyje
                is_alive = True
                if hasattr(npc, 'combat_stats'):
                    is_alive = npc.combat_stats.health > 0

                # Stworzenia lub wrogie NPCe
                is_hostile = npc.role == "creature" or (
                    hasattr(npc, 'relationship') and
                    npc.relationship.get('player', 0) < -30
                )

                if is_alive and is_hostile:
                    actions.append(ActionOption(
                        number=0,
                        command=f"atakuj {npc.name.lower()}",
                        display=f"Atakuj {npc.name}",
                        category='combat',
                        icon='⚔️'
                    ))

        return actions

    def display_menu(self, interface) -> None:
        """
        Wyświetl menu kontekstowe.

        Args:
            interface: GameInterface do wyświetlania
        """
        actions = self.generate_menu()

        if not actions:
            interface.print("💡 Nie ma dostępnych akcji kontekstowych.", 'dim')
            interface.print("   Spróbuj 'rozejrzyj' lub 'pomoc' aby zobaczyć co możesz zrobić.", 'dim')
            return

        # Header
        interface.print("╔════════════════ DOSTĘPNE AKCJE ═════════════════╗", 'yellow')

        # Grupuj akcje po kategoriach
        by_category = {}
        for action in actions:
            if action.category not in by_category:
                by_category[action.category] = []
            by_category[action.category].append(action)

        # Kolejność wyświetlania kategorii
        category_order = ['people', 'items', 'objects', 'directions', 'combat', 'other']
        category_labels = {
            'people': 'LUDZIE',
            'items': 'PRZEDMIOTY',
            'objects': 'DO ZBADANIA',
            'directions': 'WYJŚCIA',
            'combat': 'WALKA',
            'other': 'INNE'
        }

        for category in category_order:
            if category in by_category:
                # Nagłówek kategorii
                label = category_labels.get(category, category.upper())
                icon = self.category_icons.get(category, '')
                interface.print(f"║ {icon} {label}:", 'bright_yellow')

                # Akcje w kategorii
                for action in by_category[category]:
                    # Format: "║   1. Rozmawiaj z Piotrem"
                    display_line = f"║   {action.number}. {action.display}"
                    # Dopełnij spacjami do 49 znaków (50 minus ║)
                    padding = 49 - len(display_line)
                    display_line += " " * padding + "║"
                    interface.print(display_line, 'white')

                interface.print("║" + " " * 49 + "║", 'yellow')

        # Footer z quick commands
        interface.print("╠═════════════════════════════════════════════════╣", 'yellow')
        interface.print("║ Quick: [I]nventory [Q]uests [S]tatus [H]elp   ║", 'cyan')
        interface.print("║        [N]orth [S]outh [E]ast [W]est          ║", 'cyan')
        interface.print("╚═════════════════════════════════════════════════╝", 'yellow')

        # Hint
        interface.print("\n💡 Wpisz numer akcji lub komendę tekstową", 'bright_yellow')

    def get_command_by_number(self, number: int) -> Optional[str]:
        """
        Pobierz komendę na podstawie numeru z ostatniego menu.

        Args:
            number: Numer akcji

        Returns:
            Komenda do wykonania lub None
        """
        for action in self.last_menu:
            if action.number == number:
                return action.command
        return None

    def is_valid_number(self, number: int) -> bool:
        """
        Sprawdź czy numer jest prawidłowy w ostatnim menu.

        Args:
            number: Numer do sprawdzenia

        Returns:
            True jeśli prawidłowy
        """
        return any(action.number == number for action in self.last_menu)

    def is_menu_valid(self) -> bool:
        """
        Sprawdź czy ostatnie menu jest nadal aktualne.
        Menu jest nieaktualne gdy lokacja się zmieniła.

        Returns:
            True jeśli menu jest aktualne
        """
        # Brak menu = nieaktualne
        if not self.last_menu:
            return False

        # Sprawdź czy lokacja się zmieniła
        current_location = self.game_state.current_location
        return current_location == self.last_menu_location

    def invalidate_menu(self):
        """Unieważnij ostatnie menu (wymuś regenerację)."""
        self.last_menu = []
        self.last_menu_location = None
