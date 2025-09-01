# CLAUDE.md - Droga Szamana RPG Game Master

This file provides guidance to Claude Code when orchestrating the "Droga Szamana" text-based RPG project inspired by Vasily Mahanenko's LitRPG series.

## 🎮 PROJECT OVERVIEW

We are building a deep, immersive text-based RPG that captures the essence of being trapped in a game world where every action matters. Like Mahan in the books, players start as nobody and must earn everything through actual practice and skill development.

### Core Philosophy
- **NO PLACEHOLDERS** ❌ - Every function must be fully implemented
- **NO XP GRINDING** - Skills grow ONLY through use, like in the books
- **EMERGENT GAMEPLAY** - No "kill 10 wolves" quests. World lives and reacts
- **PAIN IS REAL** - Actions have consequences. Injuries matter
- **ECONOMY LIVES** - NPCs trade, craft, consume. Markets fluctuate

## ⚠️ PROJECT-SPECIFIC CRITICAL RULES

### 🔴 DISCOVERED ISSUES TO ALWAYS CHECK:
1. **Multiple NPC data files** - We have npcs.json, npc_unified.json, npc_mapping.json
   - ALWAYS use `npc_unified.json` as source of truth
   - Update ALL when changing NPC data
   
2. **Event Bus is CENTRAL** - All systems communicate through events
   - NEVER direct call between systems
   - ALWAYS emit events for cross-system communication
   
3. **GameState is SINGLETON** - Only one instance exists
   - Access via `from core.game_state import game_state`
   - NEVER create new GameState()

4. **Circular Import Risk Zones**:
   - `npc_manager` ↔ `combat` → use events
   - `quest_engine` ↔ `npc_manager` → use events
   - `game_state` → everything → careful with imports

### 📊 CURRENT PROJECT METRICS (2024-08-31):
- **Total Lines**: 22,045
- **Python Files**: 37
- **JSON Files**: 13
- **Test Coverage**: ~60% (needs improvement)
- **Known Tech Debt**:
  - [ ] Consolidate NPC data files
  - [ ] Add type hints to all functions
  - [ ] Increase test coverage to 80%
  - [ ] Refactor dialogue system (too complex)

## 📂 PROJECT STRUCTURE

```
droga-szamana-rpg/
├── core/                 # Game engine and main loop
│   ├── main.py          # Entry point & game orchestration
│   ├── game_state.py    # Global state management
│   └── event_bus.py     # Event-driven architecture
├── world/               # World simulation
│   ├── locations/       # All game locations
│   ├── time_system.py   # Day/night cycles, seasons
│   └── weather.py       # Dynamic weather system
├── npcs/                # NPC intelligence system
│   ├── npc_manager.py   # NPC lifecycle management
│   ├── ai_behaviors.py  # Behavior trees & routines
│   └── memory_system.py # NPC memory & relationships
├── player/              # Player systems
│   ├── character.py     # Player stats & attributes
│   ├── skills.py        # Skill progression system
│   └── void_walker.py   # Special abilities
├── mechanics/           # Core game mechanics
│   ├── combat.py        # Combat with pain system
│   ├── crafting.py      # Deep crafting chains
│   ├── economy.py       # Living economy simulation
│   └── reputation.py    # Multi-faction reputation
├── quests/              # Quest system
│   ├── quest_engine.py  # Emergent quest generator
│   └── quest_chains.py  # Story-driven quests
├── data/                # Game data files
│   ├── items.json       # All items & properties
│   ├── recipes.json     # Crafting recipes & chains
│   ├── world_data.json  # Location definitions
│   └── npcs.json        # NPC templates & schedules
├── ui/                  # User interface
│   ├── interface.py     # Text UI system
│   └── commands.py      # Player command parser
├── persistence/         # Save system
│   └── save_manager.py  # Save/load functionality
└── tests/               # Comprehensive testing
    └── test_all.py      # Full test suite
```

## 🔧 DEVELOPMENT COMMANDS

### Build & Test
```bash
# Run the game
python main.py

# Run comprehensive tests
python -m pytest tests/ -v
python tests/test_all.py  # Alternative comprehensive test

# Test combat system
python tests/test_combat_demo.py  # Interactive combat demo
python tests/test_combat_auto.py  # Automated combat test

# Verify dialogues
python verify_dialogues.py

# Check code quality (when .pylintrc exists)
python -m pylint core/ --rcfile=.pylintrc

# Format code
black . --line-length=100
```

### 🐛 DEBUGGING HELPERS
```bash
# Check for circular imports
python -c "from core import *; from npcs import *; from mechanics import *; print('✓')"

# Verify JSON integrity
python -c "import json; [json.load(open(f'data/{f}')) for f in ['npcs.json','items.json','recipes.json']]; print('✓ JSONs valid')"

# Count project size
find . -name "*.py" -type f | xargs wc -l | tail -1
```

### Git Workflow @docs/git-workflow.md
- Feature branches: `feature/skill-system`
- Commit format: `[MODULE] Action: Description`
- Example: `[NPC] Add: Memory system for long-term relationships`

## 🧠 THINKING MODES

Use these keywords to trigger appropriate thinking depth:
- `think` - Basic planning for simple features
- `think hard` - Complex system design (economy, NPC AI)
- `think harder` - Multi-system integration
- `ultrathink` - Full game architecture decisions

## 📋 CRITICAL REQUIREMENTS

### 1. **Full Implementation Only**
```python
# ❌ NEVER DO THIS:
def calculate_damage():
    # TODO: Implement damage calculation
    pass

# ✅ ALWAYS DO THIS:
def calculate_damage(attacker_strength, weapon_damage, defender_armor):
    base_damage = attacker_strength + weapon_damage
    mitigated = max(1, base_damage - defender_armor)
    variance = random.uniform(0.8, 1.2)
    return int(mitigated * variance)
```

### 2. **Skill Progression Through Use**
```python
# Skills MUST increase by doing, not by spending XP
# Every action checks for skill improvement
def use_skill(skill_name, difficulty):
    current_level = player.skills[skill_name]
    success = perform_skill_check(current_level, difficulty)
    
    # Chance to improve based on challenge
    if difficulty >= current_level - 2:
        improvement_chance = 0.1 * (difficulty / current_level)
        if random.random() < improvement_chance:
            improve_skill(skill_name, 0.01)
    
    return success
```

### 3. **Living NPCs**
Every NPC must have:
- Daily routines (work, eat, sleep, socialize)
- Memory of player interactions
- Personal goals and fears
- Economic participation (buy, sell, craft)
- Relationships with other NPCs

### 4. **Emergent Quests**
Quests arise from world state, not static definitions:
- Merchant robbed → Track down bandits
- Drought → Find water source
- NPC rivalry → Choose sides or mediate

## 🎯 SUBAGENT ORCHESTRATION

When implementing features, delegate to specialized subagents:

### Available Subagents
1. **npc-ai-expert** - NPC behavior, memory, relationships
2. **combat-skills-expert** - Combat mechanics, skill progression
3. **crafting-economy-expert** - Item creation, market simulation
4. **world-builder-expert** - Locations, lore, descriptions
5. **quest-designer-expert** - Dynamic quest generation

### 🔥 WHEN TO USE EACH SUBAGENT (Project-Specific):

#### **npc-ai-expert** → ALWAYS for:
- Modifying `npcs/ai_behaviors.py` (complex behavior trees)
- Updating `npcs/memory_system.py` (4-layer memory)
- Adding new NPCs to `data/npc_unified.json`
- Implementing NPC schedules or routines

#### **combat-skills-expert** → ALWAYS for:
- Modifying `mechanics/combat.py` (pain system critical)
- Updating `player/skills.py` (use-based progression)
- Balancing combat mechanics in `data/combat_mechanics.json`
- Adding new abilities in `player/ability_effects.py`

#### **crafting-economy-expert** → ALWAYS for:
- Modifying `mechanics/economy.py` (market simulation)
- Updating `mechanics/crafting.py` (recipe chains)
- Adding items to `data/items.json`
- Creating recipes in `data/recipes.json`

#### **quest-designer-expert** → ALWAYS for:
- Modifying `quests/quest_engine.py` (emergent quests)
- Updating `quests/consequences.py` (ripple effects)
- Creating quest chains in `quests/quest_chains.py`

### Orchestration Patterns

**Feature Development Flow:**
```
1. world-builder → Create location
2. npc-ai → Populate with NPCs
3. economy → Set up local market
4. quest-designer → Generate area quests
5. THIS (main) → Integrate all systems
```

**Complex System Implementation:**
```
1. THIS → Design system architecture
2. [Relevant Expert] → Implement core mechanics
3. [Other Experts] → Add integrations
4. THIS → Verify consistency & merge
```

## 🔍 CODE REVIEW CHECKLIST

Before accepting any code:
- [ ] No TODO, FIXME, or placeholder comments
- [ ] All functions have actual implementations
- [ ] Error handling for edge cases
- [ ] NPCs have full behavior trees
- [ ] Skills progress through use only
- [ ] Economy calculations are realistic
- [ ] Combat includes pain/injury system
- [ ] Save/load compatibility maintained

## 💾 GAME STATE ARCHITECTURE

### Global State Management
```python
class GameState:
    def __init__(self):
        self.world_time = 0  # In-game minutes since start
        self.player = None
        self.npcs = {}  # uuid -> NPC instance
        self.locations = {}  # name -> Location instance
        self.global_economy = EconomySimulator()
        self.event_queue = []
        self.faction_standings = {}
```

### Event-Driven Updates
All systems communicate through events:
```python
# NPC decides to craft item
event_bus.emit("npc_crafting", {
    "npc_id": npc.uuid,
    "item": "iron_sword",
    "location": npc.current_location
})

# Economy system listens and adjusts prices
# Quest system might generate "supply weapons" quest
# Player might witness if nearby
```

## 📝 POLISH LOCALIZATION

All text must be in Polish by default:
```python
MESSAGES = {
    "welcome": "Witaj w świecie Barliony, Podróżniku.",
    "skill_improved": "Twoja umiejętność {skill} wzrosła!",
    "pain_message": "Czujesz przeszywający ból w {body_part}.",
    "npc_memory": "{npc} pamięta, że {action}."
}
```

## 🎮 GAMEPLAY PRIORITIES

1. **Immersion First** - Every action should feel meaningful
2. **Challenge Through Realism** - Not artificial difficulty
3. **Discovery Over Exposition** - Let players learn by doing
4. **Consequences Matter** - Both immediate and long-term
5. **World Continues** - NPCs live even when player isn't watching

## 🚀 PERFORMANCE REQUIREMENTS

- Game must run smoothly with 100+ active NPCs
- Save files under 10MB
- Load time under 3 seconds
- Turn processing under 500ms

## 🔍 COMMON PITFALLS IN THIS PROJECT

### ❌ AVOID THESE MISTAKES:
1. **Creating new GameState()** - it's a singleton!
2. **Direct imports between systems** - use event bus
3. **Modifying only one NPC data file** - update all three
4. **Adding skills without use progression** - no XP!
5. **Hardcoding Polish text in .py files** - use data/ui_texts.json
6. **Forgetting to test after changes** - run test_all.py
7. **Not checking circular imports** - verify with import test

### ✅ ALWAYS DO:
1. **Check DEPENDENCY_MAP.md** before modifying core systems
2. **Use event_bus.emit()** for cross-system communication
3. **Test combat changes** with test_combat_demo.py
4. **Verify dialogues** with verify_dialogues.py
5. **Update ALL NPC files** when changing NPC data
6. **Add Polish text** to ui_texts.json, not code

## 📚 REFERENCES

- @README.md - Public project description
- @docs/game-design.md - Detailed design document
- @docs/skill-list.md - All 50+ skills with progression curves
- @docs/npc-personalities.md - NPC archetype definitions
- @shared/constants.py - Game balance constants

## 🔄 ITERATION PROTOCOL

When requested to enhance the game:
1. **NEVER** start from scratch
2. Load existing codebase
3. Identify integration points
4. Extend functionality
5. Maintain backward compatibility
6. Update tests

## ⚡ QUICK COMMANDS

For rapid development, use these patterns:

```bash
# Add new skill
/add-skill "Kowalstwo" smithing physical

# Create NPC with full AI
/create-npc "Grzesiek" merchant suspicious

# Generate quest chain
/quest-chain "Zagadka Pustkowi" mystery 5-parts

# Test specific system
/test-system economy --cycles 1000
```

## 🎯 CURRENT SPRINT GOALS

1. [ ] Implement base game loop with 3 locations
2. [ ] Create 10 NPCs with full routines
3. [ ] Add 20 core skills with use-based progression
4. [ ] Implement crafting with 50 recipes
5. [ ] Create pain/injury system
6. [ ] Add dynamic market economy
7. [ ] Generate 5 emergent quest types
8. [ ] Polish language throughout

---

Remember: We're not making another generic RPG. We're creating a living world where, like Mahan, the player must earn everything through genuine effort, where NPCs have their own lives, and where every action resonates through the game world.

**"Prawdziwa gra dopiero się zaczyna"** - The real game is just beginning.