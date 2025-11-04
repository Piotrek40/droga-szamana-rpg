#!/usr/bin/env python3
"""
DROGA SZAMANA - Text RPG inspired by Vasily Mahanenko's LitRPG series
Główna pętla gry
"""

import sys
import os
import time
import traceback
from typing import Optional

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game_state import game_state, GameMode
from core.event_bus import event_bus
from ui.commands import CommandParser
from ui.interface import GameInterface
from ui.smart_interface import create_smart_interface
from ui.prologue_interface import create_prologue_interface
from ui.cutscene_manager import CutsceneManager, TutorialManager, create_prison_intro_cutscene
from npcs.dialogue_system import DialogueSystem, DialogueResult
from quests.quest_engine import QuestState


class DrogaSzamanaRPG:
    """Główna klasa gry."""
    
    def __init__(self):
        """Inicjalizacja gry."""
        self.running = False
        self.game_state = game_state
        self.interface = GameInterface()
        self.command_parser = CommandParser(self.game_state)
        self.smart_interface = None  # Będzie utworzony po init_game
        self.dialogue_system = DialogueSystem()
        self.game_state.dialogue_system = self.dialogue_system  # Przypisz do game_state
        self.use_smart = True  # Domyślnie używaj smart interfejsu

        # Systemy narracyjne
        self.cutscene_manager = CutsceneManager(self.interface)
        self.tutorial_manager = TutorialManager(self.interface)
        self.game_state.tutorial_manager = self.tutorial_manager  # Przypisz do game_state

        # Prologue Interface - przyjazny interfejs dla nowych graczy
        self.prologue_interface = None  # Będzie utworzony po init_game
        self.use_prologue_interface = True  # Domyślnie włączony dla nowych graczy

        # Ustawienia
        self.auto_save_interval = 300  # 5 minut
        self.last_save_time = time.time()

        # Importuj wszystkie pluginy
        self._load_plugins()
        
    def start(self):
        """Uruchom grę."""
        self.running = True
        
        # Pokaż intro
        self.show_intro()
        
        # Menu główne
        while self.running:
            try:
                choice = self.main_menu()
                
                if choice == "1":
                    self.new_game()
                elif choice == "2":
                    self.load_game_menu()
                elif choice == "3":
                    self.show_credits()
                elif choice == "4":
                    self.running = False
                    break
                    
            except KeyboardInterrupt:
                self.interface.print("\n\nPrzerwano grę...")
                self.running = False
                break
            except Exception as e:
                self.interface.print(f"\nBłąd krytyczny: {e}")
                traceback.print_exc()
                self.running = False
                break
    
    def show_intro(self):
        """Pokaż intro gry."""
        intro = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                          DROGA SZAMANA                               ║
║                                                                       ║
║               Text RPG inspirowane serią Vasily'ego Mahanenko        ║
║                                                                       ║
║     "W tym świecie ból jest prawdziwy, śmierć ma konsekwencje,      ║
║         a każda umiejętność musi być zdobyta krwią i potem."        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

        Witaj w Barlionii, świecie gdzie zostałeś uwięziony...
        Świecie, gdzie musisz przetrwać, rozwijać się i znaleźć drogę.
        
        Pamiętaj:
        - Nie ma poziomów ani XP - uczysz się przez praktykę
        - Ból wpływa na wszystkie twoje akcje
        - NPCe żyją własnym życiem i pamiętają twoje czyny
        - Każda decyzja ma konsekwencje
        
        Twoja podróż zaczyna się w więzieniu...
"""
        self.interface.print(intro)
        time.sleep(2)
    
    def main_menu(self) -> str:
        """Wyświetl menu główne.
        
        Returns:
            Wybór użytkownika
        """
        menu = """
╔═══════════════════════════════════════════════════════════════════════╗
║                           MENU GŁÓWNE                                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║                     1. Nowa Gra                                      ║
║                     2. Wczytaj Grę                                   ║
║                     3. O Grze                                        ║
║                     4. Wyjście                                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
        self.interface.print(menu)
        return self.interface.get_input("Wybierz opcję (1-4): ")
    
    def new_game(self):
        """Rozpocznij nową grę."""
        self.interface.clear()
        self.interface.print("=== NOWA GRA ===\n")
        
        # Wybór imienia
        name = self.interface.get_input("Jak się nazywasz, więźniu? ")
        if not name:
            name = "Mahan"
        
        # Wybór trudności
        self.interface.print("\nPoziom trudności:")
        self.interface.print("1. Łatwy - dla początkujących")
        self.interface.print("2. Normalny - zbalansowane wyzwanie")
        self.interface.print("3. Trudny - dla doświadczonych")
        self.interface.print("4. Hardcore - permadeath, bez litości")
        
        diff_choice = self.interface.get_input("Wybierz (1-4): ")
        difficulty_map = {"1": "easy", "2": "normal", "3": "hard", "4": "hardcore"}
        difficulty = difficulty_map.get(diff_choice, "normal")
        
        # Wybór klasy postaci
        self.interface.print("\n=== WYBÓR KLASY ===\n")
        self.interface.print("Każda klasa ma unikalną filozofię i zdolności:\n")
        
        # Import klas
        from player.classes import ClassManager, ClassName
        class_manager = ClassManager()
        
        # Wyświetl dostępne klasy
        class_options = []
        for i, class_name in enumerate(ClassName, 1):
            char_class = class_manager.get_class(class_name)
            if char_class:
                self.interface.print(f"{i}. {char_class.name} - {char_class.description}")
                self.interface.print(f"   Filozofia: {char_class.philosophy.core_belief[:60]}...")
                ability_names = [ab.name for ab in list(char_class.abilities.values())[:2]]
                if ability_names:
                    self.interface.print(f"   Zdolności: {', '.join(ability_names)}...")
                else:
                    self.interface.print(f"   Zdolności: Brak specjalnych zdolności")
                self.interface.print("")
                class_options.append(class_name.value)
        
        # Wybór klasy
        class_choice = self.interface.get_input(f"Wybierz klasę (1-{len(class_options)}): ")
        try:
            class_index = int(class_choice) - 1
            if 0 <= class_index < len(class_options):
                selected_class = class_options[class_index]
                self.interface.print(f"\nWybrałeś klasę: {selected_class.capitalize()}")
            else:
                selected_class = class_options[0]
                self.interface.print(f"\nNieprawidłowy wybór. Domyślna klasa: {selected_class.capitalize()}")
        except (ValueError, IndexError):
            selected_class = class_options[0]
            self.interface.print(f"\nNieprawidłowy wybór. Domyślna klasa: {selected_class.capitalize()}")
        
        # Inicjalizacja gry
        self.interface.print("\n" + "="*50)
        self.game_state.init_game(name, difficulty, selected_class)
        
        # Pokaż wprowadzenie
        self.show_game_intro()
        
        # Rozpocznij główną pętlę gry
        self.game_loop()
    
    def show_game_intro(self):
        """Pokaż wprowadzenie do gry - kinowy cutscene."""
        # Resetuj flagę pomijania (dla nowych gier)
        self.cutscene_manager.reset_skip()

        # Stwórz i odtwórz cutscene wprowadzający
        intro_frames = create_prison_intro_cutscene()
        self.cutscene_manager.play_cutscene(intro_frames, skippable=True)

        # Wyczyść ekran po cutscene
        self.interface.clear()
    
    def game_loop(self):
        """Główna pętla gry."""
        # OPCJA 1: Użyj Prologue Interface (przyjazny dla nowych graczy)
        if self.use_prologue_interface:
            if not self.prologue_interface:
                self.prologue_interface = create_prologue_interface(self.game_state)

            # Uruchom pętlę z prologue interface
            self._run_prologue_game_loop()
            return

        # OPCJA 2: Użyj Smart Interface (zaawansowany)
        if self.use_smart and not self.smart_interface:
            self.smart_interface = create_smart_interface(self.game_state, self.available_plugins)

        if self.use_smart:
            # Uruchom smart interface
            self.smart_interface.run_game_loop()
            return

        # OPCJA 3: Stara pętla jako fallback
        self.interface.print("=== GRA ROZPOCZĘTA ===\n")
        
        if self.smart_interface:
            self.interface.print("💡 Smart interface aktywny. Spróbuj naturalnych komend.\n")
        else:
            self.interface.print("Wpisz 'pomoc' aby zobaczyć listę komend.\n")
        
        # Pokaż początkową lokację
        success, message = self.command_parser.parse_and_execute("rozejrzyj")
        
        # Wyświetl odpowiedni interfejs
        if self.smart_interface:
            self.smart_interface.display_contextual_content(message)
        else:
            self.interface.display_message(message)
        
        # Główna pętla
        last_update = time.time()
        
        while self.game_state.game_mode == GameMode.PLAYING:
            try:
                # Pobierz komendę od gracza
                command = self.interface.get_input("\n> ")
                
                if not command:
                    continue
                
                # Sprawdź przełączanie interfejsu
                # Sprawdź czy jesteśmy w dialogu
                if hasattr(self.game_state, 'current_dialogue') and self.game_state.current_dialogue:
                    # Obsłuż wybór opcji dialogowej
                    if command.lower() == 'anuluj' or command.lower() == 'wyjdź':
                        self.game_state.current_dialogue = None
                        message = "Zakończyłeś rozmowę."
                        success = True
                    elif command.isdigit():
                        choice = int(command) - 1
                        dialogue = self.game_state.current_dialogue
                        
                        if 0 <= choice < len(dialogue['options']):
                            # Przetwórz wybór
                            response, next_text, result, next_options, next_node_id = self.dialogue_system.process_choice(
                                dialogue['npc_id'],
                                dialogue['node_id'],
                                choice,
                                self.game_state.player
                            )
                            
                            # Sformatuj odpowiedź
                            message = f"\nTy: {dialogue['options'][choice].text}\n"
                            message += f"\n{response}\n"
                            
                            if next_text:
                                message += f"\n{next_text}\n"
                            
                            # Sprawdź czy kontynuować dialog
                            if result == DialogueResult.END or not next_options:
                                self.game_state.current_dialogue = None
                                message += "\n[Koniec rozmowy]"
                            else:
                                # Zaktualizuj opcje
                                dialogue['options'] = next_options
                                dialogue['node_id'] = next_node_id if next_node_id else 'greeting'
                                
                                message += "\n═══ OPCJE DIALOGOWE ═══\n"
                                for i, opt in enumerate(next_options, 1):
                                    message += f"{i}. {opt.text}\n"
                                message += f"\nWybierz opcję (1-{len(next_options)}) lub 'anuluj' aby zakończyć rozmowę."
                            
                            success = True
                        else:
                            message = "Nieprawidłowy numer opcji."
                            success = False
                    else:
                        message = "W trakcie rozmowy możesz tylko wybrać numer opcji lub 'anuluj'."
                        success = False
                        
                # Interface switching removed - using smart interface by default
                else:
                    # Wykonaj komendę
                    if self.smart_interface:
                        success, message = self.smart_interface.process_input(command)
                    else:
                        success, message = self.command_parser.parse_and_execute(command)
                
                # Specjalny kod dla wyjścia
                if message == "QUIT":
                    if self.confirm_quit():
                        break
                    else:
                        continue
                
                # Aktualizuj display
                if self.smart_interface:
                    # Smart interface handles display automatically
                    pass
                else:
                    self.update_interface_display(message)
                
                # Aktualizuj stan gry (1 minuta czasu gry per komenda)
                current_time = time.time()
                delta_time = 1  # Każda akcja zajmuje 1 minutę gry
                self.game_state.update(delta_time)
                
                # Auto-save
                if current_time - self.last_save_time > self.auto_save_interval:
                    self.auto_save()
                    self.last_save_time = current_time
                
                # Sprawdź czy gracz nie umarł
                if self.game_state.game_mode == GameMode.DEAD:
                    self.handle_death()
                    break
                
                # Sprawdź wydarzenia emergentne
                self.check_emergent_events()
                
            except KeyboardInterrupt:
                if self.confirm_quit():
                    break
            except EOFError:
                # Gracefully handle EOF when piping input or in non-interactive mode
                self.interface.print("\n[Koniec danych wejściowych - wychodzę z gry]")
                break
            except Exception as e:
                self.interface.print(f"Błąd: {e}")
                traceback.print_exc()
                # If we get repeated errors, ask if user wants to continue
                if hasattr(self, '_consecutive_errors'):
                    self._consecutive_errors += 1
                    if self._consecutive_errors > 3:
                        self.interface.print("\nZbyt wiele błędów. Wychodzę z gry.")
                        break
                else:
                    self._consecutive_errors = 1

    def _run_prologue_game_loop(self):
        """Pętla gry z Prologue Interface - przyjazny interfejs dla nowych graczy."""
        # Powitanie
        self.prologue_interface.show_welcome_message()

        # Pierwsza akcja - rozejrzyj się
        success, message = self.command_parser.parse_and_execute("rozejrzyj")
        print(f"\n{message}\n")

        # Główna pętla
        last_update = time.time()

        while self.game_state.game_mode == GameMode.PLAYING:
            try:
                # Wyświetl główny ekran (pełny lub kompaktowy)
                self.prologue_interface.display_game_screen()

                # Pokaż postęp tutoriali (opcjonalnie)
                # TODO: Tylko jeśli tutorial nie ukończony
                if self.game_state.tutorial_manager and len(self.game_state.first_time_commands) < 7:
                    self.prologue_interface.display_tutorial_progress()

                # Pobierz komendę z obsługą quick keys
                command, show_menu = self.prologue_interface.get_input_with_quickkeys()

                # Jeśli gracz chce zobaczyć menu akcji
                if show_menu:
                    print()  # Odstęp
                    self.prologue_interface.show_contextual_menu()
                    # Menu pokazane, nie resetuj needs_full_refresh (już zrobione w show_contextual_menu)
                    continue

                if not command:
                    continue

                # Specjalne komendy prologue interface
                if command.lower() in ['hints', 'podpowiedzi']:
                    self.prologue_interface.toggle_hints()
                    continue
                elif command.lower() in ['compact', 'kompakt']:
                    self.prologue_interface.toggle_compact_mode()
                    continue

                # Obsługa dialogów
                if hasattr(self.game_state, 'current_dialogue') and self.game_state.current_dialogue:
                    # Wyświetl kontekst dialogu (mini-status + rozmówca)
                    dialogue = self.game_state.current_dialogue
                    npc_name = dialogue.get('npc_name', 'Nieznany')
                    self.prologue_interface.display_dialogue_context(npc_name)

                    # W dialogu
                    if command.lower() in ['anuluj', 'wyjdź', 'exit']:
                        self.game_state.current_dialogue = None
                        self.prologue_interface.display_command_result(True, "Zakończyłeś rozmowę.")
                    elif command.isdigit():
                        choice = int(command) - 1
                        dialogue = self.game_state.current_dialogue

                        if 0 <= choice < len(dialogue['options']):
                            # Przetwórz wybór dialogowy
                            response, next_text, result, next_options, next_node_id = self.dialogue_system.process_choice(
                                dialogue['npc_id'],
                                dialogue['node_id'],
                                choice,
                                self.game_state.player
                            )

                            # Wyświetl odpowiedź
                            message = f"\nTy: {dialogue['options'][choice].text}\n"
                            message += f"\n{response}\n"

                            if next_text:
                                message += f"\n{next_text}\n"

                            from npcs.dialogue_system import DialogueResult
                            if result == DialogueResult.END or not next_options:
                                self.game_state.current_dialogue = None
                                message += "\n[Koniec rozmowy]"
                                # Po zakończeniu dialogu - full refresh przy następnej iteracji
                                self.prologue_interface.request_full_refresh()
                            else:
                                dialogue['options'] = next_options
                                dialogue['node_id'] = next_node_id if next_node_id else 'greeting'

                                message += "\n═══ OPCJE DIALOGOWE ═══\n"
                                for i, opt in enumerate(next_options, 1):
                                    message += f"{i}. {opt.text}\n"
                                message += f"\nWybierz opcję (1-{len(next_options)}) lub 'anuluj'."

                            print(message)
                        else:
                            self.prologue_interface.display_command_result(False, "Nieprawidłowy numer opcji.")
                    else:
                        self.prologue_interface.display_command_result(
                            False,
                            "W trakcie rozmowy możesz tylko wybrać numer opcji lub 'anuluj'."
                        )
                else:
                    # Normalna komenda
                    success, message = self.command_parser.parse_and_execute(command)

                    # Sprawdź czy to QUIT
                    if message == "QUIT":
                        if self.confirm_quit():
                            break
                        else:
                            continue

                    # Sprawdź czy to komenda "rozejrzyj" - wymaga full refresh przy następnej iteracji
                    if command.lower() in ['rozejrzyj', 'rozejrzyj się', 'look', 'l']:
                        self.prologue_interface.request_full_refresh()

                    # Wyświetl rezultat
                    self.prologue_interface.display_command_result(success, message)

                    # Aktualizuj stan gry
                    if success:
                        self.game_state.update(1)  # Minuta czasu gry

                # Auto-save
                current_time = time.time()
                if current_time - self.last_save_time > self.auto_save_interval:
                    self.auto_save()
                    self.last_save_time = current_time

                # Sprawdź śmierć gracza
                if self.game_state.game_mode == GameMode.DEAD:
                    self.handle_death()
                    break

                # Sprawdź emergentne wydarzenia
                self.check_emergent_events()

            except KeyboardInterrupt:
                if self.confirm_quit():
                    break
            except EOFError:
                self.interface.print("\n[Koniec danych wejściowych - wychodzę z gry]")
                break
            except Exception as e:
                self.interface.print(f"\n❌ Błąd: {e}")
                traceback.print_exc()
                if hasattr(self, '_consecutive_errors'):
                    self._consecutive_errors += 1
                    if self._consecutive_errors > 3:
                        self.interface.print("\nZbyt wiele błędów. Wychodzę z gry.")
                        break
                else:
                    self._consecutive_errors = 1

        print("\n👋 Dziękujemy za grę!")

    def confirm_quit(self) -> bool:
        """Potwierdź wyjście z gry.
        
        Returns:
            True jeśli gracz potwierdza wyjście
        """
        try:
            self.interface.print("\nCzy na pewno chcesz wyjść?")
            self.interface.print("Niezapisany postęp zostanie utracony!")
            choice = self.interface.get_input("(T)ak / (N)ie: ").lower()
            
            if choice in ['t', 'tak', 'yes', 'y']:
                # Zapytaj o zapis
                save_choice = self.interface.get_input("Zapisać grę przed wyjściem? (T/N): ").lower()
                if save_choice in ['t', 'tak', 'yes', 'y']:
                    self.game_state.save_game(1)
                return True
            return False
        except (EOFError, KeyboardInterrupt):
            # If we can't get input, just quit
            return True
    
    def auto_save(self):
        """Automatyczny zapis gry."""
        self.game_state.save_game(5)  # Slot 5 dla auto-save
        self.interface.print("\n[Gra zapisana automatycznie]")
    
    def check_emergent_events(self):
        """Sprawdź czy pojawiły się nowe emergentne wydarzenia."""
        if not self.game_state.quest_engine:
            return
        
        # Sprawdź czy są nowe odkrywalne questy
        discoverable = self.game_state.quest_engine.get_discoverable_quests()
        
        for quest in discoverable:
            # Quest ma seed z opisem, nie discovery_method/hint
            if hasattr(quest, 'seed') and quest.seed:
                hint = quest.seed.description if hasattr(quest.seed, 'description') else "Odkryłeś nowe zadanie"
                self.interface.print(f"\n[Odkrycie: {hint}]")
                # Zmień stan questa na aktywny po odkryciu
                quest.state = QuestState.ACTIVE
    
    def handle_death(self):
        """Obsłuż śmierć gracza."""
        death_message = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                           KONIEC GRY                                 ║
║                                                                       ║
║                     Twoja podróż dobiegła końca...                   ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

"""
        self.interface.print(death_message)
        
        # Pokaż statystyki
        stats = self.game_state.statistics
        self.interface.print(f"Przeżyłeś: Dzień {self.game_state.day}")
        self.interface.print(f"Zabici wrogowie: {stats['enemies_killed']}")
        self.interface.print(f"Ukończone questy: {stats['quests_completed']}")
        self.interface.print(f"Odkryte sekrety: {stats['secrets_found']}")
        self.interface.print(f"Razy umarłeś: {stats['times_died']}")
        
        self.interface.get_input("\n[Naciśnij Enter aby wrócić do menu]")
    
    def load_game_menu(self):
        """Menu wczytywania gry."""
        self.interface.clear()
        self.interface.print("=== WCZYTAJ GRĘ ===\n")
        
        # Pokaż dostępne zapisy
        import os
        import json
        from datetime import datetime
        
        saves_found = False
        for slot in range(1, 6):
            filepath = f"saves/save_{slot}.json"
            if os.path.exists(filepath):
                saves_found = True
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        save_data = json.load(f)
                    
                    timestamp = save_data.get('timestamp', 'Nieznany')
                    day = save_data.get('day', 1)
                    player_data = save_data.get('player', {})
                    player_name = player_data.get('name', 'Nieznany')
                    
                    if slot == 5:
                        self.interface.print(f"[AUTO] ", end="")
                    else:
                        self.interface.print(f"Slot {slot}: ", end="")
                    
                    self.interface.print(f"{player_name}, Dzień {day} ({timestamp[:19]})")
                except:
                    pass
        
        if not saves_found:
            self.interface.print("Brak zapisanych gier.")
            self.interface.get_input("\n[Naciśnij Enter aby wrócić]")
            return
        
        # Wybór slotu
        slot_str = self.interface.get_input("\nWybierz slot (1-5) lub 0 aby wrócić: ")
        
        try:
            slot = int(slot_str)
            if slot == 0:
                return
            if 1 <= slot <= 5:
                if self.game_state.load_game(slot):
                    self.interface.print("Gra wczytana pomyślnie!")
                    time.sleep(1)
                    self.game_loop()
                else:
                    self.interface.print("Nie udało się wczytać gry.")
                    self.interface.get_input("[Naciśnij Enter]")
        except:
            pass
    
    def show_credits(self):
        """Pokaż informacje o grze."""
        credits = """
╔═══════════════════════════════════════════════════════════════════════╗
║                              O GRZE                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  DROGA SZAMANA - Text RPG                                           ║
║                                                                       ║
║  Inspirowane serią książek "Droga Szamana" Vasily'ego Mahanenko     ║
║                                                                       ║
║  Cechy gry:                                                         ║
║  • System umiejętności oparty na użyciu, nie XP                    ║
║  • Realistyczny system bólu i kontuzji                              ║
║  • Żyjący świat z autonomicznymi NPCami                            ║
║  • Emergentne questy powstające z sytuacji                         ║
║  • Dynamiczna ekonomia z podażą i popytem                          ║
║  • Każda decyzja ma długoterminowe konsekwencje                    ║
║                                                                       ║
║  Wersja: 1.0.0                                                      ║
║  Stworzone z pomocą Claude AI                                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
        self.interface.print(credits)
        self.interface.get_input("\n[Naciśnij Enter aby wrócić]")
    
    def _load_plugins(self):
        """Ładuje wszystkie pluginy do smart interface."""
        self.available_plugins = []
        
        try:
            # Importuj wszystkie pluginy
            from ui.plugins.combat_plugin import CombatPlugin
            from ui.plugins.trade_plugin import TradePlugin
            from ui.plugins.abilities_plugin import AbilitiesPlugin
            from ui.plugins.quest_plugin import QuestPlugin
            from ui.plugins.crafting_plugin import CraftingPlugin
            from ui.plugins.gathering_plugin import GatheringPlugin
            from ui.plugins.exploration_plugin import ExplorationPlugin
            
            # Dodaj do listy dostępnych pluginów
            self.available_plugins = [
                CombatPlugin,
                TradePlugin,
                AbilitiesPlugin,
                QuestPlugin,
                CraftingPlugin,
                GatheringPlugin,
                ExplorationPlugin
            ]
        except ImportError as e:
            print(f"Ostrzeżenie: Nie można załadować niektórych pluginów: {e}")
            # Gra może działać bez wszystkich pluginów
    
    def update_interface_display(self, message: str):
        """Aktualizuj wyświetlacz gry z panelami."""
        if self.game_state.player:
            # Pobierz prawdziwe dane lokacji
            current_loc = None
            exits = []
            npcs = []
            items = []
            description = "Tutaj jesteś"
            
            if self.game_state.prison:
                current_loc = self.game_state.prison.get_current_location()
                if current_loc:
                    exits = list(current_loc.connections.keys())
                    npcs = [p.name for p in current_loc.prisoners] + [g.name for g in current_loc.guards]
                    items = [item.name for item in current_loc.items]
                    description = current_loc.description_day or "Tutaj jesteś"
            
            location_info = {
                'name': self.game_state.player.location or "Nieznane",
                'description': description,
                'exits': exits,
                'npcs': npcs,
                'items': items
            }
            
            # Wyświetl panele używając prawdziwego game_state
            self.interface.display_game_panels(message, self.game_state, location_info)
        else:
            # Fallback dla przypadków bez gracza
            self.interface.print(message)


def main():
    """Punkt wejścia programu."""
    try:
        game = DrogaSzamanaRPG()
        game.start()
        print("\nDziękujemy za grę!")
    except Exception as e:
        print(f"\nBłąd krytyczny: {e}")
        traceback.print_exc()
        input("\n[Naciśnij Enter aby zakończyć]")
        sys.exit(1)


if __name__ == "__main__":
    main()