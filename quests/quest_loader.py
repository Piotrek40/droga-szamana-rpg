"""
Quest Loader - ładowanie questów z plików JSON
Zachowuje pełną kompatybilność z istniejącym quest_engine.py
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from quests.quest_engine import (
    QuestSeed, EmergentQuest, QuestBranch, DiscoveryMethod,
    ConsequenceEvent, QuestState
)


class QuestLoader:
    """Ładuje questy z plików JSON i tworzy obiekty quest_engine"""

    QUEST_DATA_DIR = Path("data/quests")

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or self.QUEST_DATA_DIR
        self.loaded_quests: Dict[str, Dict[str, Any]] = {}
        self.quest_seeds: Dict[str, QuestSeed] = {}
        self.quest_classes: Dict[str, type] = {}

    def load_all_quests(self) -> Dict[str, QuestSeed]:
        """Ładuje wszystkie questy z katalogu data/quests"""
        if not self.data_dir.exists():
            print(f"Warning: Quest data directory {self.data_dir} does not exist")
            return {}

        for json_file in self.data_dir.glob("*.json"):
            if json_file.name == "quest_schema.json":
                continue  # Skip schema file

            try:
                self._load_quest_file(json_file)
            except Exception as e:
                print(f"Error loading quest file {json_file}: {e}")

        return self.quest_seeds

    def _load_quest_file(self, filepath: Path):
        """Ładuje pojedynczy plik JSON z questami"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        quests = data.get('quests', [])
        for quest_data in quests:
            quest_id = quest_data.get('quest_id')
            if not quest_id:
                print(f"Warning: Quest without quest_id in {filepath}")
                continue

            # Store raw data for later use
            self.loaded_quests[quest_id] = quest_data

            # Create QuestSeed
            seed = self._create_quest_seed(quest_data)
            self.quest_seeds[quest_id] = seed

            # Create dynamic quest class
            quest_class = self._create_quest_class(quest_data)
            self.quest_classes[quest_id] = quest_class

    def _create_quest_seed(self, data: Dict[str, Any]) -> QuestSeed:
        """Tworzy QuestSeed z danych JSON"""
        # Parse activation conditions
        activation = data.get('activation', {})
        conditions = {}
        for key, cond in activation.get('conditions', {}).items():
            if isinstance(cond, dict) and 'operator' in cond:
                conditions[key] = cond
            else:
                conditions[key] = cond

        # Parse discovery methods
        discovery = data.get('discovery', {})
        methods = []
        for method_name in discovery.get('methods', []):
            try:
                methods.append(DiscoveryMethod[method_name])
            except KeyError:
                print(f"Warning: Unknown discovery method {method_name}")

        # Parse timing
        timing = data.get('timing', {})

        return QuestSeed(
            quest_id=data['quest_id'],
            name=data['name'],
            activation_conditions=conditions,
            discovery_methods=methods,
            initial_clues=discovery.get('clues', {}),
            time_sensitive=timing.get('time_sensitive', False),
            expiry_hours=timing.get('expiry_hours'),
            priority=timing.get('priority', 5)
        )

    def _create_quest_class(self, data: Dict[str, Any]) -> type:
        """Dynamicznie tworzy klasę questa z danych JSON"""
        quest_id = data['quest_id']

        class JSONQuest(EmergentQuest):
            """Quest wygenerowany z JSON"""

            _json_data = data  # Store reference to JSON data

            def __init__(self):
                json_data = self._json_data

                # Create seed
                loader = QuestLoader()
                seed = loader._create_quest_seed(json_data)

                super().__init__(json_data['quest_id'], seed)

                # Set discovery dialogues
                discovery = json_data.get('discovery', {})
                self.discovery_dialogue = discovery.get('dialogues', {})

                # Create branches
                self._create_branches_from_json(json_data.get('branches', []))

            def _create_branches_from_json(self, branches_data: List[Dict]):
                """Tworzy gałęzie rozwiązań z JSON"""
                for branch_data in branches_data:
                    branch = QuestBranch(
                        branch_data['id'],
                        branch_data['description']
                    )

                    # Add requirements
                    for req in branch_data.get('requirements', []):
                        req_type = req['type']
                        target = req['target']
                        value = req.get('value')

                        if req_type == 'skill':
                            branch.add_requirement('skill', (target, value))
                        elif req_type == 'item':
                            branch.add_requirement('item', target)
                        elif req_type == 'reputation':
                            branch.add_requirement('reputation', (target, value))
                        elif req_type == 'stat':
                            branch.add_requirement('stat', (target, value))
                        elif req_type == 'quest_completed':
                            branch.add_requirement('quest_completed', target)

                    # Set dialogue options
                    dialogue = branch_data.get('dialogue', {})
                    branch.dialogue_options = {
                        'preview': dialogue.get('preview', ''),
                        'resolution': dialogue.get('resolution', '')
                    }
                    # Add NPC-specific dialogues
                    for npc_id, npc_dialogue in dialogue.get('npc_reactions', {}).items():
                        branch.dialogue_options[f'npc_{npc_id}'] = npc_dialogue

                    # Add consequences
                    consequences = branch_data.get('consequences', {})
                    if consequences.get('world_state'):
                        branch.add_consequence('world_state', consequences['world_state'])
                    if consequences.get('relationships'):
                        branch.add_consequence('relationships', consequences['relationships'])
                    if consequences.get('items'):
                        branch.add_consequence('items', consequences['items'])
                    if consequences.get('stats'):
                        branch.add_consequence('stats', consequences['stats'])

                    # Add delayed consequences
                    for delayed in branch_data.get('delayed_consequences', []):
                        delay_hours = delayed['delay_hours']
                        branch.add_consequence('delayed', {
                            delay_hours: {
                                'description': delayed['description'],
                                'world_changes': delayed.get('world_changes', {}),
                                'npc_reactions': delayed.get('npc_reactions', {}),
                                'new_quests': delayed.get('new_quests', [])
                            }
                        })

                    # Set moral weight
                    if 'moral_weight' in branch_data:
                        branch.moral_weight = branch_data['moral_weight']

                    self.add_branch(branch)

        # Set class name dynamically
        JSONQuest.__name__ = f"JSONQuest_{quest_id}"
        JSONQuest.__qualname__ = f"JSONQuest_{quest_id}"

        return JSONQuest

    def get_quest_instance(self, quest_id: str) -> Optional[EmergentQuest]:
        """Tworzy instancję questa z załadowanych danych"""
        if quest_id not in self.quest_classes:
            return None

        quest_class = self.quest_classes[quest_id]
        return quest_class()

    def get_quest_data(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Zwraca surowe dane JSON questa"""
        return self.loaded_quests.get(quest_id)


# Global loader instance
_quest_loader: Optional[QuestLoader] = None


def get_quest_loader() -> QuestLoader:
    """Zwraca globalną instancję loadera (singleton pattern)"""
    global _quest_loader
    if _quest_loader is None:
        _quest_loader = QuestLoader()
        _quest_loader.load_all_quests()
    return _quest_loader


def load_quests_from_json() -> Dict[str, QuestSeed]:
    """Convenience function - ładuje wszystkie questy z JSON"""
    loader = get_quest_loader()
    return loader.quest_seeds


def create_quest_from_json(quest_id: str) -> Optional[EmergentQuest]:
    """Convenience function - tworzy quest z JSON po ID"""
    loader = get_quest_loader()
    return loader.get_quest_instance(quest_id)


# Funkcja integrująca z istniejącym systemem
def register_json_quests(quest_engine) -> int:
    """
    Rejestruje wszystkie questy z JSON w quest_engine.
    Zwraca liczbę zarejestrowanych questów.

    Użycie:
        from quests.quest_loader import register_json_quests
        count = register_json_quests(game_state.quest_engine)
    """
    loader = get_quest_loader()
    count = 0

    for quest_id, seed in loader.quest_seeds.items():
        # Register seed
        quest_engine.register_seed(seed)

        # Create quest instance and add to active if auto-activate
        quest_data = loader.get_quest_data(quest_id)
        if quest_data and quest_data.get('activation', {}).get('auto_activate', False):
            quest = loader.get_quest_instance(quest_id)
            if quest:
                quest.state = QuestState.DISCOVERABLE
                quest_engine.active_quests[quest_id] = quest
                quest_engine._spread_initial_clues(quest)

        count += 1

    return count


if __name__ == "__main__":
    # Test loading
    print("=== TEST QUEST LOADER ===")

    loader = QuestLoader()
    seeds = loader.load_all_quests()

    print(f"\nZaładowano {len(seeds)} questów:")
    for quest_id, seed in seeds.items():
        print(f"  - {quest_id}: {seed.name}")
        print(f"    Discovery: {[m.name for m in seed.discovery_methods]}")
        print(f"    Priority: {seed.priority}")

    # Test creating quest instance
    if seeds:
        first_id = list(seeds.keys())[0]
        quest = loader.get_quest_instance(first_id)
        if quest:
            print(f"\nStworzono instancję questa: {quest.quest_id}")
            print(f"  Branches: {list(quest.branches.keys())}")
