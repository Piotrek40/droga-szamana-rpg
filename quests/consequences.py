"""
System konsekwencji dla questów emergentnych.
Zarządza długoterminowymi efektami decyzji gracza.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import json


class ConsequenceType(Enum):
    """Typy konsekwencji."""
    IMMEDIATE = "immediate"          # Natychmiastowa
    DELAYED = "delayed"              # Opóźniona
    RECURRING = "recurring"          # Powtarzająca się
    CONDITIONAL = "conditional"      # Warunkowa
    CASCADING = "cascading"         # Kaskadowa (wywołuje inne)
    PERMANENT = "permanent"          # Trwała zmiana świata


class ConsequenceSeverity(Enum):
    """Waga konsekwencji."""
    TRIVIAL = 1      # Drobna zmiana
    MINOR = 2        # Mała konsekwencja
    MODERATE = 3     # Umiarkowana
    MAJOR = 4        # Poważna
    CRITICAL = 5     # Krytyczna dla świata gry


@dataclass
class Consequence:
    """Pojedyncza konsekwencja."""
    id: str
    quest_id: str
    consequence_type: ConsequenceType
    severity: ConsequenceSeverity
    description: str
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    dialogue: List[str] = field(default_factory=list)
    triggered: bool = False
    trigger_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    
    def can_trigger(self, world_state: Dict, current_time: datetime) -> bool:
        """Sprawdza czy konsekwencja może się wydarzyć."""
        if self.triggered and self.consequence_type != ConsequenceType.RECURRING:
            return False
            
        if self.trigger_time and current_time < self.trigger_time:
            return False
            
        if self.expiry_time and current_time > self.expiry_time:
            return False
            
        # Sprawdź warunki
        for condition, value in self.trigger_conditions.items():
            if condition not in world_state or world_state[condition] != value:
                return False
                
        return True
    
    def apply(self, world_state: Dict, game_state: Dict) -> Dict[str, Any]:
        """Aplikuje konsekwencję do stanu gry."""
        results = {
            'consequence_id': self.id,
            'changes': {},
            'new_events': [],
            'dialogue': random.choice(self.dialogue) if self.dialogue else "",
            'severity': self.severity.value
        }
        
        # Zastosuj efekty
        for effect_type, effect_value in self.effects.items():
            if effect_type == 'world_state':
                for key, value in effect_value.items():
                    old_value = world_state.get(key, None)
                    world_state[key] = value
                    results['changes'][key] = {'old': old_value, 'new': value}
                    
            elif effect_type == 'relationships':
                if 'relationships' not in game_state:
                    game_state['relationships'] = {}
                for npc, change in effect_value.items():
                    old_rel = game_state['relationships'].get(npc, 0)
                    game_state['relationships'][npc] = old_rel + change
                    results['changes'][f'relationship_{npc}'] = {
                        'old': old_rel, 
                        'new': old_rel + change
                    }
                    
            elif effect_type == 'spawn_event':
                results['new_events'].append(effect_value)
                
            elif effect_type == 'spawn_npc':
                if 'npcs' not in world_state:
                    world_state['npcs'] = {}
                world_state['npcs'][effect_value['name']] = effect_value
                results['changes'][f'new_npc_{effect_value["name"]}'] = True
                
            elif effect_type == 'remove_npc':
                if 'npcs' in world_state and effect_value in world_state['npcs']:
                    del world_state['npcs'][effect_value]
                    results['changes'][f'removed_npc_{effect_value}'] = True
                    
            elif effect_type == 'modify_location':
                location, modifications = effect_value
                if 'locations' not in world_state:
                    world_state['locations'] = {}
                if location not in world_state['locations']:
                    world_state['locations'][location] = {}
                world_state['locations'][location].update(modifications)
                results['changes'][f'location_{location}'] = modifications
        
        self.triggered = True
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje konsekwencję do słownika."""
        return {
            'id': self.id,
            'quest_id': self.quest_id,
            'consequence_type': self.consequence_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'trigger_conditions': self.trigger_conditions,
            'effects': self.effects,
            'dialogue': self.dialogue,
            'triggered': self.triggered,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'expiry_time': self.expiry_time.isoformat() if self.expiry_time else None
        }


class ConsequenceChain:
    """Łańcuch konsekwencji - sekwencja powiązanych efektów."""
    
    def __init__(self, chain_id: str, initial_consequence: Consequence):
        self.chain_id = chain_id
        self.consequences: List[Consequence] = [initial_consequence]
        self.current_index = 0
        self.completed = False
        
    def add_consequence(self, consequence: Consequence, delay_hours: int = 0):
        """Dodaje konsekwencję do łańcucha."""
        if delay_hours > 0 and self.consequences:
            # Ustaw czas triggera względem poprzedniej
            last_trigger = self.consequences[-1].trigger_time
            if last_trigger:
                consequence.trigger_time = last_trigger + timedelta(hours=delay_hours)
        self.consequences.append(consequence)
        
    def get_next(self) -> Optional[Consequence]:
        """Zwraca następną konsekwencję w łańcuchu."""
        if self.current_index < len(self.consequences):
            return self.consequences[self.current_index]
        return None
        
    def advance(self):
        """Przechodzi do następnej konsekwencji."""
        self.current_index += 1
        if self.current_index >= len(self.consequences):
            self.completed = True


class ConsequenceWeb:
    """Sieć powiązanych konsekwencji - złożone interakcje."""
    
    def __init__(self, web_id: str):
        self.web_id = web_id
        self.nodes: Dict[str, Consequence] = {}
        self.edges: Dict[str, List[str]] = {}  # consequence_id -> [triggered_ids]
        self.triggered_nodes: List[str] = []
        
    def add_node(self, consequence: Consequence):
        """Dodaje węzeł konsekwencji."""
        self.nodes[consequence.id] = consequence
        
    def add_edge(self, from_id: str, to_id: str):
        """Dodaje połączenie między konsekwencjami."""
        if from_id not in self.edges:
            self.edges[from_id] = []
        self.edges[from_id].append(to_id)
        
    def trigger_consequence(self, consequence_id: str, world_state: Dict, 
                          game_state: Dict) -> List[str]:
        """Triggeruje konsekwencję i zwraca listę nowo aktywowanych."""
        if consequence_id not in self.nodes:
            return []
            
        newly_triggered = []
        
        # Aplikuj konsekwencję
        consequence = self.nodes[consequence_id]
        consequence.apply(world_state, game_state)
        self.triggered_nodes.append(consequence_id)
        
        # Sprawdź połączone konsekwencje
        if consequence_id in self.edges:
            for connected_id in self.edges[consequence_id]:
                if connected_id not in self.triggered_nodes:
                    connected = self.nodes[connected_id]
                    if connected.can_trigger(world_state, datetime.now()):
                        newly_triggered.append(connected_id)
                        
        return newly_triggered


class ConsequenceManager:
    """Główny menedżer systemu konsekwencji."""
    
    def __init__(self):
        self.consequences: Dict[str, Consequence] = {}
        self.chains: Dict[str, ConsequenceChain] = {}
        self.webs: Dict[str, ConsequenceWeb] = {}
        self.scheduled_consequences: List[Consequence] = []
        self.history: List[Dict] = []
        
    def register_consequence(self, consequence: Consequence):
        """Rejestruje nową konsekwencję."""
        self.consequences[consequence.id] = consequence
        
        # Jeśli ma określony czas, dodaj do zaplanowanych
        if consequence.trigger_time:
            self.scheduled_consequences.append(consequence)
            self.scheduled_consequences.sort(key=lambda x: x.trigger_time)
            
    def create_chain(self, chain_id: str, consequences: List[Consequence]) -> ConsequenceChain:
        """Tworzy łańcuch konsekwencji."""
        if not consequences:
            raise ValueError("Chain must have at least one consequence")
            
        chain = ConsequenceChain(chain_id, consequences[0])
        for cons in consequences[1:]:
            chain.add_consequence(cons)
            
        self.chains[chain_id] = chain
        return chain
        
    def create_web(self, web_id: str) -> ConsequenceWeb:
        """Tworzy sieć konsekwencji."""
        web = ConsequenceWeb(web_id)
        self.webs[web_id] = web
        return web
    
    def update(self, game_time: int):
        """Aktualizuje system konsekwencji.
        
        Args:
            game_time: Aktualny czas gry w minutach
        """
        # Na razie prosta implementacja - może być rozbudowana
        from datetime import datetime, timedelta
        
        # Konwertuj game_time na datetime
        base_time = datetime(1000, 1, 1, 0, 0)  # Bazowy czas świata gry
        current_time = base_time + timedelta(minutes=game_time)
        
        # Sprawdź zaplanowane konsekwencje
        # Potrzebujemy world_state i game_state - na razie puste
        world_state = {}
        game_state = {}
        
        # Procesuj zaplanowane konsekwencje jeśli są
        if self.scheduled_consequences:
            self.process_scheduled(current_time, world_state, game_state)
        
    def process_scheduled(self, current_time: datetime, world_state: Dict, 
                         game_state: Dict) -> List[Dict]:
        """Przetwarza zaplanowane konsekwencje."""
        triggered = []
        
        for consequence in list(self.scheduled_consequences):
            if consequence.can_trigger(world_state, current_time):
                result = consequence.apply(world_state, game_state)
                triggered.append(result)
                self.history.append({
                    'time': current_time,
                    'consequence': consequence.id,
                    'result': result
                })
                
                # Usuń jednorazowe
                if consequence.consequence_type != ConsequenceType.RECURRING:
                    self.scheduled_consequences.remove(consequence)
                    
        return triggered
        
    def process_chains(self, world_state: Dict, game_state: Dict) -> List[Dict]:
        """Przetwarza aktywne łańcuchy."""
        results = []
        
        for chain in self.chains.values():
            if not chain.completed:
                next_cons = chain.get_next()
                if next_cons and next_cons.can_trigger(world_state, datetime.now()):
                    result = next_cons.apply(world_state, game_state)
                    results.append(result)
                    chain.advance()
                    
        return results
        
    def trigger_consequence(self, consequence_id: str, world_state: Dict, 
                           game_state: Dict) -> Dict:
        """Ręcznie triggeruje konsekwencję."""
        if consequence_id not in self.consequences:
            return {'error': 'Unknown consequence'}
            
        consequence = self.consequences[consequence_id]
        return consequence.apply(world_state, game_state)
        
    def get_pending_consequences(self) -> List[Dict]:
        """Zwraca listę oczekujących konsekwencji."""
        pending = []
        for cons in self.scheduled_consequences:
            pending.append({
                'id': cons.id,
                'quest': cons.quest_id,
                'type': cons.consequence_type.value,
                'severity': cons.severity.value,
                'trigger_time': cons.trigger_time.isoformat() if cons.trigger_time else None,
                'description': cons.description
            })
        return pending
        
    def get_consequence_history(self, quest_id: Optional[str] = None) -> List[Dict]:
        """Zwraca historię konsekwencji."""
        if quest_id:
            return [h for h in self.history 
                   if self.consequences[h['consequence']].quest_id == quest_id]
        return self.history
    
    def save_state(self) -> Dict[str, Any]:
        """Zwraca stan menedżera konsekwencji do zapisu.
        
        Returns:
            Słownik ze stanem konsekwencji
        """
        return {
            'consequences': {cid: cons.to_dict() for cid, cons in self.consequences.items() if hasattr(cons, 'to_dict')},
            'scheduled_consequences': [cons.to_dict() for cons in self.scheduled_consequences if hasattr(cons, 'to_dict')],
            'history': self.history.copy()
        }
    
    def load_state(self, state: Dict[str, Any]):
        """Wczytuje stan systemu konsekwencji.
        
        Args:
            state: Słownik ze stanem do wczytania
        """
        # Wczytaj historię
        self.history = state.get('history', [])
        
        # Konsekwencje i scheduled_consequences wymagałyby deserializacji
        # Na razie pozostawiamy puste - będą odtworzone przy następnych eventach
        self.consequences = {}
        self.scheduled_consequences = []


# Predefiniowane konsekwencje dla questów więziennych

def create_prison_consequences() -> Dict[str, Consequence]:
    """Tworzy predefiniowane konsekwencje dla więzienia."""
    consequences = {}
    
    # Konsekwencje dla konfliktu o jedzenie
    consequences['food_riot_delayed'] = Consequence(
        id='food_riot_delayed',
        quest_id='prison_food_conflict',
        consequence_type=ConsequenceType.DELAYED,
        severity=ConsequenceSeverity.MAJOR,
        description='Zamieszki głodowe wybuchają po 3 dniach',
        trigger_time=datetime.now() + timedelta(days=3),
        effects={
            'world_state': {
                'prison.riot_active': True,
                'prison.violence_level': 9,
                'prison.guard_control': 2
            },
            'spawn_event': 'food_riot_event'
        },
        dialogue=[
            "Więzienie eksploduje przemocą. Głodni więźniowie atakują wszystko i wszystkich.",
            "Krzyki, ogień, krew. Głód doprowadził do szaleństwa."
        ]
    )
    
    consequences['merchant_debt_collection'] = Consequence(
        id='merchant_debt_collection',
        quest_id='prison_food_conflict',
        consequence_type=ConsequenceType.DELAYED,
        severity=ConsequenceSeverity.MODERATE,
        description='Kupiec przychodzi po zapłatę za jedzenie',
        trigger_time=datetime.now() + timedelta(days=3),
        effects={
            'world_state': {
                'prison.merchant_waiting': True,
                'prison.debt_amount': 500
            },
            'spawn_npc': {
                'name': 'Gruby Ed',
                'type': 'merchant',
                'dialogue': 'Gdzie moje pieniądze, naczelnik? Nie lubię czekać.'
            }
        },
        dialogue=[
            "Gruby Ed stoi przed bramą. 'Czas zapłacić dług!'",
            "Kupiec domaga się zapłaty. Naczelnik wygląda na zdenerwowanego."
        ]
    )
    
    # Konsekwencje dla zgub klucze
    consequences['jenkins_revenge'] = Consequence(
        id='jenkins_revenge',
        quest_id='guard_keys_lost',
        consequence_type=ConsequenceType.DELAYED,
        severity=ConsequenceSeverity.MODERATE,
        description='Jenkins szuka zemsty za utratę kluczy',
        trigger_time=datetime.now() + timedelta(days=5),
        trigger_conditions={'guard_jenkins.demoted': True},
        effects={
            'world_state': {
                'player.framed_for_theft': True,
                'player.cell_searched': True
            },
            'relationships': {
                'Jenkins': -80,
                'guards': -20
            }
        },
        dialogue=[
            "Jenkins: 'Znalazłem skradzione rzeczy w twojej celi. Ciekawe jak się tam znalazły?'",
            "Strażnik Jenkins mści się, podrzucając ci skradzione przedmioty."
        ]
    )
    
    # Konsekwencje dla dziury w murze
    consequences['tunnel_collapse'] = Consequence(
        id='tunnel_collapse',
        quest_id='hole_in_wall',
        consequence_type=ConsequenceType.CONDITIONAL,
        severity=ConsequenceSeverity.MAJOR,
        description='Tunel się zawala podczas ucieczki',
        trigger_conditions={
            'prison.tunnel_complete': True,
            'weather.heavy_rain': True
        },
        effects={
            'world_state': {
                'prison.tunnel_collapsed': True,
                'prison.casualties': 3
            },
            'spawn_event': 'tunnel_disaster_event'
        },
        dialogue=[
            "Deszcz osłabił konstrukcję. Tunel zawala się, grzebiąc uciekinierów.",
            "Krzyki spod gruzu. Tragedia która mogła być unikniona."
        ]
    )
    
    consequences['mass_escape_manhunt'] = Consequence(
        id='mass_escape_manhunt',
        quest_id='hole_in_wall',
        consequence_type=ConsequenceType.CASCADING,
        severity=ConsequenceSeverity.CRITICAL,
        description='Masowa ucieczka uruchamia obławę',
        trigger_conditions={'prison.mass_escape': True},
        effects={
            'world_state': {
                'region.martial_law': True,
                'region.bounty_hunters_active': True,
                'player.wanted_level': 5
            },
            'spawn_event': 'manhunt_event',
            'relationships': {
                'kingdom_authorities': -100
            }
        },
        dialogue=[
            "Cały region jest w stanie wojennym. Łowcy nagród polują na uciekinierów.",
            "Twoja twarz jest na każdym plakacie. Nagroda: 10000 złotych, żywy lub martwy."
        ]
    )
    
    # Konsekwencje dla choroby
    consequences['plague_spreads'] = Consequence(
        id='plague_spreads',
        quest_id='prison_disease',
        consequence_type=ConsequenceType.RECURRING,
        severity=ConsequenceSeverity.MAJOR,
        description='Choroba rozprzestrzenia się co dzień',
        effects={
            'world_state': {
                'prison.infected_count': '+5',
                'prison.death_count': '+1'
            }
        },
        dialogue=[
            "Kolejnych pięciu więźniów zachorowało. Jeden nie dożył rana.",
            "Choroba się rozprzestrzenia. Śmierć zbiera żniwo."
        ]
    )
    
    consequences['medical_reputation'] = Consequence(
        id='medical_reputation',
        quest_id='prison_disease',
        consequence_type=ConsequenceType.PERMANENT,
        severity=ConsequenceSeverity.MODERATE,
        description='Zyskujesz reputację uzdrowiciela',
        trigger_conditions={'prison.disease_cured': True},
        effects={
            'world_state': {
                'player.titles': ['Uzdrowiciel', 'Plague-Breaker']
            },
            'relationships': {
                'all_prisoners': 30,
                'medical_guild': 20
            }
        },
        dialogue=[
            "Wieść o twoich umiejętnościach rozchodzi się. Jesteś znany jako Uzdrowiciel.",
            "Nawet poza murami więzienia, twoja reputacja rośnie."
        ]
    )
    
    # Konsekwencje dla buntu
    consequences['military_intervention'] = Consequence(
        id='military_intervention',
        quest_id='prisoner_revolt',
        consequence_type=ConsequenceType.DELAYED,
        severity=ConsequenceSeverity.CRITICAL,
        description='Wojsko pacyfikuje więzienie',
        trigger_time=datetime.now() + timedelta(hours=24),
        trigger_conditions={'prison.controlled_by': 'prisoners'},
        effects={
            'world_state': {
                'prison.under_siege': True,
                'prison.military_presence': True,
                'prison.death_toll': 30
            },
            'spawn_event': 'military_siege_event'
        },
        dialogue=[
            "Wojsko otacza więzienie. 'Poddajcie się lub zginiecie!'",
            "Armaty są wycelowane w mury. To nie jest negocjacja."
        ]
    )
    
    consequences['reform_implementation'] = Consequence(
        id='reform_implementation',
        quest_id='prisoner_revolt',
        consequence_type=ConsequenceType.DELAYED,
        severity=ConsequenceSeverity.MINOR,
        description='Reformy więzienne są wprowadzane',
        trigger_time=datetime.now() + timedelta(days=7),
        trigger_conditions={'prison.reforms_promised': True},
        effects={
            'world_state': {
                'prison.food_quality': 6,
                'prison.recreation_hours': 3,
                'prison.mail_frequency': 'weekly'
            },
            'relationships': {
                'prisoners': 20,
                'reformists': 30
            }
        },
        dialogue=[
            "Obiecane reformy wchodzą w życie. Więzienie staje się znośniejsze.",
            "Więźniowie są zadowoleni. 'Może ten system jednak działa?'"
        ]
    )
    
    consequences['assassination_attempt'] = Consequence(
        id='assassination_attempt',
        quest_id='prisoner_revolt',
        consequence_type=ConsequenceType.DELAYED,
        severity=ConsequenceSeverity.MAJOR,
        description='Próba zabójstwa gracza',
        trigger_time=datetime.now() + timedelta(days=7),
        trigger_conditions={'player.marked_as_snitch': True},
        effects={
            'spawn_event': 'assassination_event',
            'world_state': {
                'player.in_danger': True
            }
        },
        dialogue=[
            "Cień z nożem podkrada się gdy śpisz...",
            "Ktoś nalał trucizny do twojego jedzenia. Uważaj!"
        ]
    )
    
    return consequences


class ReputationConsequence:
    """Specjalna klasa dla konsekwencji reputacji."""
    
    def __init__(self):
        self.reputation_thresholds = {
            -100: 'Wróg Publiczny',
            -75: 'Znienawidzony',
            -50: 'Pogardzany',
            -25: 'Nielubiany',
            0: 'Neutralny',
            25: 'Akceptowany',
            50: 'Szanowany',
            75: 'Czczony',
            100: 'Legendarny'
        }
        
    def calculate_reputation_effects(self, reputation_changes: Dict[str, int], 
                                    current_reputation: Dict[str, int]) -> Dict:
        """Oblicza efekty zmian reputacji."""
        effects = {
            'title_changes': [],
            'new_opportunities': [],
            'lost_opportunities': [],
            'npc_reactions': {}
        }
        
        for faction, change in reputation_changes.items():
            old_rep = current_reputation.get(faction, 0)
            new_rep = old_rep + change
            
            # Sprawdź zmianę progu
            old_title = self._get_title(old_rep)
            new_title = self._get_title(new_rep)
            
            if old_title != new_title:
                effects['title_changes'].append({
                    'faction': faction,
                    'old': old_title,
                    'new': new_title
                })
                
            # Sprawdź nowe możliwości
            if new_rep >= 50 and old_rep < 50:
                effects['new_opportunities'].append(f'{faction}_allied_quests')
            elif new_rep >= 25 and old_rep < 25:
                effects['new_opportunities'].append(f'{faction}_trade')
                
            # Sprawdź utracone możliwości
            if new_rep < -25 and old_rep >= -25:
                effects['lost_opportunities'].append(f'{faction}_hostile')
            elif new_rep < 0 and old_rep >= 0:
                effects['lost_opportunities'].append(f'{faction}_neutral_stance')
                
            # Reakcje NPC
            if new_rep >= 75:
                effects['npc_reactions'][faction] = 'Witają cię jak bohatera!'
            elif new_rep >= 50:
                effects['npc_reactions'][faction] = 'Traktują cię z szacunkiem.'
            elif new_rep >= 25:
                effects['npc_reactions'][faction] = 'Są przyjaźnie nastawieni.'
            elif new_rep >= 0:
                effects['npc_reactions'][faction] = 'Zachowują neutralność.'
            elif new_rep >= -25:
                effects['npc_reactions'][faction] = 'Patrzą podejrzliwie.'
            elif new_rep >= -50:
                effects['npc_reactions'][faction] = 'Otwarcie okazują niechęć.'
            elif new_rep >= -75:
                effects['npc_reactions'][faction] = 'Grożą ci przy każdej okazji.'
            else:
                effects['npc_reactions'][faction] = 'Atakują na widok!'
                
        return effects
        
    def _get_title(self, reputation: int) -> str:
        """Zwraca tytuł dla danej reputacji."""
        for threshold in sorted(self.reputation_thresholds.keys(), reverse=True):
            if reputation >= threshold:
                return self.reputation_thresholds[threshold]
        return 'Nieznany'


class MoralConsequence:
    """System konsekwencji moralnych."""
    
    def __init__(self):
        self.moral_alignment = {
            'good': 0,
            'evil': 0,
            'lawful': 0,
            'chaotic': 0
        }
        
    def apply_moral_choice(self, choice_type: str, weight: int) -> Dict:
        """Aplikuje konsekwencje wyboru moralnego."""
        effects = {
            'alignment_shift': {},
            'karma_change': 0,
            'new_paths': [],
            'closed_paths': []
        }
        
        if choice_type == 'save_innocent':
            self.moral_alignment['good'] += weight
            effects['karma_change'] = weight * 10
            if self.moral_alignment['good'] > 50:
                effects['new_paths'].append('paladin_quest_line')
                
        elif choice_type == 'sacrifice_innocent':
            self.moral_alignment['evil'] += weight
            effects['karma_change'] = -weight * 10
            if self.moral_alignment['evil'] > 50:
                effects['new_paths'].append('dark_lord_quest_line')
                
        elif choice_type == 'follow_law':
            self.moral_alignment['lawful'] += weight
            if self.moral_alignment['lawful'] > 30:
                effects['new_paths'].append('magistrate_quests')
                
        elif choice_type == 'break_law':
            self.moral_alignment['chaotic'] += weight
            if self.moral_alignment['chaotic'] > 30:
                effects['new_paths'].append('outlaw_quests')
                
        effects['alignment_shift'] = self.moral_alignment.copy()
        
        # Sprawdź zamknięte ścieżki
        if self.moral_alignment['good'] > 75:
            effects['closed_paths'].append('assassin_guild')
        if self.moral_alignment['evil'] > 75:
            effects['closed_paths'].append('temple_quests')
            
        return effects
        
    def get_moral_title(self) -> str:
        """Zwraca tytuł moralny gracza."""
        if self.moral_alignment['good'] > 75:
            if self.moral_alignment['lawful'] > 50:
                return 'Paladyn'
            else:
                return 'Bohater'
        elif self.moral_alignment['evil'] > 75:
            if self.moral_alignment['chaotic'] > 50:
                return 'Demon'
            else:
                return 'Tyran'
        elif self.moral_alignment['lawful'] > 75:
            return 'Sędzia'
        elif self.moral_alignment['chaotic'] > 75:
            return 'Anarchista'
        else:
            return 'Neutralny'


class EconomicConsequence:
    """System konsekwencji ekonomicznych."""
    
    def __init__(self):
        self.market_prices = {}
        self.trade_routes = {}
        self.economic_events = []
        
    def apply_economic_change(self, change_type: str, magnitude: float) -> Dict:
        """Aplikuje zmianę ekonomiczną."""
        effects = {
            'price_changes': {},
            'new_opportunities': [],
            'market_status': ''
        }
        
        if change_type == 'shortage':
            # Niedobór powoduje wzrost cen
            for item in ['food', 'medicine', 'weapons']:
                old_price = self.market_prices.get(item, 100)
                new_price = int(old_price * (1 + magnitude))
                self.market_prices[item] = new_price
                effects['price_changes'][item] = {
                    'old': old_price,
                    'new': new_price
                }
            effects['market_status'] = 'Kryzys - ceny szybują w górę!'
            effects['new_opportunities'].append('smuggling_quests')
            
        elif change_type == 'surplus':
            # Nadmiar obniża ceny
            for item in ['food', 'clothing', 'tools']:
                old_price = self.market_prices.get(item, 100)
                new_price = int(old_price * (1 - magnitude))
                self.market_prices[item] = new_price
                effects['price_changes'][item] = {
                    'old': old_price,
                    'new': new_price
                }
            effects['market_status'] = 'Dobrobyt - ceny spadają!'
            effects['new_opportunities'].append('merchant_quests')
            
        elif change_type == 'trade_disruption':
            # Zakłócenie handlu
            effects['market_status'] = 'Szlaki handlowe zablokowane!'
            effects['new_opportunities'].append('caravan_protection_quests')
            self.trade_routes['status'] = 'blocked'
            
        return effects