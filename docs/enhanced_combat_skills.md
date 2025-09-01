# Enhanced Combat & Skill Progression System Documentation

## Overview

The Droga Szamana RPG features a comprehensive, realistic combat system inspired by Vasily Mahanenko's LitRPG series, where pain is real, injuries have lasting consequences, and every skill must be earned through practice - never through XP spending.

## Core Systems

### 1. Enhanced Combat System (`mechanics/enhanced_combat.py`)

#### Features:
- **Pain System (0-100)**: Affects all combat actions
  - 0-30: No penalties
  - 30-50: -15% to skills
  - 50-70: -30% to skills, -1 action
  - 70-80: -45% to skills, stun chance
  - 80+: Unconsciousness

- **Injury Localization**: 
  - Body parts: Head, Torso, Left/Right Arms, Left/Right Legs
  - Each injury affects specific actions
  - Bleeding, infection risks, permanent scars

- **Weapon Mastery**:
  - 15+ weapon types (swords, axes, bows, daggers, etc.)
  - Weapon condition degradation
  - Quality levels: broken, poor, normal, good, masterwork, legendary
  - Reach and timing mechanics

- **Combat Techniques**:
  - Basic, Combo, Special, Master, Legendary techniques
  - Discoverable through practice
  - Combo chains for advanced moves

- **Environmental Factors**:
  - Darkness (-30% accuracy)
  - Slippery surface (-30% movement, -15% defense)
  - Rain (archery penalty)
  - Narrow spaces (long weapon penalty)

- **NPC AI Patterns**:
  - Aggressive, Defensive, Tactical, Berserker, Archer
  - Memory system for learning player patterns
  - Retreat behaviors based on health

### 2. Enhanced Skill System (`player/enhanced_skills.py`)

#### Features:
- **60+ Skills** across 10 categories:
  - Combat (11 weapon skills)
  - Defense (6 defensive skills)
  - Ranged (4 archery skills)
  - Magic/Void (4 void walker skills)
  - Crafting (9 profession skills)
  - Social (7 interaction skills)
  - Thievery (6 rogue skills)
  - Survival (7 wilderness skills)
  - Knowledge (6 lore skills)
  - Athletic (7 physical skills)

- **Use-Based Learning**:
  - Skills ONLY improve through practice
  - Optimal difficulty window (skill level +5 to +15)
  - Learning from failure (150% bonus at optimal difficulty)
  - Logarithmic progression (harder at higher levels)

- **Muscle Memory System**:
  - Three-layer memory: muscle, theoretical, practical
  - Skills degrade without practice
  - Peak level tracking
  - Memory affects learning speed

- **Skill Synergies**:
  - Related skills boost each other
  - Example: Swords synergizes with Parrying (+20%)
  - Max 20% bonus from all synergies

- **Technique Discovery**:
  - Hidden techniques unlock through practice
  - Requirements based on skill levels
  - Mastery percentage for each technique

### 3. Void Walker Abilities (`mechanics/enhanced_combat.py`)

Special abilities for the Void Walker class:
- **Void Touch**: Direct damage through void energy
- **Shadow Step**: Teleportation through shadows
- **Reality Tear**: Area damage and confusion
- **Void Absorption**: Damage with life steal

All void abilities:
- Cost void energy to use
- Cause pain to the user (15-25 points)
- Have cooldowns (2-5 turns)
- Must be learned through practice

### 4. Combat Integration (`mechanics/combat_integration.py`)

Bridges the enhanced systems with the existing game:
- `CombatManager`: Main interface for combat
- `CombatEncounter`: Active combat tracking
- Player/NPC conversion utilities
- Skill improvement application
- Combat history tracking

## Usage Examples

### Starting Combat
```python
from mechanics.combat_integration import CombatManager

combat_manager = CombatManager()

# Define enemies
enemies = [
    {
        'name': 'Bandit',
        'health': 60,
        'weapon': {'type': 'sword', 'damage': 12},
        'skills': {'swords': 10, 'defense': 8},
        'ai_pattern': 'aggressive'
    }
]

# Start combat with environmental factors
environment = ['darkness', 'slippery_surface']
encounter = combat_manager.start_combat(player, enemies, environment)

# Process player action
result = combat_manager.process_player_action('attack', 'Bandit')

# Process enemy turns
enemy_results = combat_manager.process_enemy_turns()

# Check victory
outcome = combat_manager.check_combat_end()
```

### Using Skills
```python
from player.enhanced_skills import EnhancedSkillSystem, SkillName

skill_system = EnhancedSkillSystem()

# Use a skill with conditions
success, message, effects = skill_system.use_skill(
    SkillName.MIECZE,  # Sword skill
    difficulty=20,      # Task difficulty
    conditions={
        'pain': 35,     # Current pain level
        'exhaustion': 20,
        'equipment_quality': 'good'
    }
)

# Check for skill improvement
if effects['learning']['improved']:
    print(f"Skill improved to level {skill.level}!")

# Apply time degradation (days without practice)
skill_system.apply_time_degradation(30)
```

### Combat Techniques
```python
# Execute a special technique
technique = combat_system.techniques['horizontal_slash']
if technique.can_execute(player_skill, stamina, weapon):
    success, result = combat_system.execute_technique(
        attacker, defender, technique
    )

# Check for combo opportunities
combo = combat_system.check_combo_opportunity(player_name, action)
if combo:
    print(f"Combo available: {combo.polish_name}")
```

## Combat Flow

1. **Initiative**: Determined by skills, equipment, and condition
2. **Player Turn**: Choose action (attack, defend, technique, ability)
3. **Skill Check**: Use appropriate skill with all modifiers
4. **Damage Application**: Apply damage, pain, and injuries
5. **Enemy Turns**: AI chooses actions based on pattern
6. **Status Updates**: Fatigue, bleeding, recovery
7. **Victory Check**: Determine if combat continues

## Key Mechanics

### Pain Accumulation
- Each hit causes pain based on damage and location
- Head hits: 1.5x pain multiplier
- Torso hits: 1.0x pain multiplier
- Limb hits: 0.7-0.9x pain multiplier

### Fatigue System
- Short-term: Stamina (regenerates quickly)
- Long-term: Exhaustion (requires rest)
- Actions cost stamina
- Low stamina reduces effectiveness

### Weapon Degradation
- Each use degrades weapon condition
- Quality affects degradation rate
- Broken weapons deal 50% damage
- Requires repair at blacksmith

### Skill Learning Chances
- Too easy (<5 level difference): 2% chance
- Optimal (5-15 difference): 15% chance
- Hard (15-30 difference): 8% chance
- Very hard (30-50 difference): 4% chance
- Impossible (>50 difference): 0% chance

## Integration Points

The system integrates with:
- **GUI** (`integrated_gui.py`): Combat display panels
- **Game State** (`core/game_state.py`): Global state tracking
- **NPCs** (`npcs/npc_manager.py`): NPC combat behaviors
- **Items** (`data/items.json`): Weapon and armor definitions
- **Save System**: Combat stats persistence

## Testing

Run comprehensive tests:
```bash
python tests/test_enhanced_combat.py
```

Tests cover:
- Weapon mastery and degradation
- Skill progression and synergies
- Pain and injury mechanics
- Combat techniques and combos
- Environmental factors
- Void Walker abilities
- NPC AI patterns
- Full system integration

## Performance Considerations

- Combat calculations optimized for 100+ NPCs
- Skill checks cached for repeated use
- Memory-efficient injury tracking
- AI decisions use pattern caching

## Polish Localization

All combat messages and skill names are in Polish:
- Combat actions: "atak", "obrona", "unik"
- Skills: "miecze", "łucznictwo", "kowalstwo"
- Messages: "Trafienie w głowę!", "Umiejętność wzrosła!"

## Future Enhancements

Potential additions:
- Mounted combat
- Dual wielding mechanics
- Team combat coordination
- Weather-specific techniques
- Crafted technique scrolls
- Combat replay system

---

*"W tym świecie ból jest prawdziwy, śmierć ma konsekwencje,  
a każda umiejętność musi być zdobyta krwią i potem."*