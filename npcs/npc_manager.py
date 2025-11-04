"""
System zarządzania NPCami dla gry Droga Szamana RPG
Kompletny manager z obsługą behavior trees, pamięci i stanów emocjonalnych
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import systemów walki
from mechanics.combat import CombatStats, Injury, BodyPart, DamageType, CombatAction, CombatSystem
from player.skills import SkillSystem, SkillName

# Konfiguracja loggera - tylko poważne błędy
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class EmotionalState(Enum):
    """Stany emocjonalne NPCa"""
    HAPPY = "happy"
    ANGRY = "angry"
    FEAR = "fear"
    SAD = "sad"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


class NPCState(Enum):
    """Stany aktywności NPCa"""
    SLEEPING = "sleeping"
    WORKING = "working"
    EATING = "eating"
    SOCIALIZING = "socializing"
    RESTING = "resting"
    PATROLLING = "patrolling"
    IDLE = "idle"
    IN_DIALOGUE = "in_dialogue"
    FLEEING = "fleeing"
    ATTACKING = "attacking"


@dataclass
class Memory:
    """Pojedyncze wspomnienie"""
    timestamp: float
    event_type: str
    description: str
    participants: List[str]
    location: str
    importance: float  # 0.0 - 1.0
    emotional_impact: Dict[str, float]
    decay_rate: float = 0.01

    def get(self, key: str, default=None):
        """Kompatybilność z dict - pobierz atrybut lub wartość domyślną"""
        return getattr(self, key, default)

    def get_current_strength(self, current_time: float) -> float:
        """Oblicza aktualną siłę wspomnienia z uwzględnieniem zapominania"""
        time_passed = current_time - self.timestamp
        decay = time_passed * self.decay_rate
        strength = self.importance * max(0.1, 1.0 - decay)
        return strength


@dataclass
class Relationship:
    """Relacja z innym NPCem lub graczem"""
    target_id: str
    trust: float = 0.0  # -100 do 100
    affection: float = 0.0  # -100 do 100
    respect: float = 0.0  # -100 do 100
    fear: float = 0.0  # 0 do 100
    familiarity: float = 0.0  # 0 do 100
    last_interaction: float = 0.0
    interaction_count: int = 0
    
    def get_overall_disposition(self) -> float:
        """Oblicza ogólne nastawienie do osoby"""
        return (self.trust * 0.3 + self.affection * 0.3 + 
                self.respect * 0.2 - self.fear * 0.2) * (self.familiarity / 100)
    
    def update_from_interaction(self, interaction_type: str, intensity: float = 1.0):
        """Aktualizuje relację na podstawie interakcji"""
        self.interaction_count += 1
        self.familiarity = min(100, self.familiarity + 2)
        self.last_interaction = time.time()
        
        # Różne typy interakcji wpływają na różne aspekty relacji
        if interaction_type == "help":
            self.trust = min(100, self.trust + 5 * intensity)
            self.affection = min(100, self.affection + 3 * intensity)
            self.respect = min(100, self.respect + 2 * intensity)
        elif interaction_type == "threat":
            self.fear = min(100, self.fear + 10 * intensity)
            self.trust = max(-100, self.trust - 15 * intensity)
            self.respect = max(-100, self.respect - 5 * intensity)
        elif interaction_type == "bribe":
            self.trust = min(100, self.trust + 2 * intensity)
            self.respect = max(-100, self.respect - 3 * intensity)
        elif interaction_type == "betray":
            self.trust = max(-100, self.trust - 30 * intensity)
            self.affection = max(-100, self.affection - 20 * intensity)
            self.fear = min(100, self.fear + 5 * intensity)
        elif interaction_type == "friendly_chat":
            self.affection = min(100, self.affection + 2 * intensity)
            self.familiarity = min(100, self.familiarity + 3)
        elif interaction_type == "insult":
            self.affection = max(-100, self.affection - 5 * intensity)
            self.respect = max(-100, self.respect - 8 * intensity)


@dataclass
class Goal:
    """Cel NPCa"""
    name: str
    type: str  # Typ celu: "escape", "survive", "revenge", "wealth", "relationship", "knowledge"
    priority: float  # 0.0 - 1.0
    completion: float = 0.0  # 0.0 - 1.0
    deadline: Optional[float] = None
    prerequisites: List[str] = field(default_factory=list)
    active: bool = True
    
    def is_urgent(self, current_time: float) -> bool:
        """Sprawdza czy cel jest pilny"""
        if not self.deadline:
            return False
        return (self.deadline - current_time) < 3600  # Mniej niż godzina


class NPC:
    """Klasa reprezentująca pojedynczego NPCa"""
    
    def __init__(self, npc_data: Dict):
        self.id = npc_data["id"]
        self.name = npc_data["name"]
        self.role = npc_data["role"]
        # Użyj spawn_location (polskie nazwy) jeśli istnieje, fallback na location
        self.location = npc_data.get("spawn_location", npc_data.get("location", "cela_1"))
        self.personality = npc_data["personality"]
        self.quirks = npc_data.get("quirks", [])
        self.inventory = npc_data.get("inventory", {})
        self.gold = npc_data.get("gold", 0)
        
        # Stan
        self.current_state = NPCState.IDLE
        self.emotional_states = {
            EmotionalState.HAPPY: 0.0,
            EmotionalState.ANGRY: 0.0,
            EmotionalState.FEAR: 0.0,
            EmotionalState.SAD: 0.0,
            EmotionalState.SURPRISE: 0.0,
            EmotionalState.DISGUST: 0.0,
            EmotionalState.NEUTRAL: 1.0
        }
        
        # Harmonogram
        self.schedule = npc_data.get("schedule", self._create_default_schedule())
        self.schedule_variation = npc_data.get("schedule_variation", 0.1)
        
        # Pamięć - używamy IntegratedMemorySystem
        from .memory_system import IntegratedMemorySystem
        self.memory = IntegratedMemorySystem(self.id)
        
        # Zachowaj kompatybilność wsteczną
        self.episodic_memory: List[Memory] = []
        # semantic_memory jest teraz property wskazujące na memory.semantic
        self.procedural_memory: Dict[str, float] = {}  # Wyuczone zachowania
        self.emotional_memory: Dict[str, Dict[str, float]] = {}  # Emocje związane z miejscami/osobami
        
        # Relacje
        self.relationships: Dict[str, Relationship] = {}
        for rel_data in npc_data.get("initial_relationships", []):
            self.relationships[rel_data["target"]] = Relationship(
                target_id=rel_data["target"],
                trust=rel_data.get("trust", 0),
                affection=rel_data.get("affection", 0),
                respect=rel_data.get("respect", 0),
                fear=rel_data.get("fear", 0),
                familiarity=rel_data.get("familiarity", 0)
            )
        
        # Cele
        self.goals: List[Goal] = []
        for goal_data in npc_data.get("goals", []):
            self.goals.append(Goal(
                name=goal_data["name"],
                type=goal_data.get("type", goal_data["name"]),  # Użyj typu lub nazwy jako fallback
                priority=goal_data["priority"],
                prerequisites=goal_data.get("prerequisites", [])
            ))
        
        # Dialogi - zawsze zapewnij przynajmniej domyślne
        self.dialogue_bank = npc_data.get("dialogues", {})
        if not self.dialogue_bank or "default" not in self.dialogue_bank:
            # Dodaj domyślne dialogi jeśli brak
            self.dialogue_bank["default"] = [
                f"Czego chcesz, {'{player_name}'}?",
                "Nie mam teraz czasu na rozmowę.",
                "Co?",
                "Hmm?",
                f"Tak, {'{player_name}'}?"
            ]
        self.dialogue_cooldowns: Dict[str, float] = {}
        
        # Statystyki bojowe - pełna integracja z systemem walki
        self.combat_stats = self._initialize_combat_stats(npc_data)
        self.injuries: Dict[BodyPart, List[Injury]] = {part: [] for part in BodyPart}
        self.skills = self._initialize_skills(npc_data)
        
        # Kompatybilność wsteczna
        self.health = self.combat_stats.health
        self.max_health = self.combat_stats.max_health
        self.energy = npc_data.get("energy", 100)
        self.max_energy = npc_data.get("max_energy", 100)
        self.hunger = npc_data.get("hunger", 50)
        self.thirst = npc_data.get("thirst", 50)
        
        # Ekwipunek bojowy
        self.weapon = npc_data.get("weapon", None)
        self.armor = npc_data.get("armor", {})
        
        # Behavior tree (będzie przypisane przez AI system)
        self.behavior_tree = None
        
        # Ostatnia aktualizacja
        self.last_update = time.time()

        logger.info(f"NPC {self.name} zainicjalizowany")

    @property
    def current_location(self) -> str:
        """Alias dla self.location dla kompatybilności wstecznej."""
        return self.location

    @current_location.setter
    def current_location(self, value: str):
        """Setter dla current_location."""
        self.location = value

    @property
    def semantic_memory(self):
        """Alias dla self.memory.semantic dla kompatybilności wstecznej."""
        return self.memory.semantic

    def _initialize_combat_stats(self, npc_data: Dict) -> CombatStats:
        """Inicjalizuje statystyki bojowe NPCa."""
        # Bazowe atrybuty NPCa
        strength = npc_data.get("strength", random.randint(8, 15))
        endurance = npc_data.get("endurance", random.randint(8, 15))
        agility = npc_data.get("agility", random.randint(8, 15))
        
        # Oblicz statystyki na podstawie atrybutów
        max_health = 50 + endurance * 5
        max_stamina = 50 + endurance * 3 + strength * 2
        
        # Modyfikatory zależne od roli
        role_modifiers = {
            "guard": {"health": 1.2, "stamina": 1.1, "defense": 0.15},
            "prisoner": {"health": 0.9, "stamina": 0.9, "defense": 0.05},
            "merchant": {"health": 0.8, "stamina": 0.8, "defense": 0.0},
            "informant": {"health": 0.85, "stamina": 1.0, "defense": 0.1},
            "creature": {"health": 0.4, "stamina": 0.6, "defense": 0.0}  # Stworzenia są słabe
        }
        
        mods = role_modifiers.get(self.role, {"health": 1.0, "stamina": 1.0, "defense": 0.1})
        
        return CombatStats(
            health=max_health * mods["health"],
            max_health=max_health * mods["health"],
            stamina=max_stamina * mods["stamina"],
            max_stamina=max_stamina * mods["stamina"],
            pain=0.0,
            exhaustion=0.0,
            attack_speed=1.0 + (agility - 10) * 0.05,
            damage_multiplier=1.0 + (strength - 10) * 0.05,
            defense_multiplier=mods["defense"]
        )
    
    def _initialize_skills(self, npc_data: Dict) -> SkillSystem:
        """Inicjalizuje umiejętności NPCa."""
        skills = SkillSystem()
        
        # Umiejętności zależne od roli
        role_skills = {
            "guard": {
                SkillName.MIECZE: random.randint(25, 40),
                SkillName.WALKA_WRECZ: random.randint(20, 35),
                SkillName.WYTRZYMALOSC: random.randint(30, 45)
            },
            "prisoner": {
                SkillName.WALKA_WRECZ: random.randint(10, 25),
                SkillName.SKRADANIE: random.randint(15, 30),
                SkillName.PERSWAZJA: random.randint(10, 20)
            },
            "merchant": {
                SkillName.HANDEL: random.randint(40, 60),
                SkillName.PERSWAZJA: random.randint(30, 45),
                SkillName.WALKA_WRECZ: random.randint(5, 15)
            },
            "informant": {
                SkillName.SKRADANIE: random.randint(30, 45),
                SkillName.PERSWAZJA: random.randint(25, 40),
                SkillName.HANDEL: random.randint(20, 35)  # Zamiast oszustwa
            },
            "creature": {
                SkillName.WALKA_WRECZ: random.randint(5, 15),  # Słabe umiejętności walki
                SkillName.SKRADANIE: random.randint(20, 40),  # Dobre skradanie
                SkillName.WYTRZYMALOSC: random.randint(5, 10)  # Niska wytrzymałość
            }
        }
        
        # Ustaw umiejętności
        for skill_name, level in role_skills.get(self.role, {}).items():
            skill = skills.get_skill(skill_name)
            skill.level = level
            skill.total_uses = level * 10  # Symulacja doświadczenia
        
        return skills
    
    def _create_default_schedule(self) -> Dict[int, str]:
        """Tworzy domyślny harmonogram"""
        schedule = {}
        for hour in range(24):
            if 22 <= hour or hour < 6:
                schedule[hour] = "sleeping"
            elif 6 <= hour < 7:
                schedule[hour] = "waking_routine"
            elif 7 <= hour < 8:
                schedule[hour] = "eating"
            elif 8 <= hour < 12:
                schedule[hour] = "working"
            elif 12 <= hour < 13:
                schedule[hour] = "eating"
            elif 13 <= hour < 18:
                schedule[hour] = "working"
            elif 18 <= hour < 19:
                schedule[hour] = "eating"
            elif 19 <= hour < 22:
                schedule[hour] = "socializing"
        return schedule
    
    def update(self, delta_time: float, world_context: Dict):
        """Aktualizuje stan NPCa"""
        current_time = time.time()
        
        # Aktualizuj potrzeby fizjologiczne
        self._update_needs(delta_time)
        
        # Aktualizuj stany emocjonalne
        self._decay_emotions(delta_time)
        
        # Sprawdź harmonogram
        self._check_schedule(current_time)
        
        # Przetwórz wspomnienia
        self._process_memories(current_time)
        
        # Aktualizuj cele
        self._update_goals(current_time)
        
        # Wykonaj behavior tree
        if self.behavior_tree:
            self.behavior_tree.execute(self, world_context)
        
        self.last_update = current_time
    
    def _update_needs(self, delta_time: float):
        """Aktualizuje potrzeby fizjologiczne"""
        # Głód i pragnienie rosną z czasem
        self.hunger = min(100, self.hunger + delta_time * 0.01)
        self.thirst = min(100, self.thirst + delta_time * 0.02)
        
        # Energia spada podczas aktywności, regeneruje się podczas snu
        if self.current_state == NPCState.SLEEPING:
            self.energy = min(self.max_energy, self.energy + delta_time * 0.05)
        elif self.current_state in [NPCState.WORKING, NPCState.PATROLLING]:
            self.energy = max(0, self.energy - delta_time * 0.02)
        else:
            self.energy = max(0, self.energy - delta_time * 0.01)
        
        # Potrzeby wpływają na emocje
        if self.hunger > 80:
            self.modify_emotion(EmotionalState.ANGRY, 0.1)
            self.modify_emotion(EmotionalState.SAD, 0.05)
        if self.energy < 20:
            self.modify_emotion(EmotionalState.SAD, 0.1)
    
    def _decay_emotions(self, delta_time: float):
        """Wygasza emocje z czasem"""
        decay_rate = 0.01 * delta_time
        for emotion in self.emotional_states:
            if emotion != EmotionalState.NEUTRAL:
                self.emotional_states[emotion] = max(0, self.emotional_states[emotion] - decay_rate)
        
        # Normalizuj emocje
        total = sum(self.emotional_states.values())
        if total > 0:
            for emotion in self.emotional_states:
                self.emotional_states[emotion] /= total
        else:
            self.emotional_states[EmotionalState.NEUTRAL] = 1.0
    
    def _check_schedule(self, current_time: float):
        """Sprawdza i aktualizuje aktywność według harmonogramu"""
        current_hour = datetime.fromtimestamp(current_time).hour
        
        # Dodaj losową wariację do harmonogramu
        if random.random() < self.schedule_variation:
            return  # Czasem ignoruj harmonogram
        
        scheduled_activity = self.schedule.get(current_hour, "idle")
        
        # Mapuj aktywność na stan
        activity_to_state = {
            "sleeping": NPCState.SLEEPING,
            "eating": NPCState.EATING,
            "working": NPCState.WORKING if self.role != "prisoner" else NPCState.IDLE,
            "socializing": NPCState.SOCIALIZING,
            "patrolling": NPCState.PATROLLING,
            "waking_routine": NPCState.IDLE,
            "idle": NPCState.IDLE
        }
        
        # Zmień stan tylko jeśli nie jest w trakcie ważniejszej aktywności
        if self.current_state not in [NPCState.FLEEING, NPCState.ATTACKING, NPCState.IN_DIALOGUE]:
            new_state = activity_to_state.get(scheduled_activity, NPCState.IDLE)
            if new_state != self.current_state:
                self.change_state(new_state)
    
    def _process_memories(self, current_time: float):
        """Przetwarza i konsoliduje wspomnienia"""
        # Usuń bardzo słabe wspomnienia
        self.episodic_memory = [
            mem for mem in self.episodic_memory 
            if mem.get_current_strength(current_time) > 0.05
        ]
        
        # Ogranicz liczbę wspomnień do 1000
        if len(self.episodic_memory) > 1000:
            # Zachowaj tylko najważniejsze
            self.episodic_memory.sort(key=lambda m: m.get_current_strength(current_time), reverse=True)
            self.episodic_memory = self.episodic_memory[:1000]
    
    def _update_goals(self, current_time: float):
        """Aktualizuje cele NPCa"""
        # Sortuj cele według priorytetu i pilności
        self.goals.sort(key=lambda g: (
            g.priority * (2.0 if g.is_urgent(current_time) else 1.0),
            g.completion
        ), reverse=True)
        
        # Dezaktywuj ukończone cele
        for goal in self.goals:
            if goal.completion >= 1.0:
                goal.active = False
    
    def change_state(self, new_state: NPCState):
        """Zmienia stan NPCa"""
        if self.current_state != new_state:
            logger.debug(f"{self.name} zmienia stan z {self.current_state.value} na {new_state.value}")
            
            # Zapisz zmianę jako wspomnienie
            self.add_memory(
                event_type="state_change",
                description=f"Zmiana stanu z {self.current_state.value} na {new_state.value}",
                participants=[self.id],
                location=self.location,
                importance=0.1
            )
            
            self.current_state = new_state
    
    def modify_emotion(self, emotion: EmotionalState, intensity: float):
        """Modyfikuje stan emocjonalny"""
        self.emotional_states[emotion] = min(1.0, self.emotional_states[emotion] + intensity)
        
        # Zmniejsz neutralność
        self.emotional_states[EmotionalState.NEUTRAL] = max(0, 
            self.emotional_states[EmotionalState.NEUTRAL] - intensity * 0.5)
        
        # Normalizuj
        total = sum(self.emotional_states.values())
        if total > 0:
            for e in self.emotional_states:
                self.emotional_states[e] /= total
    
    def get_dominant_emotion(self) -> EmotionalState:
        """Zwraca dominującą emocję"""
        return max(self.emotional_states, key=self.emotional_states.get)
    
    def add_memory(self, event_type: str, description: str, participants: List[str], 
                   location: str, importance: float, emotional_impact: Optional[Dict[str, float]] = None):
        """Dodaje nowe wspomnienie"""
        if emotional_impact is None:
            emotional_impact = {}
        
        memory = Memory(
            timestamp=time.time(),
            event_type=event_type,
            description=description,
            participants=participants,
            location=location,
            importance=importance,
            emotional_impact=emotional_impact,
            decay_rate=0.01 / max(0.1, importance)  # Ważniejsze wspomnienia wolniej zanikają
        )
        
        self.episodic_memory.append(memory)
        
        # Aktualizuj pamięć emocjonalną
        for participant in participants:
            if participant not in self.emotional_memory:
                self.emotional_memory[participant] = {}
            for emotion, value in emotional_impact.items():
                if emotion not in self.emotional_memory[participant]:
                    self.emotional_memory[participant][emotion] = 0
                self.emotional_memory[participant][emotion] += value
        
        # Wpływ na bieżące emocje
        for emotion_name, impact in emotional_impact.items():
            if hasattr(EmotionalState, emotion_name.upper()):
                emotion = EmotionalState[emotion_name.upper()]
                self.modify_emotion(emotion, impact * importance)
    
    def recall_memories(self, query_type: Optional[str] = None, 
                       participant: Optional[str] = None,
                       location: Optional[str] = None,
                       time_range: Optional[Tuple[float, float]] = None,
                       limit: int = 10) -> List[Memory]:
        """Przywołuje wspomnienia według kryteriów"""
        current_time = time.time()
        relevant_memories = []
        
        for memory in self.episodic_memory:
            # Filtruj według kryteriów
            if query_type and memory.event_type != query_type:
                continue
            if participant and participant not in memory.participants:
                continue
            if location and memory.location != location:
                continue
            if time_range and not (time_range[0] <= memory.timestamp <= time_range[1]):
                continue
            
            relevant_memories.append(memory)
        
        # Sortuj według siły wspomnienia
        relevant_memories.sort(
            key=lambda m: m.get_current_strength(current_time), 
            reverse=True
        )
        
        return relevant_memories[:limit]
    
    def get_relationship(self, target_id: str) -> Relationship:
        """Zwraca relację z daną osobą"""
        if target_id not in self.relationships:
            self.relationships[target_id] = Relationship(target_id=target_id)
        return self.relationships[target_id]
    
    def interact_with(self, target_id: str, interaction_type: str, intensity: float = 1.0):
        """Przeprowadza interakcję z inną postacią"""
        relationship = self.get_relationship(target_id)
        relationship.update_from_interaction(interaction_type, intensity)
        
        # Zapisz jako wspomnienie
        emotional_impact = {}
        if interaction_type == "help":
            emotional_impact["happy"] = 0.3
        elif interaction_type == "threat":
            emotional_impact["fear"] = 0.5
            emotional_impact["angry"] = 0.3
        elif interaction_type == "betray":
            emotional_impact["angry"] = 0.6
            emotional_impact["sad"] = 0.4
        
        self.add_memory(
            event_type=f"interaction_{interaction_type}",
            description=f"Interakcja typu {interaction_type} z {target_id}",
            participants=[self.id, target_id],
            location=self.location,
            importance=0.3 * intensity,
            emotional_impact=emotional_impact
        )
    
    def get_dialogue(self, context: Dict) -> Optional[str]:
        """Wybiera odpowiedni dialog na podstawie kontekstu"""
        current_time = time.time()
        emotion = self.get_dominant_emotion()
        
        # Określ kategorię dialogu
        dialogue_category = "default"
        
        # Sprawdź kontekst
        if "player_id" in context:
            player_id = context["player_id"]
            relationship = self.get_relationship(player_id)
            disposition = relationship.get_overall_disposition()
            
            if disposition > 50:
                dialogue_category = "friendly"
            elif disposition < -50:
                dialogue_category = "hostile"
            elif relationship.fear > 70:
                dialogue_category = "fearful"
            elif relationship.familiarity < 10:
                dialogue_category = "first_meeting"
        
        # Uwzględnij stan emocjonalny
        if emotion == EmotionalState.ANGRY:
            dialogue_category = f"{dialogue_category}_angry"
        elif emotion == EmotionalState.FEAR:
            dialogue_category = f"{dialogue_category}_fearful"
        elif emotion == EmotionalState.HAPPY:
            dialogue_category = f"{dialogue_category}_happy"
        elif emotion == EmotionalState.SAD:
            dialogue_category = f"{dialogue_category}_sad"
        
        # Uwzględnij porę dnia
        hour = datetime.fromtimestamp(current_time).hour
        if 22 <= hour or hour < 6:
            dialogue_category = f"{dialogue_category}_night"
        elif 6 <= hour < 12:
            dialogue_category = f"{dialogue_category}_morning"
        elif 12 <= hour < 18:
            dialogue_category = f"{dialogue_category}_afternoon"
        else:
            dialogue_category = f"{dialogue_category}_evening"
        
        # Uwzględnij stan NPCa
        if self.current_state == NPCState.WORKING:
            dialogue_category = f"{dialogue_category}_busy"
        elif self.current_state == NPCState.EATING:
            dialogue_category = f"{dialogue_category}_eating"
        elif self.current_state == NPCState.SLEEPING:
            return None  # Śpi, nie odpowiada
        
        # Znajdź odpowiedni dialog
        dialogues = self.dialogue_bank.get(dialogue_category, 
                                          self.dialogue_bank.get("default", []))
        
        if not dialogues:
            # Zawsze zwróć coś, nawet jeśli to tylko podstawowy dialog
            dialogues = self.dialogue_bank.get("default", [f"...", f"*{self.name} milczy*"])
        
        # Wybierz dialog z uwzględnieniem cooldownów
        available_dialogues = []
        for dialogue in dialogues:
            dialogue_id = f"{dialogue_category}_{dialogues.index(dialogue)}"
            if dialogue_id not in self.dialogue_cooldowns or \
               current_time - self.dialogue_cooldowns[dialogue_id] > 300:  # 5 minut cooldown
                available_dialogues.append((dialogue_id, dialogue))
        
        if not available_dialogues:
            # Jeśli wszystkie na cooldownie, wybierz losowy
            dialogue = random.choice(dialogues)
            dialogue_id = f"{dialogue_category}_{dialogues.index(dialogue)}"
        else:
            dialogue_id, dialogue = random.choice(available_dialogues)
        
        # Ustaw cooldown
        self.dialogue_cooldowns[dialogue_id] = current_time
        
        # Zastąp zmienne w dialogu
        dialogue = dialogue.replace("{player_name}", context.get("player_name", "nieznajomy"))
        dialogue = dialogue.replace("{time}", datetime.fromtimestamp(current_time).strftime("%H:%M"))
        dialogue = dialogue.replace("{location}", self.location)
        
        return dialogue
    
    def can_be_bribed(self, amount: int) -> bool:
        """Sprawdza czy NPC może być przekupiony"""
        if "corruptible" not in self.personality:
            return False
        
        # Uwzględnij stan emocjonalny i potrzeby
        desperation = (self.hunger / 100) * 0.3 + (100 - self.energy) / 100 * 0.2
        greed_factor = 0.5 if "greedy" in self.personality else 0.2
        
        required_amount = 50 * (1 - desperation - greed_factor)
        
        return amount >= required_amount
    
    def accept_bribe(self, amount: int, from_id: str):
        """Przyjmuje łapówkę"""
        self.gold += amount
        self.interact_with(from_id, "bribe", intensity=amount/50)
        
        self.add_memory(
            event_type="bribe_accepted",
            description=f"Przyjął łapówkę {amount} złota od {from_id}",
            participants=[self.id, from_id],
            location=self.location,
            importance=0.6,
            emotional_impact={"happy": 0.3, "disgust": 0.2}
        )
        
        # Może wpłynąć na cele
        for goal in self.goals:
            if goal.name == "gather_gold":
                goal.completion = min(1.0, goal.completion + amount/100)
    
    def share_information(self, info_type: str, with_id: str) -> Optional[str]:
        """Dzieli się informacjami z inną postacią"""
        relationship = self.get_relationship(with_id)
        
        # Sprawdź czy chce się podzielić informacją
        if relationship.trust < -20:
            return None  # Nie ufa, nie podzieli się
        
        # Sprawdź co wie
        if info_type == "tunnel":
            if "tunnel_location" in self.semantic_memory:
                if relationship.trust > 30 or self.gold < 20:  # Ufa lub jest zdesperowany
                    return self.semantic_memory["tunnel_location"]
        elif info_type == "guard_schedule":
            if "guard_patterns" in self.semantic_memory:
                if relationship.trust > 20 or relationship.fear > 60:
                    return self.semantic_memory["guard_patterns"]
        elif info_type == "weakness":
            # Sprawdź wspomnienia o słabościach
            memories = self.recall_memories(query_type="observed_weakness", limit=5)
            if memories and (relationship.trust > 50 or relationship.fear > 80):
                return memories[0].description
        
        return None
    
    # ========== METODY WALKI ==========
    
    def take_damage(self, damage: float, body_part: BodyPart, 
                   damage_type: DamageType, injury: Optional[Injury] = None) -> str:
        """
        Przyjmuje obrażenia.
        
        Args:
            damage: Ilość obrażeń
            body_part: Trafiona część ciała
            damage_type: Typ obrażeń
            injury: Kontuzja do dodania
        
        Returns:
            Opis efektu
        """
        # Redukcja przez pancerz
        armor_protection = self._get_armor_protection(body_part)
        final_damage = damage * (1.0 - armor_protection)
        
        # Aplikuj obrażenia
        combat_system = CombatSystem()
        effect = combat_system.apply_damage(
            self.combat_stats,
            final_damage,
            body_part,
            damage_type,
            injury
        )
        
        # Dodaj kontuzję
        if injury:
            self.injuries[body_part].append(injury)
        
        # Aktualizuj health dla kompatybilności
        self.health = self.combat_stats.health
        
        # Zmień stan emocjonalny
        self.modify_emotion(EmotionalState.FEAR, damage / 50)
        self.modify_emotion(EmotionalState.ANGRY, damage / 100)
        
        # Dodaj wspomnienie o ataku
        self.add_memory(
            event_type="attacked",
            description=f"Został zaatakowany - {damage:.1f} obrażeń w {body_part.value}",
            participants=["player"],
            location=self.location,
            importance=0.8,
            emotional_impact={"fear": 0.6, "angry": 0.4}
        )
        
        # Sprawdź śmierć
        if self.combat_stats.health <= 0:
            self.current_state = NPCState.IDLE  # Martwy
            return f"{self.name} pada martwy!"
        
        # Zmień stan na ucieczkę lub atak w zależności od osobowości
        if self.combat_stats.health < 30:
            if any(trait in self.personality for trait in ["coward", "cowardly"]) or self.role in ["merchant", "creature"]:
                self.current_state = NPCState.FLEEING
            else:
                self.current_state = NPCState.ATTACKING
        
        return effect
    
    def attack(self, target: Any) -> Tuple[bool, str]:
        """
        Atakuje cel.
        
        Args:
            target: Cel ataku
        
        Returns:
            (sukces, wiadomość)
        """
        combat_system = CombatSystem()
        
        # Wybierz akcję bojową na podstawie osobowości
        if "aggressive" in self.personality:
            action = CombatAction.ATAK_SILNY
        elif "cautious" in self.personality:
            action = CombatAction.ATAK_SZYBKI
        else:
            action = CombatAction.ATAK_PODSTAWOWY
        
        # Pobierz umiejętność walki
        weapon_skill = SkillName.MIECZE if self.weapon else SkillName.WALKA_WRECZ
        skill_level = self.skills.get_skill(weapon_skill).level
        
        # Obrażenia broni
        weapon_damage = 10 if self.weapon else 5
        damage_type = DamageType.CIECIE if self.weapon else DamageType.OBUCHOWE
        
        # Wykonaj atak
        success, result = combat_system.perform_attack(
            self.combat_stats,
            target.combat_stats if hasattr(target, 'combat_stats') else CombatStats(),
            skill_level,
            target.skills.get_skill(SkillName.WALKA_WRECZ).level if hasattr(target, 'skills') else 10,
            action,
            weapon_damage,
            damage_type
        )
        
        if success and result['hit']:
            # Aplikuj obrażenia do celu
            if hasattr(target, 'take_damage'):
                target.take_damage(result['damage'], result['body_part'], 
                                 damage_type, result.get('injury'))
            
            # Użyj umiejętności (może się rozwinąć)
            self.skills.use_skill(weapon_skill, 50, self.combat_stats.pain, {})
            
            return True, f"{self.name}: {result['description']}"
        else:
            return False, f"{self.name}: Atak nieudany!"
    
    def defend(self) -> Tuple[bool, str]:
        """
        Przyjmuje postawę obronną.
        
        Returns:
            (sukces, wiadomość)
        """
        combat_system = CombatSystem()
        # Użyj wytrzymałości jako umiejętności obronnej
        skill_level = self.skills.get_skill(SkillName.WYTRZYMALOSC).level
        
        success, reduction = combat_system.perform_defense(
            self.combat_stats,
            skill_level,
            CombatAction.OBRONA
        )
        
        if success:
            self.combat_stats.defense_multiplier = reduction
            return True, f"{self.name} przyjmuje postawę obronną"
        else:
            return False, f"{self.name} nie zdołał się obronić"
    
    def flee(self) -> bool:
        """
        Próbuje uciec z walki.
        
        Returns:
            True jeśli udało się uciec
        """
        # Szansa na ucieczkę zależy od zręczności i stanu
        flee_chance = 0.5
        
        if self.combat_stats.pain > 50:
            flee_chance -= 0.2
        if self.combat_stats.exhaustion > 70:
            flee_chance -= 0.3
        
        if "coward" in self.personality:
            flee_chance += 0.2
        if "brave" in self.personality:
            flee_chance -= 0.3
        
        if random.random() < flee_chance:
            self.current_state = NPCState.FLEEING
            # Zmień lokację na losową sąsiednią
            # TODO: Integracja z systemem lokacji
            return True
        
        return False
    
    def _get_armor_protection(self, body_part: BodyPart) -> float:
        """
        Zwraca ochronę pancerza dla części ciała.
        
        Args:
            body_part: Część ciała
        
        Returns:
            Redukcja obrażeń (0.0 - 0.8)
        """
        if not self.armor:
            return 0.0
        
        part_mapping = {
            BodyPart.GLOWA: 'glowa',
            BodyPart.TULOW: 'tulow',
            BodyPart.LEWA_REKA: 'rece',
            BodyPart.PRAWA_REKA: 'rece',
            BodyPart.LEWA_NOGA: 'nogi',
            BodyPart.PRAWA_NOGA: 'nogi'
        }
        
        armor_slot = part_mapping.get(body_part, 'tulow')
        armor_piece = self.armor.get(armor_slot)
        
        if not armor_piece:
            return 0.0
        
        # Strażnicy mają lepszy pancerz
        if self.role == "guard":
            return min(0.5, armor_piece.get('protection', 0.2))
        else:
            return min(0.3, armor_piece.get('protection', 0.1))
    
    def recover(self, minutes: int = 1):
        """
        Regeneracja zdrowia i staminy.
        
        Args:
            minutes: Czas regeneracji w minutach
        """
        combat_system = CombatSystem()
        
        # Regeneracja staminy
        combat_system.recover_stamina(
            self.combat_stats,
            is_resting=(self.current_state == NPCState.RESTING),
            time_passed=minutes * 60
        )
        
        # Redukcja bólu
        if self.combat_stats.pain > 0:
            pain_reduction = minutes * 0.3
            combat_system.reduce_pain(
                self.combat_stats,
                pain_reduction,
                is_medical=False
            )
        
        # Leczenie kontuzji
        for body_part, injuries in self.injuries.items():
            for injury in injuries[:]:
                blood_loss, healed = injury.update(minutes)
                
                if blood_loss > 0:
                    self.combat_stats.health -= blood_loss
                    self.health = self.combat_stats.health
                
                if healed:
                    injuries.remove(injury)
        
        # Bardzo wolna regeneracja zdrowia
        if self.current_state == NPCState.SLEEPING:
            health_regen = minutes * 0.2
            self.combat_stats.health = min(
                self.combat_stats.max_health,
                self.combat_stats.health + health_regen
            )
            self.health = self.combat_stats.health
    
    def to_dict(self) -> Dict:
        """Serializuje NPCa do słownika"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "location": self.location,
            "personality": self.personality,
            "quirks": self.quirks,
            "inventory": self.inventory,
            "gold": self.gold,
            "health": self.health,
            "energy": self.energy,
            "hunger": self.hunger,
            "thirst": self.thirst,
            "current_state": self.current_state.value,
            "emotional_states": {e.value: v for e, v in self.emotional_states.items()},
            "relationships": {
                tid: {
                    "trust": r.trust,
                    "affection": r.affection,
                    "respect": r.respect,
                    "fear": r.fear,
                    "familiarity": r.familiarity
                } for tid, r in self.relationships.items()
            },
            "goals": [
                {
                    "name": g.name,
                    "priority": g.priority,
                    "completion": g.completion,
                    "active": g.active
                } for g in self.goals
            ],
            "episodic_memory_count": len(self.episodic_memory)
        }
    
    def modify_relationship(self, target: str, trust: float = 0, affection: float = 0, 
                           fear: float = 0, respect: float = 0, familiarity: float = 0):
        """
        Modyfikuje relację z daną osobą.
        
        Args:
            target: ID osoby
            trust: Zmiana zaufania
            affection: Zmiana sympatii
            fear: Zmiana strachu
            respect: Zmiana szacunku
        """
        if target not in self.relationships:
            self.relationships[target] = Relationship(target_id=target)
        
        rel = self.relationships[target]
        rel.trust = max(-100, min(100, rel.trust + trust))
        rel.affection = max(-100, min(100, rel.affection + affection))
        rel.fear = max(0, min(100, rel.fear + fear))
        rel.respect = max(-100, min(100, rel.respect + respect))
        rel.familiarity = max(0, min(100, rel.familiarity + familiarity))


class NPCManager:
    """Manager zarządzający wszystkimi NPCami"""
    
    def __init__(self, data_file: str = "data/npc_complete.json"):
        self.npcs: Dict[str, NPC] = {}
        self.data_file = data_file
        self.world_events: List[Dict] = []
        self.time_scale = 60  # 1 sekunda = 1 minuta w grze
        self.last_update = time.time()
        
        # Wczytaj NPCów
        self.load_npcs()
        
        logger.info(f"NPCManager zainicjalizowany z {len(self.npcs)} NPCami")
    
    def load_npcs(self):
        """Wczytuje NPCów z pliku"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Nowa struktura - NPCs są w słowniku, nie liście
            npcs_data = data.get("npcs", {})
            
            for npc_id, npc_data in npcs_data.items():
                # Upewnij się że ID jest ustawione
                npc_data["id"] = npc_id
                
                # Konwertuj stats do odpowiedniego formatu jeśli potrzeba
                if "stats" in npc_data:
                    stats = npc_data["stats"]
                    # Przenieś stats do głównego poziomu dla kompatybilności
                    npc_data["health"] = stats.get("health", 100)
                    npc_data["max_health"] = stats.get("max_health", 100)
                    npc_data["energy"] = stats.get("energy", 100)
                    npc_data["max_energy"] = stats.get("max_energy", 100)
                    npc_data["strength"] = stats.get("strength", 50)
                    npc_data["agility"] = stats.get("agility", 50)
                    npc_data["intelligence"] = stats.get("intelligence", 50)
                
                npc = NPC(npc_data)
                self.npcs[npc.id] = npc
                
                # Przypisz behavior tree
                from .ai_behaviors import create_behavior_tree
                npc.behavior_tree = create_behavior_tree(npc.role, npc.personality)
            
            # Załaduj też schedule templates jeśli są
            self.schedule_templates = data.get("schedule_templates", {})
            logger.info(f"Załadowano {len(self.schedule_templates)} szablonów harmonogramów")
                
        except FileNotFoundError:
            logger.error(f"Plik {self.data_file} nie znaleziony")
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania JSON: {e}")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania NPCów: {e}")
    
    def update(self, delta_time=None, world_context=None):
        """Aktualizuje wszystkie NPCe"""
        current_time = time.time()
        
        # Użyj przekazane parametry lub oblicz domyślne
        if delta_time is None:
            delta_time = (current_time - self.last_update) * self.time_scale
        
        # Przygotuj kontekst świata jeśli nie został przekazany
        if world_context is None:
            world_context = {
                "time": current_time,
                "hour": datetime.fromtimestamp(current_time).hour,
                "npcs": self.npcs,
                "events": self.world_events[-10:],  # Ostatnie 10 wydarzeń
            }
        
        # Aktualizuj każdego NPCa
        for npc in self.npcs.values():
            npc.update(delta_time, world_context)
        
        # Przetwórz interakcje między NPCami
        self._process_npc_interactions()
        
        # Wyczyść stare wydarzenia
        if len(self.world_events) > 100:
            self.world_events = self.world_events[-50:]
        
        self.last_update = current_time
    
    def _process_npc_interactions(self):
        """Przetwarza automatyczne interakcje między NPCami"""
        for npc1_id, npc1 in self.npcs.items():
            if npc1.current_state != NPCState.SOCIALIZING:
                continue
                
            for npc2_id, npc2 in self.npcs.items():
                if npc1_id == npc2_id:
                    continue
                    
                # Sprawdź czy są w tym samym miejscu
                if npc1.location != npc2.location:
                    continue
                
                # Sprawdź czy mogą wejść w interakcję
                if npc2.current_state not in [NPCState.SOCIALIZING, NPCState.IDLE]:
                    continue
                
                # Losowa szansa na interakcję
                if random.random() < 0.1:  # 10% szans na interakcję
                    self._simulate_npc_interaction(npc1, npc2)
    
    def _simulate_npc_interaction(self, npc1: NPC, npc2: NPC):
        """Symuluje interakcję między dwoma NPCami"""
        relationship1 = npc1.get_relationship(npc2.id)
        relationship2 = npc2.get_relationship(npc1.id)
        
        # Określ typ interakcji na podstawie relacji
        if relationship1.get_overall_disposition() > 30:
            # Przyjazna interakcja
            if random.random() < 0.7:
                interaction_type = "friendly_chat"
            else:
                interaction_type = "help"
        elif relationship1.get_overall_disposition() < -30:
            # Wroga interakcja
            if random.random() < 0.8:
                interaction_type = "insult"
            else:
                interaction_type = "threat"
        else:
            # Neutralna interakcja
            interaction_type = "friendly_chat"
        
        # Przeprowadź interakcję
        npc1.interact_with(npc2.id, interaction_type)
        npc2.interact_with(npc1.id, interaction_type)
        
        # Zapisz wydarzenie
        self.add_world_event({
            "type": "npc_interaction",
            "participants": [npc1.id, npc2.id],
            "interaction_type": interaction_type,
            "location": npc1.location,
            "timestamp": time.time()
        })
        
        logger.debug(f"Interakcja: {npc1.name} -> {interaction_type} -> {npc2.name}")
    
    def add_world_event(self, event: Dict):
        """Dodaje wydarzenie do historii świata"""
        self.world_events.append(event)
        
        # Powiadom NPCów w pobliżu
        for npc in self.npcs.values():
            if npc.location == event.get("location"):
                # NPC może zapamiętać wydarzenie
                if random.random() < 0.5:  # 50% szans na zapamiętanie
                    importance = 0.2
                    if npc.id in event.get("participants", []):
                        importance = 0.5
                    
                    npc.add_memory(
                        event_type=f"witnessed_{event['type']}",
                        description=f"Był świadkiem: {event.get('description', event['type'])}",
                        participants=event.get("participants", []),
                        location=event.get("location", "unknown"),
                        importance=importance
                    )
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Zwraca NPCa po ID"""
        return self.npcs.get(npc_id)
    
    def get_npcs_in_location(self, location: str) -> List[NPC]:
        """Zwraca listę NPCów w danej lokacji"""
        return [npc for npc in self.npcs.values() if npc.location == location]
    
    def player_interact(self, player_id: str, npc_id: str, action: str, **kwargs) -> Dict:
        """Obsługuje interakcję gracza z NPCem"""
        npc = self.get_npc(npc_id)
        if not npc:
            return {"success": False, "message": "NPC nie znaleziony"}
        
        result = {"success": False, "message": "", "response": None}
        
        if action == "talk":
            # Rozmowa
            context = {
                "player_id": player_id,
                "player_name": kwargs.get("player_name", "nieznajomy"),
            }
            
            dialogue = npc.get_dialogue(context)
            if dialogue:
                npc.change_state(NPCState.IN_DIALOGUE)
                npc.interact_with(player_id, "friendly_chat")
                result["success"] = True
                result["response"] = dialogue
                
                # NPC może podzielić się informacją
                if random.random() < 0.3:  # 30% szans
                    info = npc.share_information("random", player_id)
                    if info:
                        result["extra_info"] = info
            else:
                result["message"] = f"{npc.name} nie chce rozmawiać"
                result["response"] = f"*{npc.name} milczy*"  # Zawsze zwróć jakiś string
        
        elif action == "bribe":
            # Łapówka
            amount = kwargs.get("amount", 0)
            if npc.can_be_bribed(amount):
                npc.accept_bribe(amount, player_id)
                result["success"] = True
                result["message"] = f"{npc.name} przyjął łapówkę"
                
                # Może dać informację w zamian
                info = npc.share_information(kwargs.get("info_type", "random"), player_id)
                if info:
                    result["response"] = info
            else:
                result["message"] = f"{npc.name} odrzucił łapówkę"
                npc.interact_with(player_id, "insult", 0.5)
        
        elif action == "attack":
            # Atak
            npc.change_state(NPCState.FLEEING)
            npc.interact_with(player_id, "threat", 2.0)
            npc.health -= kwargs.get("damage", 10)
            
            # Alarm
            self.add_world_event({
                "type": "attack",
                "participants": [player_id, npc_id],
                "location": npc.location,
                "description": f"{player_id} zaatakował {npc.name}",
                "timestamp": time.time()
            })
            
            result["success"] = True
            result["message"] = f"Zaatakowałeś {npc.name}"
            
            # Strażnicy reagują
            for other_npc in self.get_npcs_in_location(npc.location):
                if other_npc.role == "guard" and other_npc.id != npc_id:
                    other_npc.change_state(NPCState.ATTACKING)
                    other_npc.interact_with(player_id, "threat", 1.5)
        
        elif action == "give_item":
            # Danie przedmiotu
            item = kwargs.get("item")
            if item:
                npc.inventory[item] = npc.inventory.get(item, 0) + 1
                npc.interact_with(player_id, "help", 0.5)
                result["success"] = True
                result["message"] = f"Dałeś {item} {npc.name}"
                
                # Specjalne reakcje na przedmioty
                if item == "food" and npc.hunger > 60:
                    npc.hunger = max(0, npc.hunger - 30)
                    npc.modify_emotion(EmotionalState.HAPPY, 0.3)
                    result["response"] = "Dziękuję! Byłem bardzo głodny."
        
        return result
    
    def save_state(self, filename: str):
        """Zapisuje stan wszystkich NPCów"""
        state = {
            "npcs": {npc_id: npc.to_dict() for npc_id, npc in self.npcs.items()},
            "world_events": self.world_events[-50:],  # Ostatnie 50 wydarzeń
            "timestamp": time.time()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Stan zapisany do {filename}")
    
    def get_save_state(self) -> Dict[str, Any]:
        """Zwraca stan NPCów do zapisu w game_state.
        
        Returns:
            Słownik ze stanem NPCów
        """
        return {
            "npcs": {npc_id: npc.to_dict() for npc_id, npc in self.npcs.items()},
            "world_events": self.world_events[-50:],  # Ostatnie 50 wydarzeń
            "timestamp": time.time()
        }
    
    def load_state(self, filename: str):
        """Wczytuje stan NPCów z pliku"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Odtwórz wydarzenia
            self.world_events = state.get("world_events", [])
            
            # Aktualizuj stany NPCów
            for npc_id, npc_state in state["npcs"].items():
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    # Odtwórz podstawowe stany
                    npc.health = npc_state["health"]
                    npc.energy = npc_state["energy"]
                    npc.hunger = npc_state["hunger"]
                    npc.thirst = npc_state["thirst"]
                    npc.gold = npc_state.get("gold", 0)
                    
                    # Odtwórz relacje
                    for rel_id, rel_data in npc_state["relationships"].items():
                        rel = Relationship(target_id=rel_id)
                        rel.trust = rel_data["trust"]
                        rel.affection = rel_data["affection"]
                        rel.respect = rel_data["respect"]
                        rel.fear = rel_data["fear"]
                        rel.familiarity = rel_data["familiarity"]
                        npc.relationships[rel_id] = rel
            
            logger.info(f"Stan wczytany z {filename}")
            
        except FileNotFoundError:
            logger.warning(f"Plik stanu {filename} nie znaleziony")
        except json.JSONDecodeError as e:
            logger.error(f"Błąd wczytywania stanu: {e}")
    
    def load_state_from_dict(self, state: Dict[str, Any]):
        """Wczytuje stan NPCów ze słownika (dla game_state).
        
        Args:
            state: Słownik ze stanem NPCów
        """
        try:
            # Odtwórz wydarzenia
            self.world_events = state.get("world_events", [])
            
            # Aktualizuj stany NPCów
            for npc_id, npc_state in state.get("npcs", {}).items():
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    # Odtwórz podstawowe stany
                    npc.health = npc_state.get("health", 100)
                    npc.energy = npc_state.get("energy", 100)
                    npc.hunger = npc_state.get("hunger", 0)
                    npc.thirst = npc_state.get("thirst", 0)
                    npc.gold = npc_state.get("gold", 0)
                    
                    # Odtwórz relacje jeśli są
                    if "relationships" in npc_state:
                        for rel_id, rel_data in npc_state["relationships"].items():
                            rel = Relationship(target_id=rel_id)
                            rel.trust = rel_data.get("trust", 0)
                            rel.affection = rel_data.get("affection", 0)
                            rel.respect = rel_data.get("respect", 0)
                            rel.fear = rel_data.get("fear", 0)
                            rel.familiarity = rel_data.get("familiarity", 0)
                            npc.relationships[rel_id] = rel
            
            logger.info("Stan wczytany ze słownika")
        except Exception as e:
            logger.error(f"Błąd wczytywania stanu ze słownika: {e}")