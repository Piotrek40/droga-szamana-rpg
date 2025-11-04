"""
Plugin systemu craftingu dla Smart Interface.
Integruje tworzenie przedmiotów, receptury i łańcuchy produkcji.
"""

from typing import List, Dict, Any, Callable, Optional
from ui.smart_interface import PluginInterface, ContextualAction, ActionType


class CraftingPlugin(PluginInterface):
    """Plugin rozszerzający interfejs o funkcje craftingu."""
    
    def __init__(self):
        self.known_recipes = set()  # Znane receptury
        self.crafting_queue = []  # Kolejka produkcji
        self.material_tracker = {}  # Śledzenie materiałów
        self.quality_modifiers = {}  # Modyfikatory jakości
        self.crafting_stats = {
            "items_crafted": 0,
            "perfect_quality": 0,
            "failed_attempts": 0
        }
        
    def register_actions(self) -> List[ContextualAction]:
        """Rejestruje akcje craftingu."""
        actions = []
        
        # Otwórz crafting
        actions.append(ContextualAction(
            id="open_crafting",
            name="Otwórz warsztat",
            description="Otwórz menu craftingu",
            type=ActionType.CRAFT,
            command="crafting",
            icon="🔨",
            hotkey="c",
            condition=lambda ctx: self._has_crafting_station(ctx),
            priority=95,
            category="crafting"
        ))
        
        # Stwórz przedmiot
        actions.append(ContextualAction(
            id="craft_item",
            name="Stwórz przedmiot",
            description="Wytwórz przedmiot z materiałów",
            type=ActionType.CRAFT,
            command="stwórz",
            icon="⚒️",
            condition=lambda ctx: self._can_craft_anything(ctx),
            priority=90,
            category="crafting"
        ))
        
        # Sprawdź receptury
        actions.append(ContextualAction(
            id="check_recipes",
            name="Sprawdź receptury",
            description="Zobacz dostępne receptury",
            type=ActionType.CRAFT,
            command="receptury",
            icon="📋",
            condition=lambda ctx: len(self.known_recipes) > 0,
            priority=85,
            category="crafting"
        ))
        
        # Sprawdź materiały
        actions.append(ContextualAction(
            id="check_materials",
            name="Sprawdź materiały",
            description="Zobacz dostępne materiały",
            type=ActionType.CRAFT,
            command="materiały",
            icon="📦",
            condition=lambda ctx: self._has_materials(ctx),
            priority=80,
            category="crafting"
        ))
        
        # Ulepsz przedmiot
        actions.append(ContextualAction(
            id="upgrade_item",
            name="Ulepsz przedmiot",
            description="Popraw jakość przedmiotu",
            type=ActionType.CRAFT,
            command="ulepsz",
            icon="✨",
            condition=lambda ctx: self._has_upgradeable_item(ctx),
            priority=75,
            category="crafting"
        ))
        
        # Napraw przedmiot
        actions.append(ContextualAction(
            id="repair_item",
            name="Napraw przedmiot",
            description="Napraw uszkodzony przedmiot",
            type=ActionType.CRAFT,
            command="napraw",
            icon="🔧",
            condition=lambda ctx: self._has_damaged_item(ctx),
            priority=78,
            category="crafting"
        ))
        
        # Rozmontuj przedmiot
        actions.append(ContextualAction(
            id="disassemble",
            name="Rozmontuj przedmiot",
            description="Odzyskaj materiały z przedmiotu",
            type=ActionType.CRAFT,
            command="rozmontuj",
            icon="🔩",
            condition=lambda ctx: self._has_disassembleable_item(ctx),
            priority=70,
            category="crafting"
        ))
        
        # Naucz się receptury
        actions.append(ContextualAction(
            id="learn_recipe",
            name="Naucz się receptury",
            description="Odkryj nową recepturę",
            type=ActionType.CRAFT,
            command="naucz_receptury",
            icon="📖",
            condition=lambda ctx: self._has_recipe_to_learn(ctx),
            priority=65,
            category="crafting"
        ))
        
        # Masowa produkcja
        actions.append(ContextualAction(
            id="mass_craft",
            name="Masowa produkcja",
            description="Stwórz wiele przedmiotów naraz",
            type=ActionType.CRAFT,
            command="masowa_produkcja",
            icon="🏭",
            condition=lambda ctx: self._can_mass_produce(ctx),
            priority=72,
            category="crafting"
        ))
        
        # Eksperymentuj
        actions.append(ContextualAction(
            id="experiment",
            name="Eksperymentuj",
            description="Próbuj stworzyć coś nowego",
            type=ActionType.CRAFT,
            command="eksperymentuj",
            icon="🧪",
            condition=lambda ctx: self._has_experimental_materials(ctx),
            priority=60,
            category="crafting"
        ))
        
        # Sprawdź jakość
        actions.append(ContextualAction(
            id="check_quality",
            name="Sprawdź jakość materiałów",
            description="Oceń jakość dostępnych materiałów",
            type=ActionType.CRAFT,
            command="jakość_materiałów",
            icon="💎",
            condition=lambda ctx: self._has_materials(ctx),
            priority=68,
            category="crafting"
        ))
        
        # Statystyki craftingu
        actions.append(ContextualAction(
            id="crafting_stats",
            name="Statystyki rzemiosła",
            description="Zobacz swoje osiągnięcia w craftingu",
            type=ActionType.CRAFT,
            command="statystyki_craftingu",
            icon="📊",
            condition=lambda ctx: self.crafting_stats["items_crafted"] > 0,
            priority=55,
            category="crafting"
        ))
        
        return actions
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widgety craftingu do status bara."""
        widgets = []
        
        def crafting_queue_widget(game_state):
            """Widget pokazujący kolejkę produkcji."""
            if self.crafting_queue:
                item = self.crafting_queue[0]
                remaining = len(self.crafting_queue)
                if remaining > 1:
                    return f"⚒️ {item} (+{remaining-1})"
                return f"⚒️ Tworzenie: {item}"
            return ""
        
        def materials_widget(game_state):
            """Widget pokazujący kluczowe materiały."""
            if self.material_tracker:
                # Pokaż 3 najważniejsze materiały
                key_materials = ["żelazo", "drewno", "skóra"]
                counts = []
                for material in key_materials:
                    if material in self.material_tracker:
                        count = self.material_tracker[material]
                        if count > 0:
                            counts.append(f"{material[:3]}:{count}")
                if counts:
                    return f"📦 {' '.join(counts[:3])}"
            return ""
        
        def crafting_skill_widget(game_state):
            """Widget poziomu craftingu."""
            if hasattr(game_state, 'player'):
                player = game_state.player
                if hasattr(player, 'skills'):
                    # Zakładamy że jest skill kowalstwa
                    from player.skills import SkillName
                    smithing = player.skills.get_skill(SkillName.KOWALSTWO)
                    if smithing and smithing.level > 0:
                        return f"🔨 Kowalstwo: {smithing.level}"
            return ""
        
        def recipe_count_widget(game_state):
            """Widget liczby znanych receptur."""
            if self.known_recipes:
                return f"📋 Receptury: {len(self.known_recipes)}"
            return ""
        
        widgets.append(crafting_queue_widget)
        widgets.append(materials_widget)
        widgets.append(crafting_skill_widget)
        widgets.append(recipe_count_widget)
        
        return widgets
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Dodaje parsery dla komend craftingu."""
        parsers = {}
        
        def parse_crafting_command(text: str, context: Dict) -> Optional[str]:
            """Parser dla komend craftingu."""
            text = text.lower()
            
            # "zrób miecz" -> "stwórz miecz"
            if text.startswith("zrób "):
                item = text[5:]
                return f"stwórz {item}"
            
            # "wykuj zbroję" -> "stwórz zbroja"
            if text.startswith("wykuj "):
                item = text[6:]
                return f"stwórz {item}"
            
            # "napraw miecz" -> "napraw miecz"
            if text.startswith("napraw "):
                return text
            
            # "ulepsz broń" -> "ulepsz broń"
            if text.startswith("ulepsz "):
                return text
            
            # "rozbierz na części" -> "rozmontuj"
            if "rozbierz" in text or "na części" in text:
                return "rozmontuj"
            
            # "co mogę zrobić?" -> "receptury"
            if "co mogę zrobić" in text or "co mogę stworzyć" in text:
                return "receptury"
            
            # "jakie mam materiały?" -> "materiały"
            if "jakie mam materiały" in text or "co mam w zapasach" in text:
                return "materiały"
            
            # "stwórz 10 strzał" -> "masowa_produkcja strzała 10"
            import re
            mass_match = re.match(r"stwórz (\d+) (.+)", text)
            if mass_match:
                count = mass_match.group(1)
                item = mass_match.group(2)
                return f"masowa_produkcja {item} {count}"
            
            return None
        
        def parse_recipe_query(text: str, context: Dict) -> Optional[str]:
            """Parser dla zapytań o receptury."""
            text = text.lower()
            
            # "jak zrobić miecz?" -> "receptura miecz"
            if text.startswith("jak zrobić ") or text.startswith("jak stworzyć "):
                item = text.split(" ", 2)[2].rstrip("?")
                return f"receptura {item}"
            
            # "czego potrzebuję do zbroi?" -> "materiały_do zbroja"
            if "czego potrzebuję" in text or "co potrzebne" in text:
                words = text.split()
                if "do" in words:
                    idx = words.index("do")
                    if idx < len(words) - 1:
                        item = " ".join(words[idx+1:]).rstrip("?")
                        return f"materiały_do {item}"
            
            # "czy mogę zrobić tarczę?" -> "czy_mogę_stworzyć tarcza"
            if text.startswith("czy mogę zrobić ") or text.startswith("czy mogę stworzyć "):
                item = text.split(" ", 3)[3].rstrip("?")
                return f"czy_mogę_stworzyć {item}"
            
            return None
        
        parsers["crafting"] = parse_crafting_command
        parsers["recipe"] = parse_recipe_query
        
        return parsers
    
    def on_action_executed(self, action: str, result: Any):
        """Reaguje na wykonane akcje."""
        # Śledź crafting
        if "stworzył" in str(result) or "wytworzył" in str(result):
            self.crafting_stats["items_crafted"] += 1
            
            # Sprawdź jakość
            if "doskonałej jakości" in str(result) or "mistrzowski" in str(result):
                self.crafting_stats["perfect_quality"] += 1
        
        # Śledź niepowodzenia
        if "nie udało" in str(result) or "zniszczył" in str(result):
            self.crafting_stats["failed_attempts"] += 1
        
        # Aktualizuj materiały
        if "zużył" in str(result) or "wykorzystał" in str(result):
            self._update_material_tracker(result)
        
        # Nowe receptury
        if "nauczył się" in str(result) and "receptury" in str(result):
            self._add_recipe(result)
    
    def _has_crafting_station(self, context: Dict) -> bool:
        """Sprawdza czy jest warsztat w pobliżu."""
        location = context.get("current_location", "")
        stations = ["kuźnia", "warsztat", "stół rzemieślniczy", "kowadło", "piec"]
        return any(station in str(location).lower() for station in stations)
    
    def _can_craft_anything(self, context: Dict) -> bool:
        """Sprawdza czy gracz może cokolwiek stworzyć."""
        if not self._has_crafting_station(context):
            return False
        
        # Sprawdź czy ma materiały i receptury
        return len(self.known_recipes) > 0 and self._has_materials(context)
    
    def _has_materials(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma jakieś materiały."""
        if "player" in context and hasattr(context["player"], "inventory"):
            # Sprawdź czy ma materiały craftingowe
            crafting_materials = ["żelazo", "drewno", "skóra", "tkanina", "kamień"]
            for item in context["player"].inventory:
                if any(mat in item.get("name", "").lower() for mat in crafting_materials):
                    return True
        return False
    
    def _has_upgradeable_item(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma przedmiot do ulepszenia."""
        if "player" in context and hasattr(context["player"], "inventory"):
            for item in context["player"].inventory:
                # Sprawdź czy przedmiot może być ulepszony
                if item.get("quality", 0) < 5:  # Max quality 5
                    return True
        return False
    
    def _has_damaged_item(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma uszkodzony przedmiot."""
        if "player" in context and hasattr(context["player"], "inventory"):
            for item in context["player"].inventory:
                if item.get("durability", 100) < 100:
                    return True
        return False
    
    def _has_disassembleable_item(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma przedmiot do rozmontowania."""
        if "player" in context and hasattr(context["player"], "inventory"):
            # Niektóre przedmioty można rozmontować
            disassembleable = ["miecz", "zbroja", "tarcza", "hełm", "narzędzie"]
            for item in context["player"].inventory:
                if any(type in item.get("name", "").lower() for type in disassembleable):
                    return True
        return False
    
    def _has_recipe_to_learn(self, context: Dict) -> bool:
        """Sprawdza czy są receptury do nauczenia."""
        # Można znaleźć receptury w książkach lub od NPCów
        if "player" in context and hasattr(context["player"], "inventory"):
            for item in context["player"].inventory:
                if "receptura" in item.get("name", "").lower() or "księga" in item.get("name", "").lower():
                    return True
        return False
    
    def _can_mass_produce(self, context: Dict) -> bool:
        """Sprawdza czy można produkować masowo."""
        # Wymaga dużej ilości materiałów i znajomości receptury
        if not self._has_crafting_station(context):
            return False
        
        # Sprawdź czy ma dużo materiałów
        material_count = sum(self.material_tracker.values())
        return material_count >= 10 and len(self.known_recipes) > 0
    
    def _has_experimental_materials(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma materiały do eksperymentów."""
        if "player" in context and hasattr(context["player"], "inventory"):
            # Rzadkie materiały do eksperymentów
            rare_materials = ["kryształ", "esencja", "proszek", "kość", "klejnot"]
            for item in context["player"].inventory:
                if any(mat in item.get("name", "").lower() for mat in rare_materials):
                    return True
        return False
    
    def _update_material_tracker(self, result: Any):
        """Aktualizuje śledzenie materiałów."""
        # Parsuj zużyte materiały
        result_str = str(result).lower()
        materials = ["żelazo", "drewno", "skóra", "tkanina", "kamień"]
        
        for material in materials:
            if material in result_str:
                # Zmniejsz ilość
                if material in self.material_tracker:
                    self.material_tracker[material] = max(0, self.material_tracker[material] - 1)
    
    def _add_recipe(self, result: Any):
        """Dodaje nową recepturę."""
        # Note: Parsowanie nazwy receptury
        recipe_name = "nowa_receptura"
        self.known_recipes.add(recipe_name)
    
    def get_crafting_hints(self, context: Dict) -> List[str]:
        """Zwraca kontekstowe podpowiedzi craftingowe."""
        hints = []
        
        # Podpowiedzi o materiałach
        if self._has_materials(context):
            hints.append("🔨 Masz materiały - możesz coś stworzyć!")
        
        # Podpowiedzi o jakości
        if self.crafting_stats["perfect_quality"] > 0:
            success_rate = self.crafting_stats["perfect_quality"] / max(1, self.crafting_stats["items_crafted"])
            if success_rate > 0.5:
                hints.append("✨ Świetna jakość twoich wyrobów!")
        
        # Podpowiedzi o naprawach
        if self._has_damaged_item(context):
            hints.append("🔧 Niektóre przedmioty wymagają naprawy")
        
        # Podpowiedzi o eksperymentach
        if self._has_experimental_materials(context):
            hints.append("🧪 Masz rzadkie materiały - eksperymentuj!")
        
        return hints