"""
Plugin systemu zbierania zasobów dla Smart Interface.
Integruje zbieranie, wydobywanie i pozyskiwanie surowców.
"""

from typing import List, Dict, Any, Callable, Optional
from ui.smart_interface import PluginInterface, ContextualAction, ActionType


class GatheringPlugin(PluginInterface):
    """Plugin rozszerzający interfejs o funkcje zbierania zasobów."""
    
    def __init__(self):
        self.gathered_today = {}  # Zasoby zebrane dzisiaj
        self.resource_knowledge = {}  # Wiedza o lokalizacjach zasobów
        self.gathering_tools = set()  # Posiadane narzędzia
        self.gathering_stats = {
            "total_gathered": 0,
            "rare_finds": 0,
            "perfect_harvests": 0
        }
        
    def register_actions(self) -> List[ContextualAction]:
        """Rejestruje akcje zbierania."""
        actions = []
        
        # Zbierz zasób
        actions.append(ContextualAction(
            id="gather",
            name="Zbierz zasób",
            description="Zbierz dostępny surowiec",
            type=ActionType.GATHER,
            command="zbierz",
            icon="🌿",
            hotkey="g",
            condition=lambda ctx: self._has_gatherable_resource(ctx),
            priority=95,
            category="gathering"
        ))
        
        # Przeszukaj teren
        actions.append(ContextualAction(
            id="forage",
            name="Przeszukaj teren",
            description="Szukaj zasobów w okolicy",
            type=ActionType.GATHER,
            command="przeszukaj_teren",
            icon="🔍",
            condition=lambda ctx: self._can_forage(ctx),
            priority=90,
            category="gathering"
        ))
        
        # Wydobywaj rudę
        actions.append(ContextualAction(
            id="mine",
            name="Wydobywaj rudę",
            description="Kop w poszukiwaniu minerałów",
            type=ActionType.GATHER,
            command="kop",
            icon="⛏️",
            condition=lambda ctx: self._has_mining_spot(ctx) and self._has_pickaxe(ctx),
            priority=88,
            category="gathering"
        ))
        
        # Ścinaj drzewo
        actions.append(ContextualAction(
            id="chop_wood",
            name="Ścinaj drzewo",
            description="Zdobądź drewno",
            type=ActionType.GATHER,
            command="ścinaj",
            icon="🪓",
            condition=lambda ctx: self._has_trees(ctx) and self._has_axe(ctx),
            priority=87,
            category="gathering"
        ))
        
        # Zbieraj zioła
        actions.append(ContextualAction(
            id="harvest_herbs",
            name="Zbieraj zioła",
            description="Zbierz rośliny lecznicze",
            type=ActionType.GATHER,
            command="zbieraj_zioła",
            icon="🌱",
            condition=lambda ctx: self._has_herbs(ctx),
            priority=85,
            category="gathering"
        ))
        
        # Łów ryby
        actions.append(ContextualAction(
            id="fish",
            name="Łów ryby",
            description="Złów ryby w wodzie",
            type=ActionType.GATHER,
            command="łów",
            icon="🎣",
            condition=lambda ctx: self._has_water(ctx) and self._has_fishing_rod(ctx),
            priority=83,
            category="gathering"
        ))
        
        # Poluj
        actions.append(ContextualAction(
            id="hunt",
            name="Poluj",
            description="Zapoluj na zwierzynę",
            type=ActionType.GATHER,
            command="poluj",
            icon="🏹",
            condition=lambda ctx: self._has_wildlife(ctx) and self._has_weapon(ctx),
            priority=80,
            category="gathering"
        ))
        
        # Zbieraj wodę
        actions.append(ContextualAction(
            id="collect_water",
            name="Zbieraj wodę",
            description="Napełnij bukłak wodą",
            type=ActionType.GATHER,
            command="nabierz_wody",
            icon="💧",
            condition=lambda ctx: self._has_water_source(ctx) and self._has_container(ctx),
            priority=75,
            category="gathering"
        ))
        
        # Wykop
        actions.append(ContextualAction(
            id="dig",
            name="Wykop",
            description="Kop w ziemi szukając skarbów",
            type=ActionType.GATHER,
            command="wykop",
            icon="🕳️",
            condition=lambda ctx: self._can_dig(ctx) and self._has_shovel(ctx),
            priority=70,
            category="gathering"
        ))
        
        # Sprawdź zasoby w okolicy
        actions.append(ContextualAction(
            id="survey_resources",
            name="Oceń zasoby",
            description="Sprawdź dostępne zasoby w okolicy",
            type=ActionType.GATHER,
            command="oceń_zasoby",
            icon="📊",
            condition=lambda ctx: True,  # Zawsze dostępne
            priority=65,
            category="gathering"
        ))
        
        # Ustaw pułapkę
        actions.append(ContextualAction(
            id="set_trap",
            name="Ustaw pułapkę",
            description="Rozstaw pułapkę na zwierzynę",
            type=ActionType.GATHER,
            command="ustaw_pułapkę",
            icon="🪤",
            condition=lambda ctx: self._has_trap(ctx) and self._has_wildlife(ctx),
            priority=72,
            category="gathering"
        ))
        
        # Zbieraj grzyby
        actions.append(ContextualAction(
            id="gather_mushrooms",
            name="Zbieraj grzyby",
            description="Szukaj jadalnych grzybów",
            type=ActionType.GATHER,
            command="zbieraj_grzyby",
            icon="🍄",
            condition=lambda ctx: self._has_mushrooms(ctx),
            priority=78,
            category="gathering"
        ))
        
        return actions
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widgety zbierania do status bara."""
        widgets = []
        
        def gathering_tool_widget(game_state):
            """Widget pokazujący aktywne narzędzie."""
            tools = []
            if "kilof" in self.gathering_tools:
                tools.append("⛏️")
            if "siekiera" in self.gathering_tools:
                tools.append("🪓")
            if "wędka" in self.gathering_tools:
                tools.append("🎣")
            if tools:
                return f"🛠️ {' '.join(tools)}"
            return ""
        
        def resources_today_widget(game_state):
            """Widget pokazujący dzisiejsze zbiory."""
            if self.gathered_today:
                total = sum(self.gathered_today.values())
                if total > 0:
                    return f"🎒 Zebrano: {total}"
            return ""
        
        def resource_quality_widget(game_state):
            """Widget jakości zasobów w lokacji."""
            if hasattr(game_state, 'current_location'):
                location = str(game_state.current_location).lower()
                if "bogata" in location or "obfita" in location:
                    return "💎 Bogate złoża"
                elif "uboga" in location or "jałowa" in location:
                    return "🪨 Ubogie zasoby"
                elif any(res in location for res in ["las", "kopalnia", "rzeka"]):
                    return "🌟 Normalne zasoby"
            return ""
        
        def gathering_skill_widget(game_state):
            """Widget umiejętności zbierania."""
            if hasattr(game_state, 'player'):
                player = game_state.player
                if hasattr(player, 'skills'):
                    # Sprawdź umiejętności zbierania
                    from player.skills import SkillName
                    survival = player.skills.get_skill(SkillName.PRZETRWANIE)
                    if survival and survival.level > 0:
                        return f"🏕️ Przetrwanie: {survival.level}"
            return ""
        
        widgets.append(gathering_tool_widget)
        widgets.append(resources_today_widget)
        widgets.append(resource_quality_widget)
        widgets.append(gathering_skill_widget)
        
        return widgets
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Dodaje parsery dla komend zbierania."""
        parsers = {}
        
        def parse_gathering_command(text: str, context: Dict) -> Optional[str]:
            """Parser dla komend zbierania."""
            text = text.lower()
            
            # "zbierz wszystko" -> "zbierz wszystko"
            if text == "zbierz wszystko":
                return "zbierz wszystko"
            
            # "zbierz zioła" -> "zbieraj_zioła"
            if text.startswith("zbierz "):
                resource = text[7:]
                if resource == "zioła":
                    return "zbieraj_zioła"
                elif resource == "grzyby":
                    return "zbieraj_grzyby"
                elif resource == "wodę":
                    return "nabierz_wody"
                else:
                    return f"zbierz {resource}"
            
            # "kop rudę" -> "kop"
            if "kop" in text and any(word in text for word in ["rudę", "minerały", "kamień"]):
                return "kop"
            
            # "ścinaj drzewo" -> "ścinaj"
            if "ścinaj" in text or "tnij drzewo" in text:
                return "ścinaj"
            
            # "idź na ryby" -> "łów"
            if "ryby" in text or "łów" in text or "wędkuj" in text:
                return "łów"
            
            # "idź na polowanie" -> "poluj"
            if "polowanie" in text or "poluj" in text or "upoluj" in text:
                return "poluj"
            
            # "szukaj zasobów" -> "przeszukaj_teren"
            if "szukaj" in text and any(word in text for word in ["zasobów", "surowców", "materiałów"]):
                return "przeszukaj_teren"
            
            # "wykop skarb" -> "wykop"
            if "wykop" in text or "kop" in text and "skarb" in text:
                return "wykop"
            
            return None
        
        def parse_resource_query(text: str, context: Dict) -> Optional[str]:
            """Parser dla zapytań o zasoby."""
            text = text.lower()
            
            # "co mogę zebrać?" -> "oceń_zasoby"
            if "co mogę zebrać" in text or "jakie są zasoby" in text:
                return "oceń_zasoby"
            
            # "gdzie znajdę żelazo?" -> "lokalizacja żelazo"
            if text.startswith("gdzie znajdę ") or text.startswith("gdzie jest "):
                resource = text.split(" ", 2)[2].rstrip("?")
                return f"lokalizacja {resource}"
            
            # "ile zebrałem?" -> "statystyki_zbierania"
            if "ile zebrałem" in text or "moje zbiory" in text:
                return "statystyki_zbierania"
            
            # "czy mogę tu kopać?" -> "sprawdź_kopanie"
            if "czy mogę" in text and any(word in text for word in ["kopać", "zbierać", "ścinać"]):
                return "sprawdź_możliwości"
            
            return None
        
        parsers["gathering"] = parse_gathering_command
        parsers["resource"] = parse_resource_query
        
        return parsers
    
    def on_action_executed(self, action: str, result: Any):
        """Reaguje na wykonane akcje."""
        # Śledź zebrane zasoby
        if "zebrał" in str(result) or "zdobył" in str(result):
            self.gathering_stats["total_gathered"] += 1
            self._track_gathered_resource(result)
        
        # Śledź rzadkie znaleziska
        if "rzadki" in str(result).lower() or "wyjątkowy" in str(result).lower():
            self.gathering_stats["rare_finds"] += 1
        
        # Śledź doskonałe zbiory
        if "doskonałej jakości" in str(result) or "perfekcyjnie" in str(result):
            self.gathering_stats["perfect_harvests"] += 1
        
        # Aktualizuj wiedzę o lokalizacjach
        if "znalazł" in str(result) and "miejsce" in str(result):
            self._update_resource_knowledge(action, result)
        
        # Śledź narzędzia
        if "wyposażył" in str(result) or "wziął" in str(result):
            self._update_tools(result)
    
    def _has_gatherable_resource(self, context: Dict) -> bool:
        """Sprawdza czy są zasoby do zebrania."""
        location = str(context.get("current_location", "")).lower()
        resources = ["kamień", "patyk", "liść", "jagody", "orzechy", "kora", "mech"]
        return any(res in location for res in resources)
    
    def _can_forage(self, context: Dict) -> bool:
        """Sprawdza czy można przeszukiwać teren."""
        location = str(context.get("current_location", "")).lower()
        # Można przeszukiwać naturalne tereny
        natural = ["las", "łąka", "pole", "wzgórze", "dolina", "brzeg"]
        return any(terrain in location for terrain in natural)
    
    def _has_mining_spot(self, context: Dict) -> bool:
        """Sprawdza czy jest miejsce do kopania."""
        location = str(context.get("current_location", "")).lower()
        return any(spot in location for spot in ["kopalnia", "żyła", "skała", "kamieniołom"])
    
    def _has_pickaxe(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma kilof."""
        return "kilof" in self.gathering_tools or self._check_inventory_for_tool(context, "kilof")
    
    def _has_trees(self, context: Dict) -> bool:
        """Sprawdza czy są drzewa."""
        location = str(context.get("current_location", "")).lower()
        return any(tree in location for tree in ["drzewo", "las", "gaj", "bór"])
    
    def _has_axe(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma siekierę."""
        return "siekiera" in self.gathering_tools or self._check_inventory_for_tool(context, "siekiera")
    
    def _has_herbs(self, context: Dict) -> bool:
        """Sprawdza czy są zioła."""
        location = str(context.get("current_location", "")).lower()
        return any(herb in location for herb in ["zioła", "rośliny", "łąka", "polana"])
    
    def _has_water(self, context: Dict) -> bool:
        """Sprawdza czy jest woda."""
        location = str(context.get("current_location", "")).lower()
        return any(water in location for water in ["rzeka", "jezioro", "staw", "strumień"])
    
    def _has_fishing_rod(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma wędkę."""
        return "wędka" in self.gathering_tools or self._check_inventory_for_tool(context, "wędka")
    
    def _has_wildlife(self, context: Dict) -> bool:
        """Sprawdza czy jest dzika zwierzyna."""
        location = str(context.get("current_location", "")).lower()
        return any(wild in location for wild in ["las", "puszcza", "ostęp", "jeleń", "dzik"])
    
    def _has_weapon(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma broń."""
        if "player" in context and hasattr(context["player"], "equipment"):
            return context["player"].equipment.get("weapon") is not None
        return False
    
    def _has_water_source(self, context: Dict) -> bool:
        """Sprawdza czy jest źródło wody."""
        location = str(context.get("current_location", "")).lower()
        return any(source in location for source in ["studnia", "źródło", "rzeka", "strumień"])
    
    def _has_container(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma pojemnik."""
        return self._check_inventory_for_tool(context, "bukłak") or self._check_inventory_for_tool(context, "dzban")
    
    def _can_dig(self, context: Dict) -> bool:
        """Sprawdza czy można kopać."""
        location = str(context.get("current_location", "")).lower()
        return "ziemia" in location or "piasek" in location or "gleba" in location
    
    def _has_shovel(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma łopatę."""
        return "łopata" in self.gathering_tools or self._check_inventory_for_tool(context, "łopata")
    
    def _has_trap(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma pułapkę."""
        return self._check_inventory_for_tool(context, "pułapka") or self._check_inventory_for_tool(context, "wnyki")
    
    def _has_mushrooms(self, context: Dict) -> bool:
        """Sprawdza czy są grzyby."""
        location = str(context.get("current_location", "")).lower()
        return any(place in location for place in ["las", "cień", "wilgoć", "pień"])
    
    def _check_inventory_for_tool(self, context: Dict, tool_name: str) -> bool:
        """Sprawdza ekwipunek w poszukiwaniu narzędzia."""
        if "player" in context and hasattr(context["player"], "inventory"):
            for item in context["player"].inventory:
                if tool_name in item.get("name", "").lower():
                    return True
        return False
    
    def _track_gathered_resource(self, result: Any):
        """Śledzi zebrane zasoby."""
        # Parsuj nazwę zasobu
        resources = ["drewno", "kamień", "żelazo", "zioła", "jagody", "grzyby", "ryba", "mięso"]
        result_str = str(result).lower()
        
        for resource in resources:
            if resource in result_str:
                if resource not in self.gathered_today:
                    self.gathered_today[resource] = 0
                self.gathered_today[resource] += 1
                break
    
    def _update_resource_knowledge(self, action: str, result: Any):
        """Aktualizuje wiedzę o lokalizacjach zasobów."""
        # TODO: Parsowanie lokalizacji i typu zasobu
        pass
    
    def _update_tools(self, result: Any):
        """Aktualizuje posiadane narzędzia."""
        tools = ["kilof", "siekiera", "wędka", "łopata", "pułapka"]
        result_str = str(result).lower()
        
        for tool in tools:
            if tool in result_str:
                self.gathering_tools.add(tool)
    
    def get_gathering_hints(self, context: Dict) -> List[str]:
        """Zwraca kontekstowe podpowiedzi zbierania."""
        hints = []
        
        # Podpowiedzi o zasobach
        if self._has_gatherable_resource(context):
            hints.append("🌿 W okolicy są zasoby do zebrania")
        
        # Podpowiedzi o narzędziach
        if self._has_mining_spot(context) and not self._has_pickaxe(context):
            hints.append("⛏️ Potrzebujesz kilofa do wydobycia rudy")
        
        if self._has_trees(context) and not self._has_axe(context):
            hints.append("🪓 Potrzebujesz siekiery do ścinania drzew")
        
        # Podpowiedzi o rzadkich zasobach
        if self.gathering_stats["rare_finds"] > 0:
            hints.append("💎 Masz szczęście do rzadkich znalezisk!")
        
        # Podpowiedzi o jakości
        location = str(context.get("current_location", "")).lower()
        if "bogata" in location:
            hints.append("🌟 To miejsce obfituje w zasoby!")
        
        return hints