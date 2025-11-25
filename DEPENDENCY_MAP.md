# 🗺️ DEPENDENCY MAP - Droga Szamana RPG

## 📊 System Overview
```
main.py
├── core/
│   ├── game_state.py ← [SINGLETON] Global state holder
│   └── event_bus.py ← [HUB] All systems communicate through this
├── npcs/
│   ├── npc_manager.py → uses: memory_system, ai_behaviors
│   ├── ai_behaviors.py → uses: behavior_trees
│   └── memory_system.py → standalone (no deps)
├── mechanics/
│   ├── combat.py → uses: game_state, event_bus
│   ├── economy.py → uses: event_bus, npc_manager
│   └── crafting.py → uses: economy, items
├── player/
│   ├── character.py → uses: skills, game_state
│   └── skills.py → uses: event_bus
└── quests/
    └── quest_engine.py → uses: npc_manager, event_bus, game_state
```

## 🔗 Core Dependencies

### game_state.py
- **Imports**: `time_system, player.character, npcs.npc_manager`
- **Exports**: `GameState` (singleton)
- **Used by**: ALL systems reference this
- **Critical**: Breaking changes here affect EVERYTHING

### event_bus.py
- **Imports**: `logging, queue, typing`
- **Exports**: `EventBus, Event, EventHandler`
- **Used by**: `combat, economy, skills, quest_engine, npc_manager`
- **Critical**: Event structure changes require updating ALL listeners

### npc_manager.py
- **Imports**: `ai_behaviors, memory_system, uuid, json`
- **Exports**: `NPCManager, NPC, NPCState`
- **Used by**: `main, quest_engine, economy, combat`
- **Critical**: NPC structure changes affect save/load

## ⚠️ Circular Dependency Risks

### SAFE Patterns:
```python
# Use events instead of direct calls
event_bus.emit("npc_action", data)  # ✅
npc_manager.do_something()          # ❌ creates coupling
```

### DANGEROUS Patterns:
```python
# These create circular deps:
# combat.py imports npc_manager
# npc_manager imports combat  ❌

# Solution: Use event bus
# Both import event_bus only ✅
```

## 🔄 System Communication Flow

```
User Input → CommandParser → GameEngine
                                ↓
                            EventBus.emit()
                          ↙    ↓    ↘
                    Combat  Economy  NPCs
                          ↘    ↓    ↙
                           GameState
                                ↓
                            UI Update
```

## 📦 Data File Dependencies

### JSON Files → Python Modules:
- ⭐ `data/npc_complete.json` → `npc_manager.py, dialogue_system.py, game_state.py`
- `data/items.json` → `crafting.py, economy.py`
- `data/recipes.json` → `crafting.py`
- `data/locations.json` → `world/locations.py`
- `data/dialogues.json` → `dialogue_system.py`
- `data/ui_texts.json` → `interface.py, commands.py`

### ✅ CONSOLIDATED NPC DATA (2024-08-31):
- **OLD FILES (BACKED UP)**:
  - `npcs.json.backup`
  - `npc_unified.json.backup`
  - `npc_mapping.json.backup`
  - `npc_schedules.json.backup`
- **NEW SINGLE SOURCE**: `npc_complete.json`
  - Contains: NPCs, schedules, mappings, dialogue IDs
  - Used by: NPCManager, DialogueSystem, GameState

### Critical: Change JSON structure = update loaders!

## 🧪 Test Dependencies

### Unit Test Requirements:
- `test_combat.py` → mocks: `game_state, event_bus`
- `test_npcs.py` → mocks: `memory_system, ai_behaviors`
- `test_economy.py` → mocks: `event_bus, npc_manager`

### Integration Test Order:
1. `game_state` (no deps)
2. `event_bus` (no deps)
3. `npcs` (uses above)
4. `combat` (uses all above)
5. `economy` (uses all above)
6. `quests` (uses everything)

## 🔴 High-Risk Changes

### NEVER change without full analysis:
1. **Event structure** - all listeners break
2. **GameState fields** - save/load breaks
3. **NPC.id type** - all references break
4. **Item/Recipe JSON** - game data corrupts

### ALWAYS safe to change:
1. **Internal function logic** (same signature)
2. **Adding new events** (backward compatible)
3. **New JSON fields** (with defaults)
4. **Private methods** (start with _)

## 🚀 Adding New Systems

### Checklist for new module:
- [ ] Update this DEPENDENCY_MAP.md
- [ ] Import only from allowed dependencies
- [ ] Export clear public interface
- [ ] Subscribe to events, don't call directly
- [ ] Add unit tests with mocks
- [ ] Add integration test
- [ ] Document in module docstring

## 📈 Complexity Metrics

### Current State (2024-08-31):
- **Total Modules**: 15
- **Max Dependencies**: 5 (npc_manager)
- **Circular Risks**: 0
- **Event Types**: 12
- **Singleton Objects**: 2 (GameState, EventBus)

### Thresholds:
- Module deps >7 → split module
- Circular deps >0 → refactor immediately
- Event types >50 → categorize events
- File >500 lines → split responsibilities

## 🔧 Refactoring Opportunities

### Technical Debt:
1. [ ] `combat.py` tightly coupled to NPCs
2. [ ] `economy.py` needs abstraction layer
3. [ ] Some events lack type definitions

### Future Improvements:
1. [ ] Add dependency injection container
2. [ ] Create interfaces for major systems
3. [ ] Add event replay for debugging

---

**Last Updated**: 2024-08-31
**Next Review**: When adding new major system
**Maintainer**: Claude + Project Owner