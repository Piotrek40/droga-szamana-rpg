"""
Base classes for serialization - unifies save/load patterns across the project.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, Union
import logging
import json
import os


class Serializable(ABC):
    """Base class for all serializable objects."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary for serialization."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        """Create object from dictionary."""
        pass
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Serializable':
        """Create object from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def save_to_file(self, filepath: str) -> bool:
        """Save object to file."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            logging.error(f"Failed to save to {filepath}: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['Serializable']:
        """Load object from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return cls.from_json(f.read())
        except Exception as e:
            logging.error(f"Failed to load from {filepath}: {e}")
            return None


class AutoSerializable(Serializable):
    """Automatically handles serialization for simple objects."""
    
    def __init__(self):
        self._excluded_fields = {'_excluded_fields', '_logger'}
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def to_dict(self) -> Dict[str, Any]:
        """Automatic serialization."""
        result = {}
        
        for key, value in self.__dict__.items():
            if key in self._excluded_fields or key.startswith('_'):
                continue
            
            if isinstance(value, Serializable):
                result[key] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                result[key] = [
                    item.to_dict() if isinstance(item, Serializable) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                result[key] = {
                    k: v.to_dict() if isinstance(v, Serializable) else v
                    for k, v in value.items()
                }
            elif isinstance(value, (str, int, float, bool, type(None))):
                result[key] = value
            else:
                # Try to convert to string for unknown types
                try:
                    result[key] = str(value)
                except:
                    self._logger.warning(f"Skipping field {key} - cannot serialize {type(value)}")
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoSerializable':
        """Automatic deserialization."""
        instance = cls.__new__(cls)
        instance._excluded_fields = {'_excluded_fields', '_logger'}
        instance._logger = logging.getLogger(cls.__name__)
        
        for key, value in data.items():
            setattr(instance, key, value)
        
        return instance


class GameStateManager:
    """Unified manager for game state save/load operations."""
    
    def __init__(self, save_directory: str = "saves"):
        self.save_directory = save_directory
        self.logger = logging.getLogger(__name__)
        os.makedirs(save_directory, exist_ok=True)
    
    def save_state(self, state_object: Serializable, slot: Union[int, str], 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save game state to slot."""
        try:
            slot_dir = os.path.join(self.save_directory, f"slot_{slot}")
            os.makedirs(slot_dir, exist_ok=True)
            
            # Save main state
            state_file = os.path.join(slot_dir, "game_state.json")
            if not state_object.save_to_file(state_file):
                return False
            
            # Save metadata
            if metadata:
                metadata_file = os.path.join(slot_dir, "metadata.json")
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Game saved to slot {slot}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save to slot {slot}: {e}")
            return False
    
    def load_state(self, state_class: Type[Serializable], slot: Union[int, str]) -> Optional[Serializable]:
        """Load game state from slot."""
        try:
            slot_dir = os.path.join(self.save_directory, f"slot_{slot}")
            state_file = os.path.join(slot_dir, "game_state.json")
            
            if not os.path.exists(state_file):
                self.logger.warning(f"Save slot {slot} not found")
                return None
            
            state = state_class.load_from_file(state_file)
            if state:
                self.logger.info(f"Game loaded from slot {slot}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to load from slot {slot}: {e}")
            return None
    
    def get_save_metadata(self, slot: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get metadata for save slot."""
        try:
            slot_dir = os.path.join(self.save_directory, f"slot_{slot}")
            metadata_file = os.path.join(slot_dir, "metadata.json")
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load metadata for slot {slot}: {e}")
            return None
    
    def list_saves(self) -> List[Dict[str, Any]]:
        """List all available save slots."""
        saves = []
        
        try:
            for item in os.listdir(self.save_directory):
                if item.startswith("slot_"):
                    slot_id = item[5:]  # Remove "slot_" prefix
                    slot_dir = os.path.join(self.save_directory, item)
                    state_file = os.path.join(slot_dir, "game_state.json")
                    
                    if os.path.exists(state_file):
                        save_info = {
                            'slot': slot_id,
                            'exists': True,
                            'modified': os.path.getmtime(state_file),
                            'metadata': self.get_save_metadata(slot_id)
                        }
                        saves.append(save_info)
            
            return sorted(saves, key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list saves: {e}")
            return []
    
    def delete_save(self, slot: Union[int, str]) -> bool:
        """Delete save slot."""
        try:
            import shutil
            slot_dir = os.path.join(self.save_directory, f"slot_{slot}")
            
            if os.path.exists(slot_dir):
                shutil.rmtree(slot_dir)
                self.logger.info(f"Deleted save slot {slot}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete slot {slot}: {e}")
            return False


# Global instance for convenience
save_manager = GameStateManager()