"""
Plugin systemu eksploracji dla Smart Interface.
Integruje ruch, odkrywanie lokacji i nawigację.
"""

from typing import List, Dict, Any, Callable, Optional
from ui.smart_interface import PluginInterface, ContextualAction, ActionType


class ExplorationPlugin(PluginInterface):
    """Plugin rozszerzający interfejs o funkcje eksploracji."""
    
    def __init__(self):
        self.visited_locations = set()  # Odwiedzone lokacje
        self.discovered_secrets = set()  # Odkryte sekrety
        self.known_paths = {}  # Znane ścieżki między lokacjami
        self.current_path = []  # Aktualnie podążana ścieżka
        self.exploration_stats = {
            "locations_discovered": 0,
            "secrets_found": 0,
            "distance_traveled": 0
        }
        
    def register_actions(self) -> List[ContextualAction]:
        """Rejestruje akcje eksploracji."""
        actions = []
        
        # Ruch podstawowy - północ
        actions.append(ContextualAction(
            id="move_north",
            name="Idź na północ",
            description="Porusz się na północ",
            type=ActionType.MOVE,
            command="północ",
            icon="⬆️",
            hotkey="w",
            condition=lambda ctx: self._can_move_north(ctx),
            priority=100,
            category="movement"
        ))
        
        # Ruch podstawowy - południe
        actions.append(ContextualAction(
            id="move_south",
            name="Idź na południe",
            description="Porusz się na południe",
            type=ActionType.MOVE,
            command="południe",
            icon="⬇️",
            hotkey="s",
            condition=lambda ctx: self._can_move_south(ctx),
            priority=99,
            category="movement"
        ))
        
        # Ruch podstawowy - wschód
        actions.append(ContextualAction(
            id="move_east",
            name="Idź na wschód",
            description="Porusz się na wschód",
            type=ActionType.MOVE,
            command="wschód",
            icon="➡️",
            hotkey="d",
            condition=lambda ctx: self._can_move_east(ctx),
            priority=98,
            category="movement"
        ))
        
        # Ruch podstawowy - zachód
        actions.append(ContextualAction(
            id="move_west",
            name="Idź na zachód",
            description="Porusz się na zachód",
            type=ActionType.MOVE,
            command="zachód",
            icon="⬅️",
            hotkey="a",
            condition=lambda ctx: self._can_move_west(ctx),
            priority=97,
            category="movement"
        ))
        
        # Rozejrzyj się
        actions.append(ContextualAction(
            id="look_around",
            name="Rozejrzyj się",
            description="Dokładnie obejrzyj okolicę",
            type=ActionType.EXPLORE,
            command="rozejrzyj",
            icon="👀",
            hotkey="l",
            condition=lambda ctx: True,  # Zawsze dostępne
            priority=95,
            category="exploration"
        ))
        
        # Zbadaj obiekt
        actions.append(ContextualAction(
            id="examine",
            name="Zbadaj",
            description="Dokładnie zbadaj obiekt",
            type=ActionType.EXPLORE,
            command="zbadaj",
            icon="🔍",
            hotkey="e",
            condition=lambda ctx: self._has_examinable_objects(ctx),
            priority=90,
            category="exploration"
        ))
        
        # Mapa
        actions.append(ContextualAction(
            id="show_map",
            name="Pokaż mapę",
            description="Zobacz mapę okolicy",
            type=ActionType.EXPLORE,
            command="mapa",
            icon="🗺️",
            hotkey="m",
            condition=lambda ctx: len(self.visited_locations) > 0,
            priority=85,
            category="exploration"
        ))
        
        # Wejdź do budynku
        actions.append(ContextualAction(
            id="enter",
            name="Wejdź",
            description="Wejdź do budynku lub pomieszczenia",
            type=ActionType.MOVE,
            command="wejdź",
            icon="🚪",
            condition=lambda ctx: self._has_entrance(ctx),
            priority=88,
            category="movement"
        ))
        
        # Wyjdź z budynku
        actions.append(ContextualAction(
            id="exit",
            name="Wyjdź",
            description="Wyjdź z budynku lub pomieszczenia",
            type=ActionType.MOVE,
            command="wyjdź",
            icon="🚶",
            condition=lambda ctx: self._is_inside(ctx),
            priority=87,
            category="movement"
        ))
        
        # Wspinaj się
        actions.append(ContextualAction(
            id="climb",
            name="Wspinaj się",
            description="Wspinaj się w górę lub w dół",
            type=ActionType.MOVE,
            command="wspinaj",
            icon="🧗",
            condition=lambda ctx: self._has_climbable(ctx),
            priority=80,
            category="movement"
        ))
        
        # Przepłyń
        actions.append(ContextualAction(
            id="swim",
            name="Przepłyń",
            description="Przepłyń przez wodę",
            type=ActionType.MOVE,
            command="płyń",
            icon="🏊",
            condition=lambda ctx: self._has_water_crossing(ctx),
            priority=75,
            category="movement"
        ))
        
        # Szukaj przejścia
        actions.append(ContextualAction(
            id="search_passage",
            name="Szukaj przejścia",
            description="Poszukaj ukrytych przejść",
            type=ActionType.EXPLORE,
            command="szukaj_przejścia",
            icon="🔦",
            condition=lambda ctx: not self._all_secrets_found(ctx),
            priority=70,
            category="exploration"
        ))
        
        # Biegnij
        actions.append(ContextualAction(
            id="run",
            name="Biegnij",
            description="Szybko przemieszczaj się",
            type=ActionType.MOVE,
            command="biegnij",
            icon="🏃",
            condition=lambda ctx: self._can_run(ctx),
            priority=65,
            category="movement"
        ))
        
        # Skradaj się
        actions.append(ContextualAction(
            id="sneak",
            name="Skradaj się",
            description="Poruszaj się po cichu",
            type=ActionType.MOVE,
            command="skradaj",
            icon="🤫",
            condition=lambda ctx: self._can_sneak(ctx),
            priority=60,
            category="movement"
        ))
        
        # Ustaw punkt orientacyjny
        actions.append(ContextualAction(
            id="set_waypoint",
            name="Ustaw punkt orientacyjny",
            description="Zaznacz to miejsce na mapie",
            type=ActionType.EXPLORE,
            command="zaznacz_miejsce",
            icon="📍",
            condition=lambda ctx: True,
            priority=55,
            category="exploration"
        ))
        
        # Wróć do punktu
        actions.append(ContextualAction(
            id="return_waypoint",
            name="Wróć do punktu",
            description="Wróć do zaznaczonego miejsca",
            type=ActionType.MOVE,
            command="wróć_do_punktu",
            icon="🧭",
            condition=lambda ctx: self._has_waypoint(ctx),
            priority=58,
            category="movement"
        ))
        
        return actions
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widgety eksploracji do status bara."""
        widgets = []
        
        def location_widget(game_state):
            """Widget pokazujący aktualną lokację."""
            if hasattr(game_state, 'current_location'):
                location = game_state.current_location
                if hasattr(location, 'name'):
                    name = location.name[:20]
                    if location.name in self.visited_locations:
                        return f"📍 {name}"
                    else:
                        return f"📍 {name} (NOWA)"
            return "📍 Nieznana lokacja"
        
        def compass_widget(game_state):
            """Widget kompasu pokazujący dostępne kierunki."""
            if hasattr(game_state, 'current_location'):
                location = game_state.current_location
                if hasattr(location, 'exits'):
                    dirs = []
                    if 'north' in location.exits:
                        dirs.append("N")
                    if 'south' in location.exits:
                        dirs.append("S")
                    if 'east' in location.exits:
                        dirs.append("E")
                    if 'west' in location.exits:
                        dirs.append("W")
                    if dirs:
                        return f"🧭 [{'/'.join(dirs)}]"
            return ""
        
        def exploration_progress_widget(game_state):
            """Widget postępu eksploracji."""
            if self.exploration_stats["locations_discovered"] > 0:
                discovered = self.exploration_stats["locations_discovered"]
                if discovered < 5:
                    return f"🗺️ Odkryto: {discovered}"
                elif discovered < 10:
                    return f"🗺️ Eksplorator ({discovered})"
                else:
                    return f"🗺️ Odkrywca ({discovered})"
            return ""
        
        def movement_mode_widget(game_state):
            """Widget trybu poruszania."""
            if hasattr(game_state, 'movement_mode'):
                mode = game_state.movement_mode
                if mode == "running":
                    return "🏃 Bieg"
                elif mode == "sneaking":
                    return "🤫 Skradanie"
                elif mode == "climbing":
                    return "🧗 Wspinaczka"
            return ""
        
        widgets.append(location_widget)
        widgets.append(compass_widget)
        widgets.append(exploration_progress_widget)
        widgets.append(movement_mode_widget)
        
        return widgets
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Dodaje parsery dla komend eksploracji."""
        parsers = {}
        
        def parse_movement_command(text: str, context: Dict) -> Optional[str]:
            """Parser dla komend ruchu."""
            text = text.lower()
            
            # Kierunki podstawowe
            directions = {
                "północ": "północ", "n": "północ", "góra": "północ",
                "południe": "południe", "s": "południe", "dół": "południe",
                "wschód": "wschód", "e": "wschód", "prawo": "wschód",
                "zachód": "zachód", "w": "zachód", "lewo": "zachód"
            }
            
            for key, value in directions.items():
                if text == key or text == f"idź {key}" or text == f"idź na {key}":
                    return value
            
            # "wejdź do [miejsce]" -> "wejdź [miejsce]"
            if text.startswith("wejdź do "):
                place = text[9:]
                return f"wejdź {place}"
            
            # "wyjdź z [miejsce]" -> "wyjdź"
            if text.startswith("wyjdź"):
                return "wyjdź"
            
            # "biegnij na [kierunek]" -> "biegnij [kierunek]"
            if text.startswith("biegnij "):
                direction = text[8:]
                if direction in directions:
                    return f"biegnij {directions[direction]}"
            
            # "skradaj się do [miejsce]" -> "skradaj [miejsce]"
            if text.startswith("skradaj się"):
                if " do " in text:
                    place = text.split(" do ", 1)[1]
                    return f"skradaj {place}"
                return "skradaj"
            
            # "wspinaj się na [obiekt]" -> "wspinaj [obiekt]"
            if text.startswith("wspinaj się"):
                if " na " in text:
                    target = text.split(" na ", 1)[1]
                    return f"wspinaj {target}"
                return "wspinaj"
            
            return None
        
        def parse_exploration_command(text: str, context: Dict) -> Optional[str]:
            """Parser dla komend eksploracji."""
            text = text.lower()
            
            # "co widzę?" -> "rozejrzyj"
            if any(phrase in text for phrase in ["co widzę", "gdzie jestem", "opisz okolicę"]):
                return "rozejrzyj"
            
            # "zbadaj [obiekt]" -> "zbadaj [obiekt]"
            if text.startswith("zbadaj ") or text.startswith("sprawdź "):
                item = text.split(" ", 1)[1]
                return f"zbadaj {item}"
            
            # "pokaż mapę" -> "mapa"
            if "mapa" in text or "pokaż mapę" in text:
                return "mapa"
            
            # "szukaj tajnego przejścia" -> "szukaj_przejścia"
            if any(phrase in text for phrase in ["szukaj przejścia", "tajne przejście", "ukryte drzwi"]):
                return "szukaj_przejścia"
            
            # "wróć skąd przyszedłem" -> "wróć"
            if "wróć" in text and any(phrase in text for phrase in ["skąd przyszedłem", "do poprzedniej"]):
                return "wróć"
            
            # "zapamiętaj to miejsce" -> "zaznacz_miejsce"
            if "zapamiętaj" in text or "zaznacz" in text:
                return "zaznacz_miejsce"
            
            return None
        
        parsers["movement"] = parse_movement_command
        parsers["exploration"] = parse_exploration_command
        
        return parsers
    
    def on_action_executed(self, action: str, result: Any):
        """Reaguje na wykonane akcje."""
        # Śledź odwiedzone lokacje
        if "wszedł do" in str(result) or "dotarł do" in str(result):
            self._track_location(result)
            self.exploration_stats["distance_traveled"] += 1
        
        # Śledź odkryte sekrety
        if "odkrył" in str(result) and any(word in str(result) for word in ["przejście", "drzwi", "skrytkę"]):
            self.exploration_stats["secrets_found"] += 1
            self._track_secret(result)
        
        # Aktualizuj znane ścieżki
        if any(direction in action for direction in ["północ", "południe", "wschód", "zachód"]):
            self._update_known_paths(action, result)
    
    def _can_move_north(self, context: Dict) -> bool:
        """Sprawdza czy można iść na północ."""
        return self._check_exit(context, "north")
    
    def _can_move_south(self, context: Dict) -> bool:
        """Sprawdza czy można iść na południe."""
        return self._check_exit(context, "south")
    
    def _can_move_east(self, context: Dict) -> bool:
        """Sprawdza czy można iść na wschód."""
        return self._check_exit(context, "east")
    
    def _can_move_west(self, context: Dict) -> bool:
        """Sprawdza czy można iść na zachód."""
        return self._check_exit(context, "west")
    
    def _check_exit(self, context: Dict, direction: str) -> bool:
        """Sprawdza czy jest wyjście w danym kierunku."""
        if "current_location" in context:
            location = context["current_location"]
            if hasattr(location, 'exits'):
                return direction in location.exits
        return False
    
    def _has_examinable_objects(self, context: Dict) -> bool:
        """Sprawdza czy są obiekty do zbadania."""
        if "current_location" in context:
            location = context["current_location"]
            # Sprawdź przedmioty, NPCe, obiekty
            if hasattr(location, 'items') and location.items:
                return True
            if "npcs" in context and context["npcs"]:
                return True
            if hasattr(location, 'objects') and location.objects:
                return True
        return False
    
    def _has_entrance(self, context: Dict) -> bool:
        """Sprawdza czy jest wejście do budynku."""
        location = str(context.get("current_location", "")).lower()
        entrances = ["drzwi", "brama", "wejście", "portal", "przejście"]
        return any(entrance in location for entrance in entrances)
    
    def _is_inside(self, context: Dict) -> bool:
        """Sprawdza czy gracz jest wewnątrz budynku."""
        if "current_location" in context:
            location = context["current_location"]
            if hasattr(location, 'inside'):
                return location.inside
            # Sprawdź po nazwie
            location_str = str(location).lower()
            return any(inside in location_str for inside in ["wnętrze", "pokój", "sala", "komnata"])
        return False
    
    def _has_climbable(self, context: Dict) -> bool:
        """Sprawdza czy jest coś do wspinania."""
        location = str(context.get("current_location", "")).lower()
        climbables = ["drabina", "lina", "skała", "mur", "drzewo", "schody"]
        return any(climb in location for climb in climbables)
    
    def _has_water_crossing(self, context: Dict) -> bool:
        """Sprawdza czy jest woda do przepłynięcia."""
        location = str(context.get("current_location", "")).lower()
        water = ["rzeka", "jezioro", "strumień", "kanał", "fosa"]
        return any(w in location for w in water)
    
    def _all_secrets_found(self, context: Dict) -> bool:
        """Sprawdza czy wszystkie sekrety zostały znalezione."""
        # Zakładamy że każda lokacja może mieć maksymalnie 1 sekret
        if "current_location" in context:
            location = context["current_location"]
            if hasattr(location, 'id'):
                return location.id in self.discovered_secrets
        return False
    
    def _can_run(self, context: Dict) -> bool:
        """Sprawdza czy gracz może biegać."""
        # Nie można biegać gdy jest ranny lub przeciążony
        if "player" in context:
            player = context["player"]
            if hasattr(player, 'pain') and player.pain > 50:
                return False
            if hasattr(player, 'encumbrance') and player.encumbrance > 80:
                return False
        return True
    
    def _can_sneak(self, context: Dict) -> bool:
        """Sprawdza czy można się skradać."""
        # Można się skradać gdy są NPCe lub wrogowie
        return "npcs" in context and len(context["npcs"]) > 0
    
    def _has_waypoint(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma ustawiony punkt orientacyjny."""
        return hasattr(context.get("game_state", {}), "waypoint")
    
    def _track_location(self, result: Any):
        """Śledzi odwiedzone lokacje."""
        # Parsuj nazwę lokacji
        result_str = str(result)
        if "do" in result_str:
            # Wyciągnij nazwę po "do"
            parts = result_str.split("do", 1)
            if len(parts) > 1:
                location_name = parts[1].strip().split()[0]
                self.visited_locations.add(location_name)
                self.exploration_stats["locations_discovered"] = len(self.visited_locations)
    
    def _track_secret(self, result: Any):
        """Śledzi odkryte sekrety."""
        # Note: Parsowanie ID sekretu
        secret_id = f"secret_{len(self.discovered_secrets)}"
        self.discovered_secrets.add(secret_id)
    
    def _update_known_paths(self, action: str, result: Any):
        """Aktualizuje znane ścieżki."""
        # Note: Implementacja śledzenia ścieżek między lokacjami
        pass
    
    def get_exploration_hints(self, context: Dict) -> List[str]:
        """Zwraca kontekstowe podpowiedzi eksploracji."""
        hints = []
        
        # Podpowiedzi o nieodkrytych kierunkach
        if "current_location" in context:
            location = context["current_location"]
            if hasattr(location, 'exits'):
                unexplored = []
                for direction in ["north", "south", "east", "west"]:
                    if direction in location.exits:
                        # Note: Sprawdź czy kierunek był eksplorowany
                        pass
                
                if unexplored:
                    hints.append(f"🧭 Niezbadane kierunki: {', '.join(unexplored)}")
        
        # Podpowiedzi o sekretach
        if not self._all_secrets_found(context):
            hints.append("🔍 To miejsce może skrywać sekrety...")
        
        # Podpowiedzi o obiektach
        if self._has_examinable_objects(context):
            hints.append("👀 Są tu rzeczy warte zbadania")
        
        # Podpowiedzi o postępie
        if self.exploration_stats["locations_discovered"] == 1:
            hints.append("🗺️ Pierwsza odkryta lokacja!")
        elif self.exploration_stats["locations_discovered"] == 10:
            hints.append("🏆 Odkryłeś 10 lokacji!")
        
        return hints