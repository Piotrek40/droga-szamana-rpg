"""
Silnik questów emergentnych dla więzienia w Droga Szamana RPG.
System tworzy organiczne sytuacje wynikające ze stanu świata.
"""

import random
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

from core.event_bus import event_bus, GameEvent, EventCategory, EventPriority


class QuestState(Enum):
    """Stan questa emergentnego."""
    DORMANT = "dormant"           # Quest nieaktywny, czeka na warunki
    SEEDING = "seeding"           # Pierwsze ślady pojawiają się w świecie
    DISCOVERABLE = "discoverable"  # Można odkryć przez eksplorację
    ACTIVE = "active"             # Gracz odkrył sytuację
    INVESTIGATING = "investigating" # Gracz zbiera informacje
    RESOLVED = "resolved"         # Rozwiązany pozytywnie
    FAILED = "failed"            # Nieudany lub zignorowany
    CONSEQUENCING = "consequencing" # Konsekwencje się rozgrywają


class DiscoveryMethod(Enum):
    """Sposoby odkrycia questa."""
    OVERHEARD = "overheard"       # Podsłuchana rozmowa
    WITNESSED = "witnessed"       # Zobaczone wydarzenie
    FOUND = "found"              # Znaleziony przedmiot/ślad
    TOLD = "told"                # NPC powiedział (wymaga relacji)
    STUMBLED = "stumbled"        # Przypadkowe natrafienie
    CONSEQUENCE = "consequence"   # Wynik poprzedniego questa
    ENVIRONMENTAL = "environmental" # Zmiana w otoczeniu


class QuestObjective:
    """Podstawowy cel questa dla testów."""
    
    def __init__(self, objective_id: str, description: str, completion_check=None):
        self.id = objective_id
        self.description = description
        self.completion_check = completion_check
        self.completed = False
    
    def check_completion(self, world_state: dict) -> bool:
        """Sprawdza czy cel został osiągnięty."""
        if self.completion_check:
            return self.completion_check(world_state)
        return False


@dataclass
class QuestSeed:
    """Ziarno questa - warunki aktywacji i pierwsze ślady."""
    quest_id: str
    name: str
    activation_conditions: Dict[str, Any]
    discovery_methods: List[DiscoveryMethod]
    initial_clues: Dict[str, str]  # lokacja -> opis
    time_sensitive: bool = False
    expiry_hours: int = 72
    priority: int = 5  # 1-10, wyższy = ważniejszy
    
    def check_activation(self, world_state: Dict) -> bool:
        """Sprawdza czy warunki aktywacji są spełnione."""
        for key, required_value in self.activation_conditions.items():
            if '.' in key:  # Nested dict access
                keys = key.split('.')
                current = world_state
                for k in keys[:-1]:
                    if k not in current:
                        return False
                    current = current[k]
                if keys[-1] not in current:
                    return False
                actual_value = current[keys[-1]]
            else:
                if key not in world_state:
                    return False
                actual_value = world_state[key]
            
            # Porównanie wartości
            if isinstance(required_value, dict):
                operator = required_value.get('operator', '==')
                value = required_value['value']
                if operator == '<':
                    if not actual_value < value:
                        return False
                elif operator == '>':
                    if not actual_value > value:
                        return False
                elif operator == '<=':
                    if not actual_value <= value:
                        return False
                elif operator == '>=':
                    if not actual_value >= value:
                        return False
                elif operator == '!=':
                    if not actual_value != value:
                        return False
                elif operator == 'in':
                    if actual_value not in value:
                        return False
                elif operator == 'contains':
                    if value not in actual_value:
                        return False
            else:
                if actual_value != required_value:
                    return False
        
        return True


@dataclass
class Investigation:
    """Śledzenie postępu śledztwa gracza."""
    quest_id: str
    discovered_clues: List[str] = field(default_factory=list)
    interrogated_npcs: List[str] = field(default_factory=list)
    visited_locations: List[str] = field(default_factory=list)
    player_theories: List[str] = field(default_factory=list)
    evidence_items: List[str] = field(default_factory=list)
    
    def add_clue(self, clue_id: str) -> bool:
        """Dodaje odkrytą wskazówkę."""
        if clue_id not in self.discovered_clues:
            self.discovered_clues.append(clue_id)
            return True
        return False
    
    def get_completion_percentage(self, total_clues: int) -> float:
        """Zwraca procent odkrytych wskazówek."""
        if total_clues == 0:
            return 0.0
        return (len(self.discovered_clues) / total_clues) * 100


@dataclass
class ConsequenceEvent:
    """Wydarzenie będące konsekwencją questa."""
    event_id: str
    quest_id: str
    trigger_time: datetime
    event_type: str  # immediate, delayed, recurring
    world_changes: Dict[str, Any]
    npc_reactions: Dict[str, str]
    new_quest_seeds: List[str]
    description: str
    
    def is_due(self, current_time: datetime) -> bool:
        """Sprawdza czy czas na wykonanie konsekwencji."""
        return current_time >= self.trigger_time


class QuestBranch:
    """Gałąź decyzyjna w queście."""
    def __init__(self, branch_id: str, description: str):
        self.branch_id = branch_id
        self.description = description
        self.requirements: Dict[str, Any] = {}
        self.actions: List[Callable] = []
        self.consequences: Dict[str, Any] = {}
        self.dialogue_options: Dict[str, str] = {}
        self.skill_checks: Dict[str, int] = {}
        
    def add_requirement(self, req_type: str, value: Any):
        """Dodaje wymaganie do wybrania tej gałęzi."""
        self.requirements[req_type] = value
        
    def add_consequence(self, cons_type: str, value: Any):
        """Dodaje konsekwencję wybrania tej gałęzi."""
        self.consequences[cons_type] = value
        
    def can_choose(self, player_state: Dict) -> bool:
        """Sprawdza czy gracz może wybrać tę gałąź."""
        for req_type, req_value in self.requirements.items():
            if req_type == 'skill':
                skill_name, min_level = req_value
                if player_state.get('skills', {}).get(skill_name, 0) < min_level:
                    return False
            elif req_type == 'item':
                if req_value not in player_state.get('inventory', []):
                    return False
            elif req_type == 'reputation':
                faction, min_rep = req_value
                if player_state.get('reputation', {}).get(faction, 0) < min_rep:
                    return False
            elif req_type == 'quest_complete':
                if req_value not in player_state.get('completed_quests', []):
                    return False
        return True


class EmergentQuest:
    """Pełny quest emergentny z wszystkimi mechanizmami."""
    def __init__(self, quest_id: str, seed: QuestSeed):
        self.quest_id = quest_id
        self.seed = seed
        self.state = QuestState.DORMANT
        self.investigation = Investigation(quest_id)
        self.branches: Dict[str, QuestBranch] = {}
        self.current_branch: Optional[str] = None
        self.consequences: List[ConsequenceEvent] = []
        self.discovery_dialogue: Dict[str, List[str]] = {}
        self.resolution_paths: Dict[str, Dict] = {}
        self.moral_weight: int = 0  # -100 do 100
        self.world_impact_score: float = 0.0
        self.start_time: Optional[datetime] = None
        self.resolution_time: Optional[datetime] = None
        
    def add_branch(self, branch: QuestBranch):
        """Dodaje gałąź decyzyjną do questa."""
        self.branches[branch.branch_id] = branch
        
    def discover(self, method: DiscoveryMethod, location: str) -> Dict[str, Any]:
        """Odkrycie questa przez gracza."""
        if self.state not in [QuestState.SEEDING, QuestState.DISCOVERABLE]:
            return {"success": False, "reason": "Quest nie jest jeszcze dostępny do odkrycia"}
        
        self.state = QuestState.ACTIVE
        self.start_time = datetime.now()
        
        discovery_text = self.discovery_dialogue.get(method.value, [
            "Odkryłeś coś dziwnego...",
            "To wymaga zbadania..."
        ])
        
        return {
            "success": True,
            "method": method.value,
            "location": location,
            "dialogue": random.choice(discovery_text),
            "initial_clues": self.seed.initial_clues
        }
    
    def investigate(self, action: str, target: str, player_state: Dict) -> Dict[str, Any]:
        """Gracz prowadzi śledztwo."""
        self.state = QuestState.INVESTIGATING
        result = {"success": False, "discoveries": [], "dialogue": []}
        
        if action == "interrogate":
            if target not in self.investigation.interrogated_npcs:
                self.investigation.interrogated_npcs.append(target)
                # Odkryj wskazówki bazując na relacjach z NPC
                relationship = player_state.get('relationships', {}).get(target, 0)
                if relationship > 30:
                    clue_id = f"clue_{target}_friendly"
                    if self.investigation.add_clue(clue_id):
                        result["discoveries"].append(clue_id)
                        result["dialogue"].append(self._get_npc_dialogue(target, "friendly"))
                elif relationship < -30:
                    result["dialogue"].append(self._get_npc_dialogue(target, "hostile"))
                else:
                    clue_id = f"clue_{target}_neutral"
                    if self.investigation.add_clue(clue_id):
                        result["discoveries"].append(clue_id)
                        result["dialogue"].append(self._get_npc_dialogue(target, "neutral"))
                result["success"] = True
                
        elif action == "search":
            if target not in self.investigation.visited_locations:
                self.investigation.visited_locations.append(target)
                # Sprawdź umiejętności percepcji
                perception = player_state.get('skills', {}).get('perception', 0)
                if perception >= 5:
                    clue_id = f"clue_location_{target}_hidden"
                    if self.investigation.add_clue(clue_id):
                        result["discoveries"].append(clue_id)
                        result["dialogue"].append(f"Twoja spostrzegawczość pozwoliła ci znaleźć ukryte ślady w {target}")
                
                clue_id = f"clue_location_{target}_obvious"
                if self.investigation.add_clue(clue_id):
                    result["discoveries"].append(clue_id)
                    result["dialogue"].append(f"Znalazłeś oczywiste ślady w {target}")
                result["success"] = True
                
        elif action == "analyze":
            # Analiza zebranych dowodów
            if len(self.investigation.discovered_clues) >= 3:
                theory = self._formulate_theory()
                self.investigation.player_theories.append(theory)
                result["discoveries"].append(theory)
                result["dialogue"].append("Zaczynasz dostrzegać wzór w zebranych informacjach...")
                result["success"] = True
        
        return result
    
    def resolve(self, branch_id: str, player_state: Dict, world_state: Dict) -> Dict[str, Any]:
        """Rozwiązanie questa wybraną ścieżką."""
        if branch_id not in self.branches:
            return {"success": False, "reason": "Nieznana ścieżka rozwiązania"}
        
        branch = self.branches[branch_id]
        if not branch.can_choose(player_state):
            return {"success": False, "reason": "Nie spełniasz wymagań tej ścieżki"}
        
        self.current_branch = branch_id
        self.state = QuestState.RESOLVED
        self.resolution_time = datetime.now()
        
        # Zastosuj natychmiastowe konsekwencje
        immediate_consequences = self._apply_immediate_consequences(branch, world_state)
        
        # Zaplanuj opóźnione konsekwencje
        delayed_consequences = self._schedule_delayed_consequences(branch)
        
        # Oblicz wpływ moralny
        self.moral_weight = self._calculate_moral_impact(branch_id)
        
        # Oblicz wpływ na świat
        self.world_impact_score = self._calculate_world_impact(branch)
        
        return {
            "success": True,
            "branch": branch_id,
            "immediate_effects": immediate_consequences,
            "scheduled_effects": len(delayed_consequences),
            "moral_impact": self.moral_weight,
            "world_impact": self.world_impact_score,
            "dialogue": branch.dialogue_options.get('resolution', 'Sytuacja została rozwiązana.')
        }
    
    def fail(self, reason: str, world_state: Dict) -> Dict[str, Any]:
        """Quest kończy się niepowodzeniem."""
        self.state = QuestState.FAILED
        self.resolution_time = datetime.now()
        
        # Konsekwencje zignorowania questa
        failure_consequences = self._apply_failure_consequences(world_state)
        
        return {
            "success": False,
            "reason": reason,
            "consequences": failure_consequences,
            "dialogue": "Twoja bezczynność ma konsekwencje..."
        }
    
    def _get_npc_dialogue(self, npc: str, attitude: str) -> str:
        """Zwraca dialog NPC bazując na stosunku do gracza."""
        # To będzie nadpisane w konkretnych questach
        return f"{npc} mówi coś związanego z sytuacją ({attitude})"
    
    def _formulate_theory(self) -> str:
        """Formułuje teorię na podstawie zebranych wskazówek."""
        clue_count = len(self.investigation.discovered_clues)
        if clue_count >= 5:
            return "theory_complete"
        elif clue_count >= 3:
            return "theory_partial"
        else:
            return "theory_vague"
    
    def _apply_immediate_consequences(self, branch: QuestBranch, world_state: Dict) -> Dict:
        """Stosuje natychmiastowe konsekwencje."""
        changes = {}
        for cons_type, cons_value in branch.consequences.items():
            if cons_type == 'world_state':
                for key, value in cons_value.items():
                    world_state[key] = value
                    changes[key] = value
            elif cons_type == 'relationships':
                for npc, change in cons_value.items():
                    current = world_state.get('relationships', {}).get(npc, 0)
                    world_state.setdefault('relationships', {})[npc] = current + change
                    changes[f'relationship_{npc}'] = change
        return changes
    
    def _schedule_delayed_consequences(self, branch: QuestBranch) -> List[ConsequenceEvent]:
        """Planuje opóźnione konsekwencje."""
        delayed = []
        for cons_type, cons_value in branch.consequences.items():
            if cons_type == 'delayed':
                for delay_hours, effects in cons_value.items():
                    event = ConsequenceEvent(
                        event_id=f"{self.quest_id}_{branch.branch_id}_{delay_hours}h",
                        quest_id=self.quest_id,
                        trigger_time=datetime.now() + timedelta(hours=delay_hours),
                        event_type='delayed',
                        world_changes=effects.get('world_changes', {}),
                        npc_reactions=effects.get('npc_reactions', {}),
                        new_quest_seeds=effects.get('new_quests', []),
                        description=effects.get('description', '')
                    )
                    delayed.append(event)
                    self.consequences.append(event)
        return delayed
    
    def _calculate_moral_impact(self, branch_id: str) -> int:
        """Oblicza wpływ moralny decyzji."""
        # Będzie nadpisane w konkretnych questach
        moral_weights = {
            'violence': -30,
            'stealth': -10,
            'diplomacy': 20,
            'sacrifice': 40,
            'betrayal': -50,
            'ignore': -20
        }
        return moral_weights.get(branch_id, 0)
    
    def _calculate_world_impact(self, branch: QuestBranch) -> float:
        """Oblicza jak bardzo rozwiązanie zmienia świat."""
        impact = 0.0
        
        # Liczba zmienionych elementów świata
        world_changes = branch.consequences.get('world_state', {})
        impact += len(world_changes) * 0.1
        
        # Liczba dotkniętych NPC
        relationships = branch.consequences.get('relationships', {})
        impact += len(relationships) * 0.15
        
        # Liczba nowych questów
        new_quests = branch.consequences.get('new_quests', [])
        impact += len(new_quests) * 0.25
        
        # Opóźnione konsekwencje
        delayed = branch.consequences.get('delayed', {})
        impact += len(delayed) * 0.2
        
        return min(impact, 1.0)  # Cap at 1.0
    
    def _apply_failure_consequences(self, world_state: Dict) -> Dict:
        """Stosuje konsekwencje zignorowania questa."""
        # Będzie nadpisane w konkretnych questach
        return {"ignored": True}
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje quest do słownika.

        Returns:
            Słownik z danymi questa
        """
        return {
            'quest_id': self.quest_id,
            'seed_id': self.seed.quest_id if self.seed else None,
            'state': self.state.value if hasattr(self.state, 'value') else str(self.state),
            'moral_weight': self.moral_weight,
            'world_impact_score': self.world_impact_score,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None,
            'current_branch': self.current_branch,
            'discovered_clues': list(self.investigation.discovered_clues) if self.investigation else []
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], seed: 'QuestSeed') -> 'EmergentQuest':
        """Odtwarza quest ze słownika.

        Args:
            data: Słownik z danymi questa
            seed: Ziarno questa

        Returns:
            Odtworzony quest
        """
        quest = cls(data['quest_id'], seed)
        quest.state = QuestState(data.get('state', 'active'))
        quest.moral_weight = data.get('moral_weight', 0)
        quest.world_impact_score = data.get('world_impact_score', 0.0)
        quest.current_branch = data.get('current_branch')

        if data.get('start_time'):
            quest.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('resolution_time'):
            quest.resolution_time = datetime.fromisoformat(data['resolution_time'])

        # Odtwórz odkryte wskazówki
        if data.get('discovered_clues'):
            quest.investigation.discovered_clues = set(data['discovered_clues'])

        return quest


class QuestEngine:
    """Główny silnik zarządzający questami emergentnymi."""
    def __init__(self):
        self.quest_seeds: Dict[str, QuestSeed] = {}
        self.active_quests: Dict[str, EmergentQuest] = {}
        self.completed_quests: List[str] = []
        self.failed_quests: List[str] = []
        self.consequence_queue: List[ConsequenceEvent] = []
        self.world_state: Dict[str, Any] = {}
        self.player_state: Dict[str, Any] = {}
        self.reward_system: Optional['RewardSystem'] = None  # Inicjalizowany później
        
    def register_seed(self, seed: QuestSeed):
        """Rejestruje nowe ziarno questa."""
        self.quest_seeds[seed.quest_id] = seed
        
    def update(self, current_time: datetime):
        """Aktualizacja silnika - sprawdza aktywacje i konsekwencje."""
        # Sprawdź aktywację nowych questów
        self._check_seed_activation()
        
        # Przetwórz kolejkę konsekwencji
        self._process_consequences(current_time)
        
        # Sprawdź timeout questów
        self._check_quest_timeouts(current_time)
        
        # Aktualizuj stany questów
        self._update_quest_states()
    
    def get_all_quests(self) -> Dict[str, EmergentQuest]:
        """
        Zwraca wszystkie questy (aktywne, zakończone i nieudane).
        
        Returns:
            Słownik wszystkich questów
        """
        all_quests = {}
        all_quests.update(self.active_quests)
        # Można też dodać completed i failed jeśli potrzeba
        return all_quests
    
    def _check_seed_activation(self):
        """Sprawdza które ziarna questów mogą się aktywować."""
        for seed_id, seed in self.quest_seeds.items():
            if seed_id not in self.active_quests and seed_id not in self.completed_quests:
                if seed.check_activation(self.world_state):
                    # Aktywuj questa
                    quest = self._create_quest_from_seed(seed)
                    quest.state = QuestState.SEEDING
                    self.active_quests[seed_id] = quest
                    
                    # Rozprowadź początkowe wskazówki
                    self._spread_initial_clues(quest)
    
    def _create_quest_from_seed(self, seed: QuestSeed) -> EmergentQuest:
        """Tworzy questa z ziarna."""
        # To będzie nadpisane dla konkretnych typów questów
        return EmergentQuest(seed.quest_id, seed)
    
    def _spread_initial_clues(self, quest: EmergentQuest):
        """Rozmieszcza początkowe wskazówki w świecie."""
        for location, clue in quest.seed.initial_clues.items():
            # Dodaj wskazówkę do lokacji
            if 'locations' not in self.world_state:
                self.world_state['locations'] = {}
            if location not in self.world_state['locations']:
                self.world_state['locations'][location] = {}
            
            self.world_state['locations'][location][f'clue_{quest.quest_id}'] = clue
        
        # Zmień stan na odkrywalny po pewnym czasie
        quest.state = QuestState.DISCOVERABLE
    
    def _process_consequences(self, current_time: datetime):
        """Przetwarza zakolejkowane konsekwencje."""
        due_consequences = [c for c in self.consequence_queue if c.is_due(current_time)]
        
        for consequence in due_consequences:
            # Zastosuj zmiany świata
            for key, value in consequence.world_changes.items():
                self.world_state[key] = value
            
            # Dodaj reakcje NPC
            for npc, reaction in consequence.npc_reactions.items():
                if 'npc_reactions' not in self.world_state:
                    self.world_state['npc_reactions'] = {}
                self.world_state['npc_reactions'][npc] = reaction
            
            # Aktywuj nowe ziarna questów
            for seed_id in consequence.new_quest_seeds:
                if seed_id in self.quest_seeds:
                    # Wymuś aktywację
                    quest = self._create_quest_from_seed(self.quest_seeds[seed_id])
                    quest.state = QuestState.SEEDING
                    self.active_quests[seed_id] = quest
                    self._spread_initial_clues(quest)
            
            # Usuń z kolejki
            self.consequence_queue.remove(consequence)
    
    def _check_quest_timeouts(self, current_time: datetime):
        """Sprawdza czy questy nie przekroczyły limitu czasu."""
        for quest_id, quest in list(self.active_quests.items()):
            if quest.seed.time_sensitive and quest.start_time:
                elapsed_hours = (current_time - quest.start_time).total_seconds() / 3600
                if elapsed_hours > quest.seed.expiry_hours:
                    # Quest się nie udał z powodu upływu czasu
                    result = quest.fail("Czas minął", self.world_state)
                    self.failed_quests.append(quest_id)
                    del self.active_quests[quest_id]
    
    def _update_quest_states(self):
        """Aktualizuje stany questów bazując na warunkach świata."""
        for quest in self.active_quests.values():
            if quest.state == QuestState.CONSEQUENCING:
                # Sprawdź czy wszystkie konsekwencje zostały przetworzone
                pending = [c for c in quest.consequences if c in self.consequence_queue]
                if not pending:
                    quest.state = QuestState.RESOLVED
                    self.completed_quests.append(quest.quest_id)
                    del self.active_quests[quest.quest_id]
    
    def discover_quest(self, location: str) -> Optional[Dict]:
        """Gracz próbuje odkryć questa w lokacji."""
        # Sprawdź czy są jakieś wskazówki w tej lokacji
        location_data = self.world_state.get('locations', {}).get(location, {})
        
        for quest in self.active_quests.values():
            if quest.state == QuestState.DISCOVERABLE:
                for clue_key in location_data.keys():
                    if quest.quest_id in clue_key:
                        # Odkryto questa!
                        method = random.choice(quest.seed.discovery_methods)
                        return quest.discover(method, location)
        
        return None
    
    def get_available_branches(self, quest_id: str) -> List[Dict]:
        """Zwraca dostępne gałęzie rozwiązania questa."""
        if quest_id not in self.active_quests:
            return []
        
        quest = self.active_quests[quest_id]
        available = []
        
        for branch_id, branch in quest.branches.items():
            if branch.can_choose(self.player_state):
                available.append({
                    'id': branch_id,
                    'description': branch.description,
                    'requirements': branch.requirements,
                    'dialogue_preview': branch.dialogue_options.get('preview', '')
                })
        
        return available
    
    def resolve_quest(self, quest_id: str, branch_id: str) -> Dict:
        """Rozwiązuje questa wybraną ścieżką."""
        if quest_id not in self.active_quests:
            return {"success": False, "reason": "Quest nie jest aktywny"}
        
        quest = self.active_quests[quest_id]
        result = quest.resolve(branch_id, self.player_state, self.world_state)
        
        if result['success']:
            # Dodaj konsekwencje do kolejki
            self.consequence_queue.extend(quest.consequences)
            quest.state = QuestState.CONSEQUENCING

            # Emituj event ukończenia questa
            event_bus.emit(GameEvent(
                event_type="quest_completed",
                category=EventCategory.QUEST,
                source="quest_engine",
                data={
                    'quest_id': quest_id,
                    'quest_name': quest.seed.name,
                    'branch_id': branch_id,
                    'priority': quest.seed.priority
                },
                priority=EventPriority.HIGH
            ))

        return result
    
    def get_quest_status(self, quest_id: str) -> Dict:
        """Zwraca status questa."""
        if quest_id in self.active_quests:
            quest = self.active_quests[quest_id]
            return {
                'id': quest_id,
                'name': quest.seed.name,
                'state': quest.state.value,
                'investigation_progress': quest.investigation.get_completion_percentage(10),
                'discovered_clues': len(quest.investigation.discovered_clues),
                'time_remaining': self._get_time_remaining(quest) if quest.seed.time_sensitive else None
            }
        elif quest_id in self.completed_quests:
            return {'id': quest_id, 'state': 'completed'}
        elif quest_id in self.failed_quests:
            return {'id': quest_id, 'state': 'failed'}
        else:
            return {'id': quest_id, 'state': 'unknown'}
    
    def _get_time_remaining(self, quest: EmergentQuest) -> float:
        """Zwraca pozostały czas questa w godzinach."""
        if not quest.start_time:
            return quest.seed.expiry_hours
        
        elapsed = (datetime.now() - quest.start_time).total_seconds() / 3600
        return max(0, quest.seed.expiry_hours - elapsed)
    
    def get_active_quests(self) -> List[EmergentQuest]:
        """Zwraca listę aktywnych questów.
        
        Returns:
            Lista aktywnych questów
        """
        return list(self.active_quests.values())
    
    def get_discoverable_quests(self) -> List[EmergentQuest]:
        """Zwraca questy które można odkryć w tej chwili.
        
        Returns:
            Lista questów gotowych do odkrycia
        """
        discoverable = []
        for quest in self.active_quests.values():
            if quest.state == QuestState.DISCOVERABLE:
                discoverable.append(quest)
        return discoverable
    
    def save_state(self) -> Dict[str, Any]:
        """Zwraca stan silnika questów do zapisu.
        
        Returns:
            Słownik ze stanem questów
        """
        return {
            'active_quests': {qid: quest.to_dict() for qid, quest in self.active_quests.items()},
            'completed_quests': self.completed_quests.copy(),
            'failed_quests': self.failed_quests.copy(),
            'world_state': self.world_state.copy(),
            'player_state': self.player_state.copy()
        }
    
    def load_state(self, data: Dict[str, Any]):
        """Wczytuje stan silnika questów z zapisu.
        
        Args:
            data: Słownik ze stanem questów
        """
        self.completed_quests = data.get('completed_quests', [])
        self.failed_quests = data.get('failed_quests', [])
        self.world_state = data.get('world_state', {})
        self.player_state = data.get('player_state', {})
        
        # Odtwórz aktywne questy z zapisanych danych
        self.active_quests = {}
        saved_quests = data.get('active_quests', {})
        for quest_id, quest_data in saved_quests.items():
            seed_id = quest_data.get('seed_id')
            if seed_id and seed_id in self.quest_seeds:
                seed = self.quest_seeds[seed_id]
                quest = EmergentQuest.from_dict(quest_data, seed)
                self.active_quests[quest_id] = quest


class RewardSystem:
    """System nagród dla questów."""
    
    def __init__(self):
        """Inicjalizacja systemu nagród."""
        self.reward_pool = {
            'gold': {1: 10, 2: 25, 3: 50, 4: 100, 5: 200},
            'experience': {1: 100, 2: 250, 3: 500, 4: 1000, 5: 2000},
            'items': {
                1: ['chleb', 'woda'],
                2: ['miecz', 'tarcza'],
                3: ['metalowe_narzedzia', 'lina'],
                4: ['klucz_mistrzowski', 'mapa_sekretu'],
                5: ['artefakt', 'zwoj_umiejetnosci']
            },
            'reputation': {1: 5, 2: 10, 3: 15, 4: 25, 5: 50}
        }
    
    def calculate_reward(self, quest_difficulty: int, completion_quality: float = 1.0) -> Dict[str, Any]:
        """Oblicza nagrodę za quest.
        
        Args:
            quest_difficulty: Trudność questa (1-5)
            completion_quality: Jakość ukończenia (0.5-1.5)
            
        Returns:
            Słownik z nagrodami
        """
        difficulty = max(1, min(5, quest_difficulty))
        quality = max(0.5, min(1.5, completion_quality))
        
        reward = {
            'gold': int(self.reward_pool['gold'][difficulty] * quality),
            'experience': int(self.reward_pool['experience'][difficulty] * quality),
            'reputation': int(self.reward_pool['reputation'][difficulty] * quality)
        }
        
        # Losowy przedmiot jeśli jakość >= 1.0
        if quality >= 1.0 and random.random() < 0.7:
            items = self.reward_pool['items'][difficulty]
            reward['item'] = random.choice(items)
        
        return reward
    
    def apply_reward(self, player, reward: Dict[str, Any]) -> str:
        """Aplikuje nagrodę do gracza.
        
        Args:
            player: Obiekt gracza
            reward: Słownik z nagrodami
            
        Returns:
            Opis otrzymanych nagród
        """
        messages = []
        
        if 'gold' in reward:
            player.gold += reward['gold']
            messages.append(f"Otrzymujesz {reward['gold']} złota")
        
        if 'experience' in reward:
            if hasattr(player, 'experience'):
                player.experience += reward['experience']
                messages.append(f"Zyskujesz {reward['experience']} doświadczenia")
        
        if 'item' in reward:
            item_data = {'id': reward['item'], 'name': reward['item'].replace('_', ' ').title(), 'type': 'misc'}
            player.add_item(item_data)
            messages.append(f"Otrzymujesz przedmiot: {item_data['name']}")
        
        if 'reputation' in reward:
            messages.append(f"Twoja reputacja wzrosła o {reward['reputation']}")
        
        return "Nagrody: " + ", ".join(messages)