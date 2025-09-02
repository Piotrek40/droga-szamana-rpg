"""
Utilities wspólne dla całego projektu Droga Szamana RPG.
Centralizuje powtarzające się wzorce kodu.
"""

import logging
import time
from typing import Any, Dict, Optional, List, Union, Type
from abc import ABC, abstractmethod


class SerializableMixin:
    """Mixin dodający standardowe metody serializacji."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Standardowa serializacja do słownika."""
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue  # Pomijaj prywatne atrybuty
            
            if hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                result[key] = [
                    item.to_dict() if hasattr(item, 'to_dict') else item 
                    for item in value
                ]
            elif isinstance(value, dict):
                result[key] = {
                    k: v.to_dict() if hasattr(v, 'to_dict') else v 
                    for k, v in value.items()
                }
            else:
                result[key] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SerializableMixin':
        """Standardowa deserializacja ze słownika."""
        # Implementacja bazowa - podklasy mogą nadpisać
        instance = cls.__new__(cls)
        for key, value in data.items():
            setattr(instance, key, value)
        return instance


class UpdateableMixin:
    """Mixin dodający standardowe metody aktualizacji."""
    
    def __init__(self):
        self._last_update = time.time()
    
    def update(self, delta_time: float = None, **context) -> None:
        """Standardowa metoda aktualizacji."""
        if delta_time is None:
            current_time = time.time()
            delta_time = current_time - self._last_update
            self._last_update = current_time
        
        self._do_update(delta_time, **context)
    
    @abstractmethod
    def _do_update(self, delta_time: float, **context) -> None:
        """Metoda do implementacji w podklasach."""
        pass


class SafeMethodMixin:
    """Mixin dodający bezpieczne wywoływanie metod z obsługą błędów."""
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def safe_call(self, method_name: str, *args, default=None, **kwargs):
        """Bezpiecznie wywołuje metodę z obsługą błędów."""
        try:
            method = getattr(self, method_name)
            return method(*args, **kwargs)
        except (AttributeError, TypeError) as e:
            self._logger.debug(f"Metoda {method_name} niedostępna: {e}")
            return default
        except Exception as e:
            self._logger.error(f"Błąd w metodzie {method_name}: {e}")
            return default
    
    def safe_get_attr(self, attr_name: str, default=None):
        """Bezpiecznie pobiera atrybut."""
        return getattr(self, attr_name, default)
    
    def safe_set_attr(self, attr_name: str, value: Any) -> bool:
        """Bezpiecznie ustawia atrybut."""
        try:
            setattr(self, attr_name, value)
            return True
        except Exception as e:
            self._logger.error(f"Błąd ustawiania {attr_name}: {e}")
            return False


def safe_import(module_name: str, class_name: str = None, default=None):
    """Bezpieczny import modułu/klasy."""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        return getattr(module, class_name) if class_name else module
    except (ImportError, AttributeError):
        return default


def normalize_id(text: str) -> str:
    """Normalizuje tekst do ID (snake_case, bez polskich znaków)."""
    import re
    # Mapa polskich znaków
    polish_chars = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
        'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    
    # Zamień polskie znaki
    for pl, en in polish_chars.items():
        text = text.replace(pl, en)
    
    # Konwertuj na snake_case
    text = re.sub(r'([A-Z])', r'_\1', text).lower()
    text = re.sub(r'[^a-z0-9_]', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    
    return text


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Ogranicza wartość do zakresu min-max."""
    return max(min_val, min(value, max_val))


def lerp(a: float, b: float, t: float) -> float:
    """Interpolacja liniowa między a i b."""
    return a + (b - a) * clamp(t, 0.0, 1.0)


class EventMixin:
    """Mixin dodający standardową obsługę eventów."""
    
    def __init__(self):
        self._event_handlers = {}
    
    def on(self, event_type: str, handler):
        """Rejestruje handler dla eventu."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def emit(self, event_type: str, *args, **kwargs):
        """Emituje event."""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger = logging.getLogger(self.__class__.__name__)
                    logger.error(f"Błąd w handlerze {event_type}: {e}")


class ConfigMixin:
    """Mixin dodający obsługę konfiguracji."""
    
    def __init__(self):
        self._config = {}
    
    def set_config(self, key: str, value: Any) -> None:
        """Ustawia wartość konfiguracji."""
        self._config[key] = value
    
    def get_config(self, key: str, default=None) -> Any:
        """Pobiera wartość konfiguracji."""
        return self._config.get(key, default)
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """Aktualizuje konfigurację."""
        self._config.update(config_dict)


# Funkcje utility
def format_time(seconds: float) -> str:
    """Formatuje czas w sekundach do czytelnej formy."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def format_number(number: Union[int, float], precision: int = 1) -> str:
    """Formatuje liczbę do czytelnej formy."""
    if isinstance(number, float):
        return f"{number:.{precision}f}"
    elif number >= 1000000:
        return f"{number/1000000:.{precision}f}M"
    elif number >= 1000:
        return f"{number/1000:.{precision}f}K"
    else:
        return str(number)


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Głębokie scalanie słowników."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result