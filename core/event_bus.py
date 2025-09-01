"""System event bus dla komunikacji między modułami gry."""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class EventPriority(Enum):
    """Priorytety wydarzeń."""
    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3
    DEBUG = 1


class EventCategory(Enum):
    """Kategorie wydarzeń."""
    COMBAT = "combat"
    MOVEMENT = "movement"
    DIALOGUE = "dialogue"
    TRADE = "trade"
    CRAFT = "craft"
    QUEST = "quest"
    NPC_ACTION = "npc_action"
    TIME = "time"
    WORLD = "world"
    SYSTEM = "system"
    PLAYER_ACTION = "player_action"
    ECONOMY = "economy"
    DEATH = "death"
    DISCOVERY = "discovery"


@dataclass
class GameEvent:
    """Pojedyncze wydarzenie w grze."""
    event_type: str
    category: EventCategory
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    target: Optional[str] = None
    propagate: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwersja na słownik."""
        return {
            'event_type': self.event_type,
            'category': self.category.value,
            'data': self.data,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'target': self.target
        }


class EventBus:
    """Centralny system komunikacji wydarzeń."""
    
    def __init__(self):
        """Inicjalizacja event bus."""
        self.listeners: Dict[str, List[Callable]] = {}
        self.category_listeners: Dict[EventCategory, List[Callable]] = {}
        self.event_queue: List[GameEvent] = []
        self.event_history: List[GameEvent] = []
        self.history_limit = 1000
        self.processing = False
        self.batch_mode = False  # For batching multiple events
        self.debug_mode = False
        
        # Statystyki
        self.stats = {
            'total_events': 0,
            'events_by_category': {cat: 0 for cat in EventCategory},
            'events_by_type': {},
            'processing_time': 0
        }
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subskrypcja na konkretny typ wydarzenia.
        
        Args:
            event_type: Typ wydarzenia do nasłuchiwania
            handler: Funkcja obsługująca wydarzenie
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        if handler not in self.listeners[event_type]:
            self.listeners[event_type].append(handler)
            if self.debug_mode:
                print(f"[EventBus] Zarejestrowano handler dla {event_type}")
    
    def subscribe_category(self, category: EventCategory, handler: Callable) -> None:
        """Subskrypcja na całą kategorię wydarzeń.
        
        Args:
            category: Kategoria wydarzeń
            handler: Funkcja obsługująca
        """
        if category not in self.category_listeners:
            self.category_listeners[category] = []
        if handler not in self.category_listeners[category]:
            self.category_listeners[category].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Anulowanie subskrypcji.
        
        Args:
            event_type: Typ wydarzenia
            handler: Handler do usunięcia
        """
        if event_type in self.listeners and handler in self.listeners[event_type]:
            self.listeners[event_type].remove(handler)
    
    def emit(self, event: GameEvent) -> None:
        """Emisja wydarzenia.
        
        Args:
            event: Wydarzenie do wyemitowania
        """
        # Dodaj do kolejki
        self.event_queue.append(event)
        
        # Jeśli nie przetwarzamy już wydarzeń i nie jesteśmy w trybie batch, rozpocznij przetwarzanie
        if not self.processing and not self.batch_mode:
            self._process_queue()
    
    def emit_immediate(self, event: GameEvent) -> None:
        """Natychmiastowa emisja wydarzenia (omija kolejkę).
        
        Args:
            event: Wydarzenie do natychmiastowego przetworzenia
        """
        self._process_event(event)
    
    def start_batch(self) -> None:
        """Rozpocznij tryb batch - wydarzenia będą kolejkowane bez przetwarzania."""
        self.batch_mode = True
    
    def process_batch(self) -> None:
        """Zakończ tryb batch i przetwórz wszystkie zakolejkowane wydarzenia."""
        self.batch_mode = False
        if not self.processing:
            self._process_queue()
    
    def _process_queue(self) -> None:
        """Przetwarzanie kolejki wydarzeń."""
        self.processing = True
        
        # Sortuj całą kolejkę według priorytetu przed przetwarzaniem
        self.event_queue.sort(key=lambda e: e.priority.value, reverse=True)
        
        # Przetwórz wszystkie wydarzenia w kolejności
        while self.event_queue:
            event = self.event_queue.pop(0)
            
            if event.propagate:
                self._process_event(event)
        
        self.processing = False
    
    def _process_event(self, event: GameEvent) -> None:
        """Przetworzenie pojedynczego wydarzenia.
        
        Args:
            event: Wydarzenie do przetworzenia
        """
        # Aktualizuj statystyki
        self.stats['total_events'] += 1
        self.stats['events_by_category'][event.category] += 1
        if event.event_type not in self.stats['events_by_type']:
            self.stats['events_by_type'][event.event_type] = 0
        self.stats['events_by_type'][event.event_type] += 1
        
        # Dodaj do historii
        self.event_history.append(event)
        if len(self.event_history) > self.history_limit:
            self.event_history.pop(0)
        
        # Debug
        if self.debug_mode:
            print(f"[EventBus] Przetwarzanie: {event.event_type} [{event.category.value}]")
        
        # Wywołaj handlery dla konkretnego typu
        if event.event_type in self.listeners:
            for handler in self.listeners[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[EventBus] Błąd w handlerze dla {event.event_type}: {e}")
        
        # Wywołaj handlery dla kategorii
        if event.category in self.category_listeners:
            for handler in self.category_listeners[event.category]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[EventBus] Błąd w handlerze kategorii {event.category}: {e}")
    
    def get_history(self, category: Optional[EventCategory] = None,
                    event_type: Optional[str] = None,
                    limit: int = 100) -> List[GameEvent]:
        """Pobierz historię wydarzeń.
        
        Args:
            category: Filtruj po kategorii
            event_type: Filtruj po typie
            limit: Maksymalna liczba wydarzeń
            
        Returns:
            Lista wydarzeń z historii
        """
        history = self.event_history[-limit:]
        
        if category:
            history = [e for e in history if e.category == category]
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        
        return history
    
    def clear_history(self) -> None:
        """Wyczyść historię wydarzeń."""
        self.event_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Pobierz statystyki wydarzeń.
        
        Returns:
            Słownik ze statystykami
        """
        return self.stats.copy()
    
    def save_history(self, filepath: str) -> None:
        """Zapisz historię do pliku.
        
        Args:
            filepath: Ścieżka do pliku
        """
        history_data = [event.to_dict() for event in self.event_history]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)


# Globalny event bus
event_bus = EventBus()


# Pomocnicze funkcje emisji wydarzeń
def emit_combat_event(action: str, attacker: str, target: str, damage: int = 0, **kwargs):
    """Emituj wydarzenie bojowe."""
    event = GameEvent(
        event_type=f"combat_{action}",
        category=EventCategory.COMBAT,
        data={
            'action': action,
            'damage': damage,
            **kwargs
        },
        source=attacker,
        target=target,
        priority=EventPriority.HIGH
    )
    event_bus.emit(event)


def emit_movement_event(entity: str, from_location: str, to_location: str):
    """Emituj wydarzenie ruchu."""
    event = GameEvent(
        event_type="entity_moved",
        category=EventCategory.MOVEMENT,
        data={
            'from': from_location,
            'to': to_location
        },
        source=entity
    )
    event_bus.emit(event)


def emit_dialogue_event(speaker: str, listener: str, message: str, emotion: str = "neutral"):
    """Emituj wydarzenie dialogowe."""
    event = GameEvent(
        event_type="dialogue_spoken",
        category=EventCategory.DIALOGUE,
        data={
            'message': message,
            'emotion': emotion
        },
        source=speaker,
        target=listener
    )
    event_bus.emit(event)


def emit_trade_event(seller: str, buyer: str, item: str, price: int):
    """Emituj wydarzenie handlowe."""
    event = GameEvent(
        event_type="trade_completed",
        category=EventCategory.TRADE,
        data={
            'item': item,
            'price': price
        },
        source=seller,
        target=buyer
    )
    event_bus.emit(event)


def emit_quest_event(quest_id: str, status: str, player: str):
    """Emituj wydarzenie questowe."""
    event = GameEvent(
        event_type=f"quest_{status}",
        category=EventCategory.QUEST,
        data={
            'quest_id': quest_id,
            'status': status
        },
        source=player,
        priority=EventPriority.HIGH
    )
    event_bus.emit(event)


def emit_discovery_event(discoverer: str, discovery_type: str, location: str, details: Dict):
    """Emituj wydarzenie odkrycia."""
    event = GameEvent(
        event_type=f"discovered_{discovery_type}",
        category=EventCategory.DISCOVERY,
        data={
            'discovery_type': discovery_type,
            'location': location,
            'details': details
        },
        source=discoverer,
        priority=EventPriority.HIGH
    )
    event_bus.emit(event)


def emit_time_event(event_type: str, current_time: int, **kwargs):
    """Emituj wydarzenie czasowe."""
    event = GameEvent(
        event_type=event_type,
        category=EventCategory.TIME,
        data={
            'game_time': current_time,
            **kwargs
        }
    )
    event_bus.emit(event)