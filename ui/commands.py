"""System komend gracza - parser i wykonywanie."""

from typing import Dict, List, Tuple, Any, Optional, Callable
from enum import Enum
import re
import json
import random

# Importy dla systemu walki
from npcs.npc_manager import NPCState
from player.character import CharacterState
from core.game_state import GameMode
from npcs.dialogue.dialogue_controller import DialogueResult  # Nowy system dialogów z pamięcią


class CommandCategory(Enum):
    """Kategorie komend."""
    MOVEMENT = "ruch"
    INTERACTION = "interakcja"
    COMBAT = "walka"
    INVENTORY = "ekwipunek"
    CRAFT = "tworzenie"
    TRADE = "handel"
    QUEST = "zadania"
    SYSTEM = "system"
    DEBUG = "debug"


class Command:
    """Pojedyncza komenda."""
    
    def __init__(self, name: str, aliases: List[str], category: CommandCategory,
                 handler: Callable, description: str, usage: str = "",
                 min_args: int = 0, max_args: int = 100):
        """Inicjalizacja komendy.
        
        Args:
            name: Główna nazwa komendy
            aliases: Alternatywne nazwy
            category: Kategoria komendy
            handler: Funkcja obsługująca
            description: Opis komendy
            usage: Przykład użycia
            min_args: Minimalna liczba argumentów
            max_args: Maksymalna liczba argumentów
        """
        self.name = name
        self.aliases = aliases
        self.category = category
        self.handler = handler
        self.description = description
        self.usage = usage
        self.min_args = min_args
        self.max_args = max_args


class CommandParser:
    """Parser komend gracza."""
    
    def __init__(self, game_state):
        """Inicjalizacja parsera.

        Args:
            game_state: Referencja do stanu gry
        """
        self.game_state = game_state
        self.commands: Dict[str, Command] = {}
        self.command_history: List[str] = []
        self.history_limit = 100

        # Wczytaj konfigurację komend
        self.commands_config = self._load_commands_config()
        self.ui_texts = self._load_ui_texts()

        # Rejestracja komend
        self._register_commands()

    def _trigger_tutorial_hint(self, command_name: str, hint_id: str):
        """Pokaż tutorial hint przy pierwszym użyciu komendy.

        Args:
            command_name: Nazwa komendy (do trackingu)
            hint_id: ID hintu w TutorialManager
        """
        if command_name not in self.game_state.first_time_commands:
            self.game_state.first_time_commands.add(command_name)
            if self.game_state.tutorial_manager:
                self.game_state.tutorial_manager.show_hint(hint_id)
    
    def _load_commands_config(self) -> Dict:
        """Wczytaj konfigurację komend z JSON."""
        try:
            with open('data/commands.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'commands': {}, 'directions': {}}
    
    def _load_ui_texts(self) -> Dict:
        """Wczytaj teksty UI z JSON."""
        try:
            with open('data/ui_texts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'messages': {'errors': {}, 'success': {}}}
    
    def _register_commands(self):
        """Rejestracja wszystkich dostępnych komend."""
        
        # Ruch
        self.register(Command(
            "idź", ["idz", "pójdź", "pojdz", "rusz"],
            CommandCategory.MOVEMENT,
            self._cmd_move,
            "Porusz się w danym kierunku",
            "idź [północ/południe/wschód/zachód/góra/dół]",
            min_args=1, max_args=1
        ))
        
        self.register(Command(
            "północ", ["polnoc", "n"],
            CommandCategory.MOVEMENT,
            lambda args: self._cmd_move(["północ"]),
            "Idź na północ"
        ))
        
        self.register(Command(
            "południe", ["poludnie", "s"],
            CommandCategory.MOVEMENT,
            lambda args: self._cmd_move(["południe"]),
            "Idź na południe"
        ))
        
        self.register(Command(
            "wschód", ["wschod", "e", "w"],
            CommandCategory.MOVEMENT,
            lambda args: self._cmd_move(["wschód"]),
            "Idź na wschód"
        ))
        
        self.register(Command(
            "zachód", ["zachod", "z"],
            CommandCategory.MOVEMENT,
            lambda args: self._cmd_move(["zachód"]),
            "Idź na zachód"
        ))
        
        # Interakcja
        self.register(Command(
            "rozejrzyj", ["rozejrzyj_się", "patrz", "opisz"],
            CommandCategory.INTERACTION,
            self._cmd_look,
            "Rozejrzyj się po lokacji"
        ))
        
        self.register(Command(
            "zbadaj", ["sprawdź", "sprawdz", "obejrzyj"],
            CommandCategory.INTERACTION,
            self._cmd_examine,
            "Zbadaj obiekt lub osobę",
            "zbadaj [obiekt/osoba]",
            min_args=1
        ))
        
        self.register(Command(
            "szukaj", ["przeszukaj"],
            CommandCategory.INTERACTION,
            self._cmd_search,
            "Przeszukaj lokację"
        ))
        
        self.register(Command(
            "rozmawiaj", ["mów", "mow", "gadaj", "powiedz"],
            CommandCategory.INTERACTION,
            self._cmd_talk,
            "Rozmawiaj z NPCem",
            "rozmawiaj [imię_npc]",
            min_args=1
        ))
        
        self.register(Command(
            "weź", ["wez", "podnieś", "podnies", "zabierz"],
            CommandCategory.INTERACTION,
            self._cmd_take,
            "Weź przedmiot",
            "weź [przedmiot]",
            min_args=1
        ))
        
        self.register(Command(
            "użyj", ["uzyj", "zastosuj"],
            CommandCategory.INTERACTION,
            self._cmd_use,
            "Użyj przedmiotu",
            "użyj [przedmiot] [na czym]",
            min_args=1
        ))
        
        # Walka
        self.register(Command(
            "atakuj", ["atak", "bij", "uderz"],
            CommandCategory.COMBAT,
            self._cmd_attack,
            "Atakuj cel",
            "atakuj [cel]",
            min_args=1
        ))
        
        self.register(Command(
            "broń", ["bron", "obroń", "obron"],
            CommandCategory.COMBAT,
            self._cmd_defend,
            "Przyjmij postawę obronną"
        ))
        
        self.register(Command(
            "uciekaj", ["ucieknij", "zwiaj", "spierdalaj"],
            CommandCategory.COMBAT,
            self._cmd_flee,
            "Ucieknij z walki"
        ))
        
        # Zdolności klasowe
        self.register(Command(
            "zdolność", ["zdolnosc", "umiejętność", "umiejetnosc", "skill"],
            CommandCategory.COMBAT,
            self._cmd_ability,
            "Użyj zdolności klasowej",
            "zdolność [nazwa] [cel]",
            min_args=1
        ))
        
        self.register(Command(
            "zdolności", ["zdolnosci", "umiejętności", "umiejetnosci", "skills"],
            CommandCategory.SYSTEM,
            self._cmd_list_abilities,
            "Pokaż dostępne zdolności"
        ))
        
        # Ekwipunek
        self.register(Command(
            "ekwipunek", ["eq", "inwentarz", "plecak"],
            CommandCategory.INVENTORY,
            self._cmd_inventory,
            "Pokaż ekwipunek"
        ))
        
        self.register(Command(
            "załóż", ["zaloz", "ubierz"],
            CommandCategory.INVENTORY,
            self._cmd_equip,
            "Załóż przedmiot",
            "załóż [przedmiot]",
            min_args=1
        ))
        
        self.register(Command(
            "zdejmij", ["sciągnij", "sciagnij"],
            CommandCategory.INVENTORY,
            self._cmd_unequip,
            "Zdejmij przedmiot",
            "zdejmij [przedmiot]",
            min_args=1
        ))
        
        self.register(Command(
            "wyrzuć", ["wyrzuc", "upuść", "upusc"],
            CommandCategory.INVENTORY,
            self._cmd_drop,
            "Wyrzuć przedmiot",
            "wyrzuć [przedmiot] [ilość]",
            min_args=1
        ))
        
        # Crafting
        self.register(Command(
            "wytwórz", ["wytworz", "stwórz", "stworz", "zrób", "zrob"],
            CommandCategory.CRAFT,
            self._cmd_craft,
            "Wytwórz przedmiot",
            "wytwórz [przedmiot]",
            min_args=1
        ))
        
        self.register(Command(
            "receptury", ["przepisy", "recepty"],
            CommandCategory.CRAFT,
            self._cmd_recipes,
            "Pokaż znane receptury"
        ))
        
        # Handel
        self.register(Command(
            "handluj", ["kup", "sprzedaj"],
            CommandCategory.TRADE,
            self._cmd_trade,
            "Handluj z NPCem",
            "handluj [npc]",
            min_args=1
        ))
        
        self.register(Command(
            "targuj", ["targuj_się", "negocjuj"],
            CommandCategory.TRADE,
            self._cmd_haggle,
            "Targuj się o cenę",
            "targuj [procent]",
            min_args=1
        ))
        
        # Questy
        self.register(Command(
            "zadania", ["questy", "misje"],
            CommandCategory.QUEST,
            self._cmd_quests,
            "Pokaż aktywne zadania"
        ))
        
        self.register(Command(
            "dziennik", ["journal", "notatki"],
            CommandCategory.QUEST,
            self._cmd_journal,
            "Pokaż dziennik odkryć"
        ))
        
        # System
        self.register(Command(
            "status", ["statystyki", "stats"],
            CommandCategory.SYSTEM,
            self._cmd_status,
            "Pokaż status gracza"
        ))
        
        self.register(Command(
            "umiejętności", ["umiejetnosci", "skille"],
            CommandCategory.SYSTEM,
            self._cmd_skills,
            "Pokaż umiejętności"
        ))
        
        self.register(Command(
            "zapisz", ["save"],
            CommandCategory.SYSTEM,
            self._cmd_save,
            "Zapisz grę",
            "zapisz [slot 1-5]"
        ))
        
        self.register(Command(
            "wczytaj", ["load"],
            CommandCategory.SYSTEM,
            self._cmd_load,
            "Wczytaj grę",
            "wczytaj [slot 1-5]"
        ))
        
        self.register(Command(
            "pomoc", ["help", "?"],
            CommandCategory.SYSTEM,
            self._cmd_help,
            "Pokaż pomoc",
            "pomoc [komenda]"
        ))
        
        self.register(Command(
            "mapa", ["map", "m"],
            CommandCategory.SYSTEM,
            self._cmd_map,
            "Pokaż mapę okolicy"
        ))
        
        self.register(Command(
            "wyjdź", ["wyjdz", "quit", "exit", "koniec"],
            CommandCategory.SYSTEM,
            self._cmd_quit,
            "Wyjdź z gry"
        ))
        
        # Czas
        self.register(Command(
            "czekaj", ["wait", "odpocznij"],
            CommandCategory.SYSTEM,
            self._cmd_wait,
            "Czekaj określony czas",
            "czekaj [minuty]",
            min_args=1
        ))
        
        self.register(Command(
            "śpij", ["spij", "sen"],
            CommandCategory.SYSTEM,
            self._cmd_sleep,
            "Idź spać"
        ))
    
    def register(self, command: Command):
        """Zarejestruj nową komendę.
        
        Args:
            command: Komenda do zarejestrowania
        """
        # Zarejestruj główną nazwę
        self.commands[command.name.lower()] = command
        
        # Zarejestruj aliasy
        for alias in command.aliases:
            self.commands[alias.lower()] = command
    
    def parse_and_execute(self, input_text: str) -> Tuple[bool, str]:
        """Parsuj i wykonaj komendę.

        Args:
            input_text: Tekst wprowadzony przez gracza

        Returns:
            (sukces, wiadomość)
        """
        # Zapisz w historii
        self.command_history.append(input_text)
        if len(self.command_history) > self.history_limit:
            self.command_history.pop(0)

        # Parsuj input
        parts = input_text.strip().lower().split()

        if not parts:
            return False, "Wpisz komendę. Użyj 'pomoc' lub '?' aby zobaczyć co możesz zrobić."

        command_name = parts[0]
        args = parts[1:]

        # KROK 2: Obsługa wyboru opcji dialogowej (cyfra 1-9)
        if (command_name.isdigit() and
            hasattr(self.game_state, 'current_dialogue') and
            self.game_state.current_dialogue):
            choice_index = int(command_name) - 1  # 1-based -> 0-based
            return self._cmd_choose_dialogue_option(choice_index)

        # Obsługa komendy "anuluj" podczas dialogu
        if command_name in ['anuluj', 'koniec', 'wyjdź', 'wyjdz']:
            if hasattr(self.game_state, 'current_dialogue') and self.game_state.current_dialogue:
                self.game_state.current_dialogue = None
                return True, "[Koniec rozmowy]"

        # Znajdź komendę
        if command_name not in self.commands:
            # NOWE: Inteligentne sugestie zamiast prostego błędu
            return False, self._suggest_commands(command_name, args)

        command = self.commands[command_name]

        # Sprawdź liczbę argumentów
        if len(args) < command.min_args:
            # NOWE: Lepszy komunikat z przykładem
            error_msg = f"❌ Za mało argumentów dla '{command.name}'"
            if command.usage:
                error_msg += f"\n💡 Użycie: {command.usage}"
            # Dodaj kontekstową pomoc
            error_msg += self._add_contextual_help(command.name)
            return False, error_msg

        if len(args) > command.max_args:
            error_msg = f"❌ Za dużo argumentów dla '{command.name}'"
            if command.usage:
                error_msg += f"\n💡 Użycie: {command.usage}"
            return False, error_msg

        # Wykonaj komendę
        try:
            return command.handler(args)
        except Exception as e:
            return False, f"❌ Błąd wykonywania komendy: {str(e)}\n💡 Spróbuj 'pomoc {command.name}' aby zobaczyć jak używać tej komendy."

    def _suggest_commands(self, unknown_command: str, args: List[str]) -> str:
        """
        Generuj inteligentne sugestie dla nieznanej komendy.

        Args:
            unknown_command: Nieznana komenda
            args: Argumenty komendy

        Returns:
            Komunikat z sugestiami
        """
        error_msg = f"❌ Nie rozumiem: '{unknown_command}'"

        # 1. Znajdź podobne komendy (Levenshtein distance)
        similar_commands = self._find_similar_commands(unknown_command)

        if similar_commands:
            error_msg += "\n\n💡 Czy chodziło Ci o:"
            for i, cmd_name in enumerate(similar_commands[:3], 1):
                cmd = self.commands[cmd_name]
                error_msg += f"\n   {i}. {cmd.name} - {cmd.description}"

        # 2. Kontekstowe sugestie na podstawie argumentów
        contextual = self._get_contextual_suggestions(unknown_command, args)
        if contextual:
            error_msg += f"\n\n{contextual}"

        # 3. Hint o menu akcji
        error_msg += "\n\n💡 Wpisz '?' aby zobaczyć dostępne akcje lub 'pomoc' dla listy wszystkich komend"

        return error_msg

    def _find_similar_commands(self, command: str, max_distance: int = 3) -> List[str]:
        """
        Znajdź podobne komendy używając prostej odległości edycyjnej.

        Args:
            command: Komenda do porównania
            max_distance: Maksymalna odległość edycyjna

        Returns:
            Lista podobnych komend
        """
        def levenshtein_distance(s1: str, s2: str) -> int:
            """Oblicz odległość Levenshteina."""
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)

            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row

            return previous_row[-1]

        similar = []
        # Sprawdź główne nazwy komend (bez duplikatów)
        seen_commands = set()

        for cmd_name, cmd in self.commands.items():
            if cmd.name in seen_commands:
                continue
            seen_commands.add(cmd.name)

            distance = levenshtein_distance(command, cmd_name)
            if distance <= max_distance:
                similar.append((distance, cmd.name))

        # Sortuj po odległości
        similar.sort()
        return [cmd_name for _, cmd_name in similar]

    def _get_contextual_suggestions(self, command: str, args: List[str]) -> str:
        """
        Generuj kontekstowe sugestie na podstawie lokacji i dostępnych obiektów.

        Args:
            command: Nieznana komenda
            args: Argumenty

        Returns:
            Sugestie kontekstowe
        """
        suggestions = []

        # Sprawdź co jest dostępne w lokacji
        if self.game_state.npc_manager:
            current_loc = self.game_state.current_location

            # NPCe w lokacji
            npcs_here = []
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if hasattr(npc, 'current_location') and npc.current_location == current_loc:
                    if hasattr(npc, 'combat_stats') and npc.combat_stats.health > 0:
                        if npc.role != "creature":
                            npcs_here.append(npc.name)

            if npcs_here:
                suggestions.append(f"👥 Ludzie w pobliżu: {', '.join(npcs_here)}")
                suggestions.append(f"   Spróbuj: 'rozmawiaj {npcs_here[0].lower()}'")

        # Sprawdź przedmioty w lokacji
        if self.game_state.prison:
            location = self.game_state.prison.get_current_location()
            if location and hasattr(location, 'items') and location.items:
                items_here = []
                for item in location.items[:3]:  # Max 3
                    if hasattr(item, 'name'):
                        items_here.append(item.name)
                    elif isinstance(item, dict):
                        items_here.append(item.get('name', ''))
                    elif isinstance(item, str):
                        items_here.append(item)

                if items_here:
                    suggestions.append(f"📦 Przedmioty: {', '.join(items_here)}")
                    suggestions.append(f"   Spróbuj: 'weź {items_here[0].lower()}'")

        if suggestions:
            return "\n".join(suggestions)
        return ""

    def _add_contextual_help(self, command_name: str) -> str:
        """
        Dodaj kontekstową pomoc dla komendy.

        Args:
            command_name: Nazwa komendy

        Returns:
            Dodatkowa pomoc kontekstowa
        """
        help_text = ""

        # Pomoc dla konkretnych komend
        if command_name in ['rozmawiaj', 'mów', 'mow', 'gadaj']:
            # Pokaż dostępnych NPCów
            if self.game_state.npc_manager:
                current_loc = self.game_state.current_location
                npcs_here = []
                for npc_id, npc in self.game_state.npc_manager.npcs.items():
                    if hasattr(npc, 'current_location') and npc.current_location == current_loc:
                        if hasattr(npc, 'combat_stats') and npc.combat_stats.health > 0:
                            if npc.role != "creature":
                                npcs_here.append(npc.name)

                if npcs_here:
                    help_text += f"\n\n👥 Dostępni do rozmowy: {', '.join(npcs_here)}"
                    help_text += f"\n   Przykład: 'rozmawiaj {npcs_here[0].lower()}'"
                else:
                    help_text += "\n\n💬 Nie ma tu nikogo do rozmowy."

        elif command_name in ['weź', 'wez', 'podnieś', 'podnies']:
            # Pokaż dostępne przedmioty
            if self.game_state.prison:
                location = self.game_state.prison.get_current_location()
                if location and hasattr(location, 'items') and location.items:
                    items_here = []
                    for item in location.items[:3]:
                        if hasattr(item, 'name'):
                            items_here.append(item.name)
                        elif isinstance(item, dict):
                            items_here.append(item.get('name', ''))
                        elif isinstance(item, str):
                            items_here.append(item)

                    if items_here:
                        help_text += f"\n\n📦 Dostępne przedmioty: {', '.join(items_here)}"
                        help_text += f"\n   Przykład: 'weź {items_here[0].lower()}'"
                    else:
                        help_text += "\n\n📦 Nie ma tu nic do wzięcia."

        elif command_name in ['idź', 'idz', 'pójdź', 'pojdz']:
            # Pokaż dostępne kierunki
            if self.game_state.prison:
                location = self.game_state.prison.get_current_location()
                if location and hasattr(location, 'connections'):
                    directions = list(location.connections.keys())
                    if directions:
                        help_text += f"\n\n🚪 Dostępne kierunki: {', '.join(directions)}"
                        help_text += f"\n   Przykład: 'idź {directions[0]}'"

        return help_text

    # === HANDLERY KOMEND ===
    
    def _cmd_move(self, args: List[str]) -> Tuple[bool, str]:
        """Porusz gracza."""
        direction = args[0]
        return self.game_state.move_player(direction)
    
    def _cmd_look(self, args: List[str]) -> Tuple[bool, str]:
        """Rozejrzyj się."""
        if not self.game_state.prison:
            return False, "Gra nie jest zainicjalizowana!"

        description = self.game_state.prison.describe_current_location()

        # Dodaj informacje o NPCach w lokacji
        if self.game_state.npc_manager:
            npcs_here = []
            hostile_npcs = []
            current_location_name = self.game_state.current_location
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if hasattr(npc, 'current_location') and npc.current_location == current_location_name:
                    # Sprawdź czy NPC żyje
                    if hasattr(npc, 'combat_stats') and npc.combat_stats.health <= 0:
                        npcs_here.append(f"{npc.name} (martwy)")
                    elif npc.role == "creature":
                        # Stworzenia są wyświetlane osobno jako wrogie
                        hostile_npcs.append(npc.name)
                    else:
                        npcs_here.append(npc.name)

            if npcs_here:
                description += f"\n\nWidzisz tutaj: {', '.join(npcs_here)}"

            if hostile_npcs:
                description += f"\n\n⚔ Wrogowie: {', '.join(hostile_npcs)}"

        # Tutorial hint przy pierwszym użyciu
        self._trigger_tutorial_hint("look", "first_look")

        return True, description
    
    def _cmd_examine(self, args: List[str]) -> Tuple[bool, str]:
        """Zbadaj obiekt."""
        target = ' '.join(args)
        
        if not self.game_state.prison:
            return False, "Gra nie jest zainicjalizowana!"
        
        # Spróbuj zbadać obiekt w lokacji
        result = self.game_state.prison.examine(target)
        
        # Jeśli to NPC, pokaż więcej informacji
        if self.game_state.npc_manager:
            current_location_name = self.game_state.current_location
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if (npc.name.lower() == target or npc_id == target) and \
                   hasattr(npc, 'current_location') and npc.current_location == current_location_name:
                    # Pokaż stan NPCa
                    dominant_emotion = npc.get_dominant_emotion().value if hasattr(npc, 'get_dominant_emotion') else 'neutralny'
                    current_state = npc.current_state.value if hasattr(npc, 'current_state') else 'bezczynny'
                    health_status = f"zdrowie: {getattr(npc, 'health', 100)}/{getattr(npc, 'max_health', 100)}"
                    state_desc = f"Stan: {current_state}, Nastrój: {dominant_emotion}, {health_status}"
                    result += f"\n\n{state_desc}"
                    break
        
        # Sprawdź czy odkryto questa
        if self.game_state.quest_engine:
            discovery = self.game_state.quest_engine.discover_quest(self.game_state.current_location)
            if discovery and discovery.get('success'):
                result += f"\n\n🔍 ODKRYCIE: {discovery.get('dialogue', '')}"
                if discovery.get('initial_clues'):
                    result += "\n\nZnalezione wskazówki:"
                    for loc, clue in discovery['initial_clues'].items():
                        result += f"\n  • {loc}: {clue}"
        
        return True, result
    
    def _cmd_search(self, args: List[str]) -> Tuple[bool, str]:
        """Przeszukaj lokację."""
        if not self.game_state.prison:
            return False, "Gra nie jest zainicjalizowana!"
        
        # search_location zwraca string, nie listę
        result = self.game_state.prison.search_location()
        return True, result
    
    def _cmd_talk(self, args: List[str]) -> Tuple[bool, str]:
        """Rozmawiaj z NPCem."""
        target = ' '.join(args).lower()
        
        if not self.game_state.npc_manager:
            return False, "System NPCów nie jest zainicjalizowany!"
        
        # Znajdź NPCa - bardziej elastyczne dopasowanie
        npc_found = None
        npc_obj = None
        current_location_name = self.game_state.current_location
        
        for npc_id, npc in self.game_state.npc_manager.npcs.items():
            # Sprawdź czy NPC jest w tej lokacji
            if hasattr(npc, 'current_location') and npc.current_location == current_location_name:
                npc_name_lower = npc.name.lower()
                
                # Różne warianty dopasowania
                if (target == npc_name_lower or  # Pełna nazwa
                    target == npc_id.lower() or  # ID
                    target == npc_name_lower.split()[0] or  # Pierwsze słowo
                    target in npc_name_lower or  # Część nazwy
                    npc_name_lower.startswith(target)):  # Początek nazwy
                    npc_found = npc_id
                    npc_obj = npc
                    break
        
        if not npc_found:
            # Pokaż kto jest dostępny
            available_npcs = []
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if hasattr(npc, 'current_location') and npc.current_location == current_location_name:
                    # Nie pokazuj stworzeń jako dostępnych do rozmowy
                    if npc.role != "creature":
                        available_npcs.append(npc.name)
            
            if available_npcs:
                return False, f"Nie ma tu '{target}'. Dostępni do rozmowy: {', '.join(available_npcs)}"
            else:
                return False, "Nie ma tu nikogo do rozmowy."
        
        # Sprawdź czy to stworzenie - nie można z nimi rozmawiać
        if npc_obj and npc_obj.role == "creature":
            # Zwróć specjalną reakcję stworzenia
            creature_reactions = {
                "Szczur": ["*Szczur piszczy groźnie i pokazuje zęby*", 
                          "*Syk syk! Szczur się jeży*",
                          "*Szczur ucieka w kąt, piszcząc wściekle*"],
                "default": ["*Stworzenie warczy groźnie*",
                           "*Istota nie rozumie twoich słów*",
                           "*Dzikie stworzenie patrzy na ciebie wrogo*"]
            }
            
            reactions = creature_reactions.get(npc_obj.name, creature_reactions["default"])
            reaction = random.choice(reactions)
            
            # Możliwość sprowokowania ataku
            if "aggressive" in npc_obj.personality and random.random() < 0.3:
                reaction += "\n\n⚔ Stworzenie atakuje!"
                # Wykonaj atak stworzenia
                if hasattr(npc_obj, 'attack'):
                    success, attack_msg = npc_obj.attack(self.game_state.player)
                    reaction += f"\n{attack_msg}"
            
            return True, reaction
        
        # Tutorial hint przy pierwszej rozmowie
        self._trigger_tutorial_hint("talk", "first_npc")

        # Użyj DialogueSystem do przeprowadzenia rozmowy
        if hasattr(self.game_state, 'dialogue_system') and self.game_state.dialogue_system:
            # Rozpocznij dialog - przekaż też nazwę NPCa do lepszego mapowania
            npc_text, options = self.game_state.dialogue_system.start_dialogue(
                npc_found,
                self.game_state.player,
                npc_obj.name if npc_obj else None
            )
            
            # Zapisz stan dialogu w grze
            self.game_state.current_dialogue = {
                'npc_id': npc_found,
                'npc_name': npc_obj.name if npc_obj else 'Nieznany',  # Dodane dla kontekstu dialogu
                'node_id': 'greeting',
                'options': options
            }
            
            # Sformatuj odpowiedź
            response = f"\n{npc_obj.name}:\n{npc_text}\n"
            
            # KROK 5: Użyj wspólnej metody formatowania
            if options:
                response += self._format_dialogue_options(options)
            else:
                response += "\n[Brak dostępnych opcji dialogowych]"
            
            return True, response
        else:
            # Fallback do starego systemu
            result = self.game_state.npc_manager.player_interact(
                player_id="player",
                npc_id=npc_found,
                action="talk"
            )
            
            return True, result.get('response', 'NPC nie odpowiada.')

    def _cmd_choose_dialogue_option(self, choice_index: int) -> Tuple[bool, str]:
        """KROK 3: Obsługuje wybór opcji dialogowej przez wpisanie cyfry."""
        current = self.game_state.current_dialogue
        if not current:
            return False, "Nie prowadzisz żadnej rozmowy."

        options = current.get('options', [])

        if choice_index < 0 or choice_index >= len(options):
            return False, f"Nieprawidłowy wybór. Dostępne opcje: 1-{len(options)}"

        # Pobierz wybraną opcję
        chosen_opt = options[choice_index]
        opt_text = chosen_opt.text if hasattr(chosen_opt, 'text') else str(chosen_opt)

        # Rozpocznij odpowiedź
        response = f"\n[Ty]: {opt_text}\n"

        # Przetwórz wybór w DialogueSystem
        try:
            result_response, next_text, result, next_options, next_node = \
                self.game_state.dialogue_system.process_choice(
                    current['npc_id'],
                    current['node_id'],
                    choice_index,
                    self.game_state.player
                )

            # Dodaj odpowiedź NPC
            if result_response:
                response += f"\n{result_response}\n"
            if next_text:
                response += f"\n{current['npc_name']}: {next_text}\n"

            # Obsłuż wynik dialogu
            if result == DialogueResult.END or not next_options:
                self.game_state.current_dialogue = None
                response += "\n[Koniec rozmowy]\n"
            elif result == DialogueResult.TRADE:
                self.game_state.current_dialogue = None
                response += "\n[Rozpoczyna się handel...]\n"
                # TODO: Wywołaj system handlu
            elif result == DialogueResult.QUEST:
                response += "\n[Otrzymano zadanie!]\n"
                # Kontynuuj dialog jeśli są opcje
                if next_options:
                    current['node_id'] = next_node
                    current['options'] = next_options
                    response += self._format_dialogue_options(next_options)
                else:
                    self.game_state.current_dialogue = None
            else:  # CONTINUE
                # Aktualizuj stan dialogu
                current['node_id'] = next_node
                current['options'] = next_options
                response += self._format_dialogue_options(next_options)

            return True, response

        except Exception as e:
            self.game_state.current_dialogue = None
            return False, f"Błąd dialogu: {e}"

    def _format_dialogue_options(self, options) -> str:
        """Formatuje opcje dialogowe do wyświetlenia."""
        if not options:
            return ""
        text = "\n═══ OPCJE DIALOGOWE ═══\n"
        for i, opt in enumerate(options, 1):
            opt_text = opt.text if hasattr(opt, 'text') else str(opt)
            text += f"{i}. {opt_text}\n"
        text += f"\nWybierz opcję (1-{len(options)}) lub 'anuluj' aby zakończyć rozmowę.\n"
        return text

    def _cmd_take(self, args: List[str]) -> Tuple[bool, str]:
        """Weź przedmiot."""
        item_name = ' '.join(args).lower()
        
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        # Sprawdź czy przedmiot jest w lokacji
        if self.game_state.prison:
            location = self.game_state.prison.get_current_location()
            if location and hasattr(location, 'items'):
                # Znajdź przedmiot - obsłuż różne formaty
                item_found = None
                for item in location.items:
                    # Obsłuż różne formaty przedmiotów
                    if hasattr(item, 'name'):
                        if item.name.lower() == item_name or item_name in item.name.lower():
                            item_found = item
                            break
                    elif isinstance(item, dict):
                        if item.get('name', '').lower() == item_name or item_name in item.get('name', '').lower():
                            item_found = item
                            break
                    elif isinstance(item, str):
                        if item.lower() == item_name or item_name in item.lower():
                            item_found = item
                            break
                
                if item_found:
                    # Dodaj do ekwipunku gracza
                    if hasattr(self.game_state.player, 'equipment'):
                        # Stwórz obiekt przedmiotu jeśli to string
                        if isinstance(item_found, str):
                            item_obj = type('Item', (), {
                                'name': item_found,
                                'description': f"Zwykły {item_found}",
                                'weight': 1.0
                            })()
                        else:
                            item_obj = item_found
                        
                        # Dodaj do inventory (items, nie backpack!)
                        # Konwertuj do formatu słownikowego jeśli to obiekt
                        if hasattr(item_obj, '__dict__'):
                            item_dict = {
                                'name': getattr(item_obj, 'name', 'Nieznany'),
                                'description': getattr(item_obj, 'description', ''),
                                'weight': getattr(item_obj, 'weight', 1.0),
                                'quantity': 1
                            }
                        elif isinstance(item_obj, dict):
                            item_dict = item_obj.copy()
                            if 'quantity' not in item_dict:
                                item_dict['quantity'] = 1
                        else:
                            item_dict = {
                                'name': str(item_obj),
                                'quantity': 1
                            }
                        
                        # Sprawdź czy przedmiot już istnieje w inventory
                        existing_item = None
                        for inv_item in self.game_state.player.equipment.items:
                            if inv_item.get('name') == item_dict['name']:
                                existing_item = inv_item
                                break
                        
                        if existing_item:
                            # Zwiększ ilość istniejącego przedmiotu
                            existing_item['quantity'] = existing_item.get('quantity', 1) + 1
                        else:
                            # Dodaj nowy przedmiot
                            self.game_state.player.equipment.items.append(item_dict)
                        
                        location.items.remove(item_found)
                        
                        item_display_name = item_obj.name if hasattr(item_obj, 'name') else str(item_obj)
                        return True, f"Wziąłeś: {item_display_name}"
                    else:
                        return False, "Nie możesz teraz brać przedmiotów"
                else:
                    # Pokaż co jest dostępne
                    available = []
                    for item in location.items:
                        if hasattr(item, 'name'):
                            available.append(item.name)
                        elif isinstance(item, dict):
                            available.append(item.get('name', 'nieznany'))
                        else:
                            available.append(str(item))
                    
                    if available:
                        return False, f"Nie ma tu '{item_name}'. Dostępne: {', '.join(available)}"
                    else:
                        return False, "Nie ma tu nic do wzięcia"
        
        return False, f"Nie ma tu przedmiotu: {item_name}"
    
    def _cmd_use(self, args: List[str]) -> Tuple[bool, str]:
        """Użyj przedmiotu."""
        if len(args) < 1:
            return False, "Co chcesz użyć?"
        
        item_name = ' '.join(args).lower()
        
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        # Sprawdź czy gracz ma przedmiot
        if not self.game_state.player.equipment.has_item(item_name):
            return False, f"Nie masz przedmiotu: {item_name}"
        
        # Użyj przedmiotu
        success, message = self.game_state.player.use_item(item_name)
        return success, message
    
    def _cmd_attack(self, args: List[str]) -> Tuple[bool, str]:
        """Atakuj cel."""
        target = ' '.join(args)

        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"

        # Sprawdź czy gracz może walczyć
        if self.game_state.player.is_incapacitated():
            return False, "Jesteś zbyt osłabiony, aby walczyć!"

        # Tutorial hint przy pierwszej walce
        self._trigger_tutorial_hint("attack", "first_combat")

        # Znajdź cel
        if self.game_state.npc_manager:
            current_location_name = self.game_state.current_location
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if (npc.name.lower() == target.lower() or npc_id == target) and \
                   hasattr(npc, 'current_location') and npc.current_location == current_location_name:
                    
                    # Sprawdź czy NPC żyje
                    if hasattr(npc, 'combat_stats') and npc.combat_stats.health <= 0:
                        return False, f"{npc.name} jest już martwy."
                    
                    # Wykonaj atak gracza
                    success, message = self.game_state.player.attack(npc)
                    
                    result_messages = [message]
                    
                    # NPC reaguje jeśli przeżył
                    if success and hasattr(npc, 'combat_stats'):
                        # Sprawdź czy NPC jeszcze żyje
                        if npc.combat_stats.health > 0:
                            # NPC kontratakuje jeśli nie jest zbyt ranny
                            if npc.combat_stats.pain < 70 and npc.current_state != NPCState.FLEEING:
                                npc_success, npc_msg = npc.attack(self.game_state.player)
                                result_messages.append(f"\n{npc_msg}")
                                
                                # Sprawdź czy gracz przeżył kontratak
                                if self.game_state.player.state == CharacterState.MARTWY:
                                    result_messages.append("\n\nZGINĄŁEŚ!")
                                    self.game_state.game_mode = GameMode.DEAD
                            else:
                                # NPC próbuje uciec
                                if npc.flee():
                                    result_messages.append(f"\n{npc.name} ucieka w panice!")
                                else:
                                    result_messages.append(f"\n{npc.name} próbuje uciec, ale nie może!")
                        else:
                            result_messages.append(f"\n{npc.name} pada martwy!")
                            # Możliwość zabrania ekwipunku
                            if npc.gold > 0:
                                result_messages.append(f"Znajdziesz {npc.gold} złota.")
                                self.game_state.player.gold += npc.gold
                                npc.gold = 0
                    
                    return True, "\n".join(result_messages)
        
        return False, f"Nie ma tu celu: {target}"
    
    def _cmd_defend(self, args: List[str]) -> Tuple[bool, str]:
        """Przyjmij postawę obronną."""
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        self.game_state.player.defending = True
        return True, "Przyjmujesz postawę obronną."
    
    def _cmd_flee(self, args: List[str]) -> Tuple[bool, str]:
        """Ucieknij z walki."""
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        # Losowy kierunek ucieczki
        import random
        directions = ["północ", "południe", "wschód", "zachód"]
        direction = random.choice(directions)
        
        success, message = self.game_state.move_player(direction)
        if success:
            return True, f"Uciekasz na {direction}!"
        else:
            return False, "Nie możesz uciec!"
    
    def _cmd_ability(self, args: List[str]) -> Tuple[bool, str]:
        """Użyj zdolności klasowej."""
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        if not self.game_state.player.character_class:
            return False, "Nie masz wybranej klasy postaci!"
        
        if not args:
            return False, "Podaj nazwę zdolności!"
        
        ability_name = args[0].lower()
        target = args[1] if len(args) > 1 else None
        
        # Znajdź zdolność
        ability = None
        for ab in self.game_state.player.character_class.abilities:
            if ab.name.lower().startswith(ability_name) or ability_name in ab.name.lower():
                ability = ab
                break
        
        if not ability:
            return False, f"Nie znasz zdolności '{ability_name}'!"
        
        # Sprawdź cooldown
        if ability.name in self.game_state.player.ability_cooldowns:
            cooldown = self.game_state.player.ability_cooldowns[ability.name]
            if cooldown > 0:
                return False, f"Zdolność {ability.name} będzie dostępna za {cooldown} tur!"
        
        # Sprawdź manę (dla magów)
        if hasattr(self.game_state.player, 'mana'):
            if self.game_state.player.mana < ability.mana_cost:
                return False, f"Nie masz wystarczająco many! ({self.game_state.player.mana}/{ability.mana_cost})"
        
        # Znajdź cel jeśli potrzebny
        target_obj = None
        if ability.target_type != "self" and target:
            # Szukaj NPCa lub gracza
            current_loc = self.game_state.current_location
            if current_loc and current_loc.npcs:
                for npc_id in current_loc.npcs:
                    npc = self.game_state.npcs.get(npc_id)
                    if npc and target.lower() in npc.name.lower():
                        target_obj = npc
                        break
        
        # Wykonaj zdolność
        from player.ability_effects import AbilityEffects
        effect_method = getattr(AbilityEffects, ability.effect_function, None)
        
        if not effect_method:
            return False, f"Zdolność {ability.name} nie jest jeszcze zaimplementowana!"
        
        success, message, effects = effect_method(self.game_state.player, target_obj)
        
        if success:
            # Ustaw cooldown
            self.game_state.player.ability_cooldowns[ability.name] = ability.cooldown
            
            # Zużyj manę
            if hasattr(self.game_state.player, 'mana'):
                self.game_state.player.mana -= ability.mana_cost
            
            # Zużyj staminę
            self.game_state.player.stamina = max(0, self.game_state.player.stamina - ability.stamina_cost)
        
        return success, message
    
    def _cmd_list_abilities(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż dostępne zdolności."""
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        if not self.game_state.player.character_class:
            return False, "Nie masz wybranej klasy postaci!"
        
        output = [f"\n=== Zdolności klasy {self.game_state.player.character_class.name} ===\n"]
        
        for ability in self.game_state.player.character_class.abilities:
            # Status zdolności
            cooldown = self.game_state.player.ability_cooldowns.get(ability.name, 0)
            if cooldown > 0:
                status = f"[Cooldown: {cooldown} tur]"
            else:
                status = "[Gotowa]"
            
            # Koszt
            costs = []
            if ability.mana_cost > 0:
                costs.append(f"Mana: {ability.mana_cost}")
            if ability.stamina_cost > 0:
                costs.append(f"Stamina: {ability.stamina_cost}")
            cost_str = f" ({', '.join(costs)})" if costs else ""
            
            output.append(f"{ability.name} {status}{cost_str}")
            output.append(f"  {ability.description}")
            output.append(f"  Cel: {ability.target_type}, Cooldown: {ability.cooldown} tur")
            output.append("")
        
        # Pokaż aktualną manę dla magów
        if hasattr(self.game_state.player, 'mana'):
            output.append(f"Mana: {self.game_state.player.mana}/{self.game_state.player.max_mana}")
        
        return True, '\n'.join(output)
    
    def _cmd_inventory(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż ekwipunek."""
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"

        # Tutorial hint przy pierwszym użyciu
        self._trigger_tutorial_hint("inventory", "first_inventory")

        return True, self.game_state.player.show_inventory()
    
    def _cmd_equip(self, args: List[str]) -> Tuple[bool, str]:
        """Załóż przedmiot."""
        item_name = ' '.join(args).lower()
        
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        success, message = self.game_state.player.equip_item(item_name)
        return success, message
    
    def _cmd_unequip(self, args: List[str]) -> Tuple[bool, str]:
        """Zdejmij przedmiot."""
        item_name = ' '.join(args).lower()
        
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        success, message = self.game_state.player.unequip_item(item_name)
        return success, message
    
    def _cmd_drop(self, args: List[str]) -> Tuple[bool, str]:
        """Wyrzuć przedmiot."""
        if len(args) < 1:
            return False, "Co chcesz wyrzucić?"
        
        # Obsłuż nazwę przedmiotu i opcjonalną ilość
        parts = ' '.join(args).rsplit(' ', 1)  # Rozdziel na nazwę i potencjalną ilość
        if len(parts) == 2 and parts[1].isdigit():
            item_name = parts[0].lower()
            amount = int(parts[1])
        else:
            item_name = ' '.join(args).lower()
            amount = 1
        
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        if not self.game_state.player.equipment.has_item(item_name):
            return False, f"Nie masz przedmiotu: {item_name}"
        
        # Wyrzuć przedmiot
        success, message = self.game_state.player.drop_item(item_name, amount)
        
        if success:
            # Dodaj do lokacji
            if self.game_state.prison:
                location = self.game_state.prison.get_current_location()
                if location and hasattr(location, 'items'):
                    # Znajdź przedmiot w inventory gracza i skopiuj go
                    for inv_item in self.game_state.player.equipment.items:
                        if inv_item.get('name', '').lower() == item_name:
                            dropped_item = inv_item.copy()
                            dropped_item['quantity'] = amount
                            location.items.append(dropped_item)
                            break
        
        return success, message
    
    def _cmd_craft(self, args: List[str]) -> Tuple[bool, str]:
        """Wytwórz przedmiot."""
        item = ' '.join(args)

        if not self.game_state.crafting_system or not self.game_state.player:
            return False, "System craftingu nie jest zainicjalizowany!"

        # Spróbuj wytworzyć - przekaż gracza dla known_recipes
        result = self.game_state.crafting_system.craft(
            recipe_id=item,
            materials=self.game_state.player.inventory,
            crafter_skill=None,
            player=self.game_state.player
        )

        if result['success']:
            self.game_state.player.add_item(result['item'])
            item_name = result['item'].get('name', result['item']) if isinstance(result['item'], dict) else result['item']
            return True, f"Wytworzyłeś: {item_name} (jakość: {result['quality']})"
        else:
            return False, f"Nie udało się wytworzyć: {result['message']}"
    
    def _cmd_recipes(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż znane receptury."""
        if not self.game_state.crafting_system:
            return False, "System craftingu nie jest zainicjalizowany!"

        # Pobierz znane receptury gracza jako listę (set -> list)
        known_recipe_ids = list(self.game_state.player.known_recipes) if self.game_state.player else []
        recipes = self.game_state.crafting_system.get_known_recipes(known_recipe_ids)

        if recipes:
            text = "Znane receptury:\n"
            for recipe in recipes:
                # Recipe to obiekt, nie słownik
                materials = [f"{ing.przedmiot} x{ing.ilosc}" for ing in recipe.skladniki]
                tools = [tool.przedmiot for tool in recipe.wymagane_narzedzia]
                text += f"\n{recipe.nazwa} ({recipe.id}):\n"
                text += f"  Materiały: {', '.join(materials)}\n"
                if tools:
                    text += f"  Narzędzia: {', '.join(tools)}\n"
                text += f"  Trudność: {recipe.poziom_trudnosci}\n"
            return True, text
        else:
            return True, "Nie znasz żadnych receptur."
    
    def _cmd_trade(self, args: List[str]) -> Tuple[bool, str]:
        """Handluj z NPCem."""
        target = ' '.join(args)
        
        if not self.game_state.economy or not self.game_state.npc_manager:
            return False, "System handlu nie jest zainicjalizowany!"
        
        # Znajdź NPCa
        npc_found = None
        current_location_name = self.game_state.current_location
        for npc_id, npc in self.game_state.npc_manager.npcs.items():
            if (npc.name.lower() == target.lower() or npc_id == target) and \
               hasattr(npc, 'current_location') and npc.current_location == current_location_name:
                npc_found = npc_id
                break
        
        if not npc_found:
            return False, f"Nie ma tu handlarza o imieniu '{target}'."
        
        # Pokaż towary NPCa
        npc_data = self.game_state.economy.npcs.get(npc_found)
        if npc_data and npc_data['inventory']:
            text = f"Towary {target}:\n"
            for item, details in npc_data['inventory'].items():
                price = self.game_state.economy.get_price(item, 'prison')
                text += f"- {item}: {price} złota (ilość: {details['quantity']})\n"
            return True, text
        else:
            return True, f"{target} nie ma nic na sprzedaż."
    
    def _cmd_haggle(self, args: List[str]) -> Tuple[bool, str]:
        """Targuj się o cenę."""
        if not args:
            return False, "Podaj procent (np. 80 dla 80% ceny)"
            
        try:
            percent = int(args[0])
        except (ValueError, IndexError):
            return False, "Podaj poprawny procent (np. 80 dla 80% ceny)"
        
        if percent < 10 or percent > 150:
            return False, "Procent musi być między 10 a 150"
        
        # Sprawdź czy gracz prowadzi rozmowę z NPC który handluje
        current_location = self.game_state.prison.get_current_location()
        if not current_location:
            return False, "Nie ma tutaj nikogo do targowania"
        
        # Znajdź NPCów którzy mogą handlować
        traders = []
        if hasattr(current_location, 'prisoners'):
            traders = [p for p in current_location.prisoners if hasattr(p, 'profession') and p.profession in ['handlarz', 'rzemieślnik']]
        if not traders:
            return False, "Nie ma tutaj nikogo kto chciałby się targować"
        
        # Szansa sukcesu zależna od umiejętności perswazji gracza i procentu
        persuasion_skill = self.game_state.player.skills.get_skill_level('perswazja')
        base_chance = 0.3  # 30% base chance
        skill_bonus = persuasion_skill * 0.02  # +2% per skill level
        
        # Im bliżej normalnej ceny, tym łatwiej się targować
        if 80 <= percent <= 120:
            difficulty_modifier = 0.3
        elif 70 <= percent <= 130:
            difficulty_modifier = 0.1
        else:
            difficulty_modifier = -0.2
        
        success_chance = base_chance + skill_bonus + difficulty_modifier
        success_chance = max(0.05, min(0.95, success_chance))  # clamp 5%-95%
        
        import random
        if random.random() < success_chance:
            # Sukces - próba wzrostu umiejętności
            if random.random() < 0.15:  # 15% szans na wzrost
                self.game_state.player.skills.improve_skill('perswazja', 0.01)
                skill_msg = " [Umiejętność Perswazja wzrosła!]"
            else:
                skill_msg = ""
            
            return True, f"Udało ci się wynegocjować {percent}% ceny! Handlarz się zgodził.{skill_msg}"
        else:
            return False, f"Handlarz nie zgodził się na {percent}% ceny. Spróbuj innej oferty lub popraw swoje umiejętności perswazji."
    
    def _cmd_quests(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż aktywne zadania."""
        if not self.game_state.quest_engine:
            return False, "System questów nie jest zainicjalizowany!"

        # Tutorial hint przy pierwszym sprawdzeniu questów
        self._trigger_tutorial_hint("quests", "first_quest")

        active = self.game_state.quest_engine.get_active_quests()
        
        if active:
            text = "╔════════════════════════════════════════╗\n"
            text += "║          AKTYWNE ZADANIA              ║\n"
            text += "╠════════════════════════════════════════╣\n"
            
            for quest in active:
                text += f"\n📜 {quest.seed.name}\n"
                text += f"  Stan: {quest.state.value}\n"
                
                # Pokaż odkryte wskazówki
                if quest.investigation and quest.investigation.discovered_clues:
                    text += f"  Odkryte wskazówki: {len(quest.investigation.discovered_clues)}\n"
                    for clue in quest.investigation.discovered_clues[:3]:
                        text += f"    • {clue}\n"
                
                # Pokaż dostępne lokacje do zbadania
                if quest.seed.initial_clues:
                    text += "  Lokacje do zbadania:\n"
                    for loc in list(quest.seed.initial_clues.keys())[:3]:
                        text += f"    • {loc}\n"
                
                # Sprawdź czy quest ma limit czasowy
                if quest.seed.time_sensitive:
                    if quest.start_time:
                        from datetime import datetime
                        elapsed = (datetime.now() - quest.start_time).total_seconds() / 3600
                        remaining = quest.seed.expiry_hours - elapsed
                        if remaining > 0:
                            text += f"  ⏱️ Pozostało: {remaining:.1f} godzin\n"
                        else:
                            text += "  ⏱️ CZAS MINĄŁ!\n"
                    else:
                        text += f"  ⏱️ Limit czasu: {quest.seed.expiry_hours} godzin\n"
                
                text += "\n"
            
            text += "╚════════════════════════════════════════╝\n"
            text += "\nUżyj 'zbadaj [lokacja]' aby szukać wskazówek\n"
            text += "Użyj 'rozmawiaj [npc]' aby pytać o informacje"
            return True, text
        else:
            return True, "Nie masz obecnie żadnych odkrytych zadań.\nEksploruj świat aby znaleźć sytuacje wymagające interwencji!"
    
    def _cmd_journal(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż dziennik odkryć."""
        text = "=== DZIENNIK ODKRYĆ ===\n\n"
        
        text += f"Odkryte lokacje ({len(self.game_state.discovered_locations)}):\n"
        for loc in sorted(self.game_state.discovered_locations):
            text += f"  - {loc}\n"
        
        text += f"\nOdkryte sekrety ({len(self.game_state.discovered_secrets)}):\n"
        for secret in sorted(self.game_state.discovered_secrets):
            text += f"  - {secret}\n"
        
        return True, text
    
    def _cmd_status(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż status gracza."""
        return True, self.game_state.get_status()
    
    def _cmd_skills(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż umiejętności."""
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        return True, self.game_state.player.show_skills()
    
    def _cmd_save(self, args: List[str]) -> Tuple[bool, str]:
        """Zapisz grę."""
        slot = int(args[0]) if args else 1
        
        if slot < 1 or slot > 5:
            return False, "Nieprawidłowy slot. Użyj 1-5."
        
        success = self.game_state.save_game(slot)
        
        if success:
            return True, f"Gra zapisana w slocie {slot}."
        else:
            return False, "Błąd zapisu gry."
    
    def _cmd_load(self, args: List[str]) -> Tuple[bool, str]:
        """Wczytaj grę."""
        slot = int(args[0]) if args else 1
        
        if slot < 1 or slot > 5:
            return False, "Nieprawidłowy slot. Użyj 1-5."
        
        success = self.game_state.load_game(slot)
        
        if success:
            return True, f"Gra wczytana ze slotu {slot}."
        else:
            return False, "Błąd wczytywania gry."
    
    def _cmd_map(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż mapę okolicy."""
        if not self.game_state.prison:
            return False, "Nie możesz teraz zobaczyć mapy."
        
        current = self.game_state.current_location
        
        # Dynamiczna mapa ASCII więzienia oparta na rzeczywistej strukturze
        # Struktura zgodna z połączeniami:
        # - Korytarz centralny w środku
        # - Korytarze północny, południowy, wschodni, zachodni dookoła
        # - Cele podłączone do odpowiednich korytarzy
        
        map_str = """
╔═══════════════════════════════════════════╗
║            MAPA WIĘZIENIA                 ║
╠═══════════════════════════════════════════╣
║                                           ║
║            [Kuchnia]                      ║
║                │                          ║
║      [C2]──[K.Płn]──[C1]                 ║
║               │                           ║
║  [Wart]──[K.Zach]──[K.Cent]──[K.Wsch]──[Dz]║
║               │         │         │       ║
║      [C4]──[K.Płd]──[C3]       [C5]      ║
║               │                           ║
║           [Zbroj]                         ║
║                                           ║
╠═══════════════════════════════════════════╣
║ Legenda:                                  ║
║ [C1-5] - Cele       [K.xxx] - Korytarze  ║
║ [Dz] - Dziedziniec  [Zbroj] - Zbrojownia ║
║ [Wart] - Wartownia  @ - Twoja pozycja    ║
╚═══════════════════════════════════════════╝
"""
        
        # Mapa lokacji do symboli na mapie
        location_map = {
            'cela_1': '[C1]',
            'cela_2': '[C2]',
            'cela_3': '[C3]',
            'cela_4': '[C4]',
            'cela_5': '[C5]',
            'kuchnia': '[Kuchnia]',
            'dziedziniec': '[Dz]',
            'zbrojownia': '[Zbroj]',
            'wartownia': '[Wart]',
            'korytarz_północny': '[K.Płn]',
            'korytarz_południowy': '[K.Płd]',
            'korytarz_wschodni': '[K.Wsch]',
            'korytarz_zachodni': '[K.Zach]',
            'korytarz_centralny': '[K.Cent]'
        }
        
        # Znajdź i zastąp lokację gracza symbolem @
        if current in location_map:
            marker = location_map[current]
            # Zachowaj długość pola - jeśli marker jest krótszy niż zastępowany tekst, dodaj spacje
            marker_len = len(marker)
            new_marker = '@' + ' ' * (marker_len - 1)
            map_str = map_str.replace(marker, new_marker)
        
        # Dodaj informację o aktualnej lokacji
        current_location = self.game_state.prison.get_current_location()
        if current_location:
            map_str += f"\n\nObecna lokacja: {current_location.name}"
            if current_location.connections:
                exits = []
                for direction, dest in current_location.connections.items():
                    exits.append(f"{direction}")
                map_str += f"\nMożliwe kierunki: {', '.join(exits)}"
        
        return True, map_str
    
    def _cmd_help(self, args: List[str]) -> Tuple[bool, str]:
        """Pokaż pomoc."""
        if args:
            # Pomoc dla konkretnej komendy
            cmd_name = args[0].lower()
            if cmd_name in self.commands:
                cmd = self.commands[cmd_name]
                text = f"{cmd.name}: {cmd.description}\n"
                if cmd.usage:
                    text += f"Użycie: {cmd.usage}\n"
                if cmd.aliases:
                    text += f"Aliasy: {', '.join(cmd.aliases)}"
                return True, text
            else:
                return False, f"Nieznana komenda: {cmd_name}"
        else:
            # Lista wszystkich komend
            text = "=== DOSTĘPNE KOMENDY ===\n\n"
            
            # Grupuj po kategoriach
            by_category = {}
            for cmd in set(self.commands.values()):  # set() aby uniknąć duplikatów
                if cmd.category not in by_category:
                    by_category[cmd.category] = []
                by_category[cmd.category].append(cmd)
            
            for category in CommandCategory:
                if category in by_category:
                    text += f"{category.value.upper()}:\n"
                    for cmd in sorted(by_category[category], key=lambda c: c.name):
                        text += f"  {cmd.name} - {cmd.description}\n"
                    text += "\n"
            
            text += "Użyj 'pomoc [komenda]' dla szczegółów."
            return True, text
    
    def _cmd_quit(self, args: List[str]) -> Tuple[bool, str]:
        """Wyjdź z gry."""
        return True, "QUIT"  # Specjalny kod dla głównej pętli
    
    def _cmd_wait(self, args: List[str]) -> Tuple[bool, str]:
        """Czekaj określony czas."""
        try:
            minutes = int(args[0])
        except (ValueError, IndexError):
            return False, "Podaj liczbę minut."
        
        if minutes < 1 or minutes > 480:
            return False, "Możesz czekać od 1 do 480 minut."
        
        # Aktualizuj czas gry
        self.game_state.update(minutes)
        
        time_str = f"{self.game_state.game_time // 60:02d}:{self.game_state.game_time % 60:02d}"
        return True, f"Czekałeś {minutes} minut. Jest teraz {time_str}."
    
    def _cmd_sleep(self, args: List[str]) -> Tuple[bool, str]:
        """Idź spać."""
        if not self.game_state.player:
            return False, "Gracz nie jest zainicjalizowany!"
        
        # Sprawdź czy gracz jest w celi
        if "cela" not in self.game_state.current_location:
            return False, "Możesz spać tylko w celi."
        
        # Sprawdź porę
        hour = self.game_state.game_time // 60
        if 6 <= hour < 22:
            return False, "Jest za wcześnie na sen. Spróbuj po 22:00."
        
        # Śpij do 6:00
        sleep_time = (360 - self.game_state.game_time) % 1440
        self.game_state.update(sleep_time)
        
        # Regeneracja podczas snu
        self.game_state.player.rest(sleep_time)
        
        return True, "Spałeś całą noc. Budzisz się wypoczęty o 6:00."