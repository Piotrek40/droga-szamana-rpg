"""
Plugin systemu walki dla Smart Interface.
Dodaje kontekstowe akcje bojowe, widgety stanu walki i inteligentne podpowiedzi.
"""

from typing import List, Dict, Any, Callable, Optional
from ui.smart_interface import PluginInterface, ContextualAction, ActionType
from mechanics.combat import CombatAction, CombatSystem
from player.skills import SkillName


class CombatPlugin(PluginInterface):
    """Plugin rozszerzający interfejs o funkcje bojowe."""
    
    def __init__(self):
        self.combat_system = CombatSystem()
        self.in_combat = False
        self.current_target = None
        self.combat_log = []
        self.combo_moves = []
        
    def register_actions(self) -> List[ContextualAction]:
        """Rejestruje akcje bojowe."""
        actions = []
        
        # Podstawowy atak
        actions.append(ContextualAction(
            id="attack_basic",
            name="Atak podstawowy",
            description="Wykonuje standardowy atak",
            type=ActionType.COMBAT,
            command="atakuj",
            icon="⚔️",
            hotkey="a",
            condition=lambda ctx: self._has_enemy_nearby(ctx),
            priority=90,
            category="combat"
        ))
        
        # Silny atak
        actions.append(ContextualAction(
            id="attack_strong",
            name="Silny atak",
            description="Potężny atak zużywający więcej staminy",
            type=ActionType.COMBAT,
            command="atak_silny",
            icon="💪",
            hotkey="A",
            condition=lambda ctx: self._has_enemy_nearby(ctx) and self._has_stamina(ctx, 30),
            priority=85,
            category="combat"
        ))
        
        # Szybki atak
        actions.append(ContextualAction(
            id="attack_quick",
            name="Szybki atak",
            description="Szybka seria ciosów",
            type=ActionType.COMBAT,
            command="atak_szybki",
            icon="⚡",
            hotkey="q",
            condition=lambda ctx: self._has_enemy_nearby(ctx) and self._has_stamina(ctx, 20),
            priority=84,
            category="combat"
        ))
        
        # Obrona
        actions.append(ContextualAction(
            id="defend",
            name="Przyjmij postawę obronną",
            description="Zwiększa obronę kosztem możliwości ataku",
            type=ActionType.COMBAT,
            command="broń",
            icon="🛡️",
            hotkey="d",
            condition=lambda ctx: self.in_combat,
            priority=80,
            category="combat"
        ))
        
        # Unik
        actions.append(ContextualAction(
            id="dodge",
            name="Unik",
            description="Próba uniku następnego ataku",
            type=ActionType.COMBAT,
            command="unik",
            icon="💨",
            hotkey="e",
            condition=lambda ctx: self.in_combat and self._has_stamina(ctx, 15),
            priority=79,
            category="combat"
        ))
        
        # Riposta
        actions.append(ContextualAction(
            id="riposte",
            name="Riposta",
            description="Kontratak po udanej obronie",
            type=ActionType.COMBAT,
            command="riposta",
            icon="🔄",
            condition=lambda ctx: self._can_riposte(ctx),
            priority=78,
            category="combat"
        ))
        
        # Ocena przeciwnika
        actions.append(ContextualAction(
            id="assess",
            name="Oceń przeciwnika",
            description="Analizuje słabe punkty wroga",
            type=ActionType.COMBAT,
            command="oceń",
            icon="👁️",
            hotkey="o",
            condition=lambda ctx: self._has_enemy_nearby(ctx),
            priority=70,
            category="combat"
        ))
        
        # Użyj umiejętności
        actions.append(ContextualAction(
            id="use_skill",
            name="Użyj specjalnej umiejętności",
            description="Aktywuj specjalną technikę bojową",
            type=ActionType.COMBAT,
            command="umiejętność",
            icon="✨",
            hotkey="u",
            condition=lambda ctx: self._has_combat_skill(ctx),
            priority=75,
            category="combat"
        ))
        
        # Ucieczka
        actions.append(ContextualAction(
            id="flee",
            name="Uciekaj",
            description="Próba ucieczki z walki",
            type=ActionType.COMBAT,
            command="uciekaj",
            icon="🏃",
            hotkey="U",
            condition=lambda ctx: self.in_combat,
            priority=60,
            category="combat"
        ))
        
        # Leczenie w walce
        actions.append(ContextualAction(
            id="heal_combat",
            name="Użyj bandaży",
            description="Szybkie opatrzenie ran",
            type=ActionType.COMBAT,
            command="bandażuj",
            icon="🩹",
            hotkey="h",
            condition=lambda ctx: self._has_healing_items(ctx) and self._is_wounded(ctx),
            priority=65,
            category="combat"
        ))
        
        return actions
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widgety bojowe do status bara."""
        widgets = []
        
        def combat_status_widget(game_state):
            """Widget pokazujący status walki."""
            if not self.in_combat:
                return ""
            
            if self.current_target:
                target_health = getattr(self.current_target, 'health', 100)
                target_max = getattr(self.current_target, 'max_health', 100)
                percent = target_health / target_max
                
                bar_length = 8
                filled = int(percent * bar_length)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                return f"⚔️ Wróg: [{bar}] {int(percent*100)}%"
            return "⚔️ W walce"
        
        def combo_widget(game_state):
            """Widget pokazujący aktywne combo."""
            if not self.combo_moves:
                return ""
            
            combo_str = "→".join([m[:1].upper() for m in self.combo_moves[-3:]])
            return f"🔥 Combo: {combo_str}"
        
        def pain_widget(game_state):
            """Widget pokazujący poziom bólu."""
            if not hasattr(game_state.player, 'combat_stats'):
                return ""
            
            pain = game_state.player.combat_stats.pain
            if pain > 70:
                icon = "😵"
                color = "red"
            elif pain > 40:
                icon = "😣"
                color = "yellow"
            elif pain > 20:
                icon = "😐"
                color = "white"
            else:
                return ""
            
            bar_length = 6
            filled = int((pain / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            return f"{icon} Ból: [{bar}]"
        
        widgets.append(combat_status_widget)
        widgets.append(combo_widget)
        widgets.append(pain_widget)
        
        return widgets
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Dodaje parsery dla komend bojowych."""
        parsers = {}
        
        def parse_combat_target(text: str, context: Dict) -> Optional[str]:
            """Parser dla celów ataku."""
            # "atakuj szczura" -> "atakuj szczur"
            # "bij w głowę" -> "atakuj głowa"
            # "uderz piotra w nogę" -> "atakuj piotr noga"
            
            parts = text.lower().split()
            if not parts:
                return None
            
            action = parts[0]
            combat_actions = ["atakuj", "bij", "uderz", "wal", "tnij", "pchnij"]
            
            if action not in combat_actions:
                return None
            
            # Znajdź cel
            if len(parts) > 1:
                target = parts[1]
                # Sprawdź czy to NPC lub wróg
                if "npcs" in context:
                    for npc in context["npcs"]:
                        if target in npc["name"].lower():
                            if len(parts) > 2:
                                # Część ciała
                                body_part = parts[2]
                                return f"atakuj {npc['id']} {body_part}"
                            return f"atakuj {npc['id']}"
                
                # Może to być część ciała dla ostatniego celu
                if self.current_target and target in ["głowa", "glowa", "noga", "ręka", "reka", "tułów", "tulow"]:
                    return f"atakuj {target}"
            
            return "atakuj"
        
        def parse_combo(text: str, context: Dict) -> Optional[str]:
            """Parser dla combo."""
            # "combo AAS" -> seria ataków: atak, atak, silny
            if text.lower().startswith("combo "):
                combo_str = text[6:].upper()
                moves = []
                for char in combo_str:
                    if char == 'A':
                        moves.append("atakuj")
                    elif char == 'S':
                        moves.append("atak_silny")
                    elif char == 'Q':
                        moves.append("atak_szybki")
                    elif char == 'D':
                        moves.append("broń")
                    elif char == 'E':
                        moves.append("unik")
                
                if moves:
                    return " && ".join(moves)  # Wykonaj sekwencję
            
            return None
        
        parsers["combat_target"] = parse_combat_target
        parsers["combo"] = parse_combo
        
        return parsers
    
    def on_action_executed(self, action: str, result: Any):
        """Reaguje na wykonane akcje."""
        # Śledź akcje bojowe dla combo
        combat_keywords = ["atak", "unik", "broń", "riposta"]
        if any(keyword in action.lower() for keyword in combat_keywords):
            self.combo_moves.append(action)
            if len(self.combo_moves) > 5:
                self.combo_moves.pop(0)
            
            # Sprawdź specjalne combo
            self._check_special_combos()
        
        # Aktualizuj status walki
        if "walka rozpoczęta" in str(result).lower():
            self.in_combat = True
        elif "walka zakończona" in str(result).lower() or "uciekłeś" in str(result).lower():
            self.in_combat = False
            self.current_target = None
            self.combo_moves = []
        
        # Zapisz do logu
        if self.in_combat:
            self.combat_log.append({
                "action": action,
                "result": result,
                "timestamp": self._get_game_time()
            })
    
    def _has_enemy_nearby(self, context: Dict) -> bool:
        """Sprawdza czy jest wróg w pobliżu."""
        # Sprawdź NPCów wrogich
        if "npcs" in context:
            for npc in context["npcs"]:
                if npc.get("hostile", False):
                    return True
        
        # Sprawdź czy są stworzenia
        if "creatures" in context:
            return len(context["creatures"]) > 0
        
        return False
    
    def _has_stamina(self, context: Dict, required: int) -> bool:
        """Sprawdza czy gracz ma wystarczająco staminy."""
        if "player" in context and hasattr(context["player"], "stamina"):
            return context["player"].stamina >= required
        return False
    
    def _can_riposte(self, context: Dict) -> bool:
        """Sprawdza czy można wykonać ripostę."""
        # Riposta możliwa tylko po udanej obronie
        if self.combat_log:
            last_action = self.combat_log[-1]
            if "broń" in last_action.get("action", "") and "udana" in str(last_action.get("result", "")):
                return True
        return False
    
    def _has_combat_skill(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma specjalne umiejętności bojowe."""
        if "player" in context and hasattr(context["player"], "skills"):
            from player.skills import SkillName
            # Sprawdź tylko istniejące skille bojowe
            try:
                miecze_skill = context["player"].skills.get_skill(SkillName.MIECZE)
                if miecze_skill and miecze_skill.level > 30:
                    return True
            except (AttributeError, KeyError):
                pass
        return False
    
    def _has_healing_items(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma przedmioty leczące."""
        if "player" in context and hasattr(context["player"], "inventory"):
            healing_items = ["bandaż", "mikstura_lecznicza", "zioła"]
            for item in context["player"].inventory:
                if any(heal in item.get("name", "").lower() for heal in healing_items):
                    return True
        return False
    
    def _is_wounded(self, context: Dict) -> bool:
        """Sprawdza czy gracz jest ranny."""
        if "player" in context:
            player = context["player"]
            if hasattr(player, "health") and hasattr(player, "max_health"):
                return player.health < player.max_health * 0.8
        return False
    
    def _check_special_combos(self):
        """Sprawdza specjalne kombinacje."""
        if len(self.combo_moves) >= 3:
            last_three = "".join([m[0].upper() for m in self.combo_moves[-3:]])
            
            special_combos = {
                "AAD": "Seria z blokiem - bonus do obrony!",
                "QQE": "Błyskawiczny unik - niemożliwy do trafienia!",
                "ASA": "Młyn bojowy - podwójne obrażenia!",
                "DDE": "Perfekcyjna obrona - riposta gotowa!",
                "AQS": "Kombinacja mistrzowska - krytyczne trafienie!"
            }
            
            if last_three in special_combos:
                print(f"\n🔥 COMBO! {special_combos[last_three]}")
    
    def _get_game_time(self) -> str:
        """Pobiera czas gry."""
        # TODO: Integracja z systemem czasu
        return "00:00"
    
    def get_combat_hints(self, context: Dict) -> List[str]:
        """Zwraca kontekstowe podpowiedzi bojowe."""
        hints = []
        
        if self.in_combat:
            player = context.get("player")
            if player:
                # Podpowiedź o staminie
                if hasattr(player, "stamina") and player.stamina < 30:
                    hints.append("💡 Niska stamina! Użyj obrony aby się zregenerować.")
                
                # Podpowiedź o bólu
                if hasattr(player, "combat_stats") and player.combat_stats.pain > 50:
                    hints.append("💡 Wysoki poziom bólu zmniejsza skuteczność! Rozważ ucieczkę.")
                
                # Podpowiedź o combo
                if len(self.combo_moves) == 2:
                    hints.append("💡 Jeszcze jedna akcja do combo!")
        else:
            # Podpowiedzi poza walką
            if self._has_enemy_nearby(context):
                hints.append("⚠️ Uwaga! Wrogi przeciwnik w pobliżu.")
        
        return hints