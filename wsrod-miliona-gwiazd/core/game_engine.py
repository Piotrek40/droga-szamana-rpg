"""
Główny silnik gry Wśród Miliona Gwiazd
Zarządza pętlą gry, turami i stanem globalnym
"""

from typing import Optional
import json
import os


class GameEngine:
    """Główny silnik gry strategicznej"""

    def __init__(self):
        self.current_turn = 1
        self.game_running = False
        self.player = None
        self.galaxy = None
        self.game_over = False
        self.victory = False

    def initialize_new_game(self, player_name: str, faction: str):
        """Inicjalizuje nową grę"""
        from game.player import Player
        from game.galaxy import Galaxy

        self.player = Player(player_name, faction)
        self.galaxy = Galaxy()
        self.galaxy.generate()

        # Przydziel planetę startową graczowi
        starting_planet = self.galaxy.get_starting_planet()
        self.player.add_planet(starting_planet)
        starting_planet.owner = self.player

        self.current_turn = 1
        self.game_running = True
        self.game_over = False

        return True

    def next_turn(self):
        """Przechodzi do następnej tury"""
        if not self.game_running or self.game_over:
            return False

        self.current_turn += 1

        # Aktualizuj wszystkie systemy
        self._update_planets()
        self._update_fleets()
        self._update_research()
        self._check_victory_conditions()

        return True

    def _update_planets(self):
        """Aktualizuje wszystkie planety"""
        for planet in self.player.planets:
            planet.produce_resources(self.player)
            planet.update_construction()

    def _update_fleets(self):
        """Aktualizuje wszystkie floty"""
        for fleet in self.player.fleets:
            fleet.move()
            fleet.update_status()

    def _update_research(self):
        """Aktualizuje postęp badań"""
        if self.player.current_research:
            self.player.advance_research()

    def _check_victory_conditions(self):
        """Sprawdza warunki zwycięstwa/porażki"""
        # Porażka - brak planet
        if len(self.player.planets) == 0:
            self.game_over = True
            self.victory = False
            return

        # Zwycięstwo - kontrola 75% galaktyki
        total_planets = len(self.galaxy.planets)
        player_planets = len(self.player.planets)

        if player_planets / total_planets >= 0.75:
            self.game_over = True
            self.victory = True

    def save_game(self, slot_name: str) -> bool:
        """Zapisuje stan gry"""
        save_dir = "saves"
        os.makedirs(save_dir, exist_ok=True)

        save_data = {
            "version": "0.1.0",
            "turn": self.current_turn,
            "player": self.player.to_dict(),
            "galaxy": self.galaxy.to_dict(),
            "game_over": self.game_over,
            "victory": self.victory
        }

        save_path = os.path.join(save_dir, f"{slot_name}.json")

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Błąd zapisu: {e}")
            return False

    def load_game(self, slot_name: str) -> bool:
        """Wczytuje zapisaną grę"""
        save_path = os.path.join("saves", f"{slot_name}.json")

        if not os.path.exists(save_path):
            return False

        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            from game.player import Player
            from game.galaxy import Galaxy

            self.current_turn = save_data["turn"]
            self.player = Player.from_dict(save_data["player"])
            self.galaxy = Galaxy.from_dict(save_data["galaxy"])
            self.game_over = save_data.get("game_over", False)
            self.victory = save_data.get("victory", False)
            self.game_running = True

            return True
        except Exception as e:
            print(f"Błąd wczytywania: {e}")
            return False

    def get_game_status(self) -> dict:
        """Zwraca aktualny status gry"""
        return {
            "turn": self.current_turn,
            "planets": len(self.player.planets) if self.player else 0,
            "fleets": len(self.player.fleets) if self.player else 0,
            "resources": self.player.resources if self.player else {},
            "game_over": self.game_over,
            "victory": self.victory
        }
