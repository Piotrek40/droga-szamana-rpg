"""Zaawansowany interfejs użytkownika dla Droga Szamana RPG."""

import os
import sys
import platform
import shutil
from typing import Optional, List, Dict, Any
from datetime import datetime
import time


class Color:
    """Kolory ANSI dla terminala."""
    # Podstawowe
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Jasne
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Tła
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Style
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'


class AdvancedInterface:
    """Zaawansowany interfejs użytkownika z wieloma funkcjami."""
    
    def __init__(self):
        """Inicjalizacja interfejsu."""
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
        self.colors_enabled = self._check_color_support()
        self.input_history = []
        self.history_index = -1
        
        # Panele interfejsu - dostosuj do rozmiaru terminala
        # Zapewnij przynajmniej 10 linii dla głównej treści
        self.status_panel_height = min(6, self.terminal_height // 4)
        self.log_panel_height = min(5, self.terminal_height // 5)
        # Pozostaw większość miejsca dla głównej treści
        self.main_panel_height = max(10, self.terminal_height - self.status_panel_height - self.log_panel_height - 3)
        
        # Log wiadomości
        self.message_log = []
        self.max_log_messages = 100
        
        # Stan interfejsu
        self.show_status = True
        self.show_minimap = True
        self.auto_scroll = True
        
        # Ustawienia kolorów tematycznych
        self.theme = self._load_theme()
    
    def print(self, text: str):
        """Metoda kompatybilności dla prostego wyświetlania tekstu."""
        # Dodaj do logu i wyświetl
        self.log_message(text)
        print(text)
    
    def get_input(self, prompt: str = "> ") -> str:
        """Metoda kompatybilności dla pobierania inputu."""
        return input(prompt)
    
    def _get_terminal_width(self) -> int:
        """Pobierz szerokość terminala."""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    def _get_terminal_height(self) -> int:
        """Pobierz wysokość terminala."""
        try:
            return shutil.get_terminal_size().lines
        except:
            return 24
    
    def _check_color_support(self) -> bool:
        """Sprawdź czy terminal obsługuje kolory."""
        if platform.system() == 'Windows':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        return True
    
    def _load_theme(self) -> Dict[str, str]:
        """Załaduj motyw kolorystyczny."""
        return {
            'border': Color.CYAN,
            'title': Color.BRIGHT_YELLOW + Color.BOLD,
            'health_high': Color.BRIGHT_GREEN,
            'health_medium': Color.YELLOW,
            'health_low': Color.RED,
            'stamina': Color.BLUE,
            'pain': Color.RED,
            'hunger': Color.ORANGE if hasattr(Color, 'ORANGE') else Color.YELLOW,
            'npc_friendly': Color.GREEN,
            'npc_neutral': Color.WHITE,
            'npc_hostile': Color.RED,
            'item_common': Color.WHITE,
            'item_uncommon': Color.GREEN,
            'item_rare': Color.BLUE,
            'item_epic': Color.MAGENTA,
            'item_legendary': Color.YELLOW,
            'location': Color.CYAN,
            'time': Color.BRIGHT_BLUE,
            'quest': Color.BRIGHT_MAGENTA,
            'warning': Color.BRIGHT_YELLOW,
            'error': Color.BRIGHT_RED,
            'success': Color.BRIGHT_GREEN,
            'input': Color.BRIGHT_WHITE,
            'text': Color.WHITE
        }
    
    def colorize(self, text: str, color: str) -> str:
        """Dodaj kolor do tekstu jeśli kolory są wspierane."""
        if self.colors_enabled and color in self.theme:
            return f"{self.theme[color]}{text}{Color.RESET}"
        return text
    
    def clear_screen(self):
        """Wyczyść ekran."""
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
    
    def draw_box(self, x: int, y: int, width: int, height: int, 
                 title: str = "", color: str = "border") -> List[str]:
        """Narysuj ramkę."""
        lines = []
        
        # Górna ramka
        if title:
            title_len = len(title)
            padding = (width - title_len - 4) // 2
            top_line = "╔" + "═" * padding + f"[ {title} ]" + "═" * (width - padding - title_len - 4) + "╗"
        else:
            top_line = "╔" + "═" * (width - 2) + "╗"
        
        lines.append(self.colorize(top_line, color))
        
        # Boczne ramki
        for i in range(height - 2):
            lines.append(self.colorize("║" + " " * (width - 2) + "║", color))
        
        # Dolna ramka
        lines.append(self.colorize("╚" + "═" * (width - 2) + "╝", color))
        
        return lines
    
    def draw_status_panel(self, game_state) -> List[str]:
        """Narysuj panel statusu gracza."""
        if not game_state.player:
            return []
        
        player = game_state.player
        lines = []
        
        # Ramka statusu
        panel_width = self.terminal_width // 3
        status_box = self.draw_box(0, 0, panel_width, self.status_panel_height, "STATUS", "border")
        
        # Wypełnij informacjami
        lines.append(status_box[0])
        
        # Imię i lokacja
        name_line = f"║ {self.colorize(player.name, 'title'):<{panel_width-4}} ║"
        lines.append(name_line)
        
        location_line = f"║ {self.colorize(f'📍 {game_state.current_location}', 'location'):<{panel_width-4}} ║"
        lines.append(location_line)
        
        # Zdrowie
        health_pct = int((player.combat_stats.health / player.combat_stats.max_health) * 100) if player.combat_stats.max_health > 0 else 0
        health_color = 'health_high' if health_pct > 70 else 'health_medium' if health_pct > 30 else 'health_low'
        health_bar = self._create_bar(health_pct, 100, 20, '❤', '♡')
        health_line = f"║ {self.colorize(f'Zdrowie: {health_bar} {player.combat_stats.health:.0f}/{player.combat_stats.max_health:.0f}', health_color):<{panel_width-4}} ║"
        lines.append(health_line)
        
        # Stamina
        stamina_pct = int((player.combat_stats.stamina / player.combat_stats.max_stamina) * 100) if player.combat_stats.max_stamina > 0 else 0
        stamina_bar = self._create_bar(stamina_pct, 100, 20, '⚡', '○')
        stamina_line = f"║ {self.colorize(f'Stamina:  {stamina_bar} {player.combat_stats.stamina:.0f}/{player.combat_stats.max_stamina:.0f}', 'stamina'):<{panel_width-4}} ║"
        lines.append(stamina_line)
        
        # Ból
        pain_bar = self._create_bar(int(player.combat_stats.pain), 100, 20, '💀', '○')
        pain_line = f"║ {self.colorize(f'Ból:      {pain_bar} {player.combat_stats.pain:.0f}/100', 'pain'):<{panel_width-4}} ║"
        lines.append(pain_line)
        
        # Złoto i czas
        time_str = f"{game_state.game_time // 60:02d}:{game_state.game_time % 60:02d}"
        gold_time_line = f"║ {self.colorize(f'💰 {player.equipment.gold}', 'text')} | {self.colorize(f'🕒 {time_str}', 'time'):<{panel_width-15}} ║"
        lines.append(gold_time_line)
        
        lines.append(status_box[-1])
        
        return lines
    
    def draw_minimap_panel(self, game_state) -> List[str]:
        """Narysuj panel minimapy."""
        if not self.show_minimap:
            return []
        
        lines = []
        panel_width = self.terminal_width // 3
        minimap_box = self.draw_box(0, 0, panel_width, self.status_panel_height, "MAPA", "border")
        
        lines.append(minimap_box[0])
        
        # Prosta mapa więzienia
        prison_map = [
            "     [Zbrojownia]  [Biuro]",
            "         |           |    ",
            "[Cela5]--+--[Koryt.]--+--[Kuchnia]",
            "         |           |    ",
            "[Cela4]--+--[Dziedziniec]",
            "         |                ",
            "[Cela3]--+--[Cela2]--[Cela1]",
        ]
        
        current_loc = game_state.current_location
        for i, map_line in enumerate(prison_map[:self.status_panel_height-3]):
            # Podświetl aktualną lokację
            if current_loc in map_line.lower():
                map_line = self.colorize(map_line, 'location')
            
            padded_line = f"║ {map_line:<{panel_width-4}} ║"
            lines.append(padded_line)
        
        # Dopełnij puste linie
        while len(lines) < self.status_panel_height - 1:
            lines.append(f"║{' ' * (panel_width-2)}║")
        
        lines.append(minimap_box[-1])
        
        return lines
    
    def draw_info_panel(self, game_state) -> List[str]:
        """Narysuj panel informacyjny."""
        lines = []
        panel_width = self.terminal_width // 3
        info_box = self.draw_box(0, 0, panel_width, self.status_panel_height, "INFO", "border")
        
        lines.append(info_box[0])
        
        # Informacje o porze dnia
        if game_state.time_system:
            time_period = game_state.time_system.get_time_period()
            time_desc = game_state.time_system.get_time_description()
            activity = game_state.time_system.get_activity_level()
            
            period_line = f"║ {self.colorize(f'Pora: {time_period}', 'time'):<{panel_width-4}} ║"
            lines.append(period_line)
            
            activity_line = f"║ {self.colorize(f'Aktywność: {activity}', 'text'):<{panel_width-4}} ║"
            lines.append(activity_line)
        
        # Pogoda
        if game_state.weather_system:
            weather = game_state.weather_system.get_weather_description()
            weather_line = f"║ {self.colorize(f'🌤 {weather}', 'text'):<{panel_width-4}} ║"
            lines.append(weather_line)
        
        # NPCe w lokacji
        if game_state.npc_manager:
            npcs_here = []
            for npc_id, npc in game_state.npc_manager.npcs.items():
                if npc.current_location == game_state.current_location:
                    npcs_here.append(npc.name)
            
            if npcs_here:
                npcs_line = f"║ {self.colorize('👥 ' + ', '.join(npcs_here[:2]), 'npc_neutral'):<{panel_width-4}} ║"
                lines.append(npcs_line)
            else:
                lines.append(f"║ {self.colorize('👥 Brak postaci', 'text'):<{panel_width-4}} ║")
        
        # Dopełnij
        while len(lines) < self.status_panel_height - 1:
            lines.append(f"║{' ' * (panel_width-2)}║")
        
        lines.append(info_box[-1])
        
        return lines
    
    def draw_main_display(self, content: str) -> List[str]:
        """Narysuj główny obszar wyświetlania."""
        lines = []
        content_lines = content.split('\n')
        
        # Ramka głównego obszaru
        main_box = self.draw_box(0, 0, self.terminal_width, self.main_panel_height, "DROGA SZAMANA", "title")
        
        lines.append(main_box[0])
        
        # Wypełnij treścią
        for i in range(self.main_panel_height - 2):
            if i < len(content_lines):
                line_content = content_lines[i][:self.terminal_width-4]  # Przycięcie długich linii
                padded_line = f"║ {line_content:<{self.terminal_width-4}} ║"
                lines.append(padded_line)
            else:
                lines.append(f"║{' ' * (self.terminal_width-2)}║")
        
        lines.append(main_box[-1])
        
        return lines
    
    def draw_log_panel(self) -> List[str]:
        """Narysuj panel logów/wiadomości."""
        lines = []
        log_box = self.draw_box(0, 0, self.terminal_width, self.log_panel_height, "LOGI", "border")
        
        lines.append(log_box[0])
        
        # Pokaż ostatnie wiadomości
        recent_messages = self.message_log[-self.log_panel_height+2:] if self.message_log else []
        
        for i in range(self.log_panel_height - 2):
            if i < len(recent_messages):
                msg = recent_messages[i]
                timestamp = msg.get('time', '')
                text = msg.get('text', '')
                msg_type = msg.get('type', 'text')
                
                colored_text = self.colorize(f"[{timestamp}] {text}", msg_type)[:self.terminal_width-4]
                padded_line = f"║ {colored_text:<{self.terminal_width-4}} ║"
                lines.append(padded_line)
            else:
                lines.append(f"║{' ' * (self.terminal_width-2)}║")
        
        lines.append(log_box[-1])
        
        return lines
    
    def draw_input_line(self, prompt: str = "> ", current_input: str = "") -> str:
        """Narysuj linię wprowadzania."""
        input_box = "┌" + "─" * (self.terminal_width - 2) + "┐\n"
        input_content = f"│ {self.colorize(prompt, 'input')}{self.colorize(current_input, 'text'):<{self.terminal_width-len(prompt)-4}} │\n"
        input_bottom = "└" + "─" * (self.terminal_width - 2) + "┘"
        
        return input_box + input_content + input_bottom
    
    def _create_bar(self, value: int, max_value: int, width: int, 
                   filled_char: str = "█", empty_char: str = "░") -> str:
        """Stwórz pasek postępu."""
        filled_width = int((value / max_value) * width)
        return filled_char * filled_width + empty_char * (width - filled_width)
    
    def log_message(self, message: str, msg_type: str = "text"):
        """Dodaj wiadomość do logu."""
        timestamp = datetime.now().strftime("%H:%M")
        self.message_log.append({
            'time': timestamp,
            'text': message,
            'type': msg_type
        })
        
        # Ograniczenie rozmiaru logu
        if len(self.message_log) > self.max_log_messages:
            self.message_log.pop(0)
    
    def display_full_interface(self, game_state, main_content: str):
        """Wyświetl pełny interfejs."""
        self.clear_screen()
        
        # Aktualizuj rozmiar terminala
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
        
        # Prostszy układ - tylko główna treść i logi
        # Wyświetl główną treść
        print("═" * self.terminal_width)
        
        # Po prostu wyświetl treść bez zbędnego zawijania
        # Niech terminal sam sobie radzi z długimi liniami
        print(main_content)
        
        print("═" * self.terminal_width)
        
        # Panel logów (ostatnie wiadomości)
        print("[ Ostatnie wiadomości ]")
        for msg in self.message_log[-5:]:  # Ostatnie 5 wiadomości
            timestamp = msg.get('time', '')  # Poprawka: 'time' zamiast 'timestamp'
            text = msg.get('text', '')
            # Wyświetl pierwsze 2 linie wiadomości jeśli jest długa
            if len(text) > self.terminal_width - 10:
                lines = text.split('\n')
                if lines:
                    # Pierwsza linia wiadomości
                    first_line = lines[0][:self.terminal_width - 10]
                    print(f"[{timestamp}] {first_line}")
                    # Druga linia jeśli istnieje
                    if len(lines) > 1 and lines[1]:
                        continuation = lines[1][:self.terminal_width - 15]
                        print(f"      {continuation}...")
            else:
                print(f"[{timestamp}] {text}")
        
        print("─" * self.terminal_width)
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Zawijaj tekst do określonej szerokości z zachowaniem całych zdań."""
        if not text:
            return [""]
        
        # Użyj większej szerokości jeśli width jest zbyt małe
        width = max(width, 40)
        
        lines = []
        # Najpierw podziel na linie (zachowaj oryginalne łamanie)
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append("")
                continue
                
            if len(paragraph) <= width:
                lines.append(paragraph)
            else:
                # Zawijaj długie linie inteligentnie
                words = paragraph.split()
                current_line = ""
                
                for word in words:
                    # Sprawdź czy dodanie słowa przekroczy szerokość
                    test_line = current_line + " " + word if current_line else word
                    
                    if len(test_line) <= width:
                        current_line = test_line
                    else:
                        # Jeśli przekroczy, zapisz obecną linię i zacznij nową
                        if current_line:
                            lines.append(current_line)
                        
                        # Jeśli samo słowo jest dłuższe niż szerokość, podziel je
                        if len(word) > width:
                            while len(word) > width:
                                lines.append(word[:width])
                                word = word[width:]
                            current_line = word if word else ""
                        else:
                            current_line = word
                
                # Dodaj ostatnią linię jeśli istnieje
                if current_line:
                    lines.append(current_line)
        
        return lines if lines else [""]
    
    def get_input_with_history(self, prompt: str = "> ") -> str:
        """Pobierz input z historią komend."""
        print(self.draw_input_line(prompt))
        
        try:
            user_input = input().strip()
            
            if user_input and (not self.input_history or user_input != self.input_history[-1]):
                self.input_history.append(user_input)
                if len(self.input_history) > 100:
                    self.input_history.pop(0)
            
            return user_input
        except (EOFError, KeyboardInterrupt):
            return "quit"
    
    def show_help_screen(self):
        """Pokaż ekran pomocy."""
        self.clear_screen()
        
        help_text = """
╔═══════════════════════════════════════════════════════════════════╗
║                         POMOC - DROGA SZAMANA                     ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  PODSTAWOWE KOMENDY:                                             ║
║  • idź [kierunek] - porusz się (północ/południe/wschód/zachód)   ║
║  • rozejrzyj - opisz aktualną lokację                           ║
║  • zbadaj [obiekt] - dokładnie zbadaj obiekt lub osobę          ║
║  • rozmawiaj [npc] - rozmawiaj z postacią                       ║
║  • weź [przedmiot] - podnieś przedmiot                          ║
║  • użyj [przedmiot] - użyj przedmiotu                           ║
║                                                                   ║
║  WALKA:                                                          ║
║  • atakuj [cel] - zaatakuj                                       ║
║  • broń - przyjmij postawę obronną                              ║
║  • uciekaj - próba ucieczki                                     ║
║                                                                   ║
║  SYSTEM:                                                         ║
║  • status - pokaż szczegółowy status                            ║
║  • ekwipunek - pokaż przedmioty                                 ║
║  • umiejętności - lista umiejętności                            ║
║  • zapisz [1-5] - zapisz grę                                    ║
║  • wczytaj [1-5] - wczytaj grę                                  ║
║  • pomoc - ta pomoc                                             ║
║  • quit - wyjście z gry                                         ║
║                                                                   ║
║  SKRÓTY KLAWISZOWE:                                             ║
║  • n/s/w/e - ruch (północ/południe/zachód/wschód)              ║
║  • l - rozejrzyj się                                            ║
║  • i - inwentarz                                                ║
║                                                                   ║
║  WSKAZÓWKI:                                                      ║
║  • Umiejętności rosną tylko przez użycie                        ║
║  • Ból wpływa na wszystkie akcje                                ║
║  • NPCe pamiętają twoje czyny                                   ║
║  • Zbadaj dokładnie każdą lokację                               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

[Naciśnij Enter aby kontynuować]
"""
        print(help_text)
        input()
    
    def show_loading_screen(self, message: str = "Ładowanie..."):
        """Pokaż ekran ładowania."""
        self.clear_screen()
        
        # Animacja ładowania
        spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        
        for i in range(20):  # 2 sekundy animacji
            frame = spinner[i % len(spinner)]
            loading_text = f"\n\n{' ' * (self.terminal_width//2 - 10)}{frame} {message}\n"
            
            print(f"\033[2J\033[H{loading_text}", end='', flush=True)
            time.sleep(0.1)
    
    def toggle_status(self):
        """Przełącz widoczność panelu statusu."""
        self.show_status = not self.show_status
    
    def toggle_minimap(self):
        """Przełącz widoczność minimapy."""
        self.show_minimap = not self.show_minimap
    
    def display_game_panels(self, message: str, game_state, location_info: Dict[str, Any]):
        """Wyświetl główny interfejs gry z panelami."""
        # Dodaj wiadomość do logu
        if message:
            self.log_message(message)
        
        # Wyczyść ekran
        self.clear_screen()
        
        # Wyświetl pełny interfejs używając prawdziwego game_state
        self.display_full_interface(game_state, message or "")
    
    def clear(self):
        """Metoda kompatybilności dla czyszczenia ekranu."""
        self.clear_screen()