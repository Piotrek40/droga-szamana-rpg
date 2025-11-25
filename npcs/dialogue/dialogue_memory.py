"""
System pamięci dialogów dla NPCów.

Śledzi historię rozmów, odwiedzone węzły dialogowe,
i pozwala na dynamiczne dostosowanie dialogów na podstawie
poprzednich interakcji.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ConversationMood(Enum):
    """Nastrój rozmowy."""
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"
    FEARFUL = "fearful"
    GRATEFUL = "grateful"


@dataclass
class ConversationRecord:
    """Rekord pojedynczej rozmowy."""
    npc_id: str
    node_id: str
    choice_index: int
    choice_text: str
    game_time: int  # Czas gry w minutach
    game_day: int
    timestamp: datetime = field(default_factory=datetime.now)
    effects_applied: List[str] = field(default_factory=list)
    mood: ConversationMood = ConversationMood.NEUTRAL

    def to_dict(self) -> Dict[str, Any]:
        """Konwersja do słownika dla zapisu."""
        return {
            'npc_id': self.npc_id,
            'node_id': self.node_id,
            'choice_index': self.choice_index,
            'choice_text': self.choice_text,
            'game_time': self.game_time,
            'game_day': self.game_day,
            'timestamp': self.timestamp.isoformat(),
            'effects_applied': self.effects_applied,
            'mood': self.mood.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationRecord':
        """Tworzenie z słownika."""
        return cls(
            npc_id=data['npc_id'],
            node_id=data['node_id'],
            choice_index=data['choice_index'],
            choice_text=data.get('choice_text', ''),
            game_time=data.get('game_time', 0),
            game_day=data.get('game_day', 1),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(),
            effects_applied=data.get('effects_applied', []),
            mood=ConversationMood(data.get('mood', 'neutral'))
        )


@dataclass
class NPCDialogueState:
    """Stan dialogowy konkretnego NPCa."""
    npc_id: str
    visited_nodes: Set[str] = field(default_factory=set)
    conversation_count: int = 0
    first_meeting_day: Optional[int] = None
    last_meeting_day: Optional[int] = None
    last_meeting_time: Optional[int] = None
    relationship_score: int = 0  # -100 do +100
    unlocked_topics: Set[str] = field(default_factory=set)
    completed_branches: Set[str] = field(default_factory=set)
    special_flags: Dict[str, Any] = field(default_factory=dict)
    last_mood: ConversationMood = ConversationMood.NEUTRAL

    def to_dict(self) -> Dict[str, Any]:
        """Konwersja do słownika dla zapisu."""
        return {
            'npc_id': self.npc_id,
            'visited_nodes': list(self.visited_nodes),
            'conversation_count': self.conversation_count,
            'first_meeting_day': self.first_meeting_day,
            'last_meeting_day': self.last_meeting_day,
            'last_meeting_time': self.last_meeting_time,
            'relationship_score': self.relationship_score,
            'unlocked_topics': list(self.unlocked_topics),
            'completed_branches': list(self.completed_branches),
            'special_flags': self.special_flags,
            'last_mood': self.last_mood.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NPCDialogueState':
        """Tworzenie z słownika."""
        return cls(
            npc_id=data['npc_id'],
            visited_nodes=set(data.get('visited_nodes', [])),
            conversation_count=data.get('conversation_count', 0),
            first_meeting_day=data.get('first_meeting_day'),
            last_meeting_day=data.get('last_meeting_day'),
            last_meeting_time=data.get('last_meeting_time'),
            relationship_score=data.get('relationship_score', 0),
            unlocked_topics=set(data.get('unlocked_topics', [])),
            completed_branches=set(data.get('completed_branches', [])),
            special_flags=data.get('special_flags', {}),
            last_mood=ConversationMood(data.get('last_mood', 'neutral'))
        )


class DialogueMemory:
    """
    System pamięci dialogów.

    Zarządza historią rozmów, stanem dialogowym NPCów,
    i globalną wiedzą gracza zdobytą przez dialogi.
    """

    def __init__(self):
        """Inicjalizacja systemu pamięci."""
        self.npc_states: Dict[str, NPCDialogueState] = {}
        self.conversation_history: List[ConversationRecord] = []
        self.global_knowledge: Set[str] = set()
        self.history_limit: int = 500  # Maksymalna liczba rekordów

    def get_npc_state(self, npc_id: str) -> NPCDialogueState:
        """
        Pobierz stan dialogowy NPCa.

        Args:
            npc_id: ID NPCa

        Returns:
            Stan dialogowy (tworzony jeśli nie istnieje)
        """
        if npc_id not in self.npc_states:
            self.npc_states[npc_id] = NPCDialogueState(npc_id=npc_id)
        return self.npc_states[npc_id]

    def record_conversation_start(self, npc_id: str, game_time: int, game_day: int) -> None:
        """
        Zapisz rozpoczęcie rozmowy.

        Args:
            npc_id: ID NPCa
            game_time: Aktualny czas gry (minuty)
            game_day: Aktualny dzień gry
        """
        state = self.get_npc_state(npc_id)
        state.conversation_count += 1

        if state.first_meeting_day is None:
            state.first_meeting_day = game_day

        state.last_meeting_day = game_day
        state.last_meeting_time = game_time

    def record_node_visit(
        self,
        npc_id: str,
        node_id: str,
        choice_index: int,
        choice_text: str,
        game_time: int,
        game_day: int,
        effects: Optional[List[str]] = None,
        mood: ConversationMood = ConversationMood.NEUTRAL
    ) -> None:
        """
        Zapisz odwiedzenie węzła dialogowego.

        Args:
            npc_id: ID NPCa
            node_id: ID węzła dialogowego
            choice_index: Indeks wybranej opcji
            choice_text: Tekst wybranej opcji
            game_time: Czas gry
            game_day: Dzień gry
            effects: Lista zastosowanych efektów
            mood: Nastrój rozmowy
        """
        # Aktualizuj stan NPCa
        state = self.get_npc_state(npc_id)
        state.visited_nodes.add(node_id)
        state.last_mood = mood

        # Dodaj rekord do historii
        record = ConversationRecord(
            npc_id=npc_id,
            node_id=node_id,
            choice_index=choice_index,
            choice_text=choice_text,
            game_time=game_time,
            game_day=game_day,
            effects_applied=effects or [],
            mood=mood
        )
        self.conversation_history.append(record)

        # Ogranicz historię
        if len(self.conversation_history) > self.history_limit:
            self.conversation_history = self.conversation_history[-self.history_limit:]

    def mark_branch_completed(self, npc_id: str, branch_id: str) -> None:
        """
        Oznacz gałąź dialogową jako ukończoną.

        Args:
            npc_id: ID NPCa
            branch_id: ID gałęzi
        """
        state = self.get_npc_state(npc_id)
        state.completed_branches.add(branch_id)

    def unlock_topic(self, npc_id: str, topic: str) -> None:
        """
        Odblokuj nowy temat rozmowy.

        Args:
            npc_id: ID NPCa
            topic: Temat do odblokowania
        """
        state = self.get_npc_state(npc_id)
        state.unlocked_topics.add(topic)

    def add_knowledge(self, knowledge_id: str) -> None:
        """
        Dodaj globalną wiedzę.

        Args:
            knowledge_id: ID wiedzy
        """
        self.global_knowledge.add(knowledge_id)

    def has_knowledge(self, knowledge_id: str) -> bool:
        """
        Sprawdź czy gracz posiada wiedzę.

        Args:
            knowledge_id: ID wiedzy

        Returns:
            True jeśli gracz posiada wiedzę
        """
        return knowledge_id in self.global_knowledge

    def modify_relationship(self, npc_id: str, amount: int) -> int:
        """
        Zmień poziom relacji z NPCem.

        Args:
            npc_id: ID NPCa
            amount: Zmiana (może być ujemna)

        Returns:
            Nowy poziom relacji
        """
        state = self.get_npc_state(npc_id)
        state.relationship_score = max(-100, min(100, state.relationship_score + amount))
        return state.relationship_score

    def set_flag(self, npc_id: str, flag_name: str, value: Any) -> None:
        """
        Ustaw flagę specjalną dla NPCa.

        Args:
            npc_id: ID NPCa
            flag_name: Nazwa flagi
            value: Wartość
        """
        state = self.get_npc_state(npc_id)
        state.special_flags[flag_name] = value

    def get_flag(self, npc_id: str, flag_name: str, default: Any = None) -> Any:
        """
        Pobierz wartość flagi.

        Args:
            npc_id: ID NPCa
            flag_name: Nazwa flagi
            default: Wartość domyślna

        Returns:
            Wartość flagi lub wartość domyślna
        """
        state = self.get_npc_state(npc_id)
        return state.special_flags.get(flag_name, default)

    def is_first_meeting(self, npc_id: str) -> bool:
        """
        Sprawdź czy to pierwsze spotkanie z NPCem.

        Args:
            npc_id: ID NPCa

        Returns:
            True jeśli to pierwsze spotkanie
        """
        state = self.get_npc_state(npc_id)
        return state.conversation_count <= 1

    def has_visited_node(self, npc_id: str, node_id: str) -> bool:
        """
        Sprawdź czy węzeł był już odwiedzony.

        Args:
            npc_id: ID NPCa
            node_id: ID węzła

        Returns:
            True jeśli węzeł był odwiedzony
        """
        state = self.get_npc_state(npc_id)
        return node_id in state.visited_nodes

    def is_branch_completed(self, npc_id: str, branch_id: str) -> bool:
        """
        Sprawdź czy gałąź dialogowa jest ukończona.

        Args:
            npc_id: ID NPCa
            branch_id: ID gałęzi

        Returns:
            True jeśli gałąź ukończona
        """
        state = self.get_npc_state(npc_id)
        return branch_id in state.completed_branches

    def has_topic_unlocked(self, npc_id: str, topic: str) -> bool:
        """
        Sprawdź czy temat jest odblokowany.

        Args:
            npc_id: ID NPCa
            topic: Temat

        Returns:
            True jeśli temat odblokowany
        """
        state = self.get_npc_state(npc_id)
        return topic in state.unlocked_topics

    def get_relationship_level(self, npc_id: str) -> str:
        """
        Pobierz tekstowy poziom relacji.

        Args:
            npc_id: ID NPCa

        Returns:
            Opis poziomu relacji
        """
        state = self.get_npc_state(npc_id)
        score = state.relationship_score

        if score >= 80:
            return "przyjaciel"
        elif score >= 50:
            return "dobry_znajomy"
        elif score >= 20:
            return "znajomy"
        elif score >= -20:
            return "neutralny"
        elif score >= -50:
            return "nieufny"
        elif score >= -80:
            return "wrogi"
        else:
            return "znienawidzony"

    def get_recent_conversations(self, npc_id: str, limit: int = 10) -> List[ConversationRecord]:
        """
        Pobierz ostatnie rozmowy z NPCem.

        Args:
            npc_id: ID NPCa
            limit: Maksymalna liczba rekordów

        Returns:
            Lista ostatnich rozmów
        """
        npc_history = [r for r in self.conversation_history if r.npc_id == npc_id]
        return npc_history[-limit:]

    def days_since_last_talk(self, npc_id: str, current_day: int) -> Optional[int]:
        """
        Oblicz ile dni minęło od ostatniej rozmowy.

        Args:
            npc_id: ID NPCa
            current_day: Aktualny dzień

        Returns:
            Liczba dni lub None jeśli nigdy nie rozmawiali
        """
        state = self.get_npc_state(npc_id)
        if state.last_meeting_day is None:
            return None
        return current_day - state.last_meeting_day

    def save_state(self) -> Dict[str, Any]:
        """
        Zapisz stan pamięci do słownika.

        Returns:
            Słownik z pełnym stanem do zapisu
        """
        return {
            'npc_states': {
                npc_id: state.to_dict()
                for npc_id, state in self.npc_states.items()
            },
            'conversation_history': [
                record.to_dict()
                for record in self.conversation_history[-self.history_limit:]
            ],
            'global_knowledge': list(self.global_knowledge)
        }

    def load_state(self, data: Dict[str, Any]) -> None:
        """
        Wczytaj stan pamięci ze słownika.

        Args:
            data: Słownik z zapisanym stanem
        """
        # Wyczyść obecny stan
        self.npc_states.clear()
        self.conversation_history.clear()
        self.global_knowledge.clear()

        # Wczytaj stany NPCów
        for npc_id, state_data in data.get('npc_states', {}).items():
            self.npc_states[npc_id] = NPCDialogueState.from_dict(state_data)

        # Wczytaj historię
        for record_data in data.get('conversation_history', []):
            self.conversation_history.append(ConversationRecord.from_dict(record_data))

        # Wczytaj wiedzę
        self.global_knowledge = set(data.get('global_knowledge', []))

    def reset(self) -> None:
        """Resetuj całą pamięć (np. przy nowej grze)."""
        self.npc_states.clear()
        self.conversation_history.clear()
        self.global_knowledge.clear()
