"""Simplified enhanced combat layer used by the automated tests.

The goal is to provide predictable hooks for pain, environment and
techniques without reimplementing the full combat simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional, Tuple

import builtins

from mechanics.combat import (
    CombatStats,
    Weapon,
    Armor,
    WeaponType,
    DamageType,
    BodyPart,
    CombatAction,
    CombatTechnique,
    TechniqueType,
    EnvironmentalFactor,
    VoidWalkerAbility,
)
from player.enhanced_skills import EnhancedSkillSystem, SkillName


@dataclass
class Combatant:
    name: str
    stats: CombatStats
    weapon: Optional[Weapon] = None
    armor: Optional[Armor] = None
    skills: Dict[str, int] = field(default_factory=dict)
    injuries: List[str] = field(default_factory=list)
    ai_pattern: str = "agresywny"


class EnhancedCombatSystem:
    def __init__(self):
        self.skill_system = EnhancedSkillSystem()
        self.combat_environment: set[EnvironmentalFactor] = set()
        self.combo_tracker: Dict[str, List[str]] = {}
        self.combo_window: Dict[str, int] = {}
        self.techniques = self._build_techniques()
        self.void_abilities = self._build_void_abilities()

    # Core combat flow ------------------------------------------------------------
    def process_combat_turn(
        self, attacker: Combatant, defender: Combatant, action: CombatAction
    ) -> Dict[str, any]:
        """Resolve a single combat action with simplified rules."""

        attacker_skill = self._map_weapon_to_skill(attacker.weapon)
        attack_level = attacker.skills.get(attacker_skill, 10)
        defense_level = defender.skills.get("obrona", 5)

        base_damage = attacker.weapon.get_effective_damage() if attacker.weapon else 8
        env_mods = self.calculate_environmental_modifiers()
        accuracy_penalty = env_mods.get("accuracy", 0.0)

        # Simple hit chance: skill differential with environmental penalty
        hit_chance = 0.65 + (attack_level - defense_level) / 200.0 - abs(accuracy_penalty)
        hit = random.random() < max(0.1, min(0.9, hit_chance))

        damage = 0
        messages = []
        if hit:
            damage = max(1, int(base_damage * (1 + attack_level / 100)))
            defender.stats.health = max(0, defender.stats.health - damage)
            defender.stats.pain = min(100, defender.stats.pain + damage * 0.4)
            if defender.stats.health <= 0 or defender.stats.pain >= 90:
                defender.stats.is_conscious = False
            messages.append(f"{attacker.name} trafia i zadaje {damage} obrażeń")
        else:
            messages.append(f"{attacker.name} chybia")

        return {"damage": damage, "messages": messages}

    def calculate_combat_penalties(self, stats: CombatStats, injuries: List[str]):
        pain_ratio = stats.pain / 100.0
        injury_penalty = min(0.3, 0.05 * len(injuries))
        return {
            "attack": pain_ratio + injury_penalty,
            "accuracy": pain_ratio * 0.8,
        }

    def calculate_environmental_modifiers(self) -> Dict[str, float]:
        modifiers = {"attack": 0.0, "defense": 0.0, "accuracy": 0.0}
        if EnvironmentalFactor.CIEMNOSC in self.combat_environment:
            modifiers["accuracy"] -= 0.3
        if EnvironmentalFactor.SLISKA_POWIERZCHNIA in self.combat_environment:
            modifiers["attack"] -= 0.15
        if EnvironmentalFactor.DESZCZ in self.combat_environment:
            modifiers["accuracy"] -= 0.15
        return modifiers

    # Techniques & combos ---------------------------------------------------------
    def execute_technique(
        self, attacker: Combatant, defender: Combatant, technique: CombatTechnique
    ) -> Tuple[bool, Dict[str, any]]:
        skill_name = self._map_weapon_to_skill(attacker.weapon)
        skill_level = attacker.skills.get(skill_name, 0)
        if not technique.can_execute(skill_level, attacker.stats.stamina, attacker.weapon):
            return False, {"description": "Za mało umiejętności"}

        attacker.stats.stamina = max(0, attacker.stats.stamina - technique.stamina_cost)
        damage = int((attacker.weapon.get_effective_damage() if attacker.weapon else 10)
                     * technique.damage_multiplier)
        defender.stats.health = max(0, defender.stats.health - damage)
        defender.stats.pain = min(100, defender.stats.pain + damage * 0.5)
        description = f"{attacker.name} wykonuje {technique.polish_name} i zadaje {damage} obrażeń"
        return True, {"description": description, "damage": damage}

    def check_combo_opportunity(self, attacker_name: str, last_action: str):
        chain = self.combo_tracker.get(attacker_name, [])
        if chain and chain[-1] == last_action:
            return self.techniques.get("cios_wykańczający")
        return None

    # AI --------------------------------------------------------------------------
    def ai_choose_action(self, npc: Combatant, opponent: Combatant):
        if npc.ai_pattern == "łucznik" and npc.weapon and npc.weapon.weapon_type == WeaponType.LUKI:
            return CombatAction.ATAK_PODSTAWOWY, None
        if npc.ai_pattern == "berserker":
            return CombatAction.ATAK_SILNY, None
        if npc.stats.health < npc.stats.max_health * 0.25:
            return CombatAction.OBRONA, None
        return CombatAction.ATAK_PODSTAWOWY, None

    # Internal builders -----------------------------------------------------------
    def _build_techniques(self) -> Dict[str, CombatTechnique]:
        return {
            "ciecie_poziome": CombatTechnique(
                name="ciecie_poziome",
                polish_name="Cięcie poziome",
                type=TechniqueType.PODSTAWOWA,
                weapon_types=[WeaponType.MIECZE_DLUGIE, WeaponType.MIECZE_KROTKIE, WeaponType.MIECZE_DWURECZNE],
                skill_requirement=5,
                stamina_cost=5,
                damage_multiplier=1.2,
            ),
            "cios_wykańczający": CombatTechnique(
                name="cios_wykańczający",
                polish_name="Cios wykańczający",
                type=TechniqueType.SPECJALNA,
                weapon_types=[WeaponType.MIECZE_DLUGIE, WeaponType.MIECZE_KROTKIE, WeaponType.MIECZE_DWURECZNE],
                skill_requirement=12,
                stamina_cost=8,
                damage_multiplier=1.5,
            ),
        }

    def _build_void_abilities(self) -> Dict[str, VoidWalkerAbility]:
        return {
            "dotyk_pustki": VoidWalkerAbility(
                name="dotyk_pustki",
                polish_name="Dotyk Pustki",
                void_energy_cost=10,
                pain_increase=15,
                cooldown=2,
                level_requirement=10,
                description="Energia pustki paraliżuje cel.",
                effects={"damage": 15},
            )
        }

    def _map_weapon_to_skill(self, weapon: Optional[Weapon]) -> str:
        if not weapon:
            return "walka_wręcz"
        mapping = {
            WeaponType.MIECZE_KROTKIE: "miecze",
            WeaponType.MIECZE_DLUGIE: "miecze",
            WeaponType.MIECZE_DWURECZNE: "miecze_dwuręczne",
            WeaponType.TOPORY: "topory",
            WeaponType.LUKI: "lucznictwo",
            WeaponType.SZTYLETY: "sztylety",
        }
        return mapping.get(weapon.weapon_type, "walka_wręcz")


# Expose globally for tests that reference names directly
builtins.Combatant = Combatant
builtins.EnhancedCombatSystem = EnhancedCombatSystem

