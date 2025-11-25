"""
Główny kontroler systemu dialogów.

Ujednolica wszystkie komponenty dialogowe:
- DialogueMemory (pamięć rozmów)
- DialogueEffectApplicator (efekty z EventBus)
- Wczytywanie dialogów z JSON
- Kontekstowy wybór powitań
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import os

from npcs.dialogue.dialogue_memory import (
    DialogueMemory,
    ConversationMood,
    NPCDialogueState
)
from npcs.dialogue.dialogue_effects import DialogueEffectApplicator
from core.event_bus import (
    event_bus,
    GameEvent,
    EventCategory,
    EventPriority
)


class DialogueResult(Enum):
    """Rezultaty dialogu."""
    CONTINUE = "continue"
    END = "end"
    TRADE = "trade"
    FIGHT = "fight"
    QUEST = "quest"


@dataclass
class DialogueOption:
    """Opcja dialogowa do wyboru."""
    text: str
    response: str
    result: DialogueResult = DialogueResult.CONTINUE
    requirements: Dict[str, Any] = None
    effects: Dict[str, Any] = None
    next_node: str = None
    mood_modifier: int = 0  # Wpływ na nastrój rozmowy
    hidden: bool = False  # Ukryta jeśli wymagania nie spełnione

    def to_dict(self) -> Dict[str, Any]:
        """Konwersja do słownika."""
        return {
            'text': self.text,
            'response': self.response,
            'result': self.result.value,
            'requirements': self.requirements,
            'effects': self.effects,
            'next_node': self.next_node,
            'mood_modifier': self.mood_modifier,
            'hidden': self.hidden
        }


@dataclass
class DialogueNode:
    """Węzeł dialogu."""
    id: str
    npc_text: str
    options: List[DialogueOption]
    conditions: Dict[str, Any] = None  # Warunki pokazania węzła
    on_enter_effects: Dict[str, Any] = None  # Efekty przy wejściu do węzła

    def get_available_options(self, player, dialogue_memory: DialogueMemory = None, npc_id: str = None) -> List[DialogueOption]:
        """
        Zwróć opcje spełniające wymagania.

        Args:
            player: Obiekt gracza
            dialogue_memory: Pamięć dialogów
            npc_id: ID NPCa

        Returns:
            Lista dostępnych opcji
        """
        available = []
        for option in self.options:
            meets_requirements = self._check_requirements(option.requirements, player, dialogue_memory, npc_id)
            if meets_requirements:
                available.append(option)
            elif not option.hidden:
                # Pokazuj opcję jako niedostępną jeśli nie jest ukryta
                disabled_option = DialogueOption(
                    text=f"[Niedostępne] {option.text}",
                    response="",
                    result=DialogueResult.CONTINUE
                )
                # Nie dodajemy niedostępnych opcji - może być mylące
        return available

    def _check_requirements(
        self,
        requirements: Dict,
        player,
        dialogue_memory: DialogueMemory = None,
        npc_id: str = None
    ) -> bool:
        """
        Sprawdź czy gracz spełnia wymagania.

        Args:
            requirements: Słownik wymagań
            player: Obiekt gracza
            dialogue_memory: Pamięć dialogów
            npc_id: ID NPCa

        Returns:
            True jeśli wymagania spełnione
        """
        if not requirements:
            return True

        for req_type, req_value in requirements.items():
            # Wymagania umiejętności
            if req_type == "skill":
                if isinstance(req_value, (list, tuple)):
                    skill_name, min_level = req_value
                elif isinstance(req_value, dict):
                    skill_name = req_value.get('name')
                    min_level = req_value.get('level', 1)
                else:
                    continue

                if hasattr(player, 'get_skill_level'):
                    if player.get_skill_level(skill_name) < min_level:
                        return False
                elif hasattr(player, 'skills'):
                    skill_level = player.skills.get(skill_name, 0)
                    if skill_level < min_level:
                        return False

            # Wymagania przedmiotu
            elif req_type == "item":
                if hasattr(player, 'has_item'):
                    if not player.has_item(req_value):
                        return False
                elif hasattr(player, 'inventory'):
                    if req_value not in [item.id for item in player.inventory]:
                        return False

            # Wymagania reputacji
            elif req_type == "reputation":
                if isinstance(req_value, (list, tuple)):
                    faction, min_rep = req_value
                elif isinstance(req_value, dict):
                    faction = req_value.get('faction')
                    min_rep = req_value.get('min', 0)
                else:
                    continue

                if hasattr(player, 'get_reputation'):
                    if player.get_reputation(faction) < min_rep:
                        return False

            # Wymagania wiedzy
            elif req_type == "knowledge":
                if dialogue_memory and not dialogue_memory.has_knowledge(req_value):
                    return False
                elif hasattr(player, 'has_knowledge') and not player.has_knowledge(req_value):
                    return False

            # Wymagania relacji z NPCem
            elif req_type == "relationship":
                if dialogue_memory and npc_id:
                    state = dialogue_memory.get_npc_state(npc_id)
                    if isinstance(req_value, int):
                        if state.relationship_score < req_value:
                            return False
                    elif isinstance(req_value, dict):
                        min_rel = req_value.get('min', -100)
                        max_rel = req_value.get('max', 100)
                        if not (min_rel <= state.relationship_score <= max_rel):
                            return False

            # Wymagania flagi dialogowej
            elif req_type == "flag":
                if dialogue_memory and npc_id:
                    if isinstance(req_value, str):
                        if not dialogue_memory.get_flag(npc_id, req_value):
                            return False
                    elif isinstance(req_value, dict):
                        flag_name = req_value.get('name')
                        expected = req_value.get('value', True)
                        if dialogue_memory.get_flag(npc_id, flag_name) != expected:
                            return False

            # Wymagania odblokowanego tematu
            elif req_type == "topic_unlocked":
                if dialogue_memory and npc_id:
                    if not dialogue_memory.has_topic_unlocked(npc_id, req_value):
                        return False

            # Wymagania ukończonej gałęzi
            elif req_type == "branch_completed":
                if dialogue_memory and npc_id:
                    if not dialogue_memory.is_branch_completed(npc_id, req_value):
                        return False

            # Wymagania pierwszego spotkania
            elif req_type == "first_meeting":
                if dialogue_memory and npc_id:
                    is_first = dialogue_memory.is_first_meeting(npc_id)
                    if req_value and not is_first:
                        return False
                    elif not req_value and is_first:
                        return False

            # Wymagania questów
            elif req_type == "quest_active":
                if hasattr(player, 'has_active_quest'):
                    if not player.has_active_quest(req_value):
                        return False

            elif req_type == "quest_completed":
                if hasattr(player, 'has_completed_quest'):
                    if not player.has_completed_quest(req_value):
                        return False

            # Wymagania złota
            elif req_type == "gold":
                player_gold = getattr(player, 'gold', 0)
                if player_gold < req_value:
                    return False

        return True


class DialogueController:
    """
    Główny kontroler systemu dialogów.

    Singleton zarządzający całym systemem dialogów:
    - Wczytuje dialogi z JSON
    - Zarządza pamięcią rozmów
    - Aplikuje efekty przez EventBus
    - Zapewnia kontekstowy wybór dialogów
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, game_state=None):
        """
        Inicjalizacja kontrolera.

        Args:
            game_state: Referencja do stanu gry
        """
        if self._initialized:
            if game_state:
                self.game_state = game_state
            return

        self.game_state = game_state
        self.dialogue_trees: Dict[str, Dict[str, DialogueNode]] = {}
        self.npc_dialogue_mapping: Dict[str, str] = {}

        # Komponenty systemu
        self.memory = DialogueMemory()
        self.effect_applicator = DialogueEffectApplicator(self.memory)

        # Stan aktywnego dialogu
        self.active_dialogue: Optional[str] = None
        self.active_node: Optional[str] = None

        # Wczytaj dane
        self._load_dialogues()
        self._load_npc_mapping()

        # Zarejestruj nasłuchiwacze eventów
        self._register_event_handlers()

        self._initialized = True

    def _register_event_handlers(self) -> None:
        """Zarejestruj handlery eventów."""
        # Reaguj na eventy które mogą wpływać na dialogi
        event_bus.subscribe('quest_completed', self._on_quest_completed)
        event_bus.subscribe('reputation_changed', self._on_reputation_changed)

    def _on_quest_completed(self, event: GameEvent) -> None:
        """Handler ukończenia questu - może odblokować dialogi."""
        quest_id = event.data.get('quest_id')
        # Możemy tu automatycznie odblokować tematy rozmów związane z questem
        pass

    def _on_reputation_changed(self, event: GameEvent) -> None:
        """Handler zmiany reputacji."""
        pass

    def _load_dialogues(self) -> None:
        """Wczytaj wszystkie dialogi z plików JSON."""
        # Główny plik dialogów
        try:
            with open('data/dialogues.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._parse_dialogue_data(data.get('dialogue_trees', {}))
        except FileNotFoundError:
            print("[DialogueController] Nie znaleziono data/dialogues.json")

        # Wczytaj dialogi z folderu modularnego jeśli istnieje
        dialogues_dir = 'data/dialogues'
        if os.path.isdir(dialogues_dir):
            for filename in os.listdir(dialogues_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(dialogues_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self._parse_dialogue_data(data.get('dialogue_trees', {}))
                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        print(f"[DialogueController] Błąd wczytywania {filepath}: {e}")

        # Fallback jeśli brak dialogów
        if not self.dialogue_trees:
            self._load_fallback_dialogues()

    def _parse_dialogue_data(self, dialogue_data: Dict) -> None:
        """
        Parsuj dane dialogów z JSON do obiektów.

        Args:
            dialogue_data: Surowe dane z JSON
        """
        for npc_id, tree_data in dialogue_data.items():
            if npc_id not in self.dialogue_trees:
                self.dialogue_trees[npc_id] = {}

            for node_id, node_data in tree_data.items():
                options = []
                for opt_data in node_data.get('options', []):
                    result_str = opt_data.get('result', 'continue')
                    result_map = {
                        'continue': DialogueResult.CONTINUE,
                        'end': DialogueResult.END,
                        'trade': DialogueResult.TRADE,
                        'fight': DialogueResult.FIGHT,
                        'quest': DialogueResult.QUEST
                    }
                    result = result_map.get(result_str, DialogueResult.CONTINUE)

                    option = DialogueOption(
                        text=opt_data.get('text', ''),
                        response=opt_data.get('response', ''),
                        result=result,
                        requirements=opt_data.get('requirements'),
                        effects=opt_data.get('effects'),
                        next_node=opt_data.get('next_node'),
                        mood_modifier=opt_data.get('mood_modifier', 0),
                        hidden=opt_data.get('hidden', False)
                    )
                    options.append(option)

                node = DialogueNode(
                    id=node_data.get('id', node_id),
                    npc_text=node_data.get('npc_text', ''),
                    options=options,
                    conditions=node_data.get('conditions'),
                    on_enter_effects=node_data.get('on_enter_effects')
                )
                self.dialogue_trees[npc_id][node_id] = node

    def _load_npc_mapping(self) -> None:
        """Wczytaj mapowanie NPC -> dialogi."""
        try:
            with open('data/npc_complete.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

                for npc_id, npc_data in data.get('npcs', {}).items():
                    dialogue_id = npc_data.get('dialogue_id', npc_id)
                    self.npc_dialogue_mapping[npc_id] = dialogue_id
                    self.npc_dialogue_mapping[dialogue_id] = dialogue_id

                    if 'dialogue_tree' in npc_data:
                        self.npc_dialogue_mapping[npc_data['dialogue_tree']] = npc_data['dialogue_tree']

                for dialogue_id, map_data in data.get('dialogue_mappings', {}).items():
                    self.npc_dialogue_mapping[dialogue_id] = dialogue_id
                    if 'npc_id' in map_data:
                        self.npc_dialogue_mapping[map_data['npc_id']] = dialogue_id

        except FileNotFoundError:
            # Fallback mapping
            self.npc_dialogue_mapping = {
                'piotr': 'gadatliwy_piotr',
                'jozek': 'stary_jozef',
                'anna': 'anna',
                'brutus': 'brutus',
                'marek': 'gruby_waldek',
                'gadatliwy_piotr': 'gadatliwy_piotr',
                'cichy_tomek': 'cichy_tomek',
                'gruby_waldek': 'gruby_waldek',
                'stary_jozef': 'stary_jozef'
            }

    def _load_fallback_dialogues(self) -> None:
        """Załaduj domyślne dialogi jeśli brak danych."""
        self.dialogue_trees["default"] = {
            "greeting": DialogueNode(
                id="greeting",
                npc_text="*Postać patrzy na ciebie*\n'Czego chcesz?'",
                options=[
                    DialogueOption(
                        text="Kim jesteś?",
                        response="'Nieważne kim jestem. Ważne, że jesteśmy tu razem uwięzieni.'",
                        result=DialogueResult.END
                    ),
                    DialogueOption(
                        text="Do widzenia.",
                        response="'Tak, tak...'",
                        result=DialogueResult.END
                    )
                ]
            )
        }

    def _resolve_dialogue_id(self, npc_id: str, npc_name: str = None) -> str:
        """
        Rozwiąż ID dialogu na podstawie NPC.

        Args:
            npc_id: ID NPCa
            npc_name: Nazwa NPCa (opcjonalna)

        Returns:
            ID dialogu do użycia
        """
        # Sprawdź mapowanie
        dialogue_id = self.npc_dialogue_mapping.get(npc_id, npc_id)

        # Dodatkowe mapowanie po nazwie
        if npc_name:
            npc_name_lower = npc_name.lower()
            name_mappings = {
                ('piotr', 'gadatliwy'): 'gadatliwy_piotr',
                ('józek', 'jozek', 'józef', 'jozef'): 'stary_jozef',
                ('anna',): 'anna',
                ('tomek', 'cichy'): 'cichy_tomek',
                ('brutus',): 'brutus',
                ('marek', 'gruby', 'waldek'): 'gruby_waldek'
            }

            for keywords, target_id in name_mappings.items():
                if any(kw in npc_name_lower for kw in keywords):
                    dialogue_id = target_id
                    break

        return dialogue_id

    def _select_greeting_node(self, npc_id: str, dialogue_id: str, player) -> str:
        """
        Wybierz odpowiedni węzeł powitania na podstawie kontekstu.

        Args:
            npc_id: ID NPCa
            dialogue_id: ID dialogu
            player: Obiekt gracza

        Returns:
            ID węzła do użycia
        """
        tree = self.dialogue_trees.get(dialogue_id, {})

        # Pobierz stan pamięci
        npc_state = self.memory.get_npc_state(npc_id)

        # Sprawdź kontekstowe powitania
        if npc_state.conversation_count == 0:
            # Pierwsze spotkanie
            if 'greeting_first' in tree:
                return 'greeting_first'

        # Sprawdź powitanie zależne od relacji
        relationship_level = self.memory.get_relationship_level(npc_id)
        rel_greeting = f'greeting_{relationship_level}'
        if rel_greeting in tree:
            return rel_greeting

        # Sprawdź powitanie po ukończeniu gałęzi
        for branch in npc_state.completed_branches:
            branch_greeting = f'greeting_after_{branch}'
            if branch_greeting in tree:
                return branch_greeting

        # Domyślne powitanie
        if 'greeting' in tree:
            return 'greeting'
        elif 'start' in tree:
            return 'start'

        return list(tree.keys())[0] if tree else None

    def start_dialogue(
        self,
        npc_id: str,
        player,
        npc_name: str = None
    ) -> Tuple[str, List[DialogueOption]]:
        """
        Rozpocznij dialog z NPCem.

        Args:
            npc_id: ID NPCa
            player: Obiekt gracza
            npc_name: Nazwa NPCa (opcjonalna)

        Returns:
            Tuple (tekst NPCa, lista opcji)
        """
        # Rozwiąż ID dialogu
        dialogue_id = self._resolve_dialogue_id(npc_id, npc_name)

        # Pobierz drzewo dialogowe
        if dialogue_id not in self.dialogue_trees:
            if "default" in self.dialogue_trees:
                dialogue_id = "default"
            else:
                return "Ten NPC nie ma dialogu.", []

        tree = self.dialogue_trees[dialogue_id]

        # Pobierz czas gry
        game_time = 0
        game_day = 1
        if self.game_state:
            if hasattr(self.game_state, 'time_system'):
                game_time = getattr(self.game_state.time_system, 'current_time', 0)
                game_day = getattr(self.game_state.time_system, 'current_day', 1)
            elif hasattr(self.game_state, 'current_time'):
                game_time = self.game_state.current_time
                game_day = getattr(self.game_state, 'current_day', 1)

        # Zapisz rozpoczęcie rozmowy
        self.memory.record_conversation_start(npc_id, game_time, game_day)

        # Wybierz węzeł powitania
        greeting_node_id = self._select_greeting_node(npc_id, dialogue_id, player)
        if not greeting_node_id or greeting_node_id not in tree:
            return "Błąd dialogu.", []

        node = tree[greeting_node_id]

        # Zastosuj efekty wejścia do węzła
        if node.on_enter_effects:
            self.effect_applicator.apply_effects(
                node.on_enter_effects, player, npc_id, greeting_node_id
            )

        # Ustaw aktywny dialog
        self.active_dialogue = dialogue_id
        self.active_node = greeting_node_id

        # Emituj event rozpoczęcia dialogu
        event_bus.emit(GameEvent(
            event_type='dialogue_started',
            category=EventCategory.DIALOGUE,
            data={
                'npc_id': npc_id,
                'dialogue_id': dialogue_id,
                'node_id': greeting_node_id
            },
            source='player',
            target=npc_id,
            priority=EventPriority.NORMAL
        ))

        # Pobierz dostępne opcje
        available_options = node.get_available_options(player, self.memory, npc_id)

        return node.npc_text, available_options

    def process_choice(
        self,
        npc_id: str,
        node_id: str,
        choice_index: int,
        player
    ) -> Tuple[str, Optional[str], DialogueResult, List[DialogueOption], Optional[str]]:
        """
        Przetwórz wybór gracza.

        Args:
            npc_id: ID NPCa
            node_id: ID aktualnego węzła
            choice_index: Indeks wybranej opcji
            player: Obiekt gracza

        Returns:
            Tuple (odpowiedź, tekst następnego węzła, rezultat, opcje, ID następnego węzła)
        """
        dialogue_id = self._resolve_dialogue_id(npc_id)

        if dialogue_id not in self.dialogue_trees:
            if "default" in self.dialogue_trees:
                dialogue_id = "default"
            else:
                return "Błąd dialogu.", None, DialogueResult.END, [], None

        tree = self.dialogue_trees[dialogue_id]
        node = tree.get(node_id)

        if not node:
            return "Błąd dialogu.", None, DialogueResult.END, [], None

        available_options = node.get_available_options(player, self.memory, npc_id)

        if choice_index < 0 or choice_index >= len(available_options):
            return "Nieprawidłowy wybór.", None, DialogueResult.END, [], None

        chosen = available_options[choice_index]

        # Pobierz czas gry
        game_time = 0
        game_day = 1
        if self.game_state:
            if hasattr(self.game_state, 'time_system'):
                game_time = getattr(self.game_state.time_system, 'current_time', 0)
                game_day = getattr(self.game_state.time_system, 'current_day', 1)
            elif hasattr(self.game_state, 'current_time'):
                game_time = self.game_state.current_time
                game_day = getattr(self.game_state, 'current_day', 1)

        # Zapisz odwiedzenie węzła
        effects_list = list(chosen.effects.keys()) if chosen.effects else []
        self.memory.record_node_visit(
            npc_id=npc_id,
            node_id=node_id,
            choice_index=choice_index,
            choice_text=chosen.text,
            game_time=game_time,
            game_day=game_day,
            effects=effects_list
        )

        # Zastosuj efekty
        effect_messages = []
        if chosen.effects:
            effect_messages = self.effect_applicator.apply_effects(
                chosen.effects, player, npc_id, node_id
            )

        # Emituj event wyboru
        event_bus.emit(GameEvent(
            event_type='dialogue_choice_made',
            category=EventCategory.DIALOGUE,
            data={
                'npc_id': npc_id,
                'node_id': node_id,
                'choice_index': choice_index,
                'choice_text': chosen.text,
                'effects': effects_list
            },
            source='player',
            target=npc_id,
            priority=EventPriority.NORMAL
        ))

        # Przejdź do następnego węzła
        next_options = []
        next_npc_text = None
        next_node_id = None

        if chosen.next_node and chosen.next_node in tree:
            next_node = tree[chosen.next_node]
            next_node_id = chosen.next_node

            # Zastosuj efekty wejścia do nowego węzła
            if next_node.on_enter_effects:
                self.effect_applicator.apply_effects(
                    next_node.on_enter_effects, player, npc_id, next_node_id
                )

            next_npc_text = next_node.npc_text
            next_options = next_node.get_available_options(player, self.memory, npc_id)

            self.active_node = next_node_id

        # Jeśli dialog się kończy
        if chosen.result == DialogueResult.END or not next_options:
            event_bus.emit(GameEvent(
                event_type='dialogue_ended',
                category=EventCategory.DIALOGUE,
                data={
                    'npc_id': npc_id,
                    'dialogue_id': dialogue_id,
                    'final_node': node_id
                },
                source='player',
                target=npc_id,
                priority=EventPriority.NORMAL
            ))
            self.active_dialogue = None
            self.active_node = None

        return chosen.response, next_npc_text, chosen.result, next_options, next_node_id

    def get_dialogue(self, npc_id: str, context: str = "greeting") -> str:
        """
        Pobierz prostą odpowiedź dialogową (kompatybilność wsteczna).

        Args:
            npc_id: ID NPCa
            context: Kontekst (greeting, farewell, trade, etc.)

        Returns:
            Tekst odpowiedzi
        """
        import random

        dialogue_id = self._resolve_dialogue_id(npc_id)

        if dialogue_id in self.dialogue_trees:
            tree = self.dialogue_trees[dialogue_id]
            if 'start' in tree:
                node = tree['start']
                return node.npc_text
            elif 'greeting' in tree:
                node = tree['greeting']
                return node.npc_text

        # Domyślne odpowiedzi
        default_dialogues = {
            "greeting": [
                "Czego chcesz?",
                "Co cię tu sprowadza?",
                "Tak? O co chodzi?",
                "Witaj, więźniu.",
                "Masz do mnie jakiś interes?"
            ],
            "farewell": [
                "Do zobaczenia.",
                "Żegnaj.",
                "Trzymaj się.",
                "Uważaj na siebie.",
                "Niech cię Pustka strzeże."
            ],
            "trade": [
                "Może coś kupisz?",
                "Mam kilka rzeczy na sprzedaż.",
                "Interesujesz się handlem?",
                "Spójrz na moje towary.",
                "Co chcesz kupić?"
            ]
        }

        if context in default_dialogues:
            return random.choice(default_dialogues[context])

        return "..."

    def save_state(self) -> Dict[str, Any]:
        """
        Zapisz stan systemu dialogów.

        Returns:
            Słownik z pełnym stanem
        """
        return {
            'memory': self.memory.save_state(),
            'active_dialogue': self.active_dialogue,
            'active_node': self.active_node
        }

    def load_state(self, data: Dict[str, Any]) -> None:
        """
        Wczytaj stan systemu dialogów.

        Args:
            data: Zapisany stan
        """
        if 'memory' in data:
            self.memory.load_state(data['memory'])

        self.active_dialogue = data.get('active_dialogue')
        self.active_node = data.get('active_node')

    def reset(self) -> None:
        """Resetuj system dialogów (nowa gra)."""
        self.memory.reset()
        self.active_dialogue = None
        self.active_node = None

    def has_dialogue_tree(self, npc_id: str) -> bool:
        """
        Sprawdź czy NPC ma drzewo dialogowe.

        Args:
            npc_id: ID NPCa

        Returns:
            True jeśli ma dialogi
        """
        dialogue_id = self._resolve_dialogue_id(npc_id)
        return dialogue_id in self.dialogue_trees

    def get_npc_relationship_status(self, npc_id: str) -> Dict[str, Any]:
        """
        Pobierz status relacji z NPCem.

        Args:
            npc_id: ID NPCa

        Returns:
            Słownik ze statusem relacji
        """
        state = self.memory.get_npc_state(npc_id)
        return {
            'relationship_score': state.relationship_score,
            'relationship_level': self.memory.get_relationship_level(npc_id),
            'conversation_count': state.conversation_count,
            'first_meeting_day': state.first_meeting_day,
            'last_meeting_day': state.last_meeting_day,
            'unlocked_topics': list(state.unlocked_topics),
            'completed_branches': list(state.completed_branches)
        }


# Singleton instance - DO NOT create new instances, import this!
dialogue_controller = None


def get_dialogue_controller(game_state=None) -> DialogueController:
    """
    Pobierz instancję kontrolera dialogów.

    Args:
        game_state: Stan gry (opcjonalny)

    Returns:
        Singleton DialogueController
    """
    global dialogue_controller
    if dialogue_controller is None:
        dialogue_controller = DialogueController(game_state)
    elif game_state and dialogue_controller.game_state is None:
        dialogue_controller.game_state = game_state
    return dialogue_controller
