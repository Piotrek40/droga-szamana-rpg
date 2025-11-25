"""Interfejs użytkownika dla gry tekstowej."""

import os
import sys
import platform
from typing import Optional


class GameInterface:
    """Klasa zarządzająca interfejsem tekstowym gry."""
    
    def __init__(self):
        """Inicjalizacja interfejsu."""
        self.system = platform.system()
        self.encoding = 'utf-8'
        
        # Kolory ANSI (działają na większości terminali)
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bright_red': '\033[91m',
            'bright_green': '\033[92m',
            'bright_yellow': '\033[93m',
            'bright_blue': '\033[94m',
            'bright_magenta': '\033[95m',
            'bright_cyan': '\033[96m'
        }
        
        # Sprawdź czy terminal wspiera kolory
        self.use_colors = self._check_color_support()
    
    def _check_color_support(self) -> bool:
        """Sprawdź czy terminal wspiera kolory ANSI.
        
        Returns:
            True jeśli kolory są wspierane
        """
        # Windows 10+ wspiera kolory ANSI
        if self.system == 'Windows':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except (AttributeError, OSError, ValueError):
                return False
        
        # Unix/Linux/Mac zazwyczaj wspierają
        return self.system in ['Linux', 'Darwin']
    
    def clear(self):
        """Wyczyść ekran."""
        if self.system == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
    
    def clear_screen(self):
        """Alias dla clear() - dla kompatybilności."""
        self.clear()
    
    def print(self, text: str, color: Optional[str] = None, end: str = '\n'):
        """Wyświetl tekst z opcjonalnym kolorem.
        
        Args:
            text: Tekst do wyświetlenia
            color: Nazwa koloru (opcjonalnie)
            end: Znak końca linii
        """
        if self.use_colors and color and color in self.colors:
            print(f"{self.colors[color]}{text}{self.colors['reset']}", end=end)
        else:
            print(text, end=end)
    
    def print_header(self, text: str):
        """Wyświetl nagłówek.
        
        Args:
            text: Tekst nagłówka
        """
        width = 70
        border = "=" * width
        padding = (width - len(text) - 2) // 2
        
        self.print(border, 'cyan')
        self.print(f"║{' ' * padding}{text}{' ' * (width - padding - len(text) - 2)}║", 'cyan')
        self.print(border, 'cyan')
    
    def print_box(self, title: str, content: str, color: str = 'white'):
        """Wyświetl tekst w ramce.
        
        Args:
            title: Tytuł ramki
            content: Zawartość ramki
            color: Kolor ramki
        """
        width = 70
        lines = content.split('\n')
        
        # Górna ramka
        self.print(f"╔{'═' * (width-2)}╗", color)
        
        # Tytuł
        if title:
            title_padding = (width - len(title) - 4) // 2
            self.print(f"║ {' ' * title_padding}{title}{' ' * (width - title_padding - len(title) - 4)} ║", color)
            self.print(f"╠{'═' * (width-2)}╣", color)
        
        # Zawartość
        for line in lines:
            if len(line) > width - 4:
                # Zawijaj długie linie
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= width - 4:
                        current_line += word + " "
                    else:
                        self.print(f"║ {current_line:<{width-4}} ║", color)
                        current_line = word + " "
                if current_line:
                    self.print(f"║ {current_line:<{width-4}} ║", color)
            else:
                self.print(f"║ {line:<{width-4}} ║", color)
        
        # Dolna ramka
        self.print(f"╚{'═' * (width-2)}╝", color)
    
    def print_status(self, health: int, stamina: int, pain: int, hunger: int):
        """Wyświetl pasek statusu gracza.
        
        Args:
            health: Zdrowie (0-100)
            stamina: Stamina (0-100)
            pain: Ból (0-100)
            hunger: Głód (0-100)
        """
        # Kolory w zależności od wartości
        def get_color(value: int, reverse: bool = False) -> str:
            if reverse:  # Dla bólu i głodu - wyższe wartości są gorsze
                if value >= 70:
                    return 'red'
                elif value >= 40:
                    return 'yellow'
                else:
                    return 'green'
            else:  # Dla zdrowia i staminy - niższe wartości są gorsze
                if value <= 30:
                    return 'red'
                elif value <= 60:
                    return 'yellow'
                else:
                    return 'green'
        
        # Wyświetl paski
        self.print("┌─────────────────────────────────────────────────────────────┐")
        
        # Zdrowie
        health_bar = self._create_bar(health, 20)
        self.print(f"│ Zdrowie:  {health_bar} {health:3d}% ", get_color(health), end="")
        self.print("│", end="\n")
        
        # Stamina
        stamina_bar = self._create_bar(stamina, 20)
        self.print(f"│ Stamina:  {stamina_bar} {stamina:3d}% ", get_color(stamina), end="")
        self.print("│", end="\n")
        
        # Ból
        pain_bar = self._create_bar(pain, 20)
        self.print(f"│ Ból:      {pain_bar} {pain:3d}% ", get_color(pain, True), end="")
        self.print("│", end="\n")
        
        # Głód
        hunger_bar = self._create_bar(hunger, 20)
        self.print(f"│ Głód:     {hunger_bar} {hunger:3d}% ", get_color(hunger, True), end="")
        self.print("│", end="\n")
        
        self.print("└─────────────────────────────────────────────────────────────┘")
    
    def _create_bar(self, value: int, width: int = 20) -> str:
        """Stwórz pasek postępu.
        
        Args:
            value: Wartość (0-100)
            width: Szerokość paska
            
        Returns:
            String reprezentujący pasek
        """
        filled = int((value / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def print_inventory(self, items: list, equipped: dict, gold: int):
        """Wyświetl ekwipunek gracza.
        
        Args:
            items: Lista przedmiotów w plecaku
            equipped: Słownik założonych przedmiotów
            gold: Ilość złota
        """
        self.print_box("EKWIPUNEK", "")
        
        # Założone przedmioty
        if equipped:
            self.print("Założone:", 'cyan')
            for slot, item in equipped.items():
                self.print(f"  {slot}: {item}", 'green')
            self.print("")
        
        # Plecak
        if items:
            self.print("Plecak:", 'cyan')
            for i, item in enumerate(items, 1):
                self.print(f"  {i}. {item}")
        else:
            self.print("Plecak jest pusty.", 'dim')
        
        self.print(f"\nZłoto: {gold}", 'yellow')
    
    def print_dialogue(self, speaker: str, text: str, emotion: str = "neutral"):
        """Wyświetl dialog NPCa.
        
        Args:
            speaker: Imię mówiącego
            text: Tekst dialogu
            emotion: Emocja (neutral, angry, happy, sad, fearful)
        """
        # Kolor w zależności od emocji
        emotion_colors = {
            'neutral': 'white',
            'angry': 'red',
            'happy': 'green',
            'sad': 'blue',
            'fearful': 'yellow',
            'suspicious': 'magenta'
        }
        
        color = emotion_colors.get(emotion, 'white')
        
        self.print(f"\n{speaker}:", 'cyan')
        self.print(f'"{text}"', color)
    
    def print_combat(self, attacker: str, target: str, action: str, 
                     damage: int = 0, success: bool = True):
        """Wyświetl akcję bojową.
        
        Args:
            attacker: Atakujący
            target: Cel
            action: Typ akcji
            damage: Obrażenia
            success: Czy akcja się powiodła
        """
        if success:
            if action == "attack":
                self.print(f"⚔️ {attacker} atakuje {target} zadając {damage} obrażeń!", 'red')
            elif action == "defend":
                self.print(f"🛡️ {attacker} przyjmuje postawę obronną.", 'blue')
            elif action == "dodge":
                self.print(f"💨 {attacker} unika ataku {target}!", 'green')
            elif action == "critical":
                self.print(f"💥 {attacker} zadaje krytyczne obrażenia {target}! -{damage} HP!", 'bright_red')
        else:
            if action == "miss":
                self.print(f"✗ {attacker} chybia próbując trafić {target}.", 'dim')
            elif action == "blocked":
                self.print(f"🛡️ {target} blokuje atak {attacker}.", 'cyan')
    
    def print_discovery(self, discovery_type: str, name: str, description: str = ""):
        """Wyświetl odkrycie.
        
        Args:
            discovery_type: Typ odkrycia (secret, location, recipe, etc.)
            name: Nazwa odkrycia
            description: Opis odkrycia
        """
        icons = {
            'secret': '🔍',
            'location': '🗺️',
            'recipe': '📜',
            'skill': '⚡',
            'quest': '❗'
        }
        
        icon = icons.get(discovery_type, '✨')
        
        self.print(f"\n{icon} ODKRYCIE: {name}", 'bright_yellow')
        if description:
            self.print(description, 'yellow')
    
    def print_ascii_art(self, text: str):
        """Wyświetl tekst jako ASCII art.
        
        Args:
            text: Tekst do wyświetlenia
        """
        # Prosty ASCII art dla tytułu gry
        if text == "DROGA SZAMANA":
            art = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                          DROGA SZAMANA                               ║
║                                                                       ║
║               Text RPG inspirowane serią Vasily'ego Mahanenko        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
            """
            self.print(art, 'cyan')
        else:
            # Dla innych tekstów - wyświetl w ramce
            self.print_header(text)
    
    def get_input(self, prompt: str = "> ") -> str:
        """Pobierz input od użytkownika.
        
        Args:
            prompt: Tekst zachęty
            
        Returns:
            Wprowadzony tekst
        """
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return ""
    
    def get_choice(self, prompt: str, options: list) -> Optional[int]:
        """Pobierz wybór z listy opcji.
        
        Args:
            prompt: Tekst pytania
            options: Lista opcji do wyboru
            
        Returns:
            Numer wybranej opcji (1-based) lub None
        """
        self.print(prompt)
        for i, option in enumerate(options, 1):
            self.print(f"{i}. {option}")
        
        choice = self.get_input("Wybierz (numer): ")
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return choice_num
        except ValueError:
            pass
        
        return None
    
    def wait_for_key(self, message: str = "[Naciśnij Enter aby kontynuować]"):
        """Czekaj na naciśnięcie klawisza.
        
        Args:
            message: Wiadomość do wyświetlenia
        """
        self.get_input(message)
    
    def print_ascii_art(self, art_type: str):
        """Wyświetl ASCII art.
        
        Args:
            art_type: Typ grafiki do wyświetlenia
        """
        arts = {
            'skull': """
                 _____ 
                /     \\
               | () () |
                \\  ^  /
                 |||||
                 |||||
            """,
            
            'sword': """
                  /\\
                 /  \\
                /    \\
               /      \\
              /   /\\   \\
             /   /  \\   \\
            /___/    \\___\\
               |    |
               |    |
               |    |
               |    |
               |____|
            """,
            
            'prison': """
            |||||||||||||||||
            || || || || || ||
            || || || || || ||
            || || || || || ||
            || || || || || ||
            |||||||||||||||||
            """
        }
        
        if art_type in arts:
            self.print(arts[art_type], 'dim')