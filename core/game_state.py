"""Globalny stan gry - zarządzanie wszystkimi systemami."""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from enum import Enum

from core.event_bus import event_bus, EventCategory, GameEvent, EventPriority
from world.locations.prison import Prison
from world.time_system import TimeSystem
from world.weather import WeatherSystem
from player.character import Player, CharacterState
from npcs.npc_manager import NPCManager
from mechanics.economy import Economy
from mechanics.crafting import CraftingSystem
from quests.quest_engine import QuestEngine, QuestState
from quests.consequences import ConsequenceManager


class GameMode(Enum):
    """Tryby gry."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    DIALOGUE = "dialogue"
    COMBAT = "combat"
    TRADING = "trading"
    CRAFTING = "crafting"
    INVENTORY = "inventory"
    DEAD = "dead"


@dataclass
class GameSettings:
    """Ustawienia gry."""
    difficulty: str = "normal"  # easy, normal, hard, hardcore
    autosave_interval: int = 300  # sekundy
    language: str = "pl"
    show_hints: bool = True
    debug_mode: bool = False
    permadeath: bool = False


class GameState:
    """Główny stan gry - singleton zarządzający wszystkimi systemami."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(GameState, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicjalizacja stanu gry."""
        if self._initialized:
            return
            
        self._initialized = True
        
        # Podstawowe informacje
        self.version = "1.0.0"
        self.save_version = 1
        self.game_mode = GameMode.MENU
        self.settings = GameSettings()
        
        # Czas gry
        self.game_time = 420  # 7:00 rano start
        self.day = 1
        self.total_playtime = 0
        self.session_start = datetime.now()
        
        # Systemy gry - będą inicjalizowane w init_game()
        self.player: Optional[Player] = None
        self.prison: Optional[Prison] = None
        self.time_system: Optional[TimeSystem] = None
        self.weather_system: Optional[WeatherSystem] = None
        self.npc_manager: Optional[NPCManager] = None
        self.economy: Optional[Economy] = None
        self.crafting_system: Optional[CraftingSystem] = None
        self.quest_engine: Optional[QuestEngine] = None
        self.consequence_manager: Optional[ConsequenceManager] = None
        
        # Stan gry
        self.is_running = False  # Czy gra jest aktywna
        self.current_location = "cela_1"
        self.game_flags = {}  # Flagi do śledzenia postępu
        self.global_variables = {}  # Zmienne globalne
        self.discovered_locations = set()
        self.discovered_secrets = set()
        
        # Auto-save system
        self.auto_save_enabled = True
        self.last_auto_save = 0
        
        # Statystyki
        self.statistics = {
            'enemies_killed': 0,
            'items_crafted': 0,
            'quests_completed': 0,
            'secrets_found': 0,
            'total_damage_dealt': 0,
            'total_damage_taken': 0,
            'money_earned': 0,
            'money_spent': 0,
            'times_died': 0,
            'npcs_befriended': 0,
            'npcs_made_enemies': 0
        }
        
        # Rejestracja na wydarzenia
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Rejestracja handlerów wydarzeń."""
        # Śmierć gracza
        event_bus.subscribe("player_death", self._handle_player_death)
        
        # Odkrycia
        event_bus.subscribe("secret_discovered", self._handle_secret_discovered)
        event_bus.subscribe("location_discovered", self._handle_location_discovered)
        
        # Questy
        event_bus.subscribe("quest_completed", self._handle_quest_completed)
        
        # Statystyki
        event_bus.subscribe_category(EventCategory.COMBAT, self._update_combat_stats)
        event_bus.subscribe_category(EventCategory.TRADE, self._update_trade_stats)
        event_bus.subscribe_category(EventCategory.CRAFT, self._update_craft_stats)
    
    def init_game(self, player_name: str = "Mahan", difficulty: str = "normal", 
                   player_class: Optional[str] = None):
        """Inicjalizacja nowej gry.
        
        Args:
            player_name: Imię gracza
            difficulty: Poziom trudności
            player_class: Klasa postaci
        """
        print(f"\n=== Inicjalizacja gry: Droga Szamana ===")
        print(f"Gracz: {player_name}, Trudność: {difficulty}\n")
        
        # Ustawienia
        self.settings.difficulty = difficulty
        self.settings.permadeath = (difficulty == "hardcore")
        
        # Inicjalizacja gracza
        print("Tworzenie postaci gracza...")
        from player.classes import ClassName
        
        # Konwertuj string na enum klasy
        character_class = None
        if player_class:
            try:
                character_class = ClassName(player_class.lower())
                print(f"Wybrana klasa: {player_class.capitalize()}")
            except ValueError:
                print(f"Nieznana klasa: {player_class}. Tworzenie postaci bez klasy.")
        
        self.player = Player(player_name, character_class)
        self.player.current_location = "cela_1"
        
        # Inicjalizacja świata
        print("Generowanie więzienia...")
        self.prison = Prison()
        self.time_system = TimeSystem()
        self.weather_system = WeatherSystem()
        
        # Inicjalizacja NPCów
        print("Ożywianie NPCów...")
        self.npc_manager = NPCManager("data/npc_complete.json")
        
        # Umieść NPCów w lokacjach - bezpiecznie
        npc_locations = {
            "brutus": "biuro_naczelnika",
            "marek": "korytarz_centralny",  # poprawiona nazwa
            "jozek": "cela_2",
            "anna": "cela_4",
            "piotr": "cela_1"
        }
        
        for npc_id, location in npc_locations.items():
            if npc_id in self.npc_manager.npcs:
                self.npc_manager.npcs[npc_id].current_location = location
            else:
                print(f"Ostrzeżenie: NPC {npc_id} nie istnieje")
        
        # Inicjalizacja ekonomii
        print("Uruchamianie ekonomii...")
        self.economy = Economy()
        
        # Inicjalizacja craftingu
        print("Przygotowywanie warsztatu...")
        from mechanics.crafting import CraftingSystem
        self.crafting = CraftingSystem()
        
        # Dodaj NPCów do ekonomii
        for npc_id, npc in self.npc_manager.npcs.items():
            self.economy.add_npc(
                npc_id=npc_id,
                profession=npc.role if hasattr(npc, 'role') else 'prisoner',
                personality='normal',
                starting_gold=npc.gold if hasattr(npc, 'gold') else 10
            )
        
        # crafting_system jest aliasem dla crafting
        self.crafting_system = self.crafting
        
        # Inicjalizacja questów
        print("Aktywacja questów emergentnych...")
        self.quest_engine = QuestEngine()
        self.consequence_manager = ConsequenceManager()
        
        # Inicjalizuj questy więzienne
        self._initialize_prison_quests()
        
        # Ustaw tryb gry
        self.game_mode = GameMode.PLAYING
        self.current_location = "cela_1"
        self.discovered_locations.add("cela_1")
        
        # Dodaj szczura do celi startowej (do testowania walki)
        self._spawn_test_rat()
        
        # Wydarzenie rozpoczęcia gry
        event_bus.emit(GameEvent(
            event_type="game_started",
            category=EventCategory.SYSTEM,
            data={'player_name': player_name, 'difficulty': difficulty},
            priority=EventPriority.HIGH
        ))
        
        print("\n=== Gra zainicjalizowana pomyślnie! ===\n")
    
    def _spawn_test_rat(self):
        """Dodaje szczura testowego do celi startowej."""
        if not self.npc_manager:
            return
        
        # Dane szczura
        rat_data = {
            "id": "rat_1",
            "name": "Szczur",
            "role": "creature",  # Nowa rola dla stworzeń
            "location": "cela_1",
            "personality": ["aggressive", "cowardly"],  # Agresywny ale tchórzliwy
            "quirks": ["gryzie", "piszczy"],
            "inventory": {},
            "gold": 0,
            "health": 20,  # Słaby przeciwnik
            "max_health": 20,
            "strength": 3,  # Bardzo słaby
            "endurance": 5,
            "agility": 12,  # Szybki
            "dialogues": {
                "greeting": ["*Szczur piszczy groźnie*", "*Syk syk!*"],
                "hostile": ["*Szczur pokazuje zęby*", "*Piszczenie bojowe*"],
                "injured": ["*Bolesne piski*", "*Szczur próbuje uciec*"]
            },
            "goals": [
                {"name": "przetrwać", "priority": 10},
                {"name": "znaleźć jedzenie", "priority": 5}
            ],
            "initial_relationships": [
                {"target": "player", "trust": -20, "fear": 30, "affection": -50}
            ],
            "schedule": {
                "00:00-06:00": "sleeping",
                "06:00-12:00": "patrolling",
                "12:00-18:00": "resting",
                "18:00-24:00": "patrolling"
            }
        }
        
        # Stwórz NPCa szczura
        from npcs.npc_manager import NPC
        rat = NPC(rat_data)
        
        # Ustaw lokację
        rat.current_location = "cela_1"
        
        # Dodaj do managera NPCów
        self.npc_manager.npcs["rat_1"] = rat
        
        # Dodaj do lokacji w więzieniu
        if self.prison:
            location = self.prison.get_current_location()
            if location and not hasattr(location, 'npcs'):
                location.npcs = []
            if location:
                location.npcs.append(rat)
        
        print("W celi zauważasz małego, agresywnego szczura!")
        
        # Ustaw grę jako aktywną
        self.is_running = True
        self.game_mode = GameMode.PLAYING
        
        print("\n=== Gra zainicjalizowana pomyślnie! ===")
    
    def update(self, delta_time: float = 1.0):
        """Aktualizacja stanu gry.
        
        Args:
            delta_time: Czas od ostatniej aktualizacji (minuty w grze)
        """
        if self.game_mode != GameMode.PLAYING:
            return
        
        # Aktualizuj czas
        old_time = self.game_time
        self.game_time += delta_time
        
        # Nowy dzień?
        if self.game_time >= 1440:  # 24 * 60
            self.game_time -= 1440
            self.day += 1
            event_bus.emit(GameEvent(
                event_type="new_day",
                category=EventCategory.TIME,
                data={'day': self.day}
            ))
        
        # Aktualizuj systemy
        if self.time_system:
            self.time_system.update(self.game_time)
        
        if self.weather_system:
            self.weather_system.update(delta_time)  # Przekazuj minuty które minęły
        
        if self.npc_manager:
            self.npc_manager.update()
        
        if self.quest_engine:
            # Przekaż aktualny stan świata do silnika questów
            from datetime import datetime
            self.quest_engine.world_state = self.get_world_state()
            self.quest_engine.player_state = {
                'skills': self.player.skills if self.player else {},
                'inventory': self.player.inventory if self.player else [],
                'reputation': self.get_world_state().get('player_reputation', {}),
                'completed_quests': self.quest_engine.completed_quests
            }
            self.quest_engine.update(datetime.now())
        
        if self.consequence_manager:
            self.consequence_manager.update(self.game_time)
        
        # Regeneracja gracza i sprawdzenie stanu
        if self.player:
            self.player.regenerate(delta_time)
            self.player.update_state()
            
            # Sprawdź czy gracz nie umarł
            if self.player.state == CharacterState.MARTWY:
                self.game_mode = GameMode.DEAD
                event_bus.emit(GameEvent(
                    event_type="player_death",
                    category=EventCategory.COMBAT,
                    source="player",
                    data={'death_count': self.player.death_count}
                ))
        
        # Sprawdź wydarzenia czasowe
        self._check_time_events(old_time, self.game_time)
    
    def _check_time_events(self, old_time: int, new_time: int):
        """Sprawdź wydarzenia zależne od czasu.
        
        Args:
            old_time: Poprzedni czas
            new_time: Nowy czas
        """
        # Posiłki
        meal_times = [420, 720, 1080]  # 7:00, 12:00, 18:00
        for meal_time in meal_times:
            if old_time < meal_time <= new_time or (new_time < old_time and new_time >= meal_time):
                event_bus.emit(GameEvent(
                    event_type="meal_time",
                    category=EventCategory.TIME,
                    data={'time': meal_time}
                ))
        
        # Zmiana warty
        guard_changes = [360, 840, 1320]  # 6:00, 14:00, 22:00
        for change_time in guard_changes:
            if old_time < change_time <= new_time or (new_time < old_time and new_time >= change_time):
                event_bus.emit(GameEvent(
                    event_type="guard_change",
                    category=EventCategory.TIME,
                    data={'time': change_time}
                ))
    
    def get_world_state(self) -> Dict[str, Any]:
        """Pobierz aktualny stan świata dla innych systemów.
        
        Returns:
            Słownik ze stanem świata
        """
        state = {
            'game_time': self.game_time,
            'day': self.day,
            'player_location': self.current_location,
            'player_health': self.player.health if self.player else 100,
            'player_reputation': {},
            'discovered_secrets': list(self.discovered_secrets),
            'game_flags': self.game_flags.copy(),
            'global_variables': self.global_variables.copy()
        }
        
        # Dodaj reputację gracza
        if self.npc_manager:
            for npc_id, npc in self.npc_manager.npcs.items():
                if hasattr(npc, 'relationships') and 'player' in npc.relationships:
                    state['player_reputation'][npc_id] = npc.relationships['player'].get_overall_disposition()
        
        # Dodaj stan ekonomii
        if self.economy:
            prison_market = self.economy.markets.get('prison')
            food_supply = 0
            if prison_market and hasattr(prison_market, 'dane_rynkowe'):
                food_data = prison_market.dane_rynkowe.get('chleb')
                if food_data:
                    food_supply = food_data.podaz
            
            state['economy'] = {
                'food_supply': food_supply,
                'average_prices': self.economy.get_average_prices()
            }
        
        return state
    
    def move_player(self, direction: str) -> Tuple[bool, str]:
        """Przesuń gracza w danym kierunku.
        
        Args:
            direction: Kierunek ruchu
            
        Returns:
            (sukces, wiadomość)
        """
        if not self.prison or not self.player:
            return False, "Gra nie jest zainicjalizowana!"
        
        # Sprawdź czy gracz może się ruszyć (kontuzje, wyczerpanie)
        if self.player.is_incapacitated():
            return False, "Jesteś zbyt ranny aby się poruszać!"
        
        if self.player.stamina < 5:
            return False, "Jesteś zbyt wyczerpany aby się poruszać!"
        
        # Spróbuj się ruszyć
        old_location = self.current_location
        success, message = self.prison.move(direction)
        
        if success:
            self.current_location = self.prison.current_location  # To już jest string
            self.discovered_locations.add(self.current_location)
            self.player.current_location = self.current_location
            self.player.spend_stamina(2)
            
            # Emituj wydarzenie
            event_bus.emit(GameEvent(
                event_type="player_moved",
                category=EventCategory.MOVEMENT,
                data={
                    'from': old_location,
                    'to': self.current_location,
                    'direction': direction
                },
                source="player"
            ))
        
        return success, message
    
    def _handle_player_death(self, event: GameEvent):
        """Obsługa śmierci gracza."""
        self.statistics['times_died'] += 1
        
        if self.settings.permadeath:
            self.game_mode = GameMode.DEAD
            print("\n=== KONIEC GRY - PERMADEATH ===")
            print("Twoja podróż dobiegła końca...")
        else:
            # Respawn w celi
            self.current_location = "cela_1"
            self.player.respawn()
            print("\n=== Obudziłeś się w swojej celi... ===")
    
    def _handle_secret_discovered(self, event: GameEvent):
        """Obsługa odkrycia sekretu."""
        secret_id = event.data.get('secret_id')
        if secret_id:
            self.discovered_secrets.add(secret_id)
            self.statistics['secrets_found'] += 1
    
    def _handle_location_discovered(self, event: GameEvent):
        """Obsługa odkrycia lokacji."""
        location_id = event.data.get('location_id')
        if location_id:
            self.discovered_locations.add(location_id)
    
    def _handle_quest_completed(self, event: GameEvent):
        """Obsługa ukończenia questa."""
        self.statistics['quests_completed'] += 1
    
    def _update_combat_stats(self, event: GameEvent):
        """Aktualizacja statystyk bojowych."""
        if event.event_type == "combat_attack" and event.source == "player":
            self.statistics['total_damage_dealt'] += event.data.get('damage', 0)
        elif event.event_type == "combat_defend" and event.target == "player":
            self.statistics['total_damage_taken'] += event.data.get('damage', 0)
        elif event.event_type == "combat_kill" and event.source == "player":
            self.statistics['enemies_killed'] += 1
    
    def _update_trade_stats(self, event: GameEvent):
        """Aktualizacja statystyk handlowych."""
        if event.source == "player":
            self.statistics['money_spent'] += event.data.get('price', 0)
        elif event.target == "player":
            self.statistics['money_earned'] += event.data.get('price', 0)
    
    def _update_craft_stats(self, event: GameEvent):
        """Aktualizacja statystyk craftingu."""
        if event.source == "player":
            self.statistics['items_crafted'] += 1
    
    def save_game(self, slot: int = 1) -> bool:
        """Zapisz stan gry.
        
        Args:
            slot: Numer slotu zapisu (1-5)
            
        Returns:
            Czy zapis się powiódł
        """
        if not self.player:
            return False
        
        save_data = {
            'version': self.save_version,
            'timestamp': datetime.now().isoformat(),
            'game_time': self.game_time,
            'day': self.day,
            'total_playtime': self.total_playtime,
            'current_location': self.current_location,
            'discovered_locations': list(self.discovered_locations),
            'discovered_secrets': list(self.discovered_secrets),
            'game_flags': self.game_flags,
            'global_variables': self.global_variables,
            'statistics': self.statistics,
            'settings': {
                'difficulty': self.settings.difficulty,
                'language': self.settings.language,
                'show_hints': self.settings.show_hints
            },
            'player': self.player.to_dict() if self.player else None,
            'npcs': self.npc_manager.get_save_state() if self.npc_manager else None,
            'economy': self.economy.save_state() if self.economy else None,
            'quests': self.quest_engine.save_state() if self.quest_engine else None,
            'consequences': self.consequence_manager.save_state() if self.consequence_manager else None
        }
        
        # Utwórz folder saves jeśli nie istnieje
        os.makedirs('saves', exist_ok=True)
        
        # Zapisz do pliku
        filepath = f"saves/save_{slot}.json"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"Gra zapisana w slocie {slot}")
            return True
        except Exception as e:
            print(f"Błąd zapisu: {e}")
            return False
    
    def load_game(self, slot: int = 1) -> bool:
        """Wczytaj stan gry.
        
        Args:
            slot: Numer slotu zapisu (1-5)
            
        Returns:
            Czy wczytywanie się powiodło
        """
        filepath = f"saves/save_{slot}.json"
        
        if not os.path.exists(filepath):
            print(f"Brak zapisu w slocie {slot}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Sprawdź wersję
            if save_data['version'] != self.save_version:
                print(f"Niezgodna wersja zapisu!")
                return False
            
            # Wczytaj podstawowe dane
            self.game_time = save_data['game_time']
            self.day = save_data['day']
            self.total_playtime = save_data['total_playtime']
            self.current_location = save_data['current_location']
            self.discovered_locations = set(save_data['discovered_locations'])
            self.discovered_secrets = set(save_data['discovered_secrets'])
            self.game_flags = save_data['game_flags']
            self.global_variables = save_data['global_variables']
            self.statistics = save_data['statistics']
            
            # Wczytaj ustawienia
            settings = save_data['settings']
            self.settings.difficulty = settings['difficulty']
            self.settings.language = settings['language']
            self.settings.show_hints = settings['show_hints']
            
            # Inicjalizuj systemy jeśli nie istnieją
            if not self.prison:
                self.prison = Prison()
                self.time_system = TimeSystem()
                self.weather_system = WeatherSystem()
            
            # Wczytaj gracza
            if save_data['player']:
                self.player = Player.from_dict(save_data['player'])
            
            # Wczytaj NPCów
            if save_data['npcs'] and self.npc_manager:
                self.npc_manager.load_state_from_dict(save_data['npcs'])
            
            # Wczytaj ekonomię
            if save_data['economy'] and self.economy:
                self.economy.load_state(save_data['economy'])
            
            # Wczytaj questy
            if save_data['quests'] and self.quest_engine:
                self.quest_engine.load_state(save_data['quests'])
            
            # Wczytaj konsekwencje
            if save_data['consequences'] and self.consequence_manager:
                self.consequence_manager.load_state(save_data['consequences'])
            
            # Ustaw lokację w więzieniu
            if self.prison:
                self.prison.current_location = self.prison.locations.get(self.current_location)
            
            self.game_mode = GameMode.PLAYING
            print(f"Gra wczytana ze slotu {slot}")
            return True
            
        except Exception as e:
            print(f"Błąd wczytywania: {e}")
            return False
    
    def get_item_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Pobierz dane przedmiotu z bazy.
        
        Args:
            item_name: Nazwa przedmiotu
            
        Returns:
            Dane przedmiotu lub None jeśli nie istnieje
        """
        if not self.crafting_system or not hasattr(self.crafting_system, 'items_db'):
            return None
        
        item_data = self.crafting_system.items_db.get(item_name)
        if item_data:
            # Stwórz kompletny słownik przedmiotu z nazwą
            result = item_data.copy()
            result['name'] = item_name
            return result
        return None
    
    def get_status(self) -> str:
        """Pobierz aktualny status gry.
        
        Returns:
            Tekstowy opis statusu
        """
        if not self.player:
            return "Gra nie rozpoczęta"
        
        time_str = f"{self.game_time // 60:02d}:{self.game_time % 60:02d}"
        
        # Przygotuj informacje o klasie i manie
        class_info = ""
        mana_info = ""
        if self.player.character_class:
            class_info = f"║ Klasa: {self.player.character_class.name:32s} ║\n"
        if hasattr(self.player, 'mana') and hasattr(self.player, 'max_mana'):
            mana_info = f"║ Mana: {self.player.mana:3.0f}/{self.player.max_mana:3.0f}                            ║\n"
        
        status = f"""
╔════════════════════════════════════════╗
║         DROGA SZAMANA - STATUS         ║
╠════════════════════════════════════════╣
║ Dzień: {self.day:3d}  Czas: {time_str}            ║
║ Lokacja: {self.current_location:30s} ║
╠════════════════════════════════════════╣
║ Gracz: {self.player.name:32s} ║
{class_info}║ Zdrowie: {self.player.health:3.0f}/100  Stamina: {self.player.stamina:3.0f}/100   ║
{mana_info}║ Ból: {self.player.pain:3.0f}/100     Głód: {self.player.hunger:3.0f}/100      ║
╠════════════════════════════════════════╣
║ Złoto: {self.player.gold:5d}                      ║
║ Odkryte lokacje: {len(self.discovered_locations):2d}/20             ║
║ Odkryte sekrety: {len(self.discovered_secrets):2d}/10             ║
║ Ukończone questy: {self.statistics['quests_completed']:2d}               ║
╚════════════════════════════════════════╝
"""
        return status
    
    def _initialize_prison_quests(self):
        """Inicjalizacja questów więziennych."""
        from quests.quest_chains import GuardKeysLostQuest
        from quests.quest_engine import QuestSeed, DiscoveryMethod
        
        # Prosty quest startowy - zgubione klucze
        simple_keys_seed = QuestSeed(
            quest_id="simple_guard_keys",
            name="Zgubione Klucze Strażnika",
            activation_conditions={},  # Zawsze aktywny
            discovery_methods=[DiscoveryMethod.OVERHEARD, DiscoveryMethod.FOUND],
            initial_clues={
                "glowny_korytarz": "Słyszysz rozmowę strażników o zgubionych kluczach",
                "cela_2": "Pod łóżkiem błyszczy metalowy przedmiot", 
                "biuro_naczelnika": "Naczelnik wygląda na zdenerwowanego"
            },
            time_sensitive=False,
            priority=8
        )
        
        # Rejestruj seed i aktywuj
        self.quest_engine.register_seed(simple_keys_seed)
        
        # Stwórz quest z seeda
        keys_quest = GuardKeysLostQuest()
        keys_quest.state = QuestState.DISCOVERABLE
        self.quest_engine.active_quests[keys_quest.quest_id] = keys_quest
        
        # Dodaj wskazówki do świata
        self.quest_engine._spread_initial_clues(keys_quest)
        
        # Ustaw początkowy stan świata wspierający questa
        self.quest_engine.world_state['guard_keys_missing'] = True
        self.quest_engine.world_state['prison.tension'] = 5
        
        print(f"Zainicjalizowano system questów emergentnych")
        print(f"Aktywne questy: {len(self.quest_engine.active_quests)}")
    
    def register_seed(self, quest_seed):
        """Rejestruj seed questa w silniku questów.
        
        Args:
            quest_seed: Obiekt QuestSeed do zarejestrowania
        """
        if self.quest_engine:
            self.quest_engine.register_seed(quest_seed)
    
    def auto_save(self) -> bool:
        """Automatyczny zapis gry.
        
        Returns:
            Czy zapis się powiódł
        """
        if not self.auto_save_enabled:
            return False
            
        # Auto-save co 5 minut gry (300 sekund)
        if self.game_time - self.last_auto_save >= 300:
            self.last_auto_save = self.game_time
            return self.save_game(slot=0)  # Slot 0 dla auto-save
        
        return True
    
    def interact_with_npc(self, npc_id: str, action: str = "talk") -> Dict[str, Any]:
        """Interakcja gracza z NPCem.
        
        Args:
            npc_id: ID NPCa
            action: Typ akcji (talk, trade, etc.)
            
        Returns:
            Słownik z wynikiem interakcji
        """
        if not self.npc_manager:
            return {"success": False, "response": "Brak systemu NPCów"}
        
        return self.npc_manager.player_interact(
            player_id="player",
            npc_id=npc_id,
            action=action
        )


# Singleton
game_state = GameState()