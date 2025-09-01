#!/usr/bin/env python3
"""
System interfejsu kontekstowego dla Droga Szamana RPG.
Oferuje menu kontekstowe, podpowiedzi i intuicyjną nawigację.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
from enum import Enum
import os
import sys
import json
from dataclasses import dataclass


class ActionType(Enum):
    """Typy akcji dostępnych w grze."""
    MOVE = "move"
    INTERACT = "interact"
    EXAMINE = "examine"
    TALK = "talk"
    COMBAT = "combat"
    INVENTORY = "inventory"
    SYSTEM = "system"
    QUEST = "quest"
    CRAFT = "craft"


@dataclass
class ContextualAction:
    """Reprezentuje akcję kontekstową."""
    key: str  # Klawisz lub numer
    label: str  # Opis akcji
    action_type: ActionType
    command: str  # Komenda do wykonania
    icon: str = ""  # Opcjonalna ikona
    enabled: bool = True  # Czy akcja jest dostępna
    description: str = ""  # Dłuższy opis (tooltip)


class ContextualInterface:
    """System interfejsu kontekstowego z menu i podpowiedziami."""
    
    def __init__(self, game_state, command_parser):
        """Inicjalizacja interfejsu kontekstowego."""
        self.game_state = game_state
        self.command_parser = command_parser
        
        # Import menedżera kontekstu
        from core.context_manager import ContextManager
        self.context_manager = ContextManager(game_state)
        
        # Wczytaj teksty UI z JSON
        self.ui_texts = self._load_ui_texts()
        self.commands_config = self._load_commands_config()
        
        # Kolory dla różnych typów akcji
        self.action_colors = {
            ActionType.MOVE: '\033[36m',       # Cyan
            ActionType.INTERACT: '\033[33m',   # Yellow
            ActionType.EXAMINE: '\033[35m',    # Magenta
            ActionType.TALK: '\033[92m',       # Bright Green
            ActionType.COMBAT: '\033[91m',     # Bright Red
            ActionType.INVENTORY: '\033[94m',  # Bright Blue
            ActionType.SYSTEM: '\033[90m',     # Gray
            ActionType.QUEST: '\033[93m',      # Bright Yellow
            ActionType.CRAFT: '\033[95m'       # Bright Magenta
        }
        
        self.reset_color = '\033[0m'
        self.bold = '\033[1m'
        
        # Cache dla ostatnich akcji
        self.last_actions = []
        self.quick_slots = {}  # Szybkie sloty 1-9
        
        # Tryb interfejsu
        self.mode = "exploration"  # exploration, combat, dialogue, inventory
    
    def _load_ui_texts(self) -> Dict:
        """Wczytaj teksty interfejsu z pliku JSON."""
        try:
            with open('data/ui_texts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Ostrzeżenie: Nie znaleziono pliku ui_texts.json")
            return {}
    
    def _load_commands_config(self) -> Dict:
        """Wczytaj konfigurację komend z pliku JSON."""
        try:
            with open('data/commands.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Ostrzeżenie: Nie znaleziono pliku commands.json")
            return {}
        
    def get_contextual_actions(self) -> List[ContextualAction]:
        """Pobierz akcje dostępne w aktualnym kontekście."""
        actions = []
        
        if not self.game_state.player:
            return actions
        
        # Pobierz pełny kontekst z menedżera
        context = self.context_manager.get_current_context()
        
        # Akcje zależne od trybu
        if self.mode == "exploration":
            actions = self._get_exploration_actions_v2(context)
        elif self.mode == "combat":
            actions = self._get_combat_actions()
        elif self.mode == "dialogue":
            actions = self._get_dialogue_actions()
        elif self.mode == "inventory":
            actions = self._get_inventory_actions()
        
        # Zawsze dodaj akcje systemowe
        actions.extend(self._get_system_actions())
        
        # Przypisz klawisze numeryczne
        for i, action in enumerate(actions[:9], 1):
            action.key = str(i)
        
        # Reszta dostaje litery
        for i, action in enumerate(actions[9:], 0):
            if not action.key:
                action.key = chr(97 + i)  # a, b, c...
        
        self.last_actions = actions
        return actions
    
    def _get_exploration_actions_v2(self, context: Dict) -> List[ContextualAction]:
        """Akcje dostępne podczas eksploracji - wersja 2 z menedżerem kontekstu."""
        actions = []
        
        # Akcje ruchu - tylko rzeczywiste wyjścia
        exits = context.get('exits', {})
        directions = {
            'północ': ('↑', 'Idź na północ'),
            'południe': ('↓', 'Idź na południe'),
            'wschód': ('→', 'Idź na wschód'),
            'zachód': ('←', 'Idź na zachód'),
            'góra': ('↗', 'Idź do góry'),
            'dół': ('↘', 'Idź na dół')
        }
        
        for direction, target in exits.items():
            if direction in directions:
                icon, label = directions[direction]
            else:
                icon, label = '→', f'Idź {direction}'
            
            actions.append(ContextualAction(
                key="",
                label=f"{icon} {label}",
                action_type=ActionType.MOVE,
                command=f"idź {direction}",
                icon=icon,
                description=f"Przejdź do: {target}"
            ))
        
        # Rozejrzyj się - zawsze dostępne
        actions.append(ContextualAction(
            key="",
            label="👁️ Rozejrzyj się",
            action_type=ActionType.EXAMINE,
            command="rozejrzyj",
            icon="👁️",
            description="Dokładnie obejrzyj obecną lokację"
        ))
        
        # Szukaj - tylko jeśli są przedmioty lub obiekty
        if context.get('items') or context.get('objects'):
            actions.append(ContextualAction(
                key="",
                label="🔍 Przeszukaj obszar",
                action_type=ActionType.INTERACT,
                command="szukaj",
                icon="🔍",
                description="Przeszukaj lokację w poszukiwaniu ukrytych przedmiotów"
            ))
        
        # NPCe - tylko rzeczywiści NPCowie w lokacji
        for npc in context.get('npcs', []):
            actions.append(ContextualAction(
                key="",
                label=f"💬 Rozmawiaj z {npc.display_name}",
                action_type=ActionType.TALK,
                command=f"rozmawiaj {npc.name.split()[0]}",
                icon="💬",
                description=f"Porozmawiaj z {npc.display_name}"
            ))
        
        # Przedmioty - tylko rzeczywiste przedmioty
        for item in context.get('items', [])[:3]:  # Max 3 przedmioty
            actions.append(ContextualAction(
                key="",
                label=f"✋ Weź {item.display_name}",
                action_type=ActionType.INTERACT,
                command=f"weź {item.name}",
                icon="✋",
                description=f"Podnieś {item.display_name}"
            ))
        
        # Obiekty do zbadania - tylko rzeczywiste obiekty
        for obj in context.get('objects', [])[:2]:  # Max 2 obiekty
            actions.append(ContextualAction(
                key="",
                label=f"🔎 Zbadaj {obj.display_name}",
                action_type=ActionType.EXAMINE,
                command=f"zbadaj {obj.name}",
                icon="🔎",
                description=f"Dokładnie zbadaj {obj.display_name}"
            ))
        
        return actions
    
    def _get_exploration_actions(self) -> List[ContextualAction]:
        """Akcje dostępne podczas eksploracji."""
        actions = []
        
        # Pobierz aktualną lokację
        if self.game_state.prison:
            current_loc = self.game_state.prison.get_current_location()
            
            if current_loc:
                # Akcje ruchu - dodaj tylko dostępne kierunki
                directions = {
                    'północ': ('↑', 'Idź na północ'),
                    'południe': ('↓', 'Idź na południe'),
                    'wschód': ('→', 'Idź na wschód'),
                    'zachód': ('←', 'Idź na zachód')
                }
                
                for direction, (icon, label) in directions.items():
                    if direction in current_loc.connections:
                        target = current_loc.connections[direction]
                        actions.append(ContextualAction(
                            key="",
                            label=f"{icon} {label}",
                            action_type=ActionType.MOVE,
                            command=f"idź {direction}",
                            icon=icon,
                            description=f"Przejdź do: {target}"
                        ))
                
                # Rozejrzyj się
                actions.append(ContextualAction(
                    key="",
                    label="👁️ Rozejrzyj się",
                    action_type=ActionType.EXAMINE,
                    command="rozejrzyj",
                    icon="👁️",
                    description="Dokładnie obejrzyj obecną lokację"
                ))
                
                # Szukaj
                actions.append(ContextualAction(
                    key="",
                    label="🔍 Przeszukaj obszar",
                    action_type=ActionType.INTERACT,
                    command="szukaj",
                    icon="🔍",
                    description="Przeszukaj lokację w poszukiwaniu ukrytych przedmiotów"
                ))
                
                # NPCe w lokacji
                if self.game_state.npc_manager:
                    npcs_here = []
                    for npc_id, npc in self.game_state.npc_manager.npcs.items():
                        if hasattr(npc, 'current_location') and npc.current_location == self.game_state.current_location:
                            npcs_here.append(npc)
                    
                    for npc in npcs_here[:3]:  # Max 3 NPCów w menu
                        actions.append(ContextualAction(
                            key="",
                            label=f"💬 Rozmawiaj z {npc.name}",
                            action_type=ActionType.TALK,
                            command=f"rozmawiaj {npc.name.split()[0].lower()}",
                            icon="💬",
                            description=f"Porozmawiaj z {npc.name}"
                        ))
                
                # Przedmioty w lokacji
                if hasattr(current_loc, 'items') and current_loc.items:
                    for item in current_loc.items[:2]:  # Max 2 przedmioty
                        actions.append(ContextualAction(
                            key="",
                            label=f"✋ Weź {item.name}",
                            action_type=ActionType.INTERACT,
                            command=f"weź {item.name}",
                            icon="✋",
                            description=f"Podnieś {item.name}"
                        ))
                
                # Specjalne obiekty do zbadania
                if hasattr(current_loc, 'interactive_objects'):
                    for obj in current_loc.interactive_objects[:2]:
                        actions.append(ContextualAction(
                            key="",
                            label=f"🔎 Zbadaj {obj}",
                            action_type=ActionType.EXAMINE,
                            command=f"zbadaj {obj}",
                            icon="🔎",
                            description=f"Dokładnie zbadaj {obj}"
                        ))
        
        return actions
    
    def _get_combat_actions(self) -> List[ContextualAction]:
        """Akcje dostępne podczas walki."""
        actions = []
        
        # Podstawowe akcje bojowe
        actions.extend([
            ContextualAction(
                key="",
                label="⚔️ Atakuj",
                action_type=ActionType.COMBAT,
                command="atakuj",
                icon="⚔️",
                description="Wykonaj atak na przeciwnika"
            ),
            ContextualAction(
                key="",
                label="🛡️ Broń się",
                action_type=ActionType.COMBAT,
                command="broń",
                icon="🛡️",
                description="Przyjmij postawę obronną"
            ),
            ContextualAction(
                key="",
                label="💨 Unik",
                action_type=ActionType.COMBAT,
                command="unik",
                icon="💨",
                description="Spróbuj uniknąć następnego ataku"
            ),
            ContextualAction(
                key="",
                label="🏃 Uciekaj",
                action_type=ActionType.COMBAT,
                command="uciekaj",
                icon="🏃",
                description="Spróbuj uciec z walki"
            )
        ])
        
        return actions
    
    def _get_dialogue_actions(self) -> List[ContextualAction]:
        """Akcje dostępne podczas dialogu."""
        # To będzie wypełnione dynamicznie podczas dialogu
        return []
    
    def _get_inventory_actions(self) -> List[ContextualAction]:
        """Akcje dostępne w ekwipunku."""
        actions = []
        
        if self.game_state.player and hasattr(self.game_state.player, 'equipment'):
            # Pokaż pierwsze 3 przedmioty
            for item in self.game_state.player.equipment.backpack[:3]:
                actions.append(ContextualAction(
                    key="",
                    label=f"🎯 Użyj {item.name}",
                    action_type=ActionType.INVENTORY,
                    command=f"użyj {item.name}",
                    icon="🎯",
                    description=f"Użyj przedmiotu: {item.name}"
                ))
        
        return actions
    
    def _get_system_actions(self) -> List[ContextualAction]:
        """Akcje systemowe zawsze dostępne."""
        actions = [
            ContextualAction(
                key="i",
                label="🎒 Ekwipunek",
                action_type=ActionType.INVENTORY,
                command="ekwipunek",
                icon="🎒",
                description="Pokaż ekwipunek"
            ),
            ContextualAction(
                key="s",
                label="📊 Status",
                action_type=ActionType.SYSTEM,
                command="status",
                icon="📊",
                description="Pokaż status postaci"
            ),
            ContextualAction(
                key="q",
                label="📜 Zadania",
                action_type=ActionType.QUEST,
                command="zadania",
                icon="📜",
                description="Pokaż aktywne zadania"
            ),
            ContextualAction(
                key="m",
                label="🗺️ Mapa",
                action_type=ActionType.SYSTEM,
                command="mapa",
                icon="🗺️",
                description="Pokaż mapę okolicy"
            ),
            ContextualAction(
                key="h",
                label="❓ Pomoc",
                action_type=ActionType.SYSTEM,
                command="pomoc",
                icon="❓",
                description="Pokaż pomoc"
            )
        ]
        
        return actions
    
    def display_context_menu(self):
        """Wyświetl menu kontekstowe."""
        actions = self.get_contextual_actions()
        
        if not actions:
            return
        
        # Grupuj akcje po typie
        grouped = {}
        for action in actions:
            if action.action_type not in grouped:
                grouped[action.action_type] = []
            grouped[action.action_type].append(action)
        
        # Wyświetl menu
        print("\n" + "="*60)
        print(f"{self.bold}📍 DOSTĘPNE AKCJE:{self.reset_color}")
        print("-"*60)
        
        # Priorytet wyświetlania
        priority = [
            ActionType.MOVE,
            ActionType.TALK,
            ActionType.INTERACT,
            ActionType.EXAMINE,
            ActionType.COMBAT,
            ActionType.INVENTORY,
            ActionType.QUEST,
            ActionType.CRAFT,
            ActionType.SYSTEM
        ]
        
        for action_type in priority:
            if action_type in grouped:
                # Nagłówek grupy
                color = self.action_colors.get(action_type, '')
                
                for action in grouped[action_type]:
                    if action.enabled:
                        key_display = f"[{action.key}]" if action.key else "   "
                        print(f"{color}{key_display} {action.label}{self.reset_color}")
                    else:
                        print(f"\033[90m{key_display} {action.label} (niedostępne){self.reset_color}")
        
        print("="*60)
    
    def display_quick_help(self):
        """Wyświetl szybką pomoc kontekstową."""
        print(f"\n{self.bold}💡 WSKAZÓWKA:{self.reset_color}", end=" ")
        
        if self.mode == "exploration":
            print("Wpisz numer akcji (1-9) lub użyj pełnej komendy.")
        elif self.mode == "combat":
            print("Walczysz! Wybierz akcję bojową szybko!")
        elif self.mode == "dialogue":
            print("Wybierz opcję dialogową numerem.")
        
        print(f"Skróty: [I]nwentarz [S]tatus [Q]uesty [M]apa [H]elp")
    
    def process_contextual_input(self, user_input: str) -> Tuple[bool, str]:
        """Przetwórz input użytkownika w kontekście menu."""
        # Sprawdź czy to numer akcji
        if user_input.isdigit():
            num = int(user_input)
            if 1 <= num <= len(self.last_actions):
                action = self.last_actions[num - 1]
                return self.command_parser.parse_and_execute(action.command)
        
        # Sprawdź skróty literowe
        if len(user_input) == 1:
            for action in self.last_actions:
                if action.key.lower() == user_input.lower():
                    return self.command_parser.parse_and_execute(action.command)
        
        # Waliduj komendę przed wykonaniem
        valid, error_msg = self.context_manager.validate_command(user_input)
        if not valid:
            return False, error_msg
        
        # Normalizuj komendę i cel
        action, target = self.context_manager.get_normalized_target(user_input)
        if target:
            normalized_command = f"{action} {target}"
        else:
            normalized_command = user_input
        
        # Wykonaj znormalizowaną komendę
        return self.command_parser.parse_and_execute(normalized_command)
    
    def display_location_with_context(self, location_desc: str):
        """Wyświetl opis lokacji z kontekstem."""
        # Wyczyść ekran
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Nagłówek
        print("╔" + "═"*58 + "╗")
        print("║" + " DROGA SZAMANA - RPG ".center(58) + "║")
        print("╚" + "═"*58 + "╝")
        
        # Opis lokacji
        print("\n" + location_desc)
        
        # Menu kontekstowe
        self.display_context_menu()
        
        # Szybka pomoc
        self.display_quick_help()
    
    def show_dialogue_options(self, npc_name: str, dialogue_options: List[str]) -> int:
        """Pokaż opcje dialogowe i pobierz wybór."""
        print(f"\n{self.bold}💬 Rozmawiasz z {npc_name}:{self.reset_color}")
        print("-"*40)
        
        for i, option in enumerate(dialogue_options, 1):
            print(f"[{i}] {option}")
        
        print("-"*40)
        print("Wybierz opcję dialogową (numer): ", end="")
        
        try:
            choice = input().strip()
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(dialogue_options):
                    return num - 1
        except:
            pass
        
        return 0  # Domyślnie pierwsza opcja
    
    def show_inventory_grid(self):
        """Pokaż ekwipunek w formie siatki."""
        if not self.game_state.player:
            return
        
        equipment = self.game_state.player.equipment
        
        print("\n╔" + "═"*58 + "╗")
        print("║" + " EKWIPUNEK ".center(58) + "║")
        print("╠" + "═"*58 + "╣")
        
        # Założone przedmioty
        print("║ ZAŁOŻONE:".ljust(59) + "║")
        if equipment.equipped:
            for slot, item in equipment.equipped.items():
                line = f"║   {slot}: {item}".ljust(59) + "║"
                print(line)
        else:
            print("║   (brak)".ljust(59) + "║")
        
        print("╠" + "═"*58 + "╣")
        
        # Plecak w siatce 3x3
        print("║ PLECAK:".ljust(59) + "║")
        items = equipment.backpack
        
        for row in range(0, len(items), 3):
            line = "║ "
            for col in range(3):
                idx = row + col
                if idx < len(items):
                    item_str = f"[{idx+1}] {items[idx].name[:15]}"
                    line += item_str.ljust(18)
                else:
                    line += " " * 18
            line = line.ljust(59) + "║"
            print(line)
        
        print("╠" + "═"*58 + "╣")
        print(f"║ Złoto: {equipment.gold}".ljust(59) + "║")
        print("╚" + "═"*58 + "╝")
        
        print("\nAkcje: [numer] użyj przedmiot, [E]kwipuj, [W]yrzuć, [P]owrót")
    
    def show_map_ascii(self):
        """Pokaż mapę ASCII z aktualną pozycją."""
        if not self.game_state.prison:
            return
        
        current = self.game_state.current_location
        
        # Prosta mapa więzienia
        map_data = {
            'zbrojownia': (14, 1, 'Z'),
            'biuro_naczelnika': (26, 1, 'B'),
            'cela_5': (2, 3, '5'),
            'korytarz_centralny': (14, 3, '╬'),
            'kuchnia': (26, 3, 'K'),
            'cela_4': (2, 5, '4'),
            'dziedziniec': (14, 5, 'D'),
            'cela_3': (2, 7, '3'),
            'cela_2': (14, 7, '2'),
            'cela_1': (26, 7, '1'),
            'korytarz_północny': (20, 7, '─'),
        }
        
        # Stwórz siatkę mapy
        width, height = 30, 9
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Dodaj lokacje
        for loc_name, (x, y, symbol) in map_data.items():
            if loc_name == current:
                grid[y][x] = f"\033[92m@\033[0m"  # Gracz w zielonym
            else:
                grid[y][x] = symbol
        
        # Dodaj połączenia
        # Poziome
        for x in range(3, 25):
            if grid[3][x] == ' ':
                grid[3][x] = '─'
            if grid[7][x] == ' ':
                grid[7][x] = '─'
        
        # Pionowe
        for y in range(2, 7):
            if grid[y][14] == ' ':
                grid[y][14] = '│'
        
        # Wyświetl mapę
        print("\n╔" + "═"*30 + "╗")
        print("║" + " MAPA WIĘZIENIA ".center(30) + "║")
        print("╠" + "═"*30 + "╣")
        
        for row in grid:
            print("║" + ''.join(row) + "║")
        
        print("╠" + "═"*30 + "╣")
        print("║ @ - Twoja pozycja".ljust(30) + "║")
        print("║ 1-5 - Cele, K - Kuchnia".ljust(30) + "║")
        print("║ D - Dziedziniec, Z - Zbrojownia".ljust(30)[:30] + "║")
        print("╚" + "═"*30 + "╝")