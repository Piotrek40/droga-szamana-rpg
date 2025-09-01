"""
Combat and Skills Integration Module for Droga Szamana RPG.
Bridges enhanced combat/skills with existing game systems.
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from mechanics.enhanced_combat import (
    EnhancedCombatSystem, Combatant, Weapon, Armor, WeaponType, 
    CombatStance, DamageType, BodyPart, CombatAction, VoidWalkerAbility
)
from player.enhanced_skills import (
    EnhancedSkillSystem, SkillName, SkillCategory
)
from mechanics.combat import CombatStats, Injury
from player.character import CharacterState
# from player.classes import ClassName  # Commented out to avoid enum issues
from core.game_state import game_state


class CombatManager:
    """Manages combat encounters integrating all systems."""
    
    def __init__(self):
        """Initialize combat manager."""
        self.combat_system = EnhancedCombatSystem()
        self.skill_system = EnhancedSkillSystem()
        self.active_combat: Optional['CombatEncounter'] = None
        self.combat_history: List[Dict[str, Any]] = []
        
    def start_combat(self, player: CharacterState, enemies: List[Dict[str, Any]], 
                     environment: List[str] = None) -> 'CombatEncounter':
        """
        Start a combat encounter.
        
        Args:
            player: Player character state
            enemies: List of enemy definitions
            environment: Environmental factors
        
        Returns:
            Active combat encounter
        """
        # Create player combatant
        player_combatant = self._create_player_combatant(player)
        
        # Create enemy combatants
        enemy_combatants = []
        for enemy_data in enemies:
            enemy_combatant = self._create_enemy_combatant(enemy_data)
            enemy_combatants.append(enemy_combatant)
        
        # Set environmental factors
        if environment:
            from mechanics.enhanced_combat import EnvironmentalFactor
            for factor in environment:
                # Map string to enum
                factor_map = {
                    'ciemnosc': EnvironmentalFactor.CIEMNOSC,
                    'ciemność': EnvironmentalFactor.CIEMNOSC,
                    'darkness': EnvironmentalFactor.CIEMNOSC,
                    'sliska_powierzchnia': EnvironmentalFactor.SLISKA_POWIERZCHNIA,
                    'śliska_powierzchnia': EnvironmentalFactor.SLISKA_POWIERZCHNIA,
                    'nierownny_teren': EnvironmentalFactor.NIEROWNNY_TEREN,
                    'nierówny_teren': EnvironmentalFactor.NIEROWNNY_TEREN,
                    'mgla': EnvironmentalFactor.MGLA,
                    'mgła': EnvironmentalFactor.MGLA,
                    'deszcz': EnvironmentalFactor.DESZCZ,
                    'wiatr': EnvironmentalFactor.WIATR,
                    'woda': EnvironmentalFactor.WODA,
                    'wysokosc': EnvironmentalFactor.WYSOKOSC,
                    'wysokość': EnvironmentalFactor.WYSOKOSC,
                    'waska_przestrzen': EnvironmentalFactor.WASKA_PRZESTRZEN,
                    'wąska_przestrzeń': EnvironmentalFactor.WASKA_PRZESTRZEN,
                }
                env_factor = factor_map.get(factor.lower())
                if env_factor:
                    self.combat_system.combat_environment.add(env_factor)
        
        # Create encounter
        encounter = CombatEncounter(
            player=player_combatant,
            enemies=enemy_combatants,
            environment=self.combat_system.combat_environment,
            combat_system=self.combat_system,
            skill_system=self.skill_system
        )
        
        self.active_combat = encounter
        return encounter
    
    def _create_player_combatant(self, player: CharacterState) -> Combatant:
        """Create combatant from player character."""
        # Convert player stats to combat stats
        combat_stats = CombatStats(
            health=player.health,
            max_health=player.max_health,
            stamina=player.stamina,
            max_stamina=player.max_stamina,
            pain=getattr(player, 'pain', 0),
            exhaustion=getattr(player, 'exhaustion', 0)
        )
        
        # Add void energy if player is Void Walker
        if hasattr(player, 'character_class') and player.character_class in ['Void_Walker', 'Wędrowiec_Pustki']:
            combat_stats.void_energy = getattr(player, 'void_energy', 50)
            combat_stats.max_void_energy = getattr(player, 'max_void_energy', 100)
        
        # Get player weapon
        weapon = self._get_player_weapon(player)
        
        # Get player armor
        armor = self._get_player_armor(player)
        
        # Convert skills
        skills = self._convert_player_skills(player)
        
        combatant = Combatant(
            name=player.name,
            stats=combat_stats,
            weapon=weapon,
            armor=armor,
            skills=skills,
            stance=CombatStance.NEUTRALNA
        )
        
        # Copy injuries
        if hasattr(player, 'injuries'):
            combatant.injuries = player.injuries
        
        return combatant
    
    def _create_enemy_combatant(self, enemy_data: Dict[str, Any]) -> Combatant:
        """Create combatant from enemy data."""
        # Create combat stats
        combat_stats = CombatStats(
            health=enemy_data.get('health', 50),
            max_health=enemy_data.get('max_health', 50),
            stamina=enemy_data.get('stamina', 50),
            max_stamina=enemy_data.get('max_stamina', 50),
            pain=0,
            exhaustion=0
        )
        
        # Create weapon if specified
        weapon = None
        if 'weapon' in enemy_data:
            weapon = self._create_weapon(enemy_data['weapon'])
        
        # Create armor if specified
        armor = None
        if 'armor' in enemy_data:
            armor = self._create_armor(enemy_data['armor'])
        
        # Set skills
        skills = enemy_data.get('skills', {
            'walka_wrecz': 10,
            'obrona': 10,
            'uniki': 5
        })
        
        combatant = Combatant(
            name=enemy_data.get('name', 'Przeciwnik'),
            stats=combat_stats,
            weapon=weapon,
            armor=armor,
            skills=skills,
            ai_pattern=enemy_data.get('ai_pattern', 'taktyczny')
        )
        
        return combatant
    
    def _get_player_weapon(self, player: CharacterState) -> Optional[Weapon]:
        """Get player's equipped weapon."""
        if not hasattr(player, 'equipment') or not player.equipment:
            return None
        
        weapon_slot = player.equipment.get('weapon')
        if not weapon_slot:
            return None
        
        # Convert item to weapon
        return self._create_weapon(weapon_slot)
    
    def _get_player_armor(self, player: CharacterState) -> Optional[Armor]:
        """Get player's equipped armor."""
        if not hasattr(player, 'equipment') or not player.equipment:
            return None
        
        armor_pieces = {}
        protection = {}
        total_weight = 0
        
        # Collect all armor pieces
        for slot in ['chest', 'head', 'legs', 'arms']:
            if slot in player.equipment:
                armor_pieces[slot] = player.equipment[slot]
        
        if not armor_pieces:
            return None
        
        # Calculate combined protection
        body_part_map = {
            'head': BodyPart.GLOWA,
            'chest': BodyPart.TULOW,
            'arms': [BodyPart.LEWA_REKA, BodyPart.PRAWA_REKA],
            'legs': [BodyPart.LEWA_NOGA, BodyPart.PRAWA_NOGA]
        }
        
        for slot, item in armor_pieces.items():
            armor_value = item.get('armor', 10)
            parts = body_part_map.get(slot, [])
            if not isinstance(parts, list):
                parts = [parts]
            for part in parts:
                protection[part] = armor_value
            total_weight += item.get('weight', 1)
        
        armor = Armor(
            name="Zbroja gracza",
            polish_name="Zbroja gracza",
            protection=protection,
            weight=total_weight,
            movement_penalty=total_weight * 0.5,
            condition=100,
            quality="zwykła"
        )
        
        return armor
    
    def _convert_player_skills(self, player: CharacterState) -> Dict[str, int]:
        """Convert player skills to combat skills."""
        skills = {}
        
        # Get from player's skill system if available
        if hasattr(player, 'skills') and hasattr(player.skills, 'skills'):
            for skill_name, skill in player.skills.skills.items():
                if hasattr(skill, 'level'):
                    skills[skill_name.value if hasattr(skill_name, 'value') else skill_name] = skill.level
        
        # Add default combat skills if missing
        default_skills = {
            'walka_wrecz': 5,
            'obrona': 5,
            'uniki': 5,
            'miecze': 5,
            'zwinnosc': 10,
            'sila': 10,
            'wytrzymalosc': 10
        }
        
        for skill, level in default_skills.items():
            if skill not in skills:
                skills[skill] = level
        
        return skills
    
    def _create_weapon(self, item_data: Dict[str, Any]) -> Weapon:
        """Create weapon from item data."""
        # Determine weapon type
        weapon_type_map = {
            'noz': WeaponType.SZTYLETY,
            'sztylet': WeaponType.SZTYLETY,
            'miecz': WeaponType.MIECZE_DLUGIE,
            'miecz_krotki': WeaponType.MIECZE_KROTKIE,
            'miecz_dwureczny': WeaponType.MIECZE_DWURECZNE,
            'topor': WeaponType.TOPORY,
            'topor_dwureczny': WeaponType.TOPORY_DWURECZNE,
            'mlot': WeaponType.MLOTY,
            'mlot_bojowy': WeaponType.MLOTY_BOJOWE,
            'wlocznia': WeaponType.WLÓCZNIE,
            'maczuga': WeaponType.MACZUGI,
            'kij': WeaponType.KIJE,
            'luk': WeaponType.LUKI,
            'kusza': WeaponType.KUSZE
        }
        
        item_type = item_data.get('type', 'miecz')
        weapon_type = weapon_type_map.get(item_type, WeaponType.MIECZE_DLUGIE)
        
        # Determine damage type
        damage_type_map = {
            WeaponType.SZTYLETY: DamageType.KLUTE,
            WeaponType.MIECZE_KROTKIE: DamageType.CIECIE,
            WeaponType.MIECZE_DLUGIE: DamageType.CIECIE,
            WeaponType.TOPORY: DamageType.CIECIE,
            WeaponType.MLOTY: DamageType.OBUCHOWE,
            WeaponType.MACZUGI: DamageType.OBUCHOWE,
            WeaponType.WLÓCZNIE: DamageType.KLUTE,
            WeaponType.LUKI: DamageType.KLUTE
        }
        
        damage_type = damage_type_map.get(weapon_type, DamageType.OBUCHOWE)
        
        weapon = Weapon(
            name=item_data.get('id', 'weapon'),
            polish_name=item_data.get('nazwa', 'Broń'),
            weapon_type=weapon_type,
            damage_type=damage_type,
            base_damage=item_data.get('obrazenia', 10),
            speed=item_data.get('szybkosc', 0),
            reach=item_data.get('zasieg', 1),
            weight=item_data.get('waga', 2),
            condition=item_data.get('stan', 100),
            quality=item_data.get('jakosc', 'zwykła')
        )
        
        return weapon
    
    def _create_armor(self, item_data: Dict[str, Any]) -> Armor:
        """Create armor from item data."""
        # Default protection for all body parts
        base_protection = item_data.get('ochrona', 10)
        protection = {
            BodyPart.GLOWA: base_protection * 0.8,
            BodyPart.TULOW: base_protection,
            BodyPart.LEWA_REKA: base_protection * 0.6,
            BodyPart.PRAWA_REKA: base_protection * 0.6,
            BodyPart.LEWA_NOGA: base_protection * 0.7,
            BodyPart.PRAWA_NOGA: base_protection * 0.7
        }
        
        armor = Armor(
            name=item_data.get('id', 'armor'),
            polish_name=item_data.get('nazwa', 'Zbroja'),
            protection=protection,
            weight=item_data.get('waga', 5),
            movement_penalty=item_data.get('kara_ruchu', 10),
            condition=item_data.get('stan', 100),
            quality=item_data.get('jakosc', 'zwykła')
        )
        
        return armor
    
    def process_player_action(self, action: str, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Process player's combat action.
        
        Args:
            action: Action to perform
            target: Target enemy name
        
        Returns:
            Result of the action
        """
        if not self.active_combat:
            return {'success': False, 'message': 'Brak aktywnej walki!'}
        
        return self.active_combat.process_player_turn(action, target)
    
    def process_enemy_turns(self) -> List[Dict[str, Any]]:
        """Process all enemy turns."""
        if not self.active_combat:
            return []
        
        return self.active_combat.process_enemy_turns()
    
    def check_combat_end(self) -> Optional[str]:
        """Check if combat has ended."""
        if not self.active_combat:
            return None
        
        return self.active_combat.check_victory_condition()
    
    def apply_combat_results(self, player: CharacterState):
        """Apply combat results back to player character."""
        if not self.active_combat:
            return
        
        player_combatant = self.active_combat.player
        
        # Update player stats
        player.health = player_combatant.stats.health
        player.stamina = player_combatant.stats.stamina
        player.pain = player_combatant.stats.pain
        player.exhaustion = player_combatant.stats.exhaustion
        
        # Update void energy if applicable
        if hasattr(player_combatant.stats, 'void_energy'):
            player.void_energy = player_combatant.stats.void_energy
        
        # Update injuries
        player.injuries = player_combatant.injuries
        
        # Apply skill improvements
        self._apply_skill_improvements(player)
        
        # Update equipment condition
        if player_combatant.weapon:
            # Update weapon condition in inventory
            pass  # Would need inventory system integration
        
        if player_combatant.armor:
            # Update armor condition
            pass  # Would need inventory system integration
        
        # Add to combat history
        self.combat_history.append({
            'date': getattr(game_state, 'world_time', 0),  # Safe access to world_time
            'enemies': [e.name for e in self.active_combat.enemies],
            'result': self.check_combat_end(),
            'rounds': self.active_combat.round_count,
            'injuries_sustained': len(player_combatant.injuries)
        })
    
    def _apply_skill_improvements(self, player: CharacterState):
        """Apply skill improvements from combat."""
        # This would integrate with the player's skill system
        # For now, we'll just track that skills were used
        pass


@dataclass
class CombatEncounter:
    """Represents an active combat encounter."""
    player: Combatant
    enemies: List[Combatant]
    environment: set
    combat_system: EnhancedCombatSystem
    skill_system: EnhancedSkillSystem
    round_count: int = 0
    turn_order: List[str] = field(default_factory=list)
    combat_log: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize combat encounter."""
        self._determine_initiative()
    
    def _determine_initiative(self):
        """Determine turn order based on initiative."""
        participants = [self.player] + self.enemies
        
        # Calculate initiative for each participant
        initiatives = []
        for participant in participants:
            init_value = participant.calculate_initiative()
            initiatives.append((participant.name, init_value))
        
        # Sort by initiative (highest first)
        initiatives.sort(key=lambda x: x[1], reverse=True)
        self.turn_order = [name for name, _ in initiatives]
    
    def process_player_turn(self, action_str: str, target_name: Optional[str] = None) -> Dict[str, Any]:
        """Process player's turn."""
        result = {
            'success': False,
            'message': '',
            'effects': []
        }
        
        # Parse action
        action = self._parse_action(action_str)
        if not action:
            result['message'] = f"Nieznana akcja: {action_str}"
            return result
        
        # Find target
        target = None
        if target_name:
            target = self._find_enemy(target_name)
            if not target:
                result['message'] = f"Nie znaleziono celu: {target_name}"
                return result
        elif action in [CombatAction.ATAK_PODSTAWOWY, CombatAction.ATAK_SILNY, CombatAction.ATAK_SZYBKI]:
            # Default to first alive enemy
            for enemy in self.enemies:
                if enemy.stats.is_conscious and enemy.stats.health > 0:
                    target = enemy
                    break
        
        # Check for technique usage
        technique = None
        if 'technika:' in action_str.lower():
            tech_name = action_str.split('technika:')[1].strip()
            technique = self.combat_system.techniques.get(tech_name)
        
        # Process the action
        if target:
            combat_result = self.combat_system.process_combat_turn(
                self.player, target, action, technique
            )
            
            # Use skill
            skill_to_use = self._determine_skill_for_action(action, self.player.weapon)
            if skill_to_use:
                skill_success, skill_msg, skill_effects = self.skill_system.use_skill(
                    skill_to_use,
                    difficulty=target.get_defense_skill(),
                    conditions={
                        'pain': self.player.stats.pain,
                        'exhaustion': self.player.stats.exhaustion,
                        'injuries': self.player.injuries
                    }
                )
                result['effects'].append(f"Umiejętność: {skill_msg}")
            
            result['success'] = True
            result['message'] = '\n'.join(combat_result['messages'])
            result['effects'].extend(combat_result.get('effects', []))
        else:
            # Defensive action or no target needed
            if action in [CombatAction.OBRONA, CombatAction.UNIK, CombatAction.PAROWANIE]:
                self.player.defensive_action = action
                result['success'] = True
                result['message'] = f"Przyjmujesz postawę: {action.value}"
        
        self.round_count += 1
        self.combat_log.append(result['message'])
        return result
    
    def process_enemy_turns(self) -> List[Dict[str, Any]]:
        """Process all enemy turns."""
        results = []
        
        for enemy in self.enemies:
            if not enemy.stats.is_conscious or enemy.stats.health <= 0:
                continue
            
            # AI chooses action
            action, technique = self.combat_system.ai_choose_action(enemy, self.player)
            
            # Process the action
            combat_result = self.combat_system.process_combat_turn(
                enemy, self.player, action, technique
            )
            
            result = {
                'attacker': enemy.name,
                'action': action.value,
                'success': combat_result['success'],
                'damage': combat_result.get('damage', 0),
                'message': '\n'.join(combat_result['messages'])
            }
            
            results.append(result)
            self.combat_log.append(result['message'])
            
            # Enemy learns from combat
            enemy.memory.observed_actions.append(self.player.defensive_action or 'none')
        
        return results
    
    def check_victory_condition(self) -> Optional[str]:
        """Check if combat has ended."""
        # Check player defeat
        if not self.player.stats.is_conscious or self.player.stats.health <= 0:
            return "defeat"
        
        # Check enemy defeat
        all_defeated = True
        for enemy in self.enemies:
            if enemy.stats.is_conscious and enemy.stats.health > 0:
                all_defeated = False
                break
        
        if all_defeated:
            return "victory"
        
        # Check flee condition
        if self.player.stats.health < 10 and self.round_count > 5:
            return "flee_available"
        
        return None
    
    def _parse_action(self, action_str: str) -> Optional[CombatAction]:
        """Parse string action to CombatAction enum."""
        action_map = {
            'atak': CombatAction.ATAK_PODSTAWOWY,
            'silny_atak': CombatAction.ATAK_SILNY,
            'szybki_atak': CombatAction.ATAK_SZYBKI,
            'obrona': CombatAction.OBRONA,
            'unik': CombatAction.UNIK,
            'parowanie': CombatAction.PAROWANIE,
            'riposta': CombatAction.RIPOSTA,
            'finta': CombatAction.FINTA,
            'kopnięcie': CombatAction.KOPNIECIE,
            'pchnięcie': CombatAction.PCHNIECIE
        }
        
        for key, value in action_map.items():
            if key in action_str.lower():
                return value
        
        return None
    
    def _find_enemy(self, name: str) -> Optional[Combatant]:
        """Find enemy by name."""
        for enemy in self.enemies:
            if name.lower() in enemy.name.lower():
                return enemy
        return None
    
    def _determine_skill_for_action(self, action: CombatAction, weapon: Optional[Weapon]) -> Optional[SkillName]:
        """Determine which skill to use for the action."""
        if action in [CombatAction.ATAK_PODSTAWOWY, CombatAction.ATAK_SILNY, CombatAction.ATAK_SZYBKI]:
            if not weapon:
                return SkillName.WALKA_WRECZ
            
            weapon_skill_map = {
                WeaponType.SZTYLETY: SkillName.SZTYLETY,
                WeaponType.MIECZE_KROTKIE: SkillName.MIECZE,
                WeaponType.MIECZE_DLUGIE: SkillName.MIECZE,
                WeaponType.MIECZE_DWURECZNE: SkillName.MIECZE_DWURECZNE,
                WeaponType.TOPORY: SkillName.TOPORY,
                WeaponType.TOPORY_DWURECZNE: SkillName.TOPORY_DWURECZNE,
                WeaponType.MLOTY: SkillName.MLOTY,
                WeaponType.MLOTY_BOJOWE: SkillName.MLOTY_BOJOWE,
                WeaponType.WLÓCZNIE: SkillName.WLÓCZNIE,
                WeaponType.MACZUGI: SkillName.MACZUGI,
                WeaponType.LUKI: SkillName.LUCZNICTWO,
                WeaponType.KUSZE: SkillName.KUSZE
            }
            
            return weapon_skill_map.get(weapon.weapon_type, SkillName.WALKA_WRECZ)
        
        elif action == CombatAction.OBRONA:
            return SkillName.OBRONA
        elif action == CombatAction.UNIK:
            return SkillName.UNIKI
        elif action == CombatAction.PAROWANIE:
            return SkillName.PAROWANIE
        
        return None
    
    def get_combat_status(self) -> Dict[str, Any]:
        """Get current combat status."""
        status = {
            'round': self.round_count,
            'player': {
                'name': self.player.name,
                'health': f"{self.player.stats.health}/{self.player.stats.max_health}",
                'stamina': f"{self.player.stats.stamina}/{self.player.stats.max_stamina}",
                'pain': self.player.stats.pain,
                'stance': self.player.stance.value,
                'weapon': self.player.weapon.polish_name if self.player.weapon else "Pięści",
                'injuries': len(self.player.injuries)
            },
            'enemies': [],
            'environment': [f.value for f in self.environment]
        }
        
        for enemy in self.enemies:
            if enemy.stats.is_conscious and enemy.stats.health > 0:
                status['enemies'].append({
                    'name': enemy.name,
                    'health': f"{enemy.stats.health}/{enemy.stats.max_health}",
                    'stance': enemy.stance.value,
                    'weapon': enemy.weapon.polish_name if enemy.weapon else "Pięści",
                    'condition': self.combat_system.calculate_combat_outcome(enemy)
                })
        
        return status