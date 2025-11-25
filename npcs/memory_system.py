"""
System pamięci dla NPCów
Implementacja pamięci epizodycznej, semantycznej, proceduralnej i emocjonalnej
"""

import time
import json
import heapq
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryTrace:
    """Ślad pamięciowy z mechanizmem konsolidacji"""
    content: Any
    strength: float = 1.0
    last_access: float = field(default_factory=time.time)
    access_count: int = 0
    creation_time: float = field(default_factory=time.time)
    
    def access(self):
        """Zwiększa siłę pamięci przy dostępie"""
        self.last_access = time.time()
        self.access_count += 1
        # Każdy dostęp wzmacnia pamięć
        self.strength = min(1.0, self.strength + 0.05)
    
    def decay(self, current_time: float, decay_rate: float = 0.001):
        """Osłabia pamięć z czasem"""
        time_since_access = current_time - self.last_access
        # Pamięci często używane wolniej zanikają
        adjusted_decay = decay_rate / (1 + self.access_count * 0.1)
        self.strength *= (1 - adjusted_decay * time_since_access)
        self.strength = max(0.0, self.strength)


class EpisodicMemory:
    """System pamięci epizodycznej - konkretne wydarzenia"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.memories: List[Dict] = []
        self.memory_index: Dict[str, List[int]] = defaultdict(list)  # Indeks dla szybkiego wyszukiwania
        self.importance_threshold = 0.1
        self.consolidation_interval = 3600  # Co godzinę konsolidacja
        self.last_consolidation = time.time()
    
    def add_memory(self, event: Dict):
        """Dodaje nowe wspomnienie"""
        # Dodaj metadane
        event["timestamp"] = event.get("timestamp", time.time())
        event["strength"] = event.get("importance", 0.5)
        event["access_count"] = 0
        event["associations"] = []
        
        # Znajdź powiązania z istniejącymi wspomnieniami
        self._create_associations(event)
        
        # Dodaj do pamięci
        self.memories.append(event)
        memory_idx = len(self.memories) - 1
        
        # Indeksuj według typu i uczestników
        self.memory_index[event.get("event_type", "unknown")].append(memory_idx)
        for participant in event.get("participants", []):
            self.memory_index[f"participant_{participant}"].append(memory_idx)
        
        # Indeksuj według lokacji
        if "location" in event:
            self.memory_index[f"location_{event['location']}"].append(memory_idx)
        
        # Sprawdź pojemność
        if len(self.memories) > self.capacity:
            self._forget_weakest()
        
        # Konsoliduj jeśli minął czas
        current_time = time.time()
        if current_time - self.last_consolidation > self.consolidation_interval:
            self.consolidate()
    
    def _create_associations(self, new_event: Dict):
        """Tworzy powiązania między wspomnieniami"""
        associations = []
        
        for idx, memory in enumerate(self.memories[-20:]):  # Sprawdź ostatnie 20 wspomnień
            similarity = self._calculate_similarity(new_event, memory)
            if similarity > 0.3:  # Próg podobieństwa
                associations.append({
                    "memory_idx": len(self.memories) - 20 + idx,
                    "strength": similarity,
                    "type": self._determine_association_type(new_event, memory)
                })
                
                # Dodaj wzajemne powiązanie
                if "associations" in memory:
                    memory["associations"].append({
                        "memory_idx": len(self.memories),  # Indeks nowego wspomnienia
                        "strength": similarity,
                        "type": self._determine_association_type(memory, new_event)
                    })
        
        new_event["associations"] = associations
    
    def _calculate_similarity(self, event1: Dict, event2: Dict) -> float:
        """Oblicza podobieństwo między dwoma wydarzeniami"""
        similarity = 0.0
        
        # Podobieństwo typu wydarzenia
        if event1.get("event_type") == event2.get("event_type"):
            similarity += 0.3
        
        # Podobieństwo uczestników
        participants1 = set(event1.get("participants", []))
        participants2 = set(event2.get("participants", []))
        if participants1 and participants2:
            overlap = len(participants1.intersection(participants2))
            total = len(participants1.union(participants2))
            similarity += 0.3 * (overlap / total)
        
        # Podobieństwo lokacji
        if event1.get("location") == event2.get("location"):
            similarity += 0.2
        
        # Podobieństwo czasowe (wydarzenia blisko siebie w czasie)
        time_diff = abs(event1.get("timestamp", 0) - event2.get("timestamp", 0))
        if time_diff < 3600:  # W ciągu godziny
            similarity += 0.2 * (1 - time_diff / 3600)
        
        return min(1.0, similarity)
    
    def _determine_association_type(self, event1: Dict, event2: Dict) -> str:
        """Określa typ powiązania między wydarzeniami"""
        if event1.get("event_type") == event2.get("event_type"):
            return "similar"
        
        # Sprawdź relację przyczynową
        if event1.get("timestamp", 0) < event2.get("timestamp", 0):
            if "caused_by" in event2 and event1.get("id") in event2.get("caused_by", []):
                return "causal"
        
        # Sprawdź relację czasową
        time_diff = abs(event1.get("timestamp", 0) - event2.get("timestamp", 0))
        if time_diff < 60:  # W ciągu minuty
            return "concurrent"
        elif time_diff < 3600:  # W ciągu godziny
            return "temporal"
        
        return "related"
    
    def recall(self, query: Dict, limit: int = 10) -> List[Dict]:
        """Przywołuje wspomnienia na podstawie zapytania"""
        current_time = time.time()
        candidates = []
        
        # Użyj indeksu do szybkiego wyszukiwania
        relevant_indices = set()
        
        if "event_type" in query:
            relevant_indices.update(self.memory_index.get(query["event_type"], []))
        
        if "participant" in query:
            relevant_indices.update(self.memory_index.get(f"participant_{query['participant']}", []))
        
        if "location" in query:
            relevant_indices.update(self.memory_index.get(f"location_{query['location']}", []))
        
        # Jeśli nie ma specyficznych kryteriów, przeszukaj wszystkie
        if not relevant_indices:
            relevant_indices = range(len(self.memories))
        
        # Oblicz relevance score dla każdego kandydata
        for idx in relevant_indices:
            if idx < len(self.memories):
                memory = self.memories[idx]
                relevance = self._calculate_relevance(memory, query, current_time)
                if relevance > 0:
                    candidates.append((relevance, idx, memory))
        
        # Sortuj według relevance i zwróć top N
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Zwiększ licznik dostępu dla przywołanych wspomnień
        results = []
        for relevance, idx, memory in candidates[:limit]:
            memory["access_count"] = memory.get("access_count", 0) + 1
            memory["last_access"] = current_time
            memory["strength"] = min(1.0, memory.get("strength", 0.5) + 0.02)
            
            # Aktywuj powiązane wspomnienia (spreading activation)
            self._spread_activation(idx, strength=0.5)
            
            results.append(memory)
        
        return results
    
    def _calculate_relevance(self, memory: Dict, query: Dict, current_time: float) -> float:
        """Oblicza trafność wspomnienia względem zapytania"""
        relevance = 0.0
        
        # Sprawdź dopasowanie kryteriów
        if "event_type" in query and memory.get("event_type") == query["event_type"]:
            relevance += 0.3
        
        if "participant" in query and query["participant"] in memory.get("participants", []):
            relevance += 0.3
        
        if "location" in query and memory.get("location") == query["location"]:
            relevance += 0.2
        
        # Uwzględnij siłę wspomnienia
        strength = memory.get("strength", 0.5)
        relevance *= strength
        
        # Uwzględnij świeżość (recency effect)
        age = current_time - memory.get("timestamp", current_time)
        recency_factor = max(0.1, 1.0 - age / (7 * 24 * 3600))  # Tydzień
        relevance *= (0.7 + 0.3 * recency_factor)
        
        # Uwzględnij częstość dostępu (frequency effect)
        access_count = memory.get("access_count", 0)
        frequency_factor = min(1.0, 0.5 + access_count * 0.1)
        relevance *= frequency_factor
        
        return relevance
    
    def _spread_activation(self, memory_idx: int, strength: float = 0.5):
        """Rozprzestrzenia aktywację na powiązane wspomnienia"""
        if memory_idx >= len(self.memories):
            return
        
        memory = self.memories[memory_idx]
        associations = memory.get("associations", [])
        
        for assoc in associations:
            if assoc["memory_idx"] < len(self.memories):
                associated_memory = self.memories[assoc["memory_idx"]]
                # Wzmocnij powiązane wspomnienie
                boost = strength * assoc["strength"] * 0.1
                associated_memory["strength"] = min(1.0, associated_memory.get("strength", 0.5) + boost)
    
    def consolidate(self):
        """Konsoliduje pamięć - wzmacnia ważne, osłabia nieważne"""
        current_time = time.time()
        
        for memory in self.memories:
            # Osłab wspomnienia z czasem
            age = current_time - memory.get("timestamp", current_time)
            decay_rate = 0.001 * (1.0 / max(0.1, memory.get("importance", 0.5)))
            memory["strength"] = memory.get("strength", 0.5) * (1 - decay_rate * age / 3600)
            
            # Wzmocnij często używane wspomnienia
            if memory.get("access_count", 0) > 5:
                memory["strength"] = min(1.0, memory["strength"] + 0.1)
        
        self.last_consolidation = current_time
        
        # Usuń bardzo słabe wspomnienia
        self._forget_weakest()
    
    def _forget_weakest(self):
        """Usuwa najsłabsze wspomnienia gdy przekroczona jest pojemność"""
        if len(self.memories) <= self.capacity:
            return
        
        # Znajdź wspomnienia do usunięcia
        memories_with_strength = [
            (m.get("strength", 0.5) * m.get("importance", 0.5), idx, m) 
            for idx, m in enumerate(self.memories)
        ]
        memories_with_strength.sort(key=lambda x: x[0])
        
        # Usuń najsłabsze 10%
        to_remove = len(self.memories) - self.capacity
        indices_to_remove = set(idx for _, idx, _ in memories_with_strength[:to_remove])
        
        # Przebuduj pamięć bez usuniętych
        new_memories = []
        index_mapping = {}  # Stare indeksy -> nowe indeksy
        
        for old_idx, memory in enumerate(self.memories):
            if old_idx not in indices_to_remove:
                new_idx = len(new_memories)
                index_mapping[old_idx] = new_idx
                new_memories.append(memory)
        
        # Zaktualizuj powiązania
        for memory in new_memories:
            if "associations" in memory:
                new_associations = []
                for assoc in memory["associations"]:
                    if assoc["memory_idx"] in index_mapping:
                        assoc["memory_idx"] = index_mapping[assoc["memory_idx"]]
                        new_associations.append(assoc)
                memory["associations"] = new_associations
        
        # Przebuduj indeks
        self.memories = new_memories
        self._rebuild_index()
        
        logger.debug(f"Usunięto {to_remove} słabych wspomnień")
    
    def _rebuild_index(self):
        """Przebudowuje indeks pamięci"""
        self.memory_index.clear()
        
        for idx, memory in enumerate(self.memories):
            # Indeksuj według typu
            self.memory_index[memory.get("event_type", "unknown")].append(idx)
            
            # Indeksuj według uczestników
            for participant in memory.get("participants", []):
                self.memory_index[f"participant_{participant}"].append(idx)
            
            # Indeksuj według lokacji
            if "location" in memory:
                self.memory_index[f"location_{memory['location']}"].append(idx)
    
    def get_summary(self) -> Dict:
        """Zwraca podsumowanie stanu pamięci"""
        current_time = time.time()
        
        # Statystyki
        total_memories = len(self.memories)
        avg_strength = sum(m.get("strength", 0.5) for m in self.memories) / max(1, total_memories)
        
        # Najczęstsze typy wydarzeń
        event_types = defaultdict(int)
        for memory in self.memories:
            event_types[memory.get("event_type", "unknown")] += 1
        
        # Najważniejsze wspomnienia
        important_memories = sorted(
            self.memories,
            key=lambda m: m.get("importance", 0.5) * m.get("strength", 0.5),
            reverse=True
        )[:5]
        
        return {
            "total_memories": total_memories,
            "average_strength": avg_strength,
            "capacity_used": total_memories / self.capacity,
            "most_common_events": dict(sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:5]),
            "most_important": [
                {
                    "type": m.get("event_type"),
                    "description": m.get("description"),
                    "importance": m.get("importance"),
                    "strength": m.get("strength")
                } for m in important_memories
            ]
        }


class SemanticMemory:
    """System pamięci semantycznej - wiedza ogólna"""
    
    def __init__(self):
        self.knowledge: Dict[str, MemoryTrace] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self.relationships: Dict[str, Dict[str, float]] = defaultdict(dict)  # Relacje między konceptami
    
    def add_knowledge(self, concept: str, information: Any, category: str = "general", strength: float = 1.0):
        """Dodaje lub aktualizuje wiedzę"""
        if concept in self.knowledge:
            # Wzmocnij istniejącą wiedzę
            self.knowledge[concept].strength = min(1.0, self.knowledge[concept].strength + 0.1)
            self.knowledge[concept].access()
        else:
            # Dodaj nową wiedzę
            self.knowledge[concept] = MemoryTrace(content=information, strength=strength)
            self.categories[category].append(concept)
        
        # Znajdź powiązania z istniejącą wiedzą
        self._create_semantic_links(concept)
    
    def _create_semantic_links(self, concept: str):
        """Tworzy powiązania semantyczne"""
        # Znajdź podobne koncepty
        for other_concept in self.knowledge:
            if other_concept != concept:
                similarity = self._calculate_semantic_similarity(concept, other_concept)
                if similarity > 0.3:
                    self.relationships[concept][other_concept] = similarity
                    self.relationships[other_concept][concept] = similarity
    
    def _calculate_semantic_similarity(self, concept1: str, concept2: str) -> float:
        """Oblicza podobieństwo semantyczne między konceptami"""
        # Proste podobieństwo oparte na wspólnych słowach
        words1 = set(concept1.lower().split("_"))
        words2 = set(concept2.lower().split("_"))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get(self, concept: str, default=None):
        """Kompatybilność z dict - pobierz wiedzę lub wartość domyślną"""
        result = self.retrieve(concept, spread_activation=False)
        return result if result is not None else default

    def __getitem__(self, concept: str):
        """Kompatybilność z dict - operator []"""
        result = self.retrieve(concept, spread_activation=False)
        if result is None:
            raise KeyError(concept)
        return result

    def __setitem__(self, concept: str, value: Any):
        """Kompatybilność z dict - operator [] = """
        self.add_knowledge(concept, value)

    def __contains__(self, concept: str) -> bool:
        """Kompatybilność z dict - operator 'in'"""
        return concept in self.knowledge

    def keys(self):
        """Kompatybilność z dict - zwraca klucze"""
        return self.knowledge.keys()

    def values(self):
        """Kompatybilność z dict - zwraca wartości (treści śladów)"""
        return [trace.content for trace in self.knowledge.values()]

    def items(self):
        """Kompatybilność z dict - zwraca pary (koncept, treść)"""
        return [(concept, trace.content) for concept, trace in self.knowledge.items()]

    def __iter__(self):
        """Kompatybilność z dict - iteracja po kluczach"""
        return iter(self.knowledge)

    def __len__(self):
        """Kompatybilność z dict - liczba konceptów"""
        return len(self.knowledge)

    def retrieve(self, concept: str, spread_activation: bool = True) -> Optional[Any]:
        """Pobiera wiedzę o koncepcie"""
        if concept not in self.knowledge:
            # Spróbuj znaleźć podobny koncept
            similar = self._find_similar_concept(concept)
            if similar:
                concept = similar
            else:
                return None

        trace = self.knowledge[concept]
        trace.access()

        # Rozprzestrzenij aktywację na powiązane koncepty
        if spread_activation:
            for related, strength in self.relationships[concept].items():
                if related in self.knowledge:
                    self.knowledge[related].strength = min(1.0,
                        self.knowledge[related].strength + strength * 0.05)

        return trace.content
    
    def _find_similar_concept(self, query: str) -> Optional[str]:
        """Znajduje podobny koncept w pamięci"""
        best_match = None
        best_similarity = 0.0
        
        for concept in self.knowledge:
            similarity = self._calculate_semantic_similarity(query, concept)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = concept
        
        return best_match if best_similarity > 0.5 else None
    
    def get_related(self, concept: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Zwraca koncepty powiązane z danym"""
        if concept not in self.relationships:
            return []
        
        related = sorted(
            self.relationships[concept].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return related[:limit]
    
    def decay_all(self, current_time: float):
        """Osłabia wszystkie ślady pamięciowe"""
        for trace in self.knowledge.values():
            trace.decay(current_time)
        
        # Usuń bardzo słabe ślady
        to_remove = [k for k, v in self.knowledge.items() if v.strength < 0.01]
        for concept in to_remove:
            del self.knowledge[concept]
            # Usuń z kategorii
            for category, concepts in self.categories.items():
                if concept in concepts:
                    concepts.remove(concept)
            # Usuń relacje
            if concept in self.relationships:
                del self.relationships[concept]
            for relations in self.relationships.values():
                if concept in relations:
                    del relations[concept]


class ProceduralMemory:
    """System pamięci proceduralnej - umiejętności i nawyki"""
    
    def __init__(self):
        self.skills: Dict[str, Dict] = {}
        self.habits: List[Dict] = []
        self.action_sequences: Dict[str, List[str]] = {}
        self.success_rates: Dict[str, float] = defaultdict(lambda: 0.5)
    
    def learn_skill(self, skill_name: str, steps: List[str], context: Dict = None):
        """Uczy się nowej umiejętności"""
        if skill_name not in self.skills:
            self.skills[skill_name] = {
                "steps": steps,
                "proficiency": 0.1,
                "practice_count": 0,
                "context": context or {},
                "variations": []
            }
        else:
            # Dodaj wariację istniejącej umiejętności
            self.skills[skill_name]["variations"].append(steps)
            self.skills[skill_name]["practice_count"] += 1
            self._improve_proficiency(skill_name)
    
    def _improve_proficiency(self, skill_name: str):
        """Poprawia biegłość w umiejętności"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            # Logarytmiczny wzrost biegłości
            practice = skill["practice_count"]
            skill["proficiency"] = min(1.0, 0.1 + 0.9 * (1 - 1 / (1 + practice * 0.1)))
    
    def execute_skill(self, skill_name: str, context: Dict) -> Tuple[bool, List[str]]:
        """Wykonuje wyuczoną umiejętność"""
        if skill_name not in self.skills:
            return False, []
        
        skill = self.skills[skill_name]
        proficiency = skill["proficiency"]
        
        # Szansa na sukces zależy od biegłości
        success = random.random() < (0.3 + 0.7 * proficiency)
        
        if success:
            self.skills[skill_name]["practice_count"] += 1
            self._improve_proficiency(skill_name)
            self.success_rates[skill_name] = min(1.0, self.success_rates[skill_name] + 0.05)
            
            # Wybierz wariant wykonania
            if skill["variations"] and random.random() < proficiency:
                # Z większą biegłością, większa szansa na użycie wariantu
                steps = random.choice([skill["steps"]] + skill["variations"])
            else:
                steps = skill["steps"]
            
            return True, steps
        else:
            self.success_rates[skill_name] = max(0.0, self.success_rates[skill_name] - 0.02)
            return False, skill["steps"]
    
    def add_habit(self, trigger: str, action: str, reward: float = 0.0):
        """Dodaje nawyk"""
        habit = {
            "trigger": trigger,
            "action": action,
            "strength": 0.1,
            "executions": 0,
            "reward_history": [reward] if reward else []
        }
        
        # Sprawdź czy nawyk już istnieje
        for existing in self.habits:
            if existing["trigger"] == trigger and existing["action"] == action:
                # Wzmocnij istniejący nawyk
                existing["strength"] = min(1.0, existing["strength"] + 0.1)
                existing["executions"] += 1
                if reward:
                    existing["reward_history"].append(reward)
                return
        
        self.habits.append(habit)
    
    def trigger_habits(self, trigger: str) -> List[str]:
        """Zwraca akcje wywołane przez wyzwalacz"""
        triggered_actions = []
        
        for habit in self.habits:
            if habit["trigger"] == trigger:
                # Prawdopodobieństwo wykonania zależy od siły nawyku
                if random.random() < habit["strength"]:
                    triggered_actions.append(habit["action"])
                    habit["executions"] += 1
                    
                    # Wzmocnij nawyk przy każdym wykonaniu
                    habit["strength"] = min(1.0, habit["strength"] + 0.02)
        
        return triggered_actions
    
    def learn_sequence(self, sequence_name: str, actions: List[str]):
        """Uczy się sekwencji akcji"""
        if sequence_name not in self.action_sequences:
            self.action_sequences[sequence_name] = actions
        else:
            # Porównaj z istniejącą sekwencją i ewentualnie zaktualizuj
            existing = self.action_sequences[sequence_name]
            if len(actions) < len(existing):
                # Krótsza sekwencja - może to być optymalizacja
                self.action_sequences[f"{sequence_name}_optimized"] = actions
    
    def get_sequence(self, sequence_name: str) -> Optional[List[str]]:
        """Pobiera wyuczoną sekwencję akcji"""
        # Preferuj zoptymalizowaną wersję jeśli istnieje
        optimized = f"{sequence_name}_optimized"
        if optimized in self.action_sequences:
            return self.action_sequences[optimized]
        return self.action_sequences.get(sequence_name)
    
    def consolidate(self):
        """Konsoliduje pamięć proceduralną"""
        # Usuń słabe nawyki
        self.habits = [h for h in self.habits if h["strength"] > 0.05]
        
        # Usuń rzadko używane umiejętności
        skills_to_remove = []
        for skill_name, skill in self.skills.items():
            if skill["proficiency"] < 0.05 and skill["practice_count"] < 3:
                skills_to_remove.append(skill_name)
        
        for skill_name in skills_to_remove:
            del self.skills[skill_name]


class EmotionalMemory:
    """System pamięci emocjonalnej - emocje związane z obiektami i sytuacjami"""
    
    def __init__(self):
        self.emotional_tags: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.emotional_contexts: List[Dict] = []
        self.mood_history: List[Tuple[float, Dict[str, float]]] = []
        self.trauma_memories: List[Dict] = []
        self.positive_memories: List[Dict] = []
    
    def tag_emotion(self, entity: str, emotion: str, intensity: float):
        """Przypisuje emocję do obiektu/osoby/miejsca"""
        self.emotional_tags[entity][emotion] = min(1.0, 
            self.emotional_tags[entity][emotion] + intensity * 0.3)
        
        # Osłab przeciwne emocje
        opposite_emotions = {
            "happy": "sad",
            "sad": "happy",
            "angry": "calm",
            "calm": "angry",
            "fear": "safe",
            "safe": "fear"
        }
        
        if emotion in opposite_emotions:
            opposite = opposite_emotions[emotion]
            self.emotional_tags[entity][opposite] = max(0.0,
                self.emotional_tags[entity][opposite] - intensity * 0.2)
    
    def get_emotional_response(self, entity: str) -> Dict[str, float]:
        """Zwraca emocjonalną reakcję na obiekt"""
        if entity not in self.emotional_tags:
            return {"neutral": 1.0}
        
        emotions = self.emotional_tags[entity]
        
        # Normalizuj emocje
        total = sum(emotions.values())
        if total > 0:
            return {e: v/total for e, v in emotions.items()}
        return {"neutral": 1.0}
    
    def add_emotional_context(self, situation: Dict, emotions: Dict[str, float]):
        """Dodaje kontekst emocjonalny do sytuacji"""
        context = {
            "situation": situation,
            "emotions": emotions,
            "timestamp": time.time(),
            "strength": sum(emotions.values()) / len(emotions) if emotions else 0
        }
        
        self.emotional_contexts.append(context)
        
        # Klasyfikuj jako traumę lub pozytywne wspomnienie
        if emotions.get("fear", 0) > 0.7 or emotions.get("disgust", 0) > 0.7:
            self.trauma_memories.append(context)
        elif emotions.get("happy", 0) > 0.7:
            self.positive_memories.append(context)
        
        # Ogranicz rozmiar
        if len(self.emotional_contexts) > 500:
            # Zachowaj tylko silne konteksty
            self.emotional_contexts.sort(key=lambda x: x["strength"], reverse=True)
            self.emotional_contexts = self.emotional_contexts[:400]
    
    def find_similar_context(self, situation: Dict) -> Optional[Dict[str, float]]:
        """Znajduje podobny kontekst emocjonalny"""
        best_match = None
        best_similarity = 0.0
        
        for context in self.emotional_contexts:
            similarity = self._calculate_context_similarity(situation, context["situation"])
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = context
        
        if best_match and best_similarity > 0.5:
            return best_match["emotions"]
        return None
    
    def _calculate_context_similarity(self, situation1: Dict, situation2: Dict) -> float:
        """Oblicza podobieństwo między sytuacjami"""
        similarity = 0.0
        
        # Porównaj kluczowe elementy sytuacji
        for key in ["location", "participants", "action", "time_of_day"]:
            if key in situation1 and key in situation2:
                if situation1[key] == situation2[key]:
                    similarity += 0.25
        
        return similarity
    
    def update_mood(self, current_emotions: Dict[str, float]):
        """Aktualizuje historię nastroju"""
        self.mood_history.append((time.time(), current_emotions.copy()))
        
        # Ogranicz historię do ostatnich 100 wpisów
        if len(self.mood_history) > 100:
            self.mood_history = self.mood_history[-100:]
    
    def get_mood_trend(self) -> Dict[str, float]:
        """Analizuje trend nastroju"""
        if len(self.mood_history) < 2:
            return {"stable": 1.0}
        
        recent_moods = self.mood_history[-10:]
        emotion_trends = defaultdict(list)
        
        for _, emotions in recent_moods:
            for emotion, value in emotions.items():
                emotion_trends[emotion].append(value)
        
        trends = {}
        for emotion, values in emotion_trends.items():
            if len(values) > 1:
                # Oblicz trend (rosnący/malejący)
                trend = (values[-1] - values[0]) / len(values)
                trends[emotion] = trend
        
        return trends
    
    def process_trauma(self, trauma_event: Dict) -> Dict[str, Any]:
        """Przetwarza traumatyczne wydarzenie"""
        # Dodaj do traum
        self.trauma_memories.append({
            "event": trauma_event,
            "timestamp": time.time(),
            "processed": False,
            "intensity": trauma_event.get("intensity", 0.8),
            "triggers": self._identify_triggers(trauma_event)
        })
        
        # Oznacz powiązane elementy negatywnymi emocjami
        for element in trauma_event.get("elements", []):
            self.tag_emotion(element, "fear", 0.5)
            self.tag_emotion(element, "disgust", 0.3)
        
        return {
            "trauma_recorded": True,
            "triggers_identified": len(self.trauma_memories[-1]["triggers"]),
            "avoidance_targets": list(self.emotional_tags.keys())
        }
    
    def _identify_triggers(self, event: Dict) -> List[str]:
        """Identyfikuje wyzwalacze traumy"""
        triggers = []
        
        # Podstawowe elementy wydarzenia
        if "location" in event:
            triggers.append(f"location:{event['location']}")
        
        for participant in event.get("participants", []):
            triggers.append(f"person:{participant}")
        
        if "time" in event:
            hour = event["time"] // 3600 % 24
            if 20 <= hour or hour < 6:
                triggers.append("darkness")
        
        if "action" in event:
            triggers.append(f"action:{event['action']}")
        
        return triggers
    
    def check_triggers(self, current_situation: Dict) -> float:
        """Sprawdza czy obecna sytuacja wywołuje traumę"""
        trigger_intensity = 0.0
        
        for trauma in self.trauma_memories:
            if not trauma.get("processed", False):
                for trigger in trauma["triggers"]:
                    if "location:" in trigger:
                        location = trigger.split(":")[1]
                        if current_situation.get("location") == location:
                            trigger_intensity += trauma["intensity"] * 0.3
                    
                    elif "person:" in trigger:
                        person = trigger.split(":")[1]
                        if person in current_situation.get("participants", []):
                            trigger_intensity += trauma["intensity"] * 0.4
                    
                    elif trigger == "darkness":
                        if current_situation.get("is_dark", False):
                            trigger_intensity += trauma["intensity"] * 0.5
        
        return min(1.0, trigger_intensity)
    
    def decay_emotions(self, decay_rate: float = 0.001):
        """Osłabia emocjonalne tagi z czasem"""
        for entity in list(self.emotional_tags.keys()):
            for emotion in list(self.emotional_tags[entity].keys()):
                self.emotional_tags[entity][emotion] *= (1 - decay_rate)
                
                # Usuń bardzo słabe emocje
                if self.emotional_tags[entity][emotion] < 0.01:
                    del self.emotional_tags[entity][emotion]
            
            # Usuń encje bez emocji
            if not self.emotional_tags[entity]:
                del self.emotional_tags[entity]


class IntegratedMemorySystem:
    """Zintegrowany system pamięci łączący wszystkie typy"""
    
    def __init__(self, npc_id: str):
        self.npc_id = npc_id
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.emotional = EmotionalMemory()
        
        self.last_consolidation = time.time()
        self.consolidation_interval = 1800  # 30 minut
        
        logger.info(f"Zintegrowany system pamięci dla {npc_id} zainicjalizowany")
    
    def process_event(self, event: Dict) -> Dict[str, Any]:
        """Przetwarza wydarzenie przez wszystkie systemy pamięci"""
        results = {}
        
        # Pamięć epizodyczna
        self.episodic.add_memory(event)
        
        # Wyciągnij wiedzę semantyczną
        if "learned_fact" in event:
            self.semantic.add_knowledge(
                event["learned_fact"]["concept"],
                event["learned_fact"]["information"],
                event.get("category", "general")
            )
        
        # Sprawdź czy to nowa umiejętność
        if "skill_observed" in event:
            self.procedural.learn_skill(
                event["skill_observed"]["name"],
                event["skill_observed"]["steps"],
                event
            )
        
        # Przetwórz emocje
        if "emotional_impact" in event:
            for entity in event.get("participants", []) + [event.get("location", "")]:
                if entity:
                    for emotion, intensity in event["emotional_impact"].items():
                        self.emotional.tag_emotion(entity, emotion, intensity)
            
            self.emotional.add_emotional_context(event, event["emotional_impact"])
            
            # Sprawdź czy to trauma
            if event["emotional_impact"].get("fear", 0) > 0.7:
                results["trauma_processed"] = self.emotional.process_trauma(event)
        
        # Konsoliduj jeśli minął czas
        if time.time() - self.last_consolidation > self.consolidation_interval:
            self.consolidate_all()

        return results

    def store_episodic_memory(self, event_type: str, data: Dict) -> None:
        """Przechowuje wspomnienie epizodyczne.

        Args:
            event_type: Typ wydarzenia
            data: Dane wydarzenia
        """
        event = {
            "event_type": event_type,
            "timestamp": time.time(),
            **data
        }
        self.process_event(event)

    def get(self, key: str, default=None):
        """Kompatybilność z dict - pobierz atrybut lub wartość domyślną"""
        return getattr(self, key, default)

    def __getitem__(self, key: str):
        """Kompatybilność z dict - operator []"""
        if not hasattr(self, key):
            raise KeyError(key)
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        """Kompatybilność z dict - operator [] = """
        setattr(self, key, value)

    def recall_relevant(self, context: Dict) -> Dict[str, Any]:
        """Przywołuje relevantne informacje dla danego kontekstu"""
        recalled = {}
        
        # Przywołaj relevantne wspomnienia epizodyczne
        query = {
            "participant": context.get("target_npc"),
            "location": context.get("location"),
            "event_type": context.get("action_type")
        }
        recalled["episodes"] = self.episodic.recall(query, limit=5)
        
        # Pobierz relevantną wiedzę semantyczną
        if "query_concept" in context:
            knowledge = self.semantic.retrieve(context["query_concept"])
            if knowledge:
                recalled["knowledge"] = knowledge
                recalled["related_concepts"] = self.semantic.get_related(context["query_concept"])
        
        # Sprawdź relevantne umiejętności
        if "required_skill" in context:
            skill_name = context["required_skill"]
            if skill_name in self.procedural.skills:
                recalled["skill_proficiency"] = self.procedural.skills[skill_name]["proficiency"]
                recalled["can_execute"] = recalled["skill_proficiency"] > 0.3
        
        # Sprawdź emocjonalny kontekst
        emotional_response = {}
        for entity in context.get("present_entities", []):
            emotional_response[entity] = self.emotional.get_emotional_response(entity)
        
        recalled["emotional_context"] = emotional_response
        
        # Sprawdź wyzwalacze traumy
        recalled["trauma_triggered"] = self.emotional.check_triggers(context)
        
        # Sprawdź nawyki
        if "situation" in context:
            triggered_habits = self.procedural.trigger_habits(context["situation"])
            if triggered_habits:
                recalled["habitual_actions"] = triggered_habits
        
        return recalled
    
    def consolidate_all(self):
        """Konsoliduje wszystkie systemy pamięci"""
        current_time = time.time()
        
        # Konsoliduj każdy system
        self.episodic.consolidate()
        self.semantic.decay_all(current_time)
        self.procedural.consolidate()
        self.emotional.decay_emotions()
        
        self.last_consolidation = current_time
        
        logger.debug(f"Pamięć {self.npc_id} skonsolidowana")
    
    def get_memory_profile(self) -> Dict:
        """Zwraca profil pamięci NPCa"""
        return {
            "npc_id": self.npc_id,
            "episodic_summary": self.episodic.get_summary(),
            "semantic_concepts": len(self.semantic.knowledge),
            "learned_skills": list(self.procedural.skills.keys()),
            "skill_proficiencies": {
                name: skill["proficiency"] 
                for name, skill in self.procedural.skills.items()
            },
            "habits_count": len(self.procedural.habits),
            "emotional_associations": len(self.emotional.emotional_tags),
            "trauma_count": len(self.emotional.trauma_memories),
            "positive_memories": len(self.emotional.positive_memories),
            "mood_trend": self.emotional.get_mood_trend()
        }
    
    def save_to_file(self, filepath: str):
        """Zapisuje stan pamięci do pliku"""
        state = {
            "npc_id": self.npc_id,
            "episodic": {
                "memories": self.episodic.memories,
                "capacity": self.episodic.capacity
            },
            "semantic": {
                "knowledge": {k: {"content": v.content, "strength": v.strength} 
                            for k, v in self.semantic.knowledge.items()},
                "categories": dict(self.semantic.categories),
                "relationships": dict(self.semantic.relationships)
            },
            "procedural": {
                "skills": self.procedural.skills,
                "habits": self.procedural.habits,
                "sequences": self.procedural.action_sequences
            },
            "emotional": {
                "tags": dict(self.emotional.emotional_tags),
                "contexts": self.emotional.emotional_contexts,
                "traumas": self.emotional.trauma_memories,
                "positive": self.emotional.positive_memories
            },
            "timestamp": time.time()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Pamięć {self.npc_id} zapisana do {filepath}")
    
    def load_from_file(self, filepath: str):
        """Wczytuje stan pamięci z pliku"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Odtwórz pamięć epizodyczną
            self.episodic.memories = state["episodic"]["memories"]
            self.episodic.capacity = state["episodic"]["capacity"]
            self.episodic._rebuild_index()
            
            # Odtwórz pamięć semantyczną
            for concept, data in state["semantic"]["knowledge"].items():
                self.semantic.knowledge[concept] = MemoryTrace(
                    content=data["content"],
                    strength=data["strength"]
                )
            self.semantic.categories = defaultdict(list, state["semantic"]["categories"])
            self.semantic.relationships = defaultdict(dict, state["semantic"]["relationships"])
            
            # Odtwórz pamięć proceduralną
            self.procedural.skills = state["procedural"]["skills"]
            self.procedural.habits = state["procedural"]["habits"]
            self.procedural.action_sequences = state["procedural"]["sequences"]
            
            # Odtwórz pamięć emocjonalną
            self.emotional.emotional_tags = defaultdict(lambda: defaultdict(float), 
                                                       state["emotional"]["tags"])
            self.emotional.emotional_contexts = state["emotional"]["contexts"]
            self.emotional.trauma_memories = state["emotional"]["traumas"]
            self.emotional.positive_memories = state["emotional"]["positive"]
            
            logger.info(f"Pamięć {self.npc_id} wczytana z {filepath}")
            
        except Exception as e:
            logger.error(f"Błąd wczytywania pamięci: {e}")

# Alias dla kompatybilności wstecznej
MemorySystem = IntegratedMemorySystem

