#!/usr/bin/env python3
"""
Wśród Miliona Gwiazd
Tekstowa gra strategiczna science fiction

Główny plik uruchamiający grę
"""

import sys
import os

from core.game_engine import GameEngine
from ui.interface import GameInterface
from ui.commands import CommandParser, CommandHandler


class Game:
    """Główna klasa gry"""

    def __init__(self):
        self.engine = GameEngine()
        self.command_handler = CommandHandler(self.engine)
        self.running = False

    def run(self):
        """Uruchamia grę"""
        GameInterface.show_welcome()
        GameInterface.pause()

        self.running = True

        while self.running:
            self.show_main_menu()

    def show_main_menu(self):
        """Pokazuje menu główne"""
        GameInterface.show_main_menu()
        choice = GameInterface.get_input()

        if choice == "1":
            self.new_game()
        elif choice == "2":
            self.load_game()
        elif choice == "3":
            self.running = False
            print("\nDziękujemy za grę! Do zobaczenia wśród gwiazd!")
        else:
            GameInterface.show_error("Nieprawidłowy wybór")

    def new_game(self):
        """Rozpoczyna nową grę"""
        GameInterface.clear_screen()
        GameInterface.print_header("NOWA GRA")

        # Pobierz imię gracza
        print("Podaj swoje imię, Komandorze: ", end="")
        player_name = GameInterface.get_input()

        if not player_name:
            player_name = "Komandor"

        # Wybór frakcji
        GameInterface.show_faction_selection()
        print("Wybierz frakcję (1-4): ", end="")
        faction_choice = GameInterface.get_input()

        faction_map = {
            "1": "Imperium",
            "2": "Federacja",
            "3": "Korporacja",
            "4": "Piraci"
        }

        faction = faction_map.get(faction_choice, "Federacja")

        # Inicjalizuj grę
        print(f"\nInicjalizacja galaktyki...")
        self.engine.initialize_new_game(player_name, faction)

        GameInterface.show_success(f"Witaj, {player_name} z frakcji {faction}!")
        GameInterface.show_info(f"Otrzymałeś planetę startową: {self.engine.player.planets[0].name}")

        GameInterface.pause()

        # Rozpocznij pętlę gry
        self.game_loop()

    def load_game(self):
        """Wczytuje zapisaną grę"""
        GameInterface.clear_screen()
        GameInterface.print_header("WCZYTAJ GRĘ")

        # Pokaż dostępne zapisy
        save_dir = "saves"
        if os.path.exists(save_dir):
            saves = [f.replace('.json', '') for f in os.listdir(save_dir) if f.endswith('.json')]

            if saves:
                print("Dostępne zapisy:")
                for i, save in enumerate(saves, 1):
                    print(f"  {i}. {save}")

                print("\nPodaj nazwę zapisu: ", end="")
                slot = GameInterface.get_input()

                if self.engine.load_game(slot):
                    GameInterface.show_success(f"Wczytano grę: {slot}")
                    GameInterface.pause()
                    self.game_loop()
                else:
                    GameInterface.show_error("Nie udało się wczytać gry")
                    GameInterface.pause()
            else:
                GameInterface.show_error("Brak zapisanych gier")
                GameInterface.pause()
        else:
            GameInterface.show_error("Brak zapisanych gier")
            GameInterface.pause()

    def game_loop(self):
        """Główna pętla gry"""
        playing = True

        while playing and not self.engine.game_over:
            GameInterface.clear_screen()
            GameInterface.show_game_menu(self.engine.current_turn)

            # Pobierz komendę
            command_text = GameInterface.get_input("> ")

            # Parsuj i wykonaj
            command, args = CommandParser.parse(command_text)

            if command:
                playing = self.command_handler.execute(command, args)

            # Jeśli gra się skończyła
            if self.engine.game_over:
                GameInterface.show_game_over(self.engine.victory)
                GameInterface.pause()
                playing = False


def main():
    """Funkcja główna"""
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\n\nGra przerwana przez użytkownika.")
        print("Dziękujemy za grę!")
    except Exception as e:
        print(f"\n\n❌ Wystąpił błąd krytyczny: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
