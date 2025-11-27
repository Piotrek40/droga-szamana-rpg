"""Integration helpers bridging combat tests with existing mechanics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional

import builtins

from mechanics.combat import CombatStats, Weapon, WeaponType, DamageType
from mechanics.enhanced_combat import EnhancedCombatSystem, Combatant
from player.enhanced_skills import EnhancedSkillSystem


@dataclass
class CombatEncounter:
    player: Combatant
    enemies: List[Combatant]
    environment: List[str]
    turn_order: List[str]

    def get_combat_status(self) -> Dict:
        return {
            "player": {
                "health": self.player.stats.health,
                "stamina": self.player.stats.stamina,
                "pain": self.player.stats.pain,
            },
            "enemies": [
                {"name": enemy.name, "health": enemy.stats.health}
                for enemy in self.enemies
            ],
            "environment": self.environment,
        }


class CombatManager:
    def __init__(self):
        self.combat_system = EnhancedCombatSystem()
        self.skill_system = self.combat_system.skill_system
        self.current_encounter: Optional[CombatEncounter] = None

    # Session lifecycle -----------------------------------------------------------
    def start_combat(self, player, enemies: List[Dict], environment: List[str]):
        player_combatant = Combatant(
            name=player.name,
            stats=CombatStats(
                health=player.health,
                max_health=player.max_health,
                stamina=player.stamina,
                max_stamina=player.max_stamina,
                pain=getattr(player, "pain", 0),
                exhaustion=getattr(player, "exhaustion", 0),
            ),
            skills={},
        )

        enemy_objs: List[Combatant] = []
        for enemy in enemies:
            weapon_data = enemy.get("weapon", {})
            weapon = Weapon(
                name=weapon_data.get("type", "punch"),
                polish_name=weapon_data.get("nazwa", weapon_data.get("type", "Broń")),
                weapon_type=self._map_weapon_type(weapon_data.get("type")),
                damage_type=DamageType.CIECIE,
                base_damage=weapon_data.get("obrazenia", 8),
                speed=1,
                reach=weapon_data.get("zasieg", 1),
                weight=2,
            )
            enemy_objs.append(
                Combatant(
                    name=enemy["name"],
                    stats=CombatStats(
                        health=enemy.get("health", 50),
                        max_health=enemy.get("max_health", enemy.get("health", 50)),
                        stamina=enemy.get("stamina", 50),
                        max_stamina=enemy.get("max_stamina", enemy.get("stamina", 50)),
                    ),
                    weapon=weapon,
                    skills=enemy.get("skills", {}),
                    ai_pattern=enemy.get("ai_pattern", "agresywny"),
                )
            )

        self.current_encounter = CombatEncounter(
            player=player_combatant,
            enemies=enemy_objs,
            environment=environment,
            turn_order=[player_combatant.name] + [e.name for e in enemy_objs],
        )

        # Map textual environment to enum for combat calculations
        for env in environment:
            mapped = self._map_environment(env)
            if mapped:
                self.combat_system.combat_environment.add(mapped)

        return self.current_encounter

    # Combat round helpers --------------------------------------------------------
    def process_player_action(self, action: str, target_name: str):
        encounter = self.current_encounter
        if not encounter:
            return {"message": "Brak aktywnej walki"}

        target = next((e for e in encounter.enemies if e.name == target_name), None)
        if not target:
            return {"message": "Cel nie istnieje"}

        result = self.combat_system.process_combat_turn(
            encounter.player, target, self._map_action(action)
        )
        return {"attacker": encounter.player.name, "message": result["messages"][0]}

    def process_enemy_turns(self):
        encounter = self.current_encounter
        if not encounter:
            return []

        results = []
        for enemy in encounter.enemies:
            if enemy.stats.health <= 0:
                continue
            action, _ = self.combat_system.ai_choose_action(enemy, encounter.player)
            turn_result = self.combat_system.process_combat_turn(
                enemy, encounter.player, action
            )
            results.append({
                "attacker": enemy.name,
                "message": turn_result["messages"][0],
            })
        return results

    def check_combat_end(self) -> Optional[str]:
        if not self.current_encounter:
            return None
        if self.current_encounter.player.stats.health <= 0:
            return "enemy_victory"
        if all(enemy.stats.health <= 0 for enemy in self.current_encounter.enemies):
            return "player_victory"
        return None

    def apply_combat_results(self, player_obj) -> None:
        if not self.current_encounter:
            return
        player_obj.health = self.current_encounter.player.stats.health
        player_obj.stamina = self.current_encounter.player.stats.stamina
        player_obj.pain = self.current_encounter.player.stats.pain
        player_obj.exhaustion = self.current_encounter.player.stats.exhaustion

    # Mapping helpers -------------------------------------------------------------
    def _map_weapon_type(self, type_name: str | None) -> WeaponType:
        mapping = {
            "miecz": WeaponType.MIECZE_DLUGIE,
            "luk": WeaponType.LUKI,
            "topor": WeaponType.TOPORY,
        }
        return mapping.get(type_name, WeaponType.MIECZE_DLUGIE)

    def _map_environment(self, env: str):
        env = env.lower()
        from mechanics.combat import EnvironmentalFactor

        return {
            "ciemnosc": EnvironmentalFactor.CIEMNOSC,
            "sliska_powierzchnia": EnvironmentalFactor.SLISKA_POWIERZCHNIA,
            "nierownny_teren": EnvironmentalFactor.SLISKA_POWIERZCHNIA,
        }.get(env)

    def _map_action(self, action: str):
        from mechanics.combat import CombatAction

        return {
            "atak": CombatAction.ATAK_PODSTAWOWY,
            "obrona": CombatAction.OBRONA,
        }.get(action, CombatAction.ATAK_PODSTAWOWY)


# Make available in the global namespace for legacy test usage
builtins.CombatManager = CombatManager

