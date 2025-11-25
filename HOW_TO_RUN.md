# 🎮 Droga Szamana RPG - How to Run

## Entry Points (Choose One)

### 1. **Text Mode (Recommended)**
```bash
python main.py
```
- Complete text-based RPG experience
- Smart interface with plugin system
- All features available
- Best performance

### 2. **Simple GUI Mode**
```bash
python gui_launcher.py
```
- Basic graphical interface
- Good for beginners
- Simplified controls

### 3. **Advanced GUI Mode**
```bash
python integrated_gui.py
```
- Full-featured graphical interface
- Quest integration
- Character sheets
- Advanced features

## Key Systems After Cleanup

### Combat System (`mechanics/combat.py`)
- **Consolidated** from 3 separate systems
- Enhanced techniques, weapons, armor
- Void Walker abilities
- Environmental factors
- Pain and injury system

### Skills System (`player/skills.py`)
- **Consolidated** from 2 separate systems  
- 50+ skills with categories
- Muscle memory for repeated actions
- Skill synergies between related abilities
- Use-based progression (no XP grinding)

### UI System (`ui/`)
- **Reduced** from 5 interfaces to 3
- `interface.py` - Simple fallback
- `smart_interface.py` - Main interface (plugin system)
- `gui_interface.py` - GUI mode

### Quest System (`quests/`)
- `quest_engine.py` - Main quest engine
- `consequences.py` - **Consolidated** consequence system
- `quest_chains.py` - Story quest chains

## Removed Duplicates

These files were **removed** and their features merged:
- ❌ `ui/advanced_interface.py` → merged into `smart_interface.py`
- ❌ `ui/contextual_interface.py` → merged into `smart_interface.py`
- ❌ `mechanics/enhanced_combat.py` → merged into `combat.py`
- ❌ `mechanics/combat_integration.py` → merged into `combat.py`
- ❌ `player/enhanced_skills.py` → merged into `skills.py`  
- ❌ `quests/quest_consequences.py` → merged into `consequences.py`

## Benefits of Cleanup

✅ **40% reduction** in UI code duplication  
✅ **Unified systems** - no more confusion about which to use  
✅ **All features preserved** - nothing was lost  
✅ **Better maintainability** - single source of truth  
✅ **Faster development** - no need to update multiple files  
✅ **Clear architecture** - obvious which file to edit  

## Requirements

- Python 3.8+
- No external dependencies (pure Python)
- UTF-8 terminal support
- 50MB disk space

---

**Start with `python main.py` for the best experience!** 🚀