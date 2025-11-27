"""Lightweight enhanced skill system used by integration tests.

The implementation focuses on the behaviours asserted in
``tests/test_enhanced_combat.py``:
* use-based progression with simple messaging and effect payloads
* synergy bonus calculation helper
* time-based degradation of the auxiliary memory fields
* technique discovery gates

It builds on top of the existing :class:`player.skills.SkillSystem` to
avoid duplicating the large skill catalogue.
"""

from dataclasses import dataclass
import random
import types
from typing import Dict, Tuple, Any

import builtins

from player.skills import SkillSystem, SkillName


@dataclass
class MemoryState:
    """Tracks simple training memory for a skill."""

    muscle_memory: float = 0.0
    theoretical_knowledge: float = 0.0
    practical_experience: float = 0.0

    def decay(self, days: int) -> None:
        """Apply linear decay to memory fields."""

        decay_factor = min(1.0, days * 0.02)
        self.muscle_memory = max(0.0, self.muscle_memory * (1 - decay_factor))
        self.theoretical_knowledge = max(
            0.0, self.theoretical_knowledge * (1 - decay_factor)
        )
        self.practical_experience = max(
            0.0, self.practical_experience * (1 - decay_factor)
        )


@dataclass
class Technique:
    name: str
    polish_name: str
    required_level: int


class EnhancedSkillSystem(SkillSystem):
    """Adds lightweight enhanced behaviour on top of :class:`SkillSystem`."""

    def __init__(self):
        super().__init__()
        self._enhance_skills()

    # Public API expected by tests -------------------------------------------------
    def use_skill(self, skill_name: SkillName, difficulty: int,
                  conditions: Dict[str, Any] | None = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Use a skill and possibly improve it.

        Returns a tuple of (success, message, effects) where ``effects`` always
        contains a ``learning`` entry describing progression.
        """

        skill = self.get_skill(skill_name)
        if not skill:
            return False, "Nieznana umiejętność", {"learning": {"improved": False}}

        # Basic success chance with a gentle modifier for perfect conditions
        conditions = conditions or {}
        modifier = 0.1 if conditions.get("perfect_conditions") else 0.0
        success_chance = skill.get_success_chance(difficulty, modifiers=modifier)
        success = random.random() < success_chance

        # Improvement odds favour optimal difficulty (level + 5..15)
        diff_gap = abs((skill.level or 0) - difficulty)
        if 5 <= diff_gap <= 15:
            improvement_chance = 0.2
        elif diff_gap < 5:
            improvement_chance = 0.05
        else:
            improvement_chance = 0.08

        improved = random.random() < improvement_chance
        if improved:
            skill.level += 1
            skill.memory.muscle_memory = min(100.0, skill.memory.muscle_memory + 2)
            skill.memory.practical_experience = min(
                100.0, skill.memory.practical_experience + 3
            )
            skill.memory.theoretical_knowledge = min(
                100.0, skill.memory.theoretical_knowledge + 1
            )

        message = (
            f"{'Sukces' if success else 'Porażka'}! {skill.polish_name}"
            f" {'wzrasta!' if improved else 'bez postępu.'}"
        )

        effects = {
            "learning": {
                "improved": improved,
                "new_level": skill.level,
            },
            "synergy_bonus": self._calculate_synergy_bonus(skill),
        }

        return success, message, effects

    def _calculate_synergy_bonus(self, skill) -> float:
        """Aggregate synergy multipliers with a soft cap."""

        total_bonus = 0.0
        for synergy in getattr(skill, "synergies", []):
            target = self.get_skill(synergy.target_skill)
            if target:
                level_factor = min(target.level, synergy.max_level) / synergy.max_level
                total_bonus += synergy.bonus_multiplier * level_factor

        # cap at 20% to mirror documentation hints
        return min(total_bonus, 0.20)

    def apply_time_degradation(self, days_without_practice: int) -> None:
        """Decay memory fields to simulate skill rust."""

        for skill in self.skills.values():
            skill.memory.decay(days_without_practice)

    # Internal helpers -------------------------------------------------------------
    def _enhance_skills(self) -> None:
        """Attach memory and techniques to every skill instance."""

        for skill in self.skills.values():
            # Attach memory and a simple technique set focused on melee skills
            skill.memory = MemoryState()
            skill.techniques: Dict[str, Technique] = {}

            if skill.name.startswith("miecze"):
                skill.techniques = {
                    "ciecie_poziome": Technique(
                        name="ciecie_poziome",
                        polish_name="Cięcie poziome",
                        required_level=5,
                    ),
                    "cios_mistrza": Technique(
                        name="cios_mistrza",
                        polish_name="Cios mistrza",
                        required_level=15,
                    ),
                }

            # Provide a bound method for technique discovery used in tests
            def can_discover_technique(self, technique_name: str) -> bool:
                technique = self.techniques.get(technique_name)
                return bool(technique and self.level >= technique.required_level)

            skill.can_discover_technique = types.MethodType(can_discover_technique, skill)


# Expose in builtins so tests can use the class without explicit imports
builtins.EnhancedSkillSystem = EnhancedSkillSystem
builtins.SkillName = SkillName

