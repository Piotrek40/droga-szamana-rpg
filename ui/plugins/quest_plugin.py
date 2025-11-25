"""
Plugin systemu questów dla Smart Interface.
Integruje emergentne questy, śledzenie postępu i podpowiedzi questowe.
"""

from typing import List, Dict, Any, Callable, Optional
from ui.smart_interface import PluginInterface, ContextualAction, ActionType


class QuestPlugin(PluginInterface):
    """Plugin rozszerzający interfejs o funkcje questowe."""
    
    def __init__(self):
        self.active_quests = []  # Lista aktywnych questów
        self.quest_progress = {}  # Postęp w questach
        self.discovered_clues = set()  # Odkryte wskazówki
        self.quest_markers = {}  # Markery questowe na mapie
        
    def register_actions(self) -> List[ContextualAction]:
        """Rejestruje akcje questowe."""
        actions = []
        
        # Sprawdź questy
        actions.append(ContextualAction(
            id="check_quests",
            name="Sprawdź zadania",
            description="Zobacz listę aktywnych zadań",
            type=ActionType.QUEST,
            command="questy",
            icon="📜",
            hotkey="q",
            condition=lambda ctx: True,  # Zawsze dostępne
            priority=95,
            category="quest"
        ))
        
        # Śledź quest
        actions.append(ContextualAction(
            id="track_quest",
            name="Śledź zadanie",
            description="Ustaw aktywne śledzenie questa",
            type=ActionType.QUEST,
            command="śledź",
            icon="🎯",
            condition=lambda ctx: len(self.active_quests) > 0,
            priority=90,
            category="quest"
        ))
        
        # Przeszukaj okolicę
        actions.append(ContextualAction(
            id="investigate",
            name="Przeszukaj okolicę",
            description="Szukaj śladów i wskazówek",
            type=ActionType.QUEST,
            command="przeszukaj",
            icon="🔍",
            hotkey="i",
            condition=lambda ctx: self._has_investigation_nearby(ctx),
            priority=85,
            category="quest"
        ))
        
        # Podsłuchaj
        actions.append(ContextualAction(
            id="eavesdrop",
            name="Podsłuchaj rozmowę",
            description="Posłuchaj co mówią NPCe",
            type=ActionType.QUEST,
            command="podsłuchaj",
            icon="👂",
            condition=lambda ctx: self._has_npcs_talking(ctx),
            priority=80,
            category="quest"
        ))
        
        # Sprawdź wskazówki
        actions.append(ContextualAction(
            id="check_clues",
            name="Sprawdź wskazówki",
            description="Zobacz zebrane wskazówki",
            type=ActionType.QUEST,
            command="wskazówki",
            icon="🗒️",
            condition=lambda ctx: len(self.discovered_clues) > 0,
            priority=75,
            category="quest"
        ))
        
        # Zapytaj o quest
        actions.append(ContextualAction(
            id="ask_about_quest",
            name="Zapytaj o zadanie",
            description="Zapytaj NPC o konkretne zadanie",
            type=ActionType.QUEST,
            command="zapytaj_o_zadanie",
            icon="💬",
            condition=lambda ctx: self._has_npc_nearby(ctx) and len(self.active_quests) > 0,
            priority=70,
            category="quest"
        ))
        
        # Raportuj postęp
        actions.append(ContextualAction(
            id="report_progress",
            name="Raportuj postęp",
            description="Zgłoś postęp w zadaniu",
            type=ActionType.QUEST,
            command="raportuj",
            icon="📊",
            condition=lambda ctx: self._has_quest_to_report(ctx),
            priority=65,
            category="quest"
        ))
        
        # Porzuć quest
        actions.append(ContextualAction(
            id="abandon_quest",
            name="Porzuć zadanie",
            description="Zrezygnuj z aktywnego zadania",
            type=ActionType.QUEST,
            command="porzuć_zadanie",
            icon="❌",
            condition=lambda ctx: len(self.active_quests) > 0,
            priority=50,
            category="quest"
        ))
        
        # Odkryj sekret
        actions.append(ContextualAction(
            id="discover_secret",
            name="Odkryj sekret",
            description="Zbadaj ukryte miejsce",
            type=ActionType.QUEST,
            command="odkryj_sekret",
            icon="🗝️",
            condition=lambda ctx: self._has_secret_nearby(ctx),
            priority=88,
            category="quest"
        ))
        
        # Połącz wskazówki
        actions.append(ContextualAction(
            id="connect_clues",
            name="Połącz wskazówki",
            description="Spróbuj połączyć zebrane informacje",
            type=ActionType.QUEST,
            command="połącz_wskazówki",
            icon="🧩",
            condition=lambda ctx: len(self.discovered_clues) >= 3,
            priority=72,
            category="quest"
        ))
        
        return actions
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widgety questowe do status bara."""
        widgets = []
        
        def active_quest_widget(game_state):
            """Widget pokazujący aktywny quest."""
            if self.active_quests:
                quest = self.active_quests[0]
                progress = self.quest_progress.get(quest, 0)
                if progress > 0:
                    return f"📜 {quest[:15]}: {progress}%"
                return f"📜 {quest[:20]}"
            return ""
        
        def clues_widget(game_state):
            """Widget pokazujący liczbę wskazówek."""
            if self.discovered_clues:
                return f"🗒️ Wskazówki: {len(self.discovered_clues)}"
            return ""
        
        def quest_marker_widget(game_state):
            """Widget pokazujący kierunek do celu questa."""
            if hasattr(game_state, 'current_location'):
                location = game_state.current_location
                if location in self.quest_markers:
                    direction = self.quest_markers[location]
                    arrows = {
                        "north": "⬆️",
                        "south": "⬇️",
                        "east": "➡️",
                        "west": "⬅️",
                        "here": "📍"
                    }
                    return arrows.get(direction, "❓")
            return ""
        
        widgets.append(active_quest_widget)
        widgets.append(clues_widget)
        widgets.append(quest_marker_widget)
        
        return widgets
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Dodaje parsery dla komend questowych."""
        parsers = {}
        
        def parse_quest_command(text: str, context: Dict) -> Optional[str]:
            """Parser dla komend questowych."""
            text = text.lower()
            
            # "co mam zrobić?" -> "questy"
            if any(phrase in text for phrase in ["co mam zrobić", "jakie mam zadania", "moje zadania"]):
                return "questy"
            
            # "szukaj śladów" -> "przeszukaj"
            if any(phrase in text for phrase in ["szukaj śladów", "zbadaj okolicę", "rozejrzyj się"]):
                return "przeszukaj"
            
            # "posłuchaj co mówią" -> "podsłuchaj"
            if any(phrase in text for phrase in ["posłuchaj", "co mówią", "o czym rozmawiają"]):
                return "podsłuchaj"
            
            # "zapytaj o [quest]" -> "zapytaj_o_zadanie [quest]"
            if text.startswith("zapytaj o "):
                quest_name = text[10:]
                return f"zapytaj_o_zadanie {quest_name}"
            
            # "porzuć zadanie [nazwa]" -> "porzuć_zadanie [nazwa]"
            if text.startswith("porzuć "):
                quest_name = text[7:]
                return f"porzuć_zadanie {quest_name}"
            
            # "śledź [quest]" -> "śledź [quest]"
            if text.startswith("śledź "):
                quest_name = text[6:]
                return f"śledź {quest_name}"
            
            return None
        
        def parse_investigation(text: str, context: Dict) -> Optional[str]:
            """Parser dla komend śledczych."""
            text = text.lower()
            
            # "co tu się stało?" -> "przeszukaj"
            if "co tu się stało" in text or "co się wydarzyło" in text:
                return "przeszukaj"
            
            # "sprawdź [obiekt]" -> "zbadaj [obiekt]"
            if text.startswith("sprawdź "):
                item = text[8:]
                return f"zbadaj {item}"
            
            # "gdzie jest [cel]?" -> podpowiedź kierunku
            if text.startswith("gdzie jest ") or text.startswith("gdzie znajdę "):
                target = text.split(" ", 2)[2].rstrip("?")
                return f"kierunek {target}"
            
            return None
        
        parsers["quest"] = parse_quest_command
        parsers["investigation"] = parse_investigation
        
        return parsers
    
    def on_action_executed(self, action: str, result: Any):
        """Reaguje na wykonane akcje."""
        # Śledź postęp questów
        if "odkrył" in str(result) or "znalazł" in str(result):
            self._extract_clue(result)
        
        # Aktualizuj postęp
        if "wykonał" in str(result) or "ukończył" in str(result):
            self._update_quest_progress(action, result)
        
        # Sprawdź nowe questy
        if "nowe zadanie" in str(result).lower():
            self._extract_new_quest(result)
    
    def _has_investigation_nearby(self, context: Dict) -> bool:
        """Sprawdza czy są ślady do zbadania."""
        location = context.get("current_location")
        if location:
            # Sprawdź czy lokacja ma ślady questowe
            return any(clue for clue in ["ślad", "wskazówka", "dowód"] 
                      if clue in str(location).lower())
        return False
    
    def _has_npcs_talking(self, context: Dict) -> bool:
        """Sprawdza czy NPCe rozmawiają."""
        if "npcs" in context:
            # Sprawdź czy są co najmniej 2 NPCe w lokacji
            return len(context["npcs"]) >= 2
        return False
    
    def _has_npc_nearby(self, context: Dict) -> bool:
        """Sprawdza czy jest NPC w pobliżu."""
        return "npcs" in context and len(context["npcs"]) > 0
    
    def _has_quest_to_report(self, context: Dict) -> bool:
        """Sprawdza czy jest quest do raportowania."""
        for quest in self.active_quests:
            progress = self.quest_progress.get(quest, 0)
            if progress >= 100:
                return True
        return False
    
    def _has_secret_nearby(self, context: Dict) -> bool:
        """Sprawdza czy jest sekret w pobliżu."""
        location = context.get("current_location", "")
        secret_locations = ["ukryte przejście", "tajna skrytka", "zasłonięte drzwi"]
        return any(secret in str(location).lower() for secret in secret_locations)
    
    def _extract_clue(self, result: Any):
        """Wyciąga wskazówkę z rezultatu."""
        # Parsuj wskazówki z tekstu
        result_str = str(result).lower()
        clue_keywords = ["odkrył", "znalazł", "zauważył", "dowiedział"]
        
        for keyword in clue_keywords:
            if keyword in result_str:
                # Dodaj do odkrytych wskazówek
                self.discovered_clues.add(f"clue_{len(self.discovered_clues)}")
                break
    
    def _update_quest_progress(self, action: str, result: Any):
        """Aktualizuje postęp questa."""
        for quest in self.active_quests:
            # Sprawdź czy akcja dotyczy questa
            if quest.lower() in str(result).lower():
                current = self.quest_progress.get(quest, 0)
                self.quest_progress[quest] = min(100, current + 20)
    
    def _extract_new_quest(self, result: Any):
        """Wyciąga nowy quest z rezultatu."""
        # Parsowanie nazwy questa z komend
        quest_name = "Nowe zadanie"
        if quest_name not in self.active_quests:
            self.active_quests.append(quest_name)
            self.quest_progress[quest_name] = 0
    
    def get_quest_hints(self, context: Dict) -> List[str]:
        """Zwraca kontekstowe podpowiedzi questowe."""
        hints = []
        
        # Podpowiedzi o aktywnych questach
        if self.active_quests:
            quest = self.active_quests[0]
            progress = self.quest_progress.get(quest, 0)
            if progress < 30:
                hints.append(f"💡 Poszukaj wskazówek dotyczących: {quest}")
            elif progress < 70:
                hints.append(f"📍 Kontynuuj zadanie: {quest}")
            else:
                hints.append(f"✅ Prawie ukończone: {quest}")
        
        # Podpowiedzi o wskazówkach
        if len(self.discovered_clues) >= 3:
            hints.append("🧩 Masz wystarczająco wskazówek - spróbuj je połączyć!")
        
        # Podpowiedzi o lokacji
        if self._has_investigation_nearby(context):
            hints.append("🔍 W tej lokacji są ślady do zbadania")
        
        return hints