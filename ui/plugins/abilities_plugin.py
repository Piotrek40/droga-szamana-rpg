"""
Plugin systemu zdolności i czarów dla Smart Interface.
Integruje zdolności klasowe, czary i specjalne umiejętności.
"""

from typing import List, Dict, Any, Callable, Optional
from ui.smart_interface import PluginInterface, ContextualAction, ActionType
from player.classes import CharacterClass, ClassAbility
from player.skills import SkillName


class AbilitiesPlugin(PluginInterface):
    """Plugin rozszerzający interfejs o zdolności i czary."""
    
    def __init__(self):
        self.ability_cooldowns = {}  # Śledzi cooldowny zdolności
        self.last_ability_used = None
        self.mana_cost_multiplier = 1.0
        
    def register_actions(self) -> List[ContextualAction]:
        """Rejestruje akcje zdolności."""
        actions = []
        
        # === ZDOLNOŚCI WOJOWNIKA ===
        actions.append(ContextualAction(
            id="berserker_rage",
            name="Szał Berserka",
            description="Zwiększa siłę i odporność na ból",
            type=ActionType.COMBAT,
            command="zdolność szał_berserka",
            icon="🔥",
            hotkey="B",
            condition=lambda ctx: self._is_class(ctx, "wojownik") and self._not_on_cooldown("szał_berserka"),
            priority=95,
            category="abilities"
        ))
        
        actions.append(ContextualAction(
            id="shield_bash",
            name="Uderzenie Tarczą",
            description="Ogłusza przeciwnika tarczą",
            type=ActionType.COMBAT,
            command="zdolność uderzenie_tarczą",
            icon="🛡️",
            condition=lambda ctx: self._is_class(ctx, "wojownik") and self._has_shield(ctx),
            priority=93,
            category="abilities"
        ))
        
        # === ZDOLNOŚCI ŁOTRA ===
        actions.append(ContextualAction(
            id="stealth",
            name="Kamuflaż",
            description="Stań się niewidoczny",
            type=ActionType.EXPLORATION,
            command="zdolność kamuflaż",
            icon="👤",
            hotkey="K",
            condition=lambda ctx: self._is_class(ctx, "łotr") and not self._in_combat(ctx),
            priority=94,
            category="abilities"
        ))
        
        actions.append(ContextualAction(
            id="poison_blade",
            name="Zatrute Ostrze",
            description="Pokryj broń trucizną",
            type=ActionType.COMBAT,
            command="zdolność zatrute_ostrze",
            icon="☠️",
            condition=lambda ctx: self._is_class(ctx, "łotr") and self._has_poison(ctx),
            priority=92,
            category="abilities"
        ))
        
        # === ZDOLNOŚCI MAGA ===
        actions.append(ContextualAction(
            id="fireball",
            name="Kula Ognia",
            description="Rzuć kulę ognia w przeciwników",
            type=ActionType.COMBAT,
            command="czar kula_ognia",
            icon="🔥",
            hotkey="1",
            condition=lambda ctx: self._is_class(ctx, "mag") and self._has_mana(ctx, 30),
            priority=96,
            category="magic"
        ))
        
        actions.append(ContextualAction(
            id="frost_armor",
            name="Lodowa Zbroja",
            description="Otocz się ochronną warstwą lodu",
            type=ActionType.COMBAT,
            command="czar lodowa_zbroja",
            icon="❄️",
            hotkey="2",
            condition=lambda ctx: self._is_class(ctx, "mag") and self._has_mana(ctx, 20),
            priority=91,
            category="magic"
        ))
        
        actions.append(ContextualAction(
            id="teleport",
            name="Teleportacja",
            description="Teleportuj się do znanej lokacji",
            type=ActionType.EXPLORATION,
            command="czar teleportacja",
            icon="✨",
            hotkey="T",
            condition=lambda ctx: self._is_class(ctx, "mag") and self._has_mana(ctx, 50) and not self._in_combat(ctx),
            priority=85,
            category="magic"
        ))
        
        # === ZDOLNOŚCI ŁOWCY ===
        actions.append(ContextualAction(
            id="animal_companion",
            name="Przywołaj Towarzysza",
            description="Przywołaj zwierzęcego towarzysza",
            type=ActionType.EXPLORATION,
            command="zdolność towarzysz",
            icon="🐺",
            condition=lambda ctx: self._is_class(ctx, "łowca") and not self._has_companion(ctx),
            priority=88,
            category="abilities"
        ))
        
        actions.append(ContextualAction(
            id="track",
            name="Tropienie",
            description="Troń ślady w okolicy",
            type=ActionType.EXPLORATION,
            command="zdolność tropienie",
            icon="👣",
            hotkey="R",
            condition=lambda ctx: self._is_class(ctx, "łowca"),
            priority=87,
            category="abilities"
        ))
        
        # === ZDOLNOŚCI KAPŁANA ===
        actions.append(ContextualAction(
            id="heal",
            name="Leczenie",
            description="Ulecz siebie lub sojusznika",
            type=ActionType.COMBAT,
            command="czar leczenie",
            icon="💚",
            hotkey="H",
            condition=lambda ctx: self._is_class(ctx, "kapłan") and self._has_mana(ctx, 25),
            priority=97,
            category="magic"
        ))
        
        actions.append(ContextualAction(
            id="bless",
            name="Błogosławieństwo",
            description="Błogosław sojuszników zwiększając ich statystyki",
            type=ActionType.COMBAT,
            command="czar błogosławieństwo",
            icon="✝️",
            condition=lambda ctx: self._is_class(ctx, "kapłan") and self._has_mana(ctx, 15),
            priority=86,
            category="magic"
        ))
        
        # === ZDOLNOŚCI SZAMANA (Pustkowia) ===
        actions.append(ContextualAction(
            id="lightning_spirit",
            name="Duch Błyskawicy",
            description="Przywołaj ducha błyskawicy",
            type=ActionType.COMBAT,
            command="zdolność duch_błyskawicy",
            icon="⚡",
            condition=lambda ctx: self._is_void_walker(ctx),
            priority=98,
            category="void_powers"
        ))
        
        actions.append(ContextualAction(
            id="totem",
            name="Postaw Totem",
            description="Postaw totem wzmacniający",
            type=ActionType.COMBAT,
            command="zdolność totem",
            icon="🗿",
            condition=lambda ctx: self._is_void_walker(ctx) and self._has_totem_materials(ctx),
            priority=84,
            category="void_powers"
        ))
        
        # === UNIWERSALNE ===
        actions.append(ContextualAction(
            id="meditate",
            name="Medytacja",
            description="Medytuj aby odzyskać manę",
            type=ActionType.SYSTEM,
            command="medytuj",
            icon="🧘",
            hotkey="M",
            condition=lambda ctx: not self._in_combat(ctx) and self._has_mana_pool(ctx),
            priority=70,
            category="abilities"
        ))
        
        return actions
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widgety zdolności do status bara."""
        widgets = []
        
        def mana_widget(game_state):
            """Widget pokazujący manę."""
            if hasattr(game_state.player, 'mana'):
                mana = game_state.player.mana
                max_mana = game_state.player.max_mana
                percent = mana / max_mana if max_mana > 0 else 0
                
                bar_length = 8
                filled = int(percent * bar_length)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                return f"💙 [{bar}] {int(percent*100)}%"
            return ""
        
        def cooldown_widget(game_state):
            """Widget pokazujący cooldowny."""
            if self.ability_cooldowns:
                # Pokaż najdłuższy cooldown
                longest = max(self.ability_cooldowns.items(), key=lambda x: x[1])
                ability, turns = longest
                if turns > 0:
                    return f"⏱️ {ability[:8]}: {turns}t"
            return ""
        
        def companion_widget(game_state):
            """Widget towarzysza (dla łowcy)."""
            if hasattr(game_state.player, 'companion'):
                companion = game_state.player.companion
                if companion:
                    health_percent = companion.health / companion.max_health
                    if health_percent < 0.3:
                        icon = "🐺💔"
                    else:
                        icon = "🐺"
                    return f"{icon} {companion.name}"
            return ""
        
        widgets.append(mana_widget)
        widgets.append(cooldown_widget)
        widgets.append(companion_widget)
        
        return widgets
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Dodaje parsery dla komend zdolności."""
        parsers = {}
        
        def parse_spell_command(text: str, context: Dict) -> Optional[str]:
            """Parser dla czarów i zdolności."""
            text = text.lower()
            
            # "rzuć kulę ognia" -> "czar kula_ognia"
            if text.startswith("rzuć "):
                spell = text[5:].replace(" ", "_")
                return f"czar {spell}"
            
            # "ulecz mnie" -> "czar leczenie self"
            if "ulecz" in text:
                if "mnie" in text or "siebie" in text:
                    return "czar leczenie self"
                elif "wszystkich" in text:
                    return "czar leczenie_obszarowe"
                else:
                    # Znajdź cel
                    words = text.split()
                    if len(words) > 1:
                        target = words[-1]
                        return f"czar leczenie {target}"
                    return "czar leczenie"
            
            # "zostań niewidoczny" -> "zdolność kamuflaż"
            stealth_phrases = ["ukryj się", "schowaj się", "zostań niewidoczny", "niewidzialność"]
            if any(phrase in text for phrase in stealth_phrases):
                return "zdolność kamuflaż"
            
            # "przywołaj wilka" -> "zdolność towarzysz wilk"
            if "przywołaj" in text:
                animals = ["wilk", "niedźwiedź", "niedzwiedz", "orzeł", "orzel", "puma"]
                for animal in animals:
                    if animal in text:
                        return f"zdolność towarzysz {animal}"
                return "zdolność towarzysz"
            
            return None
        
        def parse_ability_target(text: str, context: Dict) -> Optional[str]:
            """Parser dla celów zdolności."""
            # "ulecz piotra" -> "czar leczenie piotr"
            # "błogosław wszystkich" -> "czar błogosławieństwo all"
            # "teleportuj do kuchni" -> "czar teleportacja kuchnia"
            
            ability_keywords = {
                "ulecz": "czar leczenie",
                "błogosław": "czar błogosławieństwo",
                "teleportuj": "czar teleportacja",
                "zaatakuj": "zdolność",
            }
            
            for keyword, command in ability_keywords.items():
                if keyword in text.lower():
                    # Znajdź cel
                    parts = text.lower().split()
                    keyword_index = parts.index(keyword)
                    
                    if keyword_index < len(parts) - 1:
                        target = " ".join(parts[keyword_index + 1:])
                        
                        # Specjalne cele
                        if target in ["wszystkich", "wszystko", "obszar"]:
                            return f"{command}_obszarowe"
                        elif target in ["mnie", "siebie"]:
                            return f"{command} self"
                        else:
                            return f"{command} {target}"
                    
                    return command
            
            return None
        
        parsers["spell"] = parse_spell_command
        parsers["ability_target"] = parse_ability_target
        
        return parsers
    
    def on_action_executed(self, action: str, result: Any):
        """Reaguje na wykonane akcje."""
        # Aktualizuj cooldowny
        if "zdolność" in action or "czar" in action:
            ability_name = action.split()[1] if len(action.split()) > 1 else action
            self.last_ability_used = ability_name
            
            # Ustaw cooldown (przykładowe wartości)
            cooldowns = {
                "szał_berserka": 10,
                "kamuflaż": 5,
                "kula_ognia": 2,
                "teleportacja": 15,
                "leczenie": 3,
            }
            
            if ability_name in cooldowns:
                self.ability_cooldowns[ability_name] = cooldowns[ability_name]
        
        # Zmniejsz cooldowny co turę
        for ability in list(self.ability_cooldowns.keys()):
            self.ability_cooldowns[ability] -= 1
            if self.ability_cooldowns[ability] <= 0:
                del self.ability_cooldowns[ability]
    
    def _is_class(self, context: Dict, class_name: str) -> bool:
        """Sprawdza czy gracz jest danej klasy."""
        player = context.get("player")
        if player and hasattr(player, "character_class"):
            if player.character_class is not None:
                return player.character_class.name.lower() == class_name.lower()
        return False
    
    def _is_void_walker(self, context: Dict) -> bool:
        """Sprawdza czy gracz jest Wędrowcem Pustki."""
        player = context.get("player")
        if player and hasattr(player, "is_void_walker"):
            return player.is_void_walker
        return False
    
    def _has_mana(self, context: Dict, required: int) -> bool:
        """Sprawdza czy gracz ma wystarczająco many."""
        player = context.get("player")
        if player and hasattr(player, "mana"):
            return player.mana >= required
        return False
    
    def _has_mana_pool(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma manę."""
        player = context.get("player")
        return player and hasattr(player, "mana")
    
    def _not_on_cooldown(self, ability: str) -> bool:
        """Sprawdza czy zdolność nie jest na cooldownie."""
        return self.ability_cooldowns.get(ability, 0) <= 0
    
    def _in_combat(self, context: Dict) -> bool:
        """Sprawdza czy gracz jest w walce."""
        game_state = context.get("game_state")
        return game_state and getattr(game_state, "in_combat", False)
    
    def _has_shield(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma tarczę."""
        player = context.get("player")
        if player and hasattr(player, "equipment"):
            return player.equipment.get("shield") is not None
        return False
    
    def _has_poison(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma truciznę."""
        player = context.get("player")
        if player and hasattr(player, "inventory"):
            return any("trucizna" in item.get("name", "").lower() for item in player.inventory)
        return False
    
    def _has_companion(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma towarzysza."""
        player = context.get("player")
        return player and hasattr(player, "companion") and player.companion is not None
    
    def _has_totem_materials(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma materiały na totem."""
        player = context.get("player")
        if player and hasattr(player, "inventory"):
            required = ["drewno", "kamień"]
            inventory_names = [item.get("name", "").lower() for item in player.inventory]
            return all(any(req in name for name in inventory_names) for req in required)
        return False
    
    def get_ability_hints(self, context: Dict) -> List[str]:
        """Zwraca kontekstowe podpowiedzi dla zdolności."""
        hints = []
        
        player = context.get("player")
        if player:
            # Podpowiedź o manie
            if hasattr(player, "mana"):
                mana_percent = player.mana / player.max_mana if player.max_mana > 0 else 0
                if mana_percent < 0.2:
                    hints.append("💙 Niska mana! Użyj medytacji aby ją odnowić.")
            
            # Podpowiedź o cooldownach
            if self.ability_cooldowns:
                ready_soon = [a for a, cd in self.ability_cooldowns.items() if cd == 1]
                if ready_soon:
                    hints.append(f"⏱️ {ready_soon[0]} będzie gotowe w następnej turze!")
            
            # Podpowiedź klasowa
            if hasattr(player, "character_class"):
                class_tips = {
                    "wojownik": "💪 Pamiętaj o Szale Berserka gdy masz mało zdrowia!",
                    "łotr": "👤 Użyj kamuflaż aby uniknąć walki.",
                    "mag": "🔥 Kula ognia zadaje obrażenia obszarowe!",
                    "łowca": "🐺 Twój towarzysz może walczyć za ciebie.",
                    "kapłan": "💚 Lecz sojuszników aby utrzymać drużynę przy życiu.",
                }
                
                class_name = player.character_class.name.lower()
                if class_name in class_tips and not self._in_combat(context):
                    hints.append(class_tips[class_name])
        
        return hints