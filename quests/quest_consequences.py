"""
System konsekwencji questów dla Droga Szamana RPG
Zarządza długoterminowymi efektami wyborów gracza
"""

import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class ConsequenceType(Enum):
    """Typy konsekwencji"""
    IMMEDIATE = "immediate"          # Natychmiastowe
    DELAYED = "delayed"              # Opóźnione
    RECURRING = "recurring"          # Powtarzające się
    CONDITIONAL = "conditional"      # Warunkowe
    CASCADE = "cascade"              # Kaskadowe (wywołują inne)
    PERMANENT = "permanent"          # Trwałe zmiany


class ConsequenceScope(Enum):
    """Zakres wpływu konsekwencji"""
    PERSONAL = "personal"            # Tylko gracz
    LOCAL = "local"                  # Lokalna społeczność
    FACTION = "faction"              # Cała frakcja
    REGIONAL = "regional"            # Region
    GLOBAL = "global"                # Cały świat gry


@dataclass
class ConsequenceEffect:
    """Pojedynczy efekt konsekwencji"""
    target_type: str                # "npc", "location", "economy", "player"
    target_id: str                   # ID celu
    effect_type: str                 # Typ efektu
    magnitude: float                 # Siła efektu
    duration: Optional[int] = None   # Czas trwania w godzinach
    
    def apply(self, world_state: Dict, target_object: Any) -> Dict[str, Any]:
        """Aplikuje efekt do celu"""
        result = {"success": False, "changes": {}}
        
        if self.target_type == "npc":
            result = self._apply_to_npc(target_object)
        elif self.target_type == "location":
            result = self._apply_to_location(world_state, self.target_id)
        elif self.target_type == "economy":
            result = self._apply_to_economy(world_state)
        elif self.target_type == "player":
            result = self._apply_to_player(target_object)
        
        return result
    
    def _apply_to_npc(self, npc) -> Dict[str, Any]:
        """Aplikuje efekt do NPCa"""
        changes = {}
        
        if self.effect_type == "relationship":
            npc.modify_relationship("player", 
                                   trust=self.magnitude * 10,
                                   respect=self.magnitude * 5)
            changes["relationship"] = self.magnitude * 10
            
        elif self.effect_type == "emotion":
            emotion_map = {
                "anger": "ANGRY",
                "fear": "FEAR", 
                "happiness": "HAPPY",
                "sadness": "SAD"
            }
            if self.effect_type in emotion_map:
                npc.modify_emotion(emotion_map[self.effect_type], self.magnitude)
                changes["emotion"] = self.effect_type
                
        elif self.effect_type == "memory":
            npc.add_memory(
                event_type="quest_consequence",
                description=f"Konsekwencja questa - zmiana o {self.magnitude}",
                participants=["player"],
                location=npc.location,
                importance=abs(self.magnitude)
            )
            changes["memory_added"] = True
            
        elif self.effect_type == "goal":
            # Modyfikuje cele NPCa
            for goal in npc.goals:
                if "player" in goal.name.lower():
                    goal.priority *= (1 + self.magnitude)
            changes["goals_modified"] = True
        
        return {"success": True, "changes": changes}
    
    def _apply_to_location(self, world_state: Dict, location_id: str) -> Dict[str, Any]:
        """Aplikuje efekt do lokacji"""
        changes = {}
        locations = world_state.get("locations", {})
        
        if location_id in locations:
            loc = locations[location_id]
            
            if self.effect_type == "security":
                loc["security_level"] = loc.get("security_level", 1.0) * (1 + self.magnitude)
                changes["security"] = self.magnitude
                
            elif self.effect_type == "prosperity":
                loc["prosperity"] = loc.get("prosperity", 0.5) + self.magnitude
                changes["prosperity"] = self.magnitude
                
            elif self.effect_type == "danger":
                loc["danger_level"] = loc.get("danger_level", 0.3) + self.magnitude
                changes["danger"] = self.magnitude
                
            elif self.effect_type == "accessibility":
                loc["accessible"] = self.magnitude > 0
                changes["accessible"] = self.magnitude > 0
        
        return {"success": True, "changes": changes}
    
    def _apply_to_economy(self, world_state: Dict) -> Dict[str, Any]:
        """Aplikuje efekt do ekonomii"""
        changes = {}
        economy = world_state.get("economy", {})
        
        if self.effect_type == "inflation":
            economy["inflation_rate"] = economy.get("inflation_rate", 1.0) * (1 + self.magnitude)
            changes["inflation"] = self.magnitude
            
        elif self.effect_type == "shortage":
            item_id = self.target_id
            shortages = economy.get("shortages", {})
            shortages[item_id] = shortages.get(item_id, 0) + self.magnitude
            economy["shortages"] = shortages
            changes[f"shortage_{item_id}"] = self.magnitude
            
        elif self.effect_type == "trade_route":
            routes = economy.get("trade_routes", [])
            if self.magnitude > 0:
                routes.append(self.target_id)
            else:
                routes = [r for r in routes if r != self.target_id]
            economy["trade_routes"] = routes
            changes["trade_routes"] = len(routes)
        
        world_state["economy"] = economy
        return {"success": True, "changes": changes}
    
    def _apply_to_player(self, player) -> Dict[str, Any]:
        """Aplikuje efekt do gracza"""
        changes = {}
        
        if self.effect_type == "reputation":
            faction = self.target_id
            current = player.reputation.get(faction, 0)
            player.reputation[faction] = current + self.magnitude * 10
            changes[f"rep_{faction}"] = self.magnitude * 10
            
        elif self.effect_type == "skill":
            skill_name = self.target_id
            if hasattr(player.skills, skill_name):
                skill = getattr(player.skills, skill_name)
                skill.level += int(self.magnitude)
                changes[f"skill_{skill_name}"] = int(self.magnitude)
                
        elif self.effect_type == "curse":
            player.curses = player.curses if hasattr(player, 'curses') else []
            player.curses.append({
                "name": self.target_id,
                "strength": self.magnitude,
                "duration": self.duration
            })
            changes["curse_added"] = self.target_id
            
        elif self.effect_type == "blessing":
            player.blessings = player.blessings if hasattr(player, 'blessings') else []
            player.blessings.append({
                "name": self.target_id,
                "strength": self.magnitude,
                "duration": self.duration
            })
            changes["blessing_added"] = self.target_id
        
        return {"success": True, "changes": changes}


@dataclass
class ConsequenceChain:
    """Łańcuch konsekwencji - jedna konsekwencja wywołuje kolejne"""
    chain_id: str
    name: str
    triggers: List[str]                    # Warunki aktywacji
    effects: List[ConsequenceEffect]       # Efekty do zastosowania
    next_chains: List[str] = field(default_factory=list)  # Kolejne łańcuchy
    probability: float = 1.0                # Prawdopodobieństwo aktywacji
    delay_hours: int = 0                    # Opóźnienie
    
    def should_activate(self, world_state: Dict, trigger_event: str) -> bool:
        """Sprawdza czy łańcuch powinien się aktywować"""
        if trigger_event not in self.triggers:
            return False
        
        # Sprawdź prawdopodobieństwo
        if random.random() > self.probability:
            return False
        
        # Można dodać dodatkowe warunki
        return True
    
    def get_activation_time(self) -> datetime:
        """Zwraca czas aktywacji"""
        return datetime.now() + timedelta(hours=self.delay_hours)


@dataclass 
class TrackedConsequence:
    """Śledzona konsekwencja w czasie"""
    consequence_id: str
    quest_id: str
    branch_id: str
    activation_time: datetime
    expiry_time: Optional[datetime]
    effects: List[ConsequenceEffect]
    scope: ConsequenceScope
    type: ConsequenceType
    applied: bool = False
    reversed: bool = False
    
    def is_due(self) -> bool:
        """Sprawdza czy czas zastosować konsekwencję"""
        return datetime.now() >= self.activation_time and not self.applied
    
    def has_expired(self) -> bool:
        """Sprawdza czy konsekwencja wygasła"""
        if not self.expiry_time:
            return False
        return datetime.now() >= self.expiry_time
    
    def can_be_reversed(self) -> bool:
        """Sprawdza czy konsekwencja może być cofnięta"""
        return self.type != ConsequenceType.PERMANENT and not self.reversed


class ConsequenceTracker:
    """System śledzący i zarządzający konsekwencjami"""
    
    def __init__(self):
        self.active_consequences: Dict[str, TrackedConsequence] = {}
        self.consequence_history: List[TrackedConsequence] = []
        self.consequence_chains: Dict[str, ConsequenceChain] = {}
        self.world_state_snapshot: Dict[str, Any] = {}
        self.ripple_effects: List[Dict] = []
        
        # Inicjalizuj łańcuchy konsekwencji
        self._initialize_consequence_chains()
    
    def _initialize_consequence_chains(self):
        """Inicjalizuje predefiniowane łańcuchy konsekwencji"""
        
        # Łańcuch: Zdrada więźniów
        betrayal_chain = ConsequenceChain(
            chain_id="prisoner_betrayal",
            name="Zemsta zdrajcy",
            triggers=["player_snitch", "betrayed_escape"],
            effects=[
                ConsequenceEffect("npc", "all_prisoners", "relationship", -5.0),
                ConsequenceEffect("player", "prisoners", "reputation", -8.0),
                ConsequenceEffect("location", "cells", "danger", 0.5)
            ],
            next_chains=["assassination_attempt"],
            probability=0.8,
            delay_hours=24
        )
        self.consequence_chains["prisoner_betrayal"] = betrayal_chain
        
        # Łańcuch: Próba zabójstwa
        assassination_chain = ConsequenceChain(
            chain_id="assassination_attempt",
            name="Próba zabójstwa",
            triggers=["prisoner_betrayal", "extreme_hatred"],
            effects=[
                ConsequenceEffect("player", "health", "damage", -0.3),
                ConsequenceEffect("location", "player_location", "danger", 0.8)
            ],
            next_chains=["revenge_cycle"],
            probability=0.6,
            delay_hours=48
        )
        self.consequence_chains["assassination_attempt"] = assassination_chain
        
        # Łańcuch: Ekonomiczny kryzys
        economic_crisis = ConsequenceChain(
            chain_id="economic_collapse",
            name="Kryzys ekonomiczny",
            triggers=["trade_route_destroyed", "monopoly_broken"],
            effects=[
                ConsequenceEffect("economy", "all", "inflation", 0.5),
                ConsequenceEffect("economy", "food", "shortage", 0.7),
                ConsequenceEffect("npc", "merchants", "goal", -0.5)
            ],
            next_chains=["social_unrest"],
            probability=0.7,
            delay_hours=72
        )
        self.consequence_chains["economic_collapse"] = economic_crisis
        
        # Łańcuch: Społeczne niepokoje
        social_unrest = ConsequenceChain(
            chain_id="social_unrest",
            name="Niepokoje społeczne",
            triggers=["economic_collapse", "extreme_hunger", "guard_brutality"],
            effects=[
                ConsequenceEffect("location", "all", "danger", 0.4),
                ConsequenceEffect("npc", "all", "emotion", -0.3),
                ConsequenceEffect("location", "all", "security", -0.5)
            ],
            next_chains=["prison_riot", "martial_law"],
            probability=0.9,
            delay_hours=24
        )
        self.consequence_chains["social_unrest"] = social_unrest
        
        # Łańcuch: Reforma więzienia
        prison_reform = ConsequenceChain(
            chain_id="prison_reform",
            name="Reforma systemu",
            triggers=["corruption_exposed", "riot_suppressed", "external_intervention"],
            effects=[
                ConsequenceEffect("location", "all", "security", 0.3),
                ConsequenceEffect("economy", "all", "prosperity", 0.2),
                ConsequenceEffect("npc", "guards", "goal", 0.5)
            ],
            next_chains=["improved_conditions"],
            probability=0.5,
            delay_hours=168  # Tydzień
        )
        self.consequence_chains["prison_reform"] = prison_reform
    
    def add_consequence(self, quest_id: str, branch_id: str, 
                       consequence_data: Dict) -> str:
        """Dodaje nową konsekwencję do śledzenia"""
        consequence_id = f"{quest_id}_{branch_id}_{int(time.time())}"
        
        # Parsuj dane konsekwencji
        effects = []
        for effect_data in consequence_data.get("effects", []):
            effect = ConsequenceEffect(
                target_type=effect_data["target_type"],
                target_id=effect_data["target_id"],
                effect_type=effect_data["effect_type"],
                magnitude=effect_data["magnitude"],
                duration=effect_data.get("duration")
            )
            effects.append(effect)
        
        # Określ typ i zakres
        cons_type = ConsequenceType[consequence_data.get("type", "DELAYED").upper()]
        scope = ConsequenceScope[consequence_data.get("scope", "LOCAL").upper()]
        
        # Oblicz czasy
        delay = consequence_data.get("delay_hours", 0)
        duration = consequence_data.get("duration_hours")
        
        activation_time = datetime.now() + timedelta(hours=delay)
        expiry_time = None
        if duration:
            expiry_time = activation_time + timedelta(hours=duration)
        
        # Stwórz śledzoną konsekwencję
        tracked = TrackedConsequence(
            consequence_id=consequence_id,
            quest_id=quest_id,
            branch_id=branch_id,
            activation_time=activation_time,
            expiry_time=expiry_time,
            effects=effects,
            scope=scope,
            type=cons_type
        )
        
        self.active_consequences[consequence_id] = tracked
        
        # Sprawdź łańcuchy
        self._check_chain_triggers(consequence_data.get("trigger_event"))
        
        return consequence_id
    
    def _check_chain_triggers(self, trigger_event: Optional[str]):
        """Sprawdza czy wydarzenie wywołuje łańcuchy konsekwencji"""
        if not trigger_event:
            return
        
        for chain in self.consequence_chains.values():
            if chain.should_activate(self.world_state_snapshot, trigger_event):
                self._activate_chain(chain)
    
    def _activate_chain(self, chain: ConsequenceChain):
        """Aktywuje łańcuch konsekwencji"""
        # Dodaj konsekwencję łańcucha
        consequence_data = {
            "effects": [
                {
                    "target_type": eff.target_type,
                    "target_id": eff.target_id,
                    "effect_type": eff.effect_type,
                    "magnitude": eff.magnitude,
                    "duration": eff.duration
                }
                for eff in chain.effects
            ],
            "type": "CASCADE",
            "scope": "LOCAL",
            "delay_hours": chain.delay_hours,
            "trigger_event": chain.chain_id
        }
        
        self.add_consequence(f"chain_{chain.chain_id}", "auto", consequence_data)
        
        # Zaplanuj kolejne łańcuchy
        for next_chain_id in chain.next_chains:
            if next_chain_id in self.consequence_chains:
                # Będą sprawdzone gdy ten łańcuch się wykona
                pass
    
    def process_due_consequences(self, world_state: Dict, 
                                npc_manager, player) -> List[Dict]:
        """Przetwarza wszystkie należne konsekwencje"""
        processed = []
        self.world_state_snapshot = world_state.copy()
        
        for cons_id, consequence in list(self.active_consequences.items()):
            if consequence.is_due():
                result = self._apply_consequence(consequence, world_state, 
                                                npc_manager, player)
                processed.append({
                    "id": cons_id,
                    "quest": consequence.quest_id,
                    "branch": consequence.branch_id,
                    "effects": result
                })
                
                consequence.applied = True
                
                # Przenieś do historii jeśli nie powtarzalna
                if consequence.type != ConsequenceType.RECURRING:
                    self.consequence_history.append(consequence)
                    del self.active_consequences[cons_id]
                
                # Zapisz efekty uboczne
                self._track_ripple_effects(consequence, result)
        
        # Sprawdź wygasłe konsekwencje
        self._check_expired_consequences(world_state, npc_manager, player)
        
        return processed
    
    def _apply_consequence(self, consequence: TrackedConsequence,
                          world_state: Dict, npc_manager, player) -> Dict:
        """Aplikuje pojedynczą konsekwencję"""
        results = {"applied_effects": [], "failed_effects": []}
        
        for effect in consequence.effects:
            # Znajdź cel efektu
            target = None
            if effect.target_type == "npc":
                if effect.target_id == "all":
                    # Zastosuj do wszystkich NPCów
                    for npc in npc_manager.npcs.values():
                        effect_result = effect.apply(world_state, npc)
                        results["applied_effects"].append(effect_result)
                    continue
                else:
                    target = npc_manager.npcs.get(effect.target_id)
            elif effect.target_type == "player":
                target = player
            elif effect.target_type in ["location", "economy"]:
                target = world_state
            
            if target:
                effect_result = effect.apply(world_state, target)
                if effect_result["success"]:
                    results["applied_effects"].append(effect_result)
                else:
                    results["failed_effects"].append(effect_result)
        
        return results
    
    def _check_expired_consequences(self, world_state: Dict, 
                                   npc_manager, player):
        """Sprawdza i cofa wygasłe konsekwencje"""
        for cons_id, consequence in list(self.active_consequences.items()):
            if consequence.has_expired() and consequence.can_be_reversed():
                # Cofnij efekty
                self._reverse_consequence(consequence, world_state, 
                                         npc_manager, player)
                consequence.reversed = True
                
                # Przenieś do historii
                self.consequence_history.append(consequence)
                del self.active_consequences[cons_id]
    
    def _reverse_consequence(self, consequence: TrackedConsequence,
                            world_state: Dict, npc_manager, player):
        """Cofa efekty konsekwencji"""
        for effect in consequence.effects:
            # Odwróć efekt (ujemna magnitude)
            reversed_effect = ConsequenceEffect(
                target_type=effect.target_type,
                target_id=effect.target_id,
                effect_type=effect.effect_type,
                magnitude=-effect.magnitude,
                duration=None
            )
            
            # Znajdź i zastosuj
            target = None
            if effect.target_type == "npc":
                target = npc_manager.npcs.get(effect.target_id)
            elif effect.target_type == "player":
                target = player
            elif effect.target_type in ["location", "economy"]:
                target = world_state
            
            if target:
                reversed_effect.apply(world_state, target)
    
    def _track_ripple_effects(self, consequence: TrackedConsequence, 
                             results: Dict):
        """Śledzi efekty uboczne konsekwencji"""
        ripple = {
            "timestamp": datetime.now().isoformat(),
            "source": consequence.consequence_id,
            "scope": consequence.scope.value,
            "primary_effects": len(results.get("applied_effects", [])),
            "cascades": []
        }
        
        # Analiza wpływu na szerszy kontekst
        if consequence.scope == ConsequenceScope.LOCAL:
            ripple["affected_area"] = "immediate_surroundings"
        elif consequence.scope == ConsequenceScope.FACTION:
            ripple["affected_area"] = "entire_faction"
        elif consequence.scope == ConsequenceScope.GLOBAL:
            ripple["affected_area"] = "entire_world"
            # Globalne konsekwencje mogą wywołać więcej efektów
            ripple["cascades"].append("potential_world_events")
        
        self.ripple_effects.append(ripple)
    
    def predict_consequences(self, quest_id: str, branch_id: str) -> List[Dict]:
        """Przewiduje konsekwencje wyboru danej gałęzi"""
        predictions = []
        
        # Szukaj w aktywnych questach
        # To wymaga integracji z quest_engine
        
        return predictions
    
    def get_consequence_timeline(self) -> List[Dict]:
        """Zwraca oś czasu konsekwencji"""
        timeline = []
        
        # Aktywne konsekwencje
        for cons in self.active_consequences.values():
            timeline.append({
                "time": cons.activation_time.isoformat(),
                "type": "scheduled",
                "quest": cons.quest_id,
                "branch": cons.branch_id,
                "scope": cons.scope.value
            })
        
        # Historia
        for cons in self.consequence_history[-20:]:  # Ostatnie 20
            timeline.append({
                "time": cons.activation_time.isoformat(),
                "type": "completed",
                "quest": cons.quest_id,
                "branch": cons.branch_id,
                "reversed": cons.reversed
            })
        
        # Sortuj chronologicznie
        timeline.sort(key=lambda x: x["time"])
        
        return timeline
    
    def get_karma_score(self) -> Dict[str, float]:
        """Oblicza karmę na podstawie konsekwencji"""
        karma = {
            "good": 0.0,
            "evil": 0.0,
            "neutral": 0.0,
            "chaos": 0.0,
            "order": 0.0
        }
        
        # Analizuj historię konsekwencji
        for cons in self.consequence_history:
            for effect in cons.effects:
                # Pozytywne efekty na NPCów = dobra karma
                if effect.target_type == "npc" and effect.magnitude > 0:
                    karma["good"] += abs(effect.magnitude)
                elif effect.target_type == "npc" and effect.magnitude < 0:
                    karma["evil"] += abs(effect.magnitude)
                
                # Chaos vs porządek
                if effect.effect_type in ["danger", "unrest"]:
                    karma["chaos"] += abs(effect.magnitude)
                elif effect.effect_type in ["security", "order"]:
                    karma["order"] += abs(effect.magnitude)
        
        # Normalizuj
        total = sum(karma.values())
        if total > 0:
            for key in karma:
                karma[key] = karma[key] / total * 100
        
        return karma
    
    def save_state(self) -> Dict:
        """Zapisuje stan systemu konsekwencji"""
        return {
            "active": {
                cid: {
                    "quest_id": c.quest_id,
                    "branch_id": c.branch_id,
                    "activation_time": c.activation_time.isoformat(),
                    "expiry_time": c.expiry_time.isoformat() if c.expiry_time else None,
                    "type": c.type.value,
                    "scope": c.scope.value,
                    "applied": c.applied,
                    "effects": [
                        {
                            "target_type": e.target_type,
                            "target_id": e.target_id,
                            "effect_type": e.effect_type,
                            "magnitude": e.magnitude
                        }
                        for e in c.effects
                    ]
                }
                for cid, c in self.active_consequences.items()
            },
            "history_count": len(self.consequence_history),
            "ripple_effects": self.ripple_effects[-10:]  # Ostatnie 10
        }
    
    def load_state(self, data: Dict):
        """Wczytuje stan systemu konsekwencji"""
        self.active_consequences.clear()
        
        for cid, cons_data in data.get("active", {}).items():
            effects = []
            for eff_data in cons_data["effects"]:
                effects.append(ConsequenceEffect(
                    target_type=eff_data["target_type"],
                    target_id=eff_data["target_id"],
                    effect_type=eff_data["effect_type"],
                    magnitude=eff_data["magnitude"]
                ))
            
            tracked = TrackedConsequence(
                consequence_id=cid,
                quest_id=cons_data["quest_id"],
                branch_id=cons_data["branch_id"],
                activation_time=datetime.fromisoformat(cons_data["activation_time"]),
                expiry_time=datetime.fromisoformat(cons_data["expiry_time"]) if cons_data["expiry_time"] else None,
                effects=effects,
                scope=ConsequenceScope[cons_data["scope"].upper()],
                type=ConsequenceType[cons_data["type"].upper()],
                applied=cons_data["applied"]
            )
            
            self.active_consequences[cid] = tracked
        
        self.ripple_effects = data.get("ripple_effects", [])


# Alias dla kompatybilności z testami
ConsequenceManager = ConsequenceTracker
ConsequenceSystem = ConsequenceTracker