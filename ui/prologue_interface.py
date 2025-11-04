"""
Prologue Interface - Przyjazny interfejs dla nowych graczy
Wrapper wokół istniejących systemów UI dodający beginner-friendly features
"""

import time
from typing import Optional, Dict, List, Any, Tuple
from ui.interface import GameInterface
from core.game_state import GameState
from ui.contextual_menu import ContextualActionMenu


class PrologueInterface:
    """
    Przyjazny interfejs dla nowych graczy w prologu.
    Wykorzystuje istniejący GameInterface dodając:
    - Wizualny status panel
    - Kontekstowe podpowiedzi
    - Quick action menu
    - Location context
    - Beginner-friendly prompts
    """

    def __init__(self, base_interface: GameInterface, game_state: GameState):
        """
        Args:
            base_interface: Podstawowy GameInterface
            game_state: Stan gry
        """
        self.interface = base_interface
        self.game_state = game_state
        self.show_hints = True  # Pokazuj hinty dla nowych graczy
        self.compact_mode = False  # Tryb kompaktowy (mniej ozdobników)

        # Contextual Action Menu - inteligentne menu akcji
        self.contextual_menu = ContextualActionMenu(game_state)

    def display_game_screen(self):
        """Wyświetl główny ekran gry z wszystkimi panelami."""
        # Wyczyść ekran (opcjonalnie - można wyłączyć)
        # self.interface.clear()

        # Panel statusu
        self._display_status_panel()

        print()  # Odstęp

        # Panel lokacji
        self._display_location_panel()

        print()  # Odstęp

        # Panel szybkich akcji (jeśli hinty włączone)
        if self.show_hints:
            self._display_quick_actions()

    def _display_status_panel(self):
        """Wyświetl przyjazny panel statusu gracza."""
        if not self.game_state.player:
            return

        player = self.game_state.player

        # Header
        self.interface.print("╔════════════════════ STATUS ═══════════════════╗", 'cyan')

        # Imię i lokacja
        location_name = self.game_state.current_location.replace('_', ' ').title()
        self.interface.print(
            f"║ {player.name:<20} 📍 {location_name:<20} ║",
            'cyan'
        )

        self.interface.print("╠═══════════════════════════════════════════════╣", 'cyan')

        # Zdrowie
        hp = player.health
        max_hp = player.max_health
        hp_percent = (hp / max_hp * 100) if max_hp > 0 else 0
        hp_bar = self._create_bar(hp_percent, 20, '❤')
        hp_color = self._get_health_color(hp_percent)
        self.interface.print(f"║ ❤️  HP    {hp_bar} {hp:>3}/{max_hp:<3} ║", hp_color)

        # Stamina
        stamina = player.stamina
        max_stamina = player.max_stamina
        st_percent = (stamina / max_stamina * 100) if max_stamina > 0 else 0
        st_bar = self._create_bar(st_percent, 20, '⚡')
        st_color = self._get_stamina_color(st_percent)
        self.interface.print(f"║ ⚡ STAM  {st_bar} {stamina:>3}/{max_stamina:<3} ║", st_color)

        # Ból (jeśli większy niż 0)
        if hasattr(player, 'pain') and player.pain > 0:
            pain = player.pain
            pain_bar = self._create_bar(pain, 20, '!')
            pain_color = self._get_pain_color(pain)
            self.interface.print(f"║ 💢 BÓL  {pain_bar} {pain:>3}%    ║", pain_color)

        # Głód (jeśli większy niż 30)
        if hasattr(player, 'hunger') and player.hunger > 30:
            hunger = player.hunger
            hunger_bar = self._create_bar(hunger, 20, '🍞')
            hunger_color = self._get_hunger_color(hunger)
            self.interface.print(f"║ 🍞 GŁÓD {hunger_bar} {hunger:>3}%    ║", hunger_color)

        # Footer
        self.interface.print("╚═══════════════════════════════════════════════╝", 'cyan')

    def _display_location_panel(self):
        """Wyświetl panel informacji o lokacji."""
        if not self.game_state.prison:
            return

        location = self.game_state.prison.get_current_location()
        if not location:
            return

        # Header
        self.interface.print("╔══════════════════ LOKACJA ════════════════════╗", 'green')

        # Nazwa lokacji
        loc_name = location.name.upper()
        self.interface.print(f"║ 🗺️  {loc_name:<42} ║", 'bright_green')

        self.interface.print("╠═══════════════════════════════════════════════╣", 'green')

        # Opis (skrócony do 45 znaków per linia)
        desc = location.description_day or location.description_night or "Tutaj jesteś."
        desc_lines = self._wrap_text(desc, 45)
        for line in desc_lines[:2]:  # Max 2 linie opisu
            self.interface.print(f"║ {line:<45} ║", 'white')

        # Wyjścia
        if location.connections:
            exits = ", ".join(location.connections.keys())
            exits_short = exits if len(exits) <= 41 else exits[:38] + "..."
            self.interface.print("╠═══════════════════════════════════════════════╣", 'green')
            self.interface.print(f"║ 🚪 Wyjścia: {exits_short:<33} ║", 'yellow')

        # NPCe w lokacji
        npcs_here = self._get_npcs_in_location()
        if npcs_here:
            npcs_str = ", ".join(npcs_here[:3])  # Max 3 NPCów
            if len(npcs_here) > 3:
                npcs_str += f" +{len(npcs_here)-3}"
            npcs_short = npcs_str if len(npcs_str) <= 38 else npcs_str[:35] + "..."
            self.interface.print(f"║ 👥 Ludzie: {npcs_short:<36} ║", 'cyan')

        # Przedmioty (jeśli są)
        if location.items:
            items_count = len(location.items)
            self.interface.print(f"║ 📦 Przedmiotów: {items_count:<30} ║", 'magenta')

        # Footer
        self.interface.print("╚═══════════════════════════════════════════════╝", 'green')

    def _display_quick_actions(self):
        """Wyświetl panel szybkich akcji dla nowych graczy."""
        self.interface.print("╔══════════════ SZYBKIE KLAWISZE ══════════════╗", 'yellow')
        self.interface.print("║                                               ║", 'yellow')

        # Podstawowe akcje (2 kolumny dla kompaktu)
        actions_row1 = [
            ("[?]", "Menu Akcji"),
            ("[L]", "Rozejrzyj"),
            ("[I]", "Ekwipunek"),
        ]

        actions_row2 = [
            ("[Q]", "Questy"),
            ("[X]", "Status"),
            ("[H]", "Pomoc"),
        ]

        actions_row3 = [
            ("[N]", "Północ"),
            ("[S]", "Południe"),
            ("[E]", "Wschód"),
            ("[W]", "Zachód"),
        ]

        # Wyświetl pierwszy rząd
        row1_text = "║  " + "  ".join([f"{k} {n:<10}" for k, n in actions_row1])
        row1_text += " " * (49 - len(row1_text)) + "║"
        self.interface.print(row1_text, 'white')

        # Wyświetl drugi rząd
        row2_text = "║  " + "  ".join([f"{k} {n:<10}" for k, n in actions_row2])
        row2_text += " " * (49 - len(row2_text)) + "║"
        self.interface.print(row2_text, 'white')

        self.interface.print("║                                               ║", 'yellow')

        # Wyświetl nawigację
        row3_text = "║  " + "  ".join([f"{k} {n:<7}" for k, n in actions_row3])
        row3_text += " " * (49 - len(row3_text)) + "║"
        self.interface.print(row3_text, 'cyan')

        self.interface.print("║                                               ║", 'yellow')
        self.interface.print("╚═══════════════════════════════════════════════╝", 'yellow')

        # Hint o pisaniu komend i numerach
        if self.show_hints:
            self.interface.print(
                "\n💡 Wpisz [?] aby zobaczyć numbered menu akcji lub komendę tekstową",
                'bright_yellow'
            )

    def get_input_with_quickkeys(self, prompt: str = "\n> ") -> Tuple[str, bool]:
        """
        Pobierz input od gracza z obsługą quick keys i numbered actions.

        Args:
            prompt: Tekst zachęty

        Returns:
            Tuple (komenda, czy_pokazac_menu) - komenda do wykonania i flaga czy pokazać menu
        """
        user_input = self.interface.get_input(prompt).strip()

        # Sprawdź czy to numer (numbered action)
        if user_input.isdigit():
            number = int(user_input)
            command = self.contextual_menu.get_command_by_number(number)
            if command:
                self.interface.print(f"→ {command}", 'dim')
                return command, False
            else:
                self.interface.print(f"❌ Nieprawidłowy numer: {number}", 'red')
                return "", False

        user_input_lower = user_input.lower()

        # Extended Quick keys mapping
        quick_keys = {
            # Podstawowe (już były)
            'l': 'rozejrzyj',
            'i': 'ekwipunek',
            'q': 'questy',
            'h': 'pomoc',

            # NOWE - Nawigacja
            'n': 'idź północ',
            'e': 'idź wschód',
            'w': 'idź zachód',

            # NOWE - Akcje
            't': None,  # Talk - pokaż menu z NPCami
            'g': None,  # Get/Grab - pokaż menu z przedmiotami
            'x': 'status',  # eXamine self

            # NOWE - Systemy
            'm': 'mapa',
            '?': None,  # Pokaż contextual menu

            # Dodatkowe aliasy
            's': 'idź południe',  # South (konflikt ze status, ale południe ważniejsze)
        }

        # Jeśli to single-letter quick key
        if len(user_input_lower) == 1 and user_input_lower in quick_keys:
            translated = quick_keys[user_input_lower]

            # Specjalne case: '?' pokazuje contextual menu
            if user_input_lower == '?':
                return "", True  # Sygnał aby pokazać menu

            # Specjalne case: 't' i 'g' wymagają kontekstu
            if user_input_lower == 't':
                # TODO: Pokaż tylko NPCów do wyboru
                self.interface.print("💬 Z kim chcesz rozmawiać? (wpisz imię lub numer z menu)", 'cyan')
                return "", True

            if user_input_lower == 'g':
                # TODO: Pokaż tylko przedmioty do wyboru
                self.interface.print("📦 Co chcesz wziąć? (wpisz nazwę lub numer z menu)", 'cyan')
                return "", True

            if translated:
                self.interface.print(f"→ {translated}", 'dim')
                return translated, False

        # Jeśli to normalna komenda, zwróć jak jest
        return user_input, False

    def show_welcome_message(self):
        """Pokaż wiadomość powitalną dla nowych graczy."""
        self.interface.print("\n" + "═" * 50, 'cyan')
        self.interface.print("           🎮 WITAJ W DRODZE SZAMANA! 🎮           ", 'bright_cyan')
        self.interface.print("═" * 50 + "\n", 'cyan')

        welcome = """
Znajdujesz się w więzieniu. Twoja podróż dopiero się zaczyna...

💡 PIERWSZE KROKI:
  • Wpisz 'rozejrzyj' (lub naciśnij L) aby przyjrzeć się celi
  • Wpisz 'ekwipunek' (lub naciśnij I) aby sprawdzić co masz
  • Wpisz 'pomoc' (lub naciśnij H) aby zobaczyć wszystkie komendy

🎯 PAMIĘTAJ:
  • Możesz używać naturalnego języka ("weź chleb", "porozmawiaj z Piotrem")
  • Używaj skrótów: L, I, Q, H
  • Wpisz 'pomoc' w każdej chwili aby zobaczyć dostępne komendy

Powodzenia, Szamanie! 🔥
"""
        self.interface.print(welcome, 'white')
        self.interface.get_input("\n[Naciśnij Enter aby rozpocząć]")

    def display_command_result(self, success: bool, message: str):
        """
        Wyświetl rezultat komendy w przyjazny sposób.

        Args:
            success: Czy komenda się powiodła
            message: Wiadomość do wyświetlenia
        """
        if success:
            # Sukces - normalny tekst
            print(f"\n{message}\n")
        else:
            # Błąd - podświetl na czerwono
            self.interface.print(f"\n❌ {message}\n", 'bright_red')

            # Zasugeruj pomoc jeśli komenda nieznana
            if "nieznana" in message.lower() or "nie rozumiem" in message.lower():
                self.interface.print(
                    "💡 Spróbuj wpisać 'pomoc' aby zobaczyć dostępne komendy.",
                    'yellow'
                )

    def display_tutorial_progress(self):
        """Wyświetl postęp w tutorialu (opcjonalnie)."""
        if not self.game_state.tutorial_manager:
            return

        # Ile hintów już pokazano
        shown = len(self.game_state.first_time_commands)
        total = 7  # Mamy 7 tutorial hints

        if shown > 0 and shown < total:
            progress_bar = self._create_bar((shown / total) * 100, 20, '●')
            self.interface.print(
                f"\n📚 Tutorial: {progress_bar} {shown}/{total} kroków",
                'bright_yellow'
            )

    def toggle_hints(self):
        """Przełącz pokazywanie hintów."""
        self.show_hints = not self.show_hints
        if self.show_hints:
            self.interface.print("✅ Podpowiedzi włączone", 'green')
        else:
            self.interface.print("❌ Podpowiedzi wyłączone", 'red')

    def toggle_compact_mode(self):
        """Przełącz tryb kompaktowy."""
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            self.interface.print("✅ Tryb kompaktowy włączony", 'green')
        else:
            self.interface.print("✅ Tryb normalny włączony", 'green')

    def show_contextual_menu(self):
        """Wyświetl menu kontekstowe z dostępnymi akcjami."""
        self.contextual_menu.display_menu(self.interface)

    # === Helper Methods ===

    def _create_bar(self, percent: float, width: int = 20, fill_char: str = '█') -> str:
        """
        Stwórz wizualny pasek postępu.

        Args:
            percent: Procent zapełnienia (0-100)
            width: Szerokość paska
            fill_char: Znak zapełnienia

        Returns:
            String z paskiem
        """
        filled = int(width * percent / 100)
        empty = width - filled
        return f"[{fill_char * filled}{'·' * empty}]"

    def _get_health_color(self, percent: float) -> str:
        """Zwróć kolor dla poziomu zdrowia."""
        if percent >= 70:
            return 'bright_green'
        elif percent >= 40:
            return 'yellow'
        else:
            return 'bright_red'

    def _get_stamina_color(self, percent: float) -> str:
        """Zwróć kolor dla poziomu staminy."""
        if percent >= 50:
            return 'bright_cyan'
        elif percent >= 25:
            return 'yellow'
        else:
            return 'red'

    def _get_pain_color(self, pain: int) -> str:
        """Zwróć kolor dla poziomu bólu."""
        if pain >= 70:
            return 'bright_red'
        elif pain >= 40:
            return 'yellow'
        else:
            return 'white'

    def _get_hunger_color(self, hunger: int) -> str:
        """Zwróć kolor dla poziomu głodu."""
        if hunger >= 70:
            return 'bright_red'
        elif hunger >= 50:
            return 'yellow'
        else:
            return 'white'

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """
        Zawiń tekst do określonej szerokości.

        Args:
            text: Tekst do zawinięcia
            width: Maksymalna szerokość linii

        Returns:
            Lista linii
        """
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines if lines else [""]

    def _get_npcs_in_location(self) -> List[str]:
        """
        Pobierz listę NPCów w obecnej lokacji.

        Returns:
            Lista imion NPCów
        """
        npcs = []

        if not self.game_state.npc_manager:
            return npcs

        current_loc = self.game_state.current_location

        for npc_id, npc in self.game_state.npc_manager.npcs.items():
            if hasattr(npc, 'current_location') and npc.current_location == current_loc:
                # Sprawdź czy nie jest marty i nie jest stworzeniem
                is_alive = True
                if hasattr(npc, 'combat_stats'):
                    is_alive = npc.combat_stats.health > 0

                if is_alive and npc.role != "creature":
                    npcs.append(npc.name)

        return npcs


# === Convenience Functions ===

def create_prologue_interface(game_state: GameState) -> PrologueInterface:
    """
    Stwórz PrologueInterface dla danego game state.

    Args:
        game_state: Stan gry

    Returns:
        Nowy PrologueInterface
    """
    base_interface = GameInterface()
    return PrologueInterface(base_interface, game_state)
