"""
Smart Interface System - Rozszerzalny, inteligentny interfejs dla gry Droga Szamana.

Ten moduł implementuje:
- Inteligentny parser z fuzzy matching
- Kontekstowe menu akcji
- Wizualny status bar
- System pluginów dla łatwej rozbudowy
"""

import os
import sys
import time
import json
import re
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from difflib import SequenceMatcher, get_close_matches
import unicodedata
from collections import defaultdict

# Import systemów gry
from core.game_state import GameState
from ui.interface import GameInterface as TextInterface
from ui.commands import CommandParser, Command, CommandCategory
from world.locations.prison import Prison
from npcs.npc_manager import NPCManager
from player.character import Character


class ActionType(Enum):
    """Typy akcji dostępnych w grze."""
    MOVEMENT = "movement"
    MOVE = "movement"  # Alias dla kompatybilności
    INTERACTION = "interaction"
    COMBAT = "combat"
    INVENTORY = "inventory"
    SYSTEM = "system"
    DIALOGUE = "dialogue"
    CRAFTING = "crafting"
    CRAFT = "crafting"  # Alias dla kompatybilności
    TRADE = "trade"
    QUEST = "quest"
    EXPLORATION = "exploration"
    EXPLORE = "exploration"  # Alias dla kompatybilności
    GATHER = "gathering"
    GATHERING = "gathering"


@dataclass
class ContextualAction:
    """Pojedyncza akcja kontekstowa."""
    id: str
    name: str
    description: str
    type: ActionType
    command: str  # Rzeczywista komenda do wykonania
    icon: str = "•"
    hotkey: Optional[str] = None
    condition: Optional[Callable] = None  # Funkcja sprawdzająca czy akcja dostępna
    priority: int = 50  # 0-100, wyższy = wyżej na liście
    category: str = "general"
    
    def is_available(self, context: Dict[str, Any]) -> bool:
        """Sprawdza czy akcja jest dostępna w danym kontekście."""
        if self.condition:
            return self.condition(context)
        return True


class PluginInterface:
    """Interfejs dla pluginów rozszerzających UI."""
    
    def register_actions(self) -> List[ContextualAction]:
        """Zwraca listę akcji do zarejestrowania."""
        return []
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Zwraca słownik parserów dla nowych typów komend."""
        return {}
    
    def register_status_widgets(self) -> List[Callable]:
        """Zwraca listę widgetów do status bara."""
        return []
    
    def on_location_change(self, old_location: str, new_location: str):
        """Wywoływane przy zmianie lokacji."""
        pass
    
    def on_action_executed(self, action: str, result: Any):
        """Wywoływane po wykonaniu akcji."""
        pass


class FuzzyParser:
    """Inteligentny parser z fuzzy matching."""
    
    def __init__(self):
        self.command_aliases = self._load_aliases()
        self.common_typos = self._load_typos()
        self.polish_replacements = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l',
            'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
        }
        
    def _load_aliases(self) -> Dict[str, List[str]]:
        """Ładuje aliasy komend."""
        try:
            with open('data/commands.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('aliases', {})
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return {
                "rozmawiaj": ["mów", "gadaj", "powiedz", "talk", "speak"],
                "idź": ["idz", "go", "move", "przejdź", "przejdz"],
                "weź": ["wez", "take", "zabierz", "podnieś", "podnies"],
                "użyj": ["uzyj", "use", "zastosuj"],
                "zbadaj": ["sprawdź", "sprawdz", "obejrzyj", "examine", "look"],
                "atakuj": ["atak", "bij", "uderz", "attack", "fight"],
            }
    
    def _load_typos(self) -> Dict[str, str]:
        """Ładuje popularne literówki."""
        return {
            "polnoc": "północ",
            "poludnie": "południe",
            "wschod": "wschód",
            "zachod": "zachód",
            "rozmawiaaj": "rozmawiaj",
            "wez": "weź",
            "uzyj": "użyj",
            "idz": "idź",
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalizuje tekst (małe litery, usunięcie polskich znaków opcjonalnie)."""
        text = text.lower().strip()
        # Zamień popularne literówki
        for typo, correct in self.common_typos.items():
            text = text.replace(typo, correct)
        return text
    
    def find_best_match(self, input_cmd: str, available_commands: List[str], 
                       threshold: float = 0.6) -> Optional[Tuple[str, float]]:
        """Znajduje najlepsze dopasowanie komendy."""
        input_cmd = self.normalize_text(input_cmd)
        
        # Sprawdź dokładne dopasowanie
        if input_cmd in available_commands:
            return (input_cmd, 1.0)
        
        # Sprawdź aliasy
        for base_cmd, aliases in self.command_aliases.items():
            if input_cmd in aliases or input_cmd == base_cmd:
                if base_cmd in available_commands:
                    return (base_cmd, 0.95)
        
        # Fuzzy matching
        matches = get_close_matches(input_cmd, available_commands, n=1, cutoff=threshold)
        if matches:
            best_match = matches[0]
            ratio = SequenceMatcher(None, input_cmd, best_match).ratio()
            return (best_match, ratio)
        
        # Sprawdź częściowe dopasowanie
        for cmd in available_commands:
            if input_cmd in cmd or cmd.startswith(input_cmd):
                return (cmd, 0.7)
        
        return None
    
    def parse_natural_language(self, input_text: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Parsuje naturalny język na komendę gry.
        
        Przykłady:
        - "porozmawiaj z piotrem" -> "rozmawiaj gadatliwy_piotr"
        - "weź klucz" -> "weź żelazny_klucz"
        - "idź do kuchni" -> "idź zachód" (jeśli kuchnia na zachód)
        """
        input_text = self.normalize_text(input_text)
        
        # Wzorce dla naturalnego języka
        patterns = [
            (r"porozmawiaj z (.+)", "rozmawiaj {0}"),
            (r"idź do (.+)", "idź {0}"),
            (r"idz (.+)", "idź {0}"),
            (r"weź (.+)", "weź {0}"),
            (r"użyj (.+) na (.+)", "użyj {0} {1}"),
            (r"zbadaj (.+)", "zbadaj {0}"),
            (r"atakuj (.+)", "atakuj {0}"),
            (r"kup (.+) od (.+)", "kup {0} {1}"),
            (r"sprzedaj (.+) do (.+)", "sprzedaj {0} {1}"),
        ]
        
        for pattern, template in patterns:
            match = re.match(pattern, input_text)
            if match:
                # Znajdź najlepsze dopasowanie dla obiektów
                groups = match.groups()
                resolved_groups = []
                
                for group in groups:
                    # Spróbuj dopasować do NPCów
                    if "npcs" in context:
                        npc_match = self._find_npc(group, context["npcs"])
                        if npc_match:
                            resolved_groups.append(npc_match)
                            continue
                    
                    # Spróbuj dopasować do przedmiotów
                    if "items" in context:
                        item_match = self._find_item(group, context["items"])
                        if item_match:
                            resolved_groups.append(item_match)
                            continue
                    
                    # Spróbuj dopasować do kierunków
                    direction_match = self._find_direction(group)
                    if direction_match:
                        resolved_groups.append(direction_match)
                        continue
                    
                    # Użyj oryginalnego tekstu
                    resolved_groups.append(group)
                
                return template.format(*resolved_groups)
        
        return None
    
    def _find_npc(self, name: str, npcs: List[Dict]) -> Optional[str]:
        """Znajduje NPCa po części nazwy."""
        name = name.lower()
        for npc in npcs:
            npc_name = npc.get("name", "").lower()
            npc_id = npc.get("id", "").lower()
            if name in npc_name or name in npc_id:
                return npc_id
        return None
    
    def _find_item(self, name: str, items: List[Dict]) -> Optional[str]:
        """Znajduje przedmiot po części nazwy."""
        name = name.lower()
        for item in items:
            item_name = item.get("name", "").lower()
            item_id = item.get("id", "").lower()
            if name in item_name or name in item_id:
                return item_id
        return None
    
    def _find_direction(self, text: str) -> Optional[str]:
        """Znajduje kierunek."""
        directions = {
            "północ": ["polnoc", "north", "n", "góra", "gora"],
            "południe": ["poludnie", "south", "s", "dół", "dol"],
            "wschód": ["wschod", "east", "e", "prawo"],
            "zachód": ["zachod", "west", "w", "lewo"],
        }
        
        text = text.lower()
        for direction, aliases in directions.items():
            if text == direction or text in aliases:
                return direction
        return None


class ContextualMenu:
    """System kontekstowego menu akcji."""
    
    def __init__(self):
        self.actions: List[ContextualAction] = []
        self.categories = {
            "movement": "🚶 RUCH",
            "interaction": "💬 INTERAKCJA",
            "combat": "⚔️ WALKA",
            "inventory": "🎒 EKWIPUNEK",
            "exploration": "🔍 EKSPLORACJA",
            "system": "⚙️ SYSTEM",
            "quest": "🎯 ZADANIA",
        }
        self._register_base_actions()
    
    def _register_base_actions(self):
        """Rejestruje podstawowe akcje."""
        # Akcje systemowe zawsze dostępne
        self.register_action(ContextualAction(
            id="status",
            name="Status postaci",
            description="Pokazuje pełny status gracza",
            type=ActionType.SYSTEM,
            command="status",
            icon="📊",
            hotkey="s",
            priority=90,
            category="system"
        ))
        
        self.register_action(ContextualAction(
            id="inventory",
            name="Ekwipunek",
            description="Pokazuje ekwipunek",
            type=ActionType.SYSTEM,
            command="ekwipunek",
            icon="🎒",
            hotkey="i",
            priority=85,
            category="system"
        ))
        
        self.register_action(ContextualAction(
            id="map",
            name="Mapa",
            description="Pokazuje mapę okolicy",
            type=ActionType.SYSTEM,
            command="mapa",
            icon="🗺️",
            hotkey="m",
            priority=80,
            category="system"
        ))
        
        self.register_action(ContextualAction(
            id="help",
            name="Pomoc",
            description="Pokazuje pomoc",
            type=ActionType.SYSTEM,
            command="pomoc",
            icon="❓",
            hotkey="?",
            priority=70,
            category="system"
        ))
    
    def register_action(self, action: ContextualAction):
        """Rejestruje nową akcję."""
        # Usuń starą wersję jeśli istnieje
        self.actions = [a for a in self.actions if a.id != action.id]
        self.actions.append(action)
    
    def get_available_actions(self, context: Dict[str, Any]) -> List[ContextualAction]:
        """Zwraca dostępne akcje w danym kontekście."""
        available = []
        
        for action in self.actions:
            if action.is_available(context):
                available.append(action)
        
        # Sortuj według priorytetu i kategorii
        available.sort(key=lambda a: (-a.priority, a.category, a.name))
        return available
    
    def generate_menu(self, context: Dict[str, Any]) -> str:
        """Generuje wizualne menu kontekstowe."""
        actions = self.get_available_actions(context)
        
        if not actions:
            return "Brak dostępnych akcji."
        
        # Grupuj akcje według kategorii
        grouped = defaultdict(list)
        for action in actions:
            grouped[action.category].append(action)
        
        # Buduj menu
        menu_lines = []
        menu_lines.append("╔════════════════ DOSTĘPNE AKCJE ════════════════╗")
        
        for i, (category, category_actions) in enumerate(grouped.items()):
            if i > 0:
                menu_lines.append("║" + "─" * 48 + "║")
            
            # Nagłówek kategorii
            category_name = self.categories.get(category, category.upper())
            menu_lines.append(f"║ {category_name:<46} ║")
            
            # Akcje w kategorii
            for j, action in enumerate(category_actions[:5]):  # Max 5 na kategorię
                hotkey = f"[{action.hotkey}]" if action.hotkey else f"[{len(menu_lines)-1}]"
                line = f"║ {hotkey:>4} {action.icon} {action.name:<37} ║"
                menu_lines.append(line)
        
        menu_lines.append("╚═════════════════════════════════════════════════╝")
        menu_lines.append("Wpisz numer, skrót lub pełną komendę:")
        
        return "\n".join(menu_lines)
    
    def execute_by_hotkey(self, hotkey: str, context: Dict[str, Any]) -> Optional[str]:
        """Wykonuje akcję po hotkey lub numerze."""
        actions = self.get_available_actions(context)
        
        # Sprawdź hotkey
        for action in actions:
            if action.hotkey == hotkey:
                return action.command
        
        # Sprawdź numer
        try:
            index = int(hotkey) - 1
            if 0 <= index < len(actions):
                return actions[index].command
        except ValueError:
            pass
        
        return None


class StatusBar:
    """Wizualny pasek statusu."""
    
    def __init__(self, interface: TextInterface):
        self.interface = interface
        self.widgets: List[Callable] = []
        self._register_base_widgets()
    
    def _register_base_widgets(self):
        """Rejestruje podstawowe widgety."""
        self.widgets.append(self._health_widget)
        self.widgets.append(self._stamina_widget)
        self.widgets.append(self._hunger_widget)
        self.widgets.append(self._location_widget)
        self.widgets.append(self._time_widget)
        self.widgets.append(self._quest_widget)
    
    def _health_widget(self, game_state: GameState) -> str:
        """Widget zdrowia."""
        if not game_state.player:
            return ""
        
        health = game_state.player.health
        max_health = game_state.player.max_health
        percent = health / max_health
        
        # Kolorowe paski
        if percent > 0.7:
            color = "green"
        elif percent > 0.3:
            color = "yellow"
        else:
            color = "red"
        
        bar_length = 10
        filled = int(percent * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"❤️ [{bar}] {int(percent*100)}%"
    
    def _stamina_widget(self, game_state: GameState) -> str:
        """Widget staminy."""
        if not game_state.player:
            return ""
        
        stamina = game_state.player.stamina
        max_stamina = game_state.player.max_stamina
        percent = stamina / max_stamina
        
        bar_length = 10
        filled = int(percent * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"⚡ [{bar}] {int(percent*100)}%"
    
    def _hunger_widget(self, game_state: GameState) -> str:
        """Widget głodu."""
        if not game_state.player:
            return ""
        
        hunger = getattr(game_state.player, 'hunger', 50)
        percent = (100 - hunger) / 100  # Odwrócone - mniej głodu = lepiej
        
        bar_length = 10
        filled = int(percent * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"🍖 [{bar}] {int(percent*100)}%"
    
    def _location_widget(self, game_state: GameState) -> str:
        """Widget lokacji."""
        location = game_state.current_location or "Nieznana"
        return f"📍 {location}"
    
    def _time_widget(self, game_state: GameState) -> str:
        """Widget czasu."""
        game_time = game_state.game_time
        hour = int(game_time // 60)
        minute = int(game_time % 60)
        
        # Ikona pory dnia
        if 6 <= hour < 12:
            icon = "🌅"  # Rano
        elif 12 <= hour < 18:
            icon = "☀️"  # Dzień
        elif 18 <= hour < 22:
            icon = "🌇"  # Wieczór
        else:
            icon = "🌙"  # Noc
        
        return f"{icon} {hour:02d}:{minute:02d}"
    
    def _quest_widget(self, game_state: GameState) -> str:
        """Widget aktywnego questa."""
        # Integracja z systemem questów dostępna przez game_state.quest_engine
        if hasattr(game_state, 'active_quest'):
            quest_name = getattr(game_state.active_quest, 'name', 'Brak')
            progress = getattr(game_state.active_quest, 'progress', 0)
            return f"🎯 {quest_name} ({progress}%)"
        return "🎯 Brak aktywnego zadania"
    
    def register_widget(self, widget: Callable):
        """Rejestruje nowy widget."""
        self.widgets.append(widget)
    
    def render(self, game_state: GameState) -> str:
        """Renderuje pasek statusu."""
        lines = []
        
        # Górna linia
        lines.append("╭" + "─" * 78 + "╮")
        
        # Pierwsza linia - podstawowe staty
        stat_widgets = []
        stat_widgets.append(self._health_widget(game_state))
        stat_widgets.append(self._stamina_widget(game_state))
        stat_widgets.append(self._hunger_widget(game_state))
        
        stats_line = " │ ".join(filter(None, stat_widgets))
        lines.append(f"│ {stats_line:<76} │")
        
        # Druga linia - lokacja i czas
        info_widgets = []
        info_widgets.append(self._location_widget(game_state))
        info_widgets.append(self._time_widget(game_state))
        info_widgets.append(self._quest_widget(game_state))
        
        info_line = " │ ".join(filter(None, info_widgets))
        lines.append(f"│ {info_line:<76} │")
        
        # Dolna linia
        lines.append("╰" + "─" * 78 + "╯")
        
        return "\n".join(lines)


class SmartInterface:
    """
    Główny inteligentny interfejs gry.
    Łączy wszystkie komponenty w spójny system.
    """
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.text_interface = TextInterface()
        self.parser = FuzzyParser()
        self.menu = ContextualMenu()
        self.status_bar = StatusBar(self.text_interface)
        self.command_parser = CommandParser(game_state)
        
        # System pluginów
        self.plugins: List[PluginInterface] = []
        
        # Historia i cache
        self.command_history: List[str] = []
        self.last_suggestions: List[str] = []
        self.context_cache: Dict[str, Any] = {}
        
        # Ustawienia
        self.settings = {
            "show_menu": True,
            "show_status": True,
            "show_hints": True,
            "auto_complete": True,
            "fuzzy_threshold": 0.6,
            "max_history": 100,
        }
        
        # Inicjalizacja
        self._initialize_context_actions()
    
    def _initialize_context_actions(self):
        """Inicjalizuje akcje kontekstowe na podstawie stanu gry."""
        # Akcje ruchu
        for direction in ["północ", "południe", "wschód", "zachód"]:
            self.menu.register_action(ContextualAction(
                id=f"move_{direction}",
                name=f"Idź na {direction}",
                description=f"Przemieszcza się na {direction}",
                type=ActionType.MOVEMENT,
                command=f"idź {direction}",
                icon="🚶",
                condition=lambda ctx, d=direction: d in ctx.get("exits", []),
                priority=75,
                category="movement"
            ))
        
        # Akcje eksploracji
        self.menu.register_action(ContextualAction(
            id="search",
            name="Przeszukaj lokację",
            description="Dokładnie przeszukuje obecną lokację",
            type=ActionType.EXPLORATION,
            command="przeszukaj",
            icon="🔍",
            hotkey="p",
            priority=70,
            category="exploration"
        ))
        
        self.menu.register_action(ContextualAction(
            id="examine",
            name="Zbadaj otoczenie",
            description="Dokładnie bada otoczenie",
            type=ActionType.EXPLORATION,
            command="rozejrzyj",
            icon="👁️",
            hotkey="r",
            priority=65,
            category="exploration"
        ))
    
    def register_plugin(self, plugin: PluginInterface):
        """Rejestruje plugin rozszerzający interfejs."""
        self.plugins.append(plugin)
        
        # Zarejestruj akcje z pluginu
        for action in plugin.register_actions():
            self.menu.register_action(action)
        
        # Zarejestruj widgety
        for widget in plugin.register_status_widgets():
            self.status_bar.register_widget(widget)
    
    def get_current_context(self) -> Dict[str, Any]:
        """Pobiera aktualny kontekst gry."""
        context = {
            "location": self.game_state.current_location,
            "player": self.game_state.player,
            "game_state": self.game_state,
        }
        
        # Dodaj informacje o lokacji
        if self.game_state.prison:
            current_loc = self.game_state.prison.get_current_location()
            if current_loc:
                context["exits"] = list(current_loc.connections.keys())
                context["items"] = current_loc.items
                context["npcs"] = []
                
                # Znajdź NPCów w lokacji
                if self.game_state.npc_manager:
                    for npc_id, npc in self.game_state.npc_manager.npcs.items():
                        if npc.location == self.game_state.current_location:
                            context["npcs"].append({
                                "id": npc_id,
                                "name": npc.name
                            })
        
        # Pozwól pluginom dodać do kontekstu
        for plugin in self.plugins:
            plugin_context = getattr(plugin, 'get_context', lambda: {})()
            context.update(plugin_context)
        
        self.context_cache = context
        return context
    
    def display_main_screen(self):
        """Wyświetla główny ekran gry."""
        self.text_interface.clear_screen()
        
        # Status bar
        if self.settings["show_status"]:
            print(self.status_bar.render(self.game_state))
            print()
        
        # Opis lokacji
        if self.game_state.prison:
            current_loc = self.game_state.prison.get_current_location()
            if current_loc:
                # Nazwa lokacji
                self.text_interface.print_header(current_loc.name)
                
                # Opis
                print(current_loc.get_description(
                    self.game_state.time_system,
                    self.game_state.weather_system
                ))
                print()
                
                # NPCe w lokacji
                context = self.get_current_context()
                if context.get("npcs"):
                    print("Osoby tutaj:")
                    for npc in context["npcs"]:
                        print(f"  • {npc['name']}")
                    print()
        
        # Menu kontekstowe
        if self.settings["show_menu"]:
            context = self.get_current_context()
            print(self.menu.generate_menu(context))
            print()
    
    def process_input(self, user_input: str) -> Tuple[bool, str]:
        """
        Przetwarza input użytkownika z inteligentnym parsowaniem.
        
        Returns:
            (success, message)
        """
        # Dodaj do historii
        self.command_history.append(user_input)
        if len(self.command_history) > self.settings["max_history"]:
            self.command_history.pop(0)
        
        # Sprawdź hotkey/numer z menu
        context = self.get_current_context()
        command = self.menu.execute_by_hotkey(user_input, context)
        
        if command:
            # Wykonaj komendę z menu
            return self.command_parser.parse_and_execute(command)
        
        # Spróbuj naturalnego języka
        parsed = self.parser.parse_natural_language(user_input, context)
        if parsed:
            print(f"💡 Interpretuję jako: {parsed}")
            return self.command_parser.parse_and_execute(parsed)
        
        # Fuzzy matching na dostępnych komendach
        available_commands = [cmd.name for cmd in self.command_parser.commands.values()]
        match = self.parser.find_best_match(user_input, available_commands)
        
        if match:
            best_match, confidence = match
            if confidence >= self.settings["fuzzy_threshold"]:
                if confidence < 0.9:
                    # Zapytaj o potwierdzenie
                    print(f"❓ Czy chodziło Ci o: '{best_match}'? (Enter=TAK, n=NIE)")
                    confirm = input("> ").strip().lower()
                    if confirm == 'n' or confirm == 'nie':
                        return self._suggest_alternatives(user_input)
                
                return self.command_parser.parse_and_execute(best_match)
        
        # Nie znaleziono - zasugeruj alternatywy
        return self._suggest_alternatives(user_input)
    
    def _suggest_alternatives(self, failed_input: str) -> Tuple[bool, str]:
        """Sugeruje alternatywne komendy."""
        suggestions = []
        context = self.get_current_context()
        
        # Znajdź podobne akcje
        actions = self.menu.get_available_actions(context)
        for action in actions[:5]:
            if any(word in failed_input.lower() for word in action.name.lower().split()):
                suggestions.append(f"  • {action.command} - {action.description}")
        
        if suggestions:
            message = f"❌ Nie rozumiem komendy '{failed_input}'\n"
            message += "💡 Może chodziło Ci o:\n"
            message += "\n".join(suggestions)
        else:
            message = f"❌ Nie rozumiem komendy '{failed_input}'\n"
            message += "💡 Wpisz 'pomoc' aby zobaczyć dostępne komendy"
        
        return False, message
    
    def run_game_loop(self):
        """Główna pętla gry z inteligentnym interfejsem."""
        self.text_interface.print_ascii_art("DROGA SZAMANA")
        print("\n🎮 Witaj w inteligentnym interfejsie gry!")
        print("💡 Możesz używać naturalnego języka lub wybierać opcje z menu.\n")
        
        while self.game_state.is_running:
            try:
                # Wyświetl ekran główny
                self.display_main_screen()
                
                # Pobierz input
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                # Specjalne komendy interfejsu
                if user_input.lower() in ['quit', 'exit', 'wyjdź', 'wyjdz']:
                    print("Czy na pewno chcesz wyjść? (t/n)")
                    if input("> ").lower() in ['t', 'tak', 'y', 'yes']:
                        self.game_state.is_running = False
                        break
                    continue
                
                # Przetwórz komendę
                success, message = self.process_input(user_input)
                
                # Wyświetl rezultat
                if message:
                    print(message)
                
                # Aktualizuj stan gry
                if success:
                    self.game_state.update(1)  # Minuta czasu gry
                    
                    # Powiadom pluginy
                    for plugin in self.plugins:
                        plugin.on_action_executed(user_input, message)
                
                print()  # Odstęp przed następną akcją
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Przerwano. Wpisz 'wyjdź' aby zakończyć grę.")
            except Exception as e:
                print(f"\n❌ Błąd: {str(e)}")
                print("Gra kontynuuje...")
        
        print("\n👋 Dziękujemy za grę! Do zobaczenia!")


# Plugin przykładowy - System achievementów
class AchievementPlugin(PluginInterface):
    """Przykładowy plugin dodający system achievementów."""
    
    def __init__(self):
        self.achievements = {
            "first_talk": {"name": "Gaduła", "desc": "Porozmawiaj z NPCem", "unlocked": False},
            "first_item": {"name": "Zbieracz", "desc": "Weź pierwszy przedmiot", "unlocked": False},
            "explorer": {"name": "Odkrywca", "desc": "Odwiedź 5 lokacji", "unlocked": False},
        }
        self.visited_locations = set()
    
    def register_actions(self) -> List[ContextualAction]:
        """Dodaje akcję sprawdzania achievementów."""
        return [
            ContextualAction(
                id="achievements",
                name="Osiągnięcia",
                description="Pokazuje zdobyte osiągnięcia",
                type=ActionType.SYSTEM,
                command="osiagniecia",
                icon="🏆",
                hotkey="a",
                priority=60,
                category="system"
            )
        ]
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widget achievementów do status bara."""
        def achievement_widget(game_state):
            unlocked = sum(1 for a in self.achievements.values() if a["unlocked"])
            total = len(self.achievements)
            return f"🏆 {unlocked}/{total}"
        
        return [achievement_widget]
    
    def on_action_executed(self, action: str, result: Any):
        """Sprawdza czy odblokować achievement."""
        if "rozmawiaj" in action and not self.achievements["first_talk"]["unlocked"]:
            self.achievements["first_talk"]["unlocked"] = True
            print("🏆 Osiągnięcie odblokowane: Gaduła!")
        
        if "weź" in action and not self.achievements["first_item"]["unlocked"]:
            self.achievements["first_item"]["unlocked"] = True
            print("🏆 Osiągnięcie odblokowane: Zbieracz!")
    
    def on_location_change(self, old_location: str, new_location: str):
        """Sprawdza achievement odkrywcy."""
        self.visited_locations.add(new_location)
        if len(self.visited_locations) >= 5 and not self.achievements["explorer"]["unlocked"]:
            self.achievements["explorer"]["unlocked"] = True
            print("🏆 Osiągnięcie odblokowane: Odkrywca!")


def create_smart_interface(game_state: GameState, plugin_classes: List = None) -> SmartInterface:
    """Fabryka tworząca smart interface z wszystkimi dostępnymi pluginami."""
    interface = SmartInterface(game_state)
    
    # Dodaj przykładowy plugin achievementów
    interface.register_plugin(AchievementPlugin())
    
    # Lista domyślnych pluginów do załadowania
    default_plugins = []
    
    # Próbuj załadować wszystkie dostępne pluginy
    try:
        from ui.plugins.combat_plugin import CombatPlugin
        default_plugins.append(CombatPlugin)
    except ImportError:
        pass
    
    try:
        from ui.plugins.trade_plugin import TradePlugin
        default_plugins.append(TradePlugin)
    except ImportError:
        pass
    
    try:
        from ui.plugins.abilities_plugin import AbilitiesPlugin
        default_plugins.append(AbilitiesPlugin)
    except ImportError:
        pass
    
    try:
        from ui.plugins.quest_plugin import QuestPlugin
        default_plugins.append(QuestPlugin)
    except ImportError:
        pass
    
    try:
        from ui.plugins.crafting_plugin import CraftingPlugin
        default_plugins.append(CraftingPlugin)
    except ImportError:
        pass
    
    try:
        from ui.plugins.gathering_plugin import GatheringPlugin
        default_plugins.append(GatheringPlugin)
    except ImportError:
        pass
    
    try:
        from ui.plugins.exploration_plugin import ExplorationPlugin
        default_plugins.append(ExplorationPlugin)
    except ImportError:
        pass
    
    # Użyj przekazanych pluginów lub domyślnych
    plugins_to_load = plugin_classes if plugin_classes else default_plugins
    
    # Zarejestruj wszystkie pluginy
    for plugin_class in plugins_to_load:
        try:
            plugin_instance = plugin_class()
            interface.register_plugin(plugin_instance)
            print(f"✅ Załadowano plugin: {plugin_class.__name__}")
        except Exception as e:
            print(f"⚠️ Nie można załadować pluginu {plugin_class.__name__}: {e}")
    
    print(f"📦 Załadowano {len(interface.plugins)} pluginów do Smart Interface")
    
    return interface