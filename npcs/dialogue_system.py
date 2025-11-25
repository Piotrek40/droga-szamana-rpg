#!/usr/bin/env python3
"""
System dialogów z wyborem odpowiedzi dla NPCów.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import json


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
    text: str  # Tekst opcji
    response: str  # Odpowiedź NPCa
    result: DialogueResult = DialogueResult.CONTINUE
    requirements: Dict[str, Any] = None  # Wymagania (umiejętności, przedmioty)
    effects: Dict[str, Any] = None  # Efekty wyboru (reputacja, przedmioty)
    next_node: str = None  # Następny węzeł dialogu


@dataclass
class DialogueNode:
    """Węzeł dialogu."""
    id: str
    npc_text: str  # Co mówi NPC
    options: List[DialogueOption]  # Dostępne opcje odpowiedzi
    
    def get_available_options(self, player) -> List[DialogueOption]:
        """Zwróć opcje spełniające wymagania."""
        available = []
        for option in self.options:
            if self._check_requirements(option.requirements, player):
                available.append(option)
        return available
    
    def _check_requirements(self, requirements: Dict, player) -> bool:
        """Sprawdź czy gracz spełnia wymagania."""
        if not requirements:
            return True
        
        for req_type, req_value in requirements.items():
            if req_type == "skill":
                skill_name, min_level = req_value
                if player.get_skill_level(skill_name) < min_level:
                    return False
            elif req_type == "item":
                if not player.has_item(req_value):
                    return False
            elif req_type == "reputation":
                faction, min_rep = req_value
                if player.get_reputation(faction) < min_rep:
                    return False
        
        return True


class DialogueSystem:
    """System zarządzania dialogami."""
    
    def __init__(self, game_state=None):
        """Inicjalizacja systemu dialogów."""
        self.game_state = game_state
        self.dialogue_trees = {}
        self.dialogue_data = self._load_dialogues_from_json()
        self._load_dialogues()
        
        # Wczytaj mapowanie NPCów z nowego pliku
        self.npc_dialogue_mapping = self._load_npc_mapping()
        self.npc_complete_data = self._load_npc_complete()
    
    def _load_npc_complete(self) -> Dict:
        """Wczytaj kompletne dane NPCów z nowego pliku."""
        try:
            with open('data/npc_complete.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Ostrzeżenie: Nie znaleziono pliku npc_complete.json")
            return {'npcs': {}, 'dialogue_mappings': {}}
    
    def _load_npc_mapping(self) -> Dict:
        """Wczytaj mapowanie NPCów z pliku JSON."""
        try:
            # Najpierw spróbuj z nowego pliku kompletnego
            with open('data/npc_complete.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Stwórz mapowanie ID -> dialogue_id
                mapping = {}
                
                # Z danych NPCów
                for npc_id, npc_data in data.get('npcs', {}).items():
                    dialogue_id = npc_data.get('dialogue_id', npc_id)
                    mapping[npc_id] = dialogue_id
                    # Dodaj też mapowanie dla samego dialogue_id
                    mapping[dialogue_id] = dialogue_id
                    
                    # Dodaj mapowanie dla dialogue_tree jeśli różne
                    if 'dialogue_tree' in npc_data:
                        mapping[npc_data['dialogue_tree']] = npc_data['dialogue_tree']
                
                # Z dialogue_mappings jeśli istnieją
                for dialogue_id, map_data in data.get('dialogue_mappings', {}).items():
                    mapping[dialogue_id] = dialogue_id
                    if 'npc_id' in map_data:
                        mapping[map_data['npc_id']] = dialogue_id
                
                return mapping
                
        except FileNotFoundError:
            # Fallback do starego pliku jeśli nowy nie istnieje
            try:
                with open('data/npc_mapping.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    mapping = {}
                    for npc_id, info in data['npc_mapping']['mappings'].items():
                        mapping[npc_id] = info['dialogue_id']
                        mapping[info['dialogue_id']] = info['dialogue_id']
                    return mapping
            except FileNotFoundError:
                print("Ostrzeżenie: Nie znaleziono plików mapowania, używam domyślnego")
                # Zwróć domyślne mapowanie
                return {
                    'piotr': 'gadatliwy_piotr',
                    'jozek': 'stary_jozef',
                    'anna': 'anna',
                    'brutus': 'brutus',
                    'marek': 'gruby_waldek',
                    'szczuply': 'szczuply',
                    'gadatliwy_piotr': 'gadatliwy_piotr',
                    'cichy_tomek': 'cichy_tomek',
                    'gruby_waldek': 'gruby_waldek',
                    'stary_jozef': 'stary_jozef'
                }
    
    def _load_dialogues_from_json(self) -> Dict:
        """Wczytaj dialogi z pliku JSON."""
        try:
            with open('data/dialogues.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Ostrzeżenie: Nie znaleziono pliku dialogues.json")
            return {'dialogue_trees': {}}
    
    def _load_dialogues(self):
        """Załaduj drzewa dialogowe z pliku JSON."""
        # Wczytaj wszystkie drzewa dialogowe z JSON
        dialogue_data = self.dialogue_data.get('dialogue_trees', {})
        
        for npc_id, tree_data in dialogue_data.items():
            dialogue_tree = {}
            
            for node_id, node_data in tree_data.items():
                # Konwertuj opcje z JSON na obiekty DialogueOption
                options = []
                for opt_data in node_data.get('options', []):
                    # Konwertuj result z stringa na enum
                    result_str = opt_data.get('result', 'continue')
                    if result_str == 'end':
                        result = DialogueResult.END
                    elif result_str == 'trade':
                        result = DialogueResult.TRADE
                    elif result_str == 'fight':
                        result = DialogueResult.FIGHT
                    elif result_str == 'quest':
                        result = DialogueResult.QUEST
                    else:
                        result = DialogueResult.CONTINUE
                    
                    option = DialogueOption(
                        text=opt_data.get('text', ''),
                        response=opt_data.get('response', ''),
                        result=result,
                        requirements=opt_data.get('requirements'),
                        effects=opt_data.get('effects'),
                        next_node=opt_data.get('next_node')
                    )
                    options.append(option)
                
                # Stwórz węzeł dialogu
                node = DialogueNode(
                    id=node_data.get('id', node_id),
                    npc_text=node_data.get('npc_text', ''),
                    options=options
                )
                dialogue_tree[node_id] = node
            
            self.dialogue_trees[npc_id] = dialogue_tree
        
        # Jeśli nie ma dialogów w JSON, dodaj fallback
        if not self.dialogue_trees:
            self._load_fallback_dialogues()
    
    def _load_fallback_dialogues(self):
        """Załaduj podstawowe dialogi jeśli JSON jest pusty."""
        # Podstawowy dialog dla NPCów bez zdefiniowanych dialogów
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
    
    def start_dialogue(self, npc_id: str, player, npc_name: str = None) -> Tuple[str, List[DialogueOption]]:
        """Rozpocznij dialog z NPCem."""
        # Mapuj ID NPCa na ID dialogu
        dialogue_id = self.npc_dialogue_mapping.get(npc_id, npc_id)
        
        # Dodatkowe mapowanie bazujące na nazwie NPCa
        if npc_name:
            npc_name_lower = npc_name.lower()
            # Mapowanie na podstawie nazwy
            if 'piotr' in npc_name_lower or 'gadatliwy' in npc_name_lower:
                dialogue_id = 'gadatliwy_piotr'
            elif 'józek' in npc_name_lower or 'jozek' in npc_name_lower or 'józef' in npc_name_lower:
                dialogue_id = 'stary_jozef'
            elif 'anna' in npc_name_lower:
                dialogue_id = 'anna'  # Anna ma własne dialogi
            elif 'tomek' in npc_name_lower or 'cichy' in npc_name_lower:
                dialogue_id = 'cichy_tomek'
            elif 'brutus' in npc_name_lower:
                dialogue_id = 'brutus'
            elif 'marek' in npc_name_lower or 'gruby' in npc_name_lower or 'waldek' in npc_name_lower:
                dialogue_id = 'gruby_waldek'  # Marek używa dialogów Waldka
        
        # Sprawdź czy NPC ma dedykowane dialogi
        if dialogue_id not in self.dialogue_trees:
            # Użyj domyślnego dialogu jeśli nie ma dedykowanego
            if "default" in self.dialogue_trees:
                tree = self.dialogue_trees["default"]
            else:
                return "Ten NPC nie ma dialogu.", []
        else:
            tree = self.dialogue_trees[dialogue_id]  # Użyj dialogue_id, nie npc_id!
        
        node = tree.get("greeting")
        
        if not node:
            return "Błąd dialogu.", []
        
        available_options = node.get_available_options(player)
        return node.npc_text, available_options
    
    def process_choice(self, npc_id: str, node_id: str, choice_index: int, player) -> Tuple[str, Optional[str], DialogueResult, List[DialogueOption], Optional[str]]:
        """Przetwórz wybór gracza."""
        # Mapuj ID NPCa na ID dialogu
        dialogue_id = self.npc_dialogue_mapping.get(npc_id, npc_id)
        
        # Sprawdź czy używamy domyślnego dialogu
        if dialogue_id not in self.dialogue_trees:
            if "default" in self.dialogue_trees:
                tree = self.dialogue_trees["default"]
            else:
                return "Błąd dialogu.", None, DialogueResult.END, [], None
        else:
            tree = self.dialogue_trees[dialogue_id]
        
        node = tree.get(node_id)
        
        if not node:
            return "Błąd dialogu.", None, DialogueResult.END, [], None
        
        available_options = node.get_available_options(player)
        
        if choice_index < 0 or choice_index >= len(available_options):
            return "Nieprawidłowy wybór.", None, DialogueResult.END, [], None
        
        chosen = available_options[choice_index]
        
        # Zastosuj efekty
        if chosen.effects:
            self._apply_effects(chosen.effects, player)
        
        # Jeśli jest następny węzeł, pobierz go
        next_options = []
        if chosen.next_node and chosen.next_node in tree:
            next_node = tree[chosen.next_node]
            next_options = next_node.get_available_options(player)
            return chosen.response, next_node.npc_text, chosen.result, next_options, chosen.next_node
        
        return chosen.response, None, chosen.result, [], None
    
    def get_dialogue(self, npc_id: str, context: str = "greeting") -> str:
        """Pobierz odpowiedź dialogową NPCa.
        
        Args:
            npc_id: ID NPCa
            context: Kontekst dialogu (greeting, farewell, trade, etc.)
            
        Returns:
            Tekst odpowiedzi NPCa
        """
        # Spróbuj znaleźć specyficzny dialog dla NPCa
        if npc_id in self.dialogue_trees:
            tree = self.dialogue_trees[npc_id]
            if 'start' in tree:
                node = tree['start']
                if isinstance(node, DialogueNode):
                    return node.npc_text
                elif isinstance(node, dict) and 'npc_text' in node:
                    return node['npc_text']
        
        # Jeśli nie ma specyficznego dialogu, zwróć domyślny
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
    
    def _apply_effects(self, effects: Dict, player):
        """Zastosuj efekty wyboru dialogowego."""
        for effect_type, effect_value in effects.items():
            if effect_type == "knowledge":
                # Dodaj wiedzę
                if hasattr(player, 'add_knowledge'):
                    player.add_knowledge(effect_value)
            elif effect_type == "reputation":
                # Zmień reputację
                faction, amount = effect_value
                if hasattr(player, 'change_reputation'):
                    player.change_reputation(faction, amount)
            elif effect_type == "item":
                # Daj przedmiot
                if hasattr(player, 'add_item'):
                    player.add_item(effect_value)
            elif effect_type == "quest":
                # Rozpocznij zadanie
                if hasattr(player, 'start_quest'):
                    player.start_quest(effect_value)