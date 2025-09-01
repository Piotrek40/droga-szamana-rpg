#!/usr/bin/env python3
"""
Inteligentny menedżer kontekstu gry.
Zarządza spójnością między wszystkimi systemami.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re


@dataclass
class ContextualEntity:
    """Encja w kontekście gry."""
    id: str
    name: str
    display_name: str
    type: str  # 'npc', 'item', 'object', 'location'
    location: str
    available: bool = True
    interaction_commands: List[str] = None
    
    def __post_init__(self):
        if self.interaction_commands is None:
            self.interaction_commands = []


class ContextManager:
    """Menedżer kontekstu zapewniający spójność między systemami."""
    
    def __init__(self, game_state):
        """Inicjalizacja menedżera kontekstu."""
        self.game_state = game_state
        self.current_context = {}
        self._entity_cache = {}
        
    def get_current_context(self) -> Dict[str, Any]:
        """Pobierz pełny kontekst obecnej sytuacji."""
        context = {
            'location': self._get_location_context(),
            'npcs': self._get_npcs_in_location(),
            'items': self._get_items_in_location(),
            'objects': self._get_interactive_objects(),
            'exits': self._get_available_exits(),
            'player': self._get_player_context(),
            'available_actions': self._get_available_actions()
        }
        self.current_context = context
        return context
    
    def _get_location_context(self) -> Dict[str, Any]:
        """Pobierz kontekst lokacji."""
        if not self.game_state.prison:
            return {}
        
        location = self.game_state.prison.get_current_location()
        if not location:
            return {}
        
        return {
            'id': self.game_state.current_location,
            'name': location.name,
            'description': location.get_description(
                self.game_state.time_system,
                self.game_state.weather_system
            ),
            'type': location.type.value if hasattr(location, 'type') else 'unknown',
            'visited': location.visited if hasattr(location, 'visited') else False
        }
    
    def _get_npcs_in_location(self) -> List[ContextualEntity]:
        """Pobierz NPCów w obecnej lokacji."""
        npcs = []
        
        if not self.game_state.npc_manager:
            return npcs
        
        current_loc = self.game_state.current_location
        
        for npc_id, npc in self.game_state.npc_manager.npcs.items():
            # Sprawdź czy NPC jest w tej lokacji
            if hasattr(npc, 'current_location') and npc.current_location == current_loc:
                # Utwórz różne warianty nazwy do rozpoznawania
                base_name = npc.name.lower()
                first_name = base_name.split()[0] if ' ' in base_name else base_name
                
                entity = ContextualEntity(
                    id=npc_id,
                    name=base_name,
                    display_name=npc.name,
                    type='npc',
                    location=current_loc,
                    available=True,
                    interaction_commands=[
                        f"rozmawiaj {base_name}",
                        f"rozmawiaj {first_name}",
                        f"rozmawiaj {npc_id}",
                        f"zbadaj {base_name}",
                        f"zbadaj {first_name}",
                        f"atakuj {base_name}",
                        f"atakuj {first_name}"
                    ]
                )
                npcs.append(entity)
                self._entity_cache[npc_id] = entity
                self._entity_cache[base_name] = entity
                self._entity_cache[first_name] = entity
        
        return npcs
    
    def _get_items_in_location(self) -> List[ContextualEntity]:
        """Pobierz przedmioty w obecnej lokacji."""
        items = []
        
        if not self.game_state.prison:
            return items
        
        location = self.game_state.prison.get_current_location()
        if not location or not hasattr(location, 'items'):
            return items
        
        current_loc = self.game_state.current_location
        
        for item in location.items:
            # Obsłuż różne formaty przedmiotów
            if hasattr(item, 'name'):
                item_name = item.name
                item_id = getattr(item, 'id', item_name.lower().replace(' ', '_'))
            elif isinstance(item, dict):
                item_name = item.get('name', 'nieznany')
                item_id = item.get('id', item_name.lower().replace(' ', '_'))
            elif isinstance(item, str):
                item_name = item
                item_id = item.lower().replace(' ', '_')
            else:
                continue
            
            base_name = item_name.lower()
            
            entity = ContextualEntity(
                id=item_id,
                name=base_name,
                display_name=item_name,
                type='item',
                location=current_loc,
                available=True,
                interaction_commands=[
                    f"weź {base_name}",
                    f"weź {item_id}",
                    f"zbadaj {base_name}",
                    f"zbadaj {item_id}",
                    f"użyj {base_name}",
                ]
            )
            items.append(entity)
            self._entity_cache[item_id] = entity
            self._entity_cache[base_name] = entity
        
        return items
    
    def _get_interactive_objects(self) -> List[ContextualEntity]:
        """Pobierz obiekty interaktywne w lokacji."""
        objects = []
        
        if not self.game_state.prison:
            return objects
        
        location = self.game_state.prison.get_current_location()
        if not location:
            return objects
        
        current_loc = self.game_state.current_location
        
        # Pobierz obiekty interaktywne
        if hasattr(location, 'interactive_objects'):
            for obj in location.interactive_objects:
                obj_name = obj if isinstance(obj, str) else str(obj)
                obj_id = obj_name.lower().replace(' ', '_')
                
                entity = ContextualEntity(
                    id=obj_id,
                    name=obj_name.lower(),
                    display_name=obj_name,
                    type='object',
                    location=current_loc,
                    available=True,
                    interaction_commands=[
                        f"zbadaj {obj_name.lower()}",
                        f"zbadaj {obj_id}",
                        f"użyj {obj_name.lower()}",
                    ]
                )
                objects.append(entity)
                self._entity_cache[obj_id] = entity
                self._entity_cache[obj_name.lower()] = entity
        
        return objects
    
    def _get_available_exits(self) -> Dict[str, str]:
        """Pobierz dostępne wyjścia."""
        if not self.game_state.prison:
            return {}
        
        location = self.game_state.prison.get_current_location()
        if not location:
            return {}
        
        return location.connections if hasattr(location, 'connections') else {}
    
    def _get_player_context(self) -> Dict[str, Any]:
        """Pobierz kontekst gracza."""
        if not self.game_state.player:
            return {}
        
        player = self.game_state.player
        return {
            'name': player.name,
            'health': player.combat_stats.health if hasattr(player, 'combat_stats') else 100,
            'max_health': player.combat_stats.max_health if hasattr(player, 'combat_stats') else 100,
            'state': player.state.value if hasattr(player, 'state') else 'normalny',
            'can_fight': not player.is_incapacitated() if hasattr(player, 'is_incapacitated') else True,
            'inventory_count': len(player.equipment.items) if hasattr(player, 'equipment') else 0
        }
    
    def _get_available_actions(self) -> List[str]:
        """Pobierz listę dostępnych akcji."""
        actions = ['rozejrzyj', 'status', 'ekwipunek', 'umiejętności', 'pomoc', 'mapa']
        
        # Dodaj kierunki ruchu
        exits = self._get_available_exits()
        for direction in exits.keys():
            actions.append(f"idź {direction}")
            actions.append(direction)  # Skrót
        
        # Dodaj akcje dla NPCów
        for npc in self._get_npcs_in_location():
            actions.extend(npc.interaction_commands)
        
        # Dodaj akcje dla przedmiotów
        for item in self._get_items_in_location():
            actions.extend(item.interaction_commands)
        
        # Dodaj akcje dla obiektów
        for obj in self._get_interactive_objects():
            actions.extend(obj.interaction_commands)
        
        # Jeśli jest coś do przeszukania
        if self._get_items_in_location() or self._get_interactive_objects():
            actions.append('szukaj')
        
        return list(set(actions))  # Usuń duplikaty
    
    def validate_command(self, command: str) -> tuple[bool, str]:
        """Waliduj czy komenda jest możliwa w obecnym kontekście."""
        # Pobierz świeży kontekst
        context = self.get_current_context()
        
        # Podziel komendę
        parts = command.lower().strip().split()
        if not parts:
            return False, "Brak komendy"
        
        action = parts[0]
        target = ' '.join(parts[1:]) if len(parts) > 1 else None
        
        # Sprawdź podstawowe komendy
        if action in ['rozejrzyj', 'status', 'ekwipunek', 'umiejętności', 'pomoc', 'mapa', 'szukaj']:
            return True, ""
        
        # Sprawdź ruch
        if action in ['idź', 'idziesz', 'idz']:
            if target and target in context['exits']:
                return True, ""
            else:
                available = list(context['exits'].keys())
                if available:
                    return False, f"Nie możesz iść w tym kierunku. Dostępne: {', '.join(available)}"
                else:
                    return False, "Nie ma żadnych wyjść z tej lokacji"
        
        # Skrót kierunku
        if action in ['północ', 'południe', 'wschód', 'zachód', 'góra', 'dół']:
            if action in context['exits']:
                return True, ""
            else:
                available = list(context['exits'].keys())
                if available:
                    return False, f"Nie możesz iść w tym kierunku. Dostępne: {', '.join(available)}"
                else:
                    return False, "Nie ma żadnych wyjść z tej lokacji"
        
        # Sprawdź interakcje z NPCami
        if action in ['rozmawiaj', 'mów', 'gadaj', 'powiedz']:
            if not target:
                npcs = context['npcs']
                if npcs:
                    names = [npc.display_name for npc in npcs]
                    return False, f"Z kim chcesz rozmawiać? Dostępni: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nikogo do rozmowy"
            
            # Znajdź NPC
            npc_found = self._find_entity_by_name(target, 'npc')
            if npc_found:
                return True, ""
            else:
                npcs = context['npcs']
                if npcs:
                    names = [npc.display_name for npc in npcs]
                    return False, f"Nie ma tu '{target}'. Dostępni: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nikogo do rozmowy"
        
        # Sprawdź zbieranie przedmiotów
        if action in ['weź', 'wez', 'podnieś', 'podnies']:
            if not target:
                items = context['items']
                if items:
                    names = [item.display_name for item in items]
                    return False, f"Co chcesz wziąć? Dostępne: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nic do wzięcia"
            
            # Znajdź przedmiot
            item_found = self._find_entity_by_name(target, 'item')
            if item_found:
                return True, ""
            else:
                items = context['items']
                if items:
                    names = [item.display_name for item in items]
                    return False, f"Nie ma tu '{target}'. Dostępne: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nic do wzięcia"
        
        # Sprawdź badanie
        if action in ['zbadaj', 'sprawdź', 'sprawdz', 'obejrzyj']:
            if not target:
                entities = context['npcs'] + context['items'] + context['objects']
                if entities:
                    names = [e.display_name for e in entities]
                    return False, f"Co chcesz zbadać? Dostępne: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nic do zbadania"
            
            # Znajdź cel
            entity_found = self._find_entity_by_name(target)
            if entity_found:
                return True, ""
            else:
                entities = context['npcs'] + context['items'] + context['objects']
                if entities:
                    names = [e.display_name for e in entities]
                    return False, f"Nie możesz zbadać '{target}'. Dostępne: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nic do zbadania"
        
        # Sprawdź atak
        if action in ['atakuj', 'zaatakuj', 'bij', 'uderz']:
            if not context['player']['can_fight']:
                return False, "Jesteś zbyt osłabiony aby walczyć!"
            
            if not target:
                npcs = context['npcs']
                if npcs:
                    names = [npc.display_name for npc in npcs]
                    return False, f"Kogo chcesz zaatakować? Dostępni: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nikogo do zaatakowania"
            
            # Znajdź NPC
            npc_found = self._find_entity_by_name(target, 'npc')
            if npc_found:
                return True, ""
            else:
                npcs = context['npcs']
                if npcs:
                    names = [npc.display_name for npc in npcs]
                    return False, f"Nie możesz zaatakować '{target}'. Dostępni: {', '.join(names)}"
                else:
                    return False, "Nie ma tu nikogo do zaatakowania"
        
        # Domyślnie pozwól - może to być specjalna komenda
        return True, ""
    
    def _find_entity_by_name(self, name: str, entity_type: str = None) -> Optional[ContextualEntity]:
        """Znajdź encję po nazwie."""
        name_lower = name.lower().strip()
        
        # Sprawdź cache
        if name_lower in self._entity_cache:
            entity = self._entity_cache[name_lower]
            if entity_type is None or entity.type == entity_type:
                return entity
        
        # Szukaj w obecnym kontekście
        context = self.current_context if self.current_context else self.get_current_context()
        
        # Przeszukaj wszystkie encje
        all_entities = []
        if entity_type in [None, 'npc']:
            all_entities.extend(context.get('npcs', []))
        if entity_type in [None, 'item']:
            all_entities.extend(context.get('items', []))
        if entity_type in [None, 'object']:
            all_entities.extend(context.get('objects', []))
        
        # Szukaj dokładnego dopasowania
        for entity in all_entities:
            if entity.name == name_lower or entity.id == name_lower:
                return entity
            # Sprawdź też pierwsze słowo nazwy
            if ' ' in entity.name:
                first_word = entity.name.split()[0]
                if first_word == name_lower:
                    return entity
        
        # Szukaj częściowego dopasowania
        for entity in all_entities:
            if name_lower in entity.name or name_lower in entity.id:
                return entity
        
        return None
    
    def get_normalized_target(self, command: str) -> tuple[str, str]:
        """Normalizuj komendę i cel do właściwego formatu."""
        parts = command.lower().strip().split()
        if not parts:
            return "", ""
        
        action = parts[0]
        target = ' '.join(parts[1:]) if len(parts) > 1 else ""
        
        # Jeśli jest cel, znajdź właściwą encję
        if target:
            entity = self._find_entity_by_name(target)
            if entity:
                # Zwróć właściwy identyfikator dla różnych akcji
                if action in ['rozmawiaj', 'mów', 'gadaj']:
                    # Dla rozmowy użyj pierwszego słowa lub id
                    if ' ' in entity.name:
                        target = entity.name.split()[0]
                    else:
                        target = entity.id
                elif action in ['weź', 'wez', 'podnieś']:
                    # Dla przedmiotów użyj pełnej nazwy
                    target = entity.name
                elif action in ['zbadaj', 'sprawdź', 'obejrzyj']:
                    # Dla badania użyj nazwy
                    target = entity.name
                elif action in ['atakuj', 'bij', 'uderz']:
                    # Dla ataku użyj pierwszego słowa
                    if ' ' in entity.name:
                        target = entity.name.split()[0]
                    else:
                        target = entity.id
        
        return action, target