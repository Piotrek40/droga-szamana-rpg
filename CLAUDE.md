# 🛡️ CLAUDE.md - Droga Szamana RPG Integration Safety Protocol

> **CRITICAL**: Ten dokument WYMUSZA sprawdzanie integracji przed KAŻDĄ zmianą kodu.
> **Cel: ZERO błędów integracji, 100% stabilności systemu**

## 🚨 PROTOKÓŁ BEZPIECZEŃSTWA - WYKONAJ PRZED KAŻDĄ ZMIANĄ

### ✅ PRE-MODIFICATION CHECKLIST
```bash
# [ ] 1. Sprawdź zależności funkcji/klasy którą modyfikujesz:
grep -r "nazwa_funkcji" --include="*.py" .

# [ ] 2. Zweryfikuj circular imports:
python -c "from core import *; from npcs import *; from mechanics import *; print('✓')"

# [ ] 3. Sprawdź event subscribers jeśli zmieniasz eventy:
grep -r "event_bus.subscribe" --include="*.py" . | grep "EVENT_NAME"

# [ ] 4. Test integracji PRZED zmianami:
python tests/test_all.py

# [ ] 5. Sprawdź save compatibility jeśli zmieniasz struktury danych:
python -c "from persistence.save_manager import SaveManager; SaveManager.verify_compatibility()"
```

## 🏗️ ARCHITEKTURA KRYTYCZNA

### System Layers (NIE NARUSZAJ HIERARCHII!)
```
┌─────────────────────────────────────┐
│         UI Layer (ui/)              │ ← Może importować wszystko
├─────────────────────────────────────┤
│     Game Logic (quests/, world/)    │ ← Może importować core + mechanics
├─────────────────────────────────────┤
│    Mechanics (mechanics/, npcs/)    │ ← Może importować tylko core
├─────────────────────────────────────┤
│      Core (core/, player/)          │ ← NIE MOŻE importować nic powyżej!
└─────────────────────────────────────┘
```

### 🔴 SINGLETON PATTERN - KRYTYCZNE!
```python
# ❌ NIGDY TAK:
from core.game_state import GameState
game_state = GameState()  # BŁĄD! Tworzy nową instancję!

# ✅ ZAWSZE TAK:
from core.game_state import game_state  # Import gotowej instancji singleton
```

## 📊 MAPA ZALEŻNOŚCI SYSTEMÓW

### Critical Dependency Chains
```
USER INPUT
    ↓
ui.commands.CommandParser.parse()
    ↓
core.game_state.GameState.process_command()
    ↓
EVENT_BUS.emit(event_type, data)
    ↓
┌──────────────────────────────────┐
│ PARALLEL EVENT HANDLERS:         │
├→ npcs.NPCManager.handle_event()  │
├→ quests.QuestEngine.on_event()   │
├→ mechanics.Economy.update()      │
├→ persistence.SaveManager.mark()  │
└──────────────────────────────────┘
    ↓
core.game_state.GameState.update()
    ↓
ui.interface.display_output()
```

### 🔄 Update Order (KOLEJNOŚĆ KRYTYCZNA!)
```python
# main.py - NIGDY nie zmieniaj kolejności!
def game_loop():
    1. time_system.update()      # Musi być pierwsze (czas dla wszystkich)
    2. weather.update()           # Zależy od czasu
    3. npc_manager.update()       # NPCe działają w świecie
    4. quest_engine.update()      # Questy reagują na NPCe
    5. economy.update()           # Ekonomia po questach
    6. player.update()            # Gracz na końcu
```

## ⚠️ PUNKTY KRYTYCZNE - HIGHEST RISK

### 1. 🔴 NPC Data Files (LEGACY PROBLEM!)
```python
# PROBLEM: 3 różne pliki NPC, tylko jeden aktywny
ACTIVE:     data/npc_complete.json  ✅ UŻYWAJ TEGO
DEPRECATED: data/npcs.json          ❌ NIE UŻYWAJ
DEPRECATED: data/archive/*          ❌ NIE UŻYWAJ

# PRZED zmianą NPC sprawdź:
grep -r "npcs.json" --include="*.py" .  # Powinno być 0 wyników!
```

### 2. 🔴 Event Bus Error Propagation
```python
# PROBLEM: Jeden błąd w handlerze przerywa cały łańcuch
# ZAWSZE wrap event handlers w try/except:

@event_bus.subscribe(EventType.QUEST_COMPLETE)
def handle_quest(data):
    try:
        # twój kod
    except Exception as e:
        logger.error(f"Quest handler failed: {e}")
        # NIE propaguj błędu dalej!
```

### 3. 🔴 Circular Import Zones
```python
# ZAGROŻONE OBSZARY:
mechanics/economy.py ←→ mechanics/crafting.py ←→ mechanics/merchant_ai.py

# ZASADA: Używaj importów w funkcjach, nie na górze pliku:
def calculate_price():
    from mechanics.crafting import get_recipe_cost  # Import lokalny
```

## 🎯 ŁAŃCUCHY ZALEŻNOŚCI (Modification Chains)

### Quest Complete Chain
```bash
# JEŚLI modyfikujesz complete_quest(), MUSISZ sprawdzić:
1. quests/quest_engine.py → complete_quest()
   ↓ emits EVENT_QUEST_COMPLETE
2. npcs/npc_manager.py → on_quest_complete() 
   ↓ updates NPC memories
3. player/character.py → add_experience()
   ↓ may trigger level_up
4. ui/interface.py → show_notification()
   ↓ displays to user
5. persistence/save_manager.py → mark_dirty()
   ↓ schedules autosave

# TEST: python tests/test_quest_system.py
```

### Combat Death Chain  
```bash
# JEŚLI modyfikujesz handle_death(), MUSISZ sprawdzić:
1. mechanics/combat.py → handle_death()
   ↓ emits EVENT_ENTITY_DEATH
2. quests/quest_engine.py → on_entity_death()
   ↓ may complete/fail quests
3. npcs/memory_system.py → remember_death()
   ↓ NPCs remember who died
4. world/locations/location.py → remove_entity()
   ↓ removes from location
5. persistence/save_manager.py → save_death_state()
   ↓ permanent consequences

# TEST: python tests/test_combat_demo.py
```

### Save/Load Chain
```bash
# JEŚLI modyfikujesz struktury danych, MUSISZ:
1. Zaktualizować save_manager.py → SAVE_VERSION
2. Dodać migrację w save_manager.py → migrate_save()
3. Zaktualizować tests/test_save_compatibility.py
4. Sprawdzić wszystkie miejsca serializacji:
   grep -r "to_dict\|from_dict" --include="*.py" .
```

## 🚫 ZAKAZY ABSOLUTNE (NEVER MODIFY!)

### Protected Files
```python
# NIE MODYFIKUJ bez konsultacji z całym zespołem:
core/event_bus.py         # Fundament komunikacji
core/game_state.py        # Singleton pattern krytyczny
data/npc_complete.json    # Tylko przez NPC expert agents
persistence/save_format.py # Kompatybilność wsteczna
```

### Protected Functions (NIE ZMIENIAJ SYGNATUR!)
```python
GameState.__init__()      # Singleton pattern
EventBus.emit()          # Cały system na tym polega
EventBus.subscribe()     # j.w.
SaveManager.save_game()  # Format musi być stały
SaveManager.load_game()  # j.w.
Player.to_dict()        # Serializacja krytyczna
NPC.to_dict()           # j.w.
```

### Protected Data Structures
```python
# Format MUSI pozostać kompatybilny:
EVENT_CATEGORIES = [...]  # Dodawaj, nie usuwaj!
ITEM_TYPES = [...]        # j.w.
SKILL_LIST = [...]        # j.w.
```

## 🧪 TESTY DYMU (Smoke Tests) - PO KAŻDEJ ZMIANIE

### Quick Integration Test
```bash
# Uruchom po KAŻDEJ zmianie (30 sekund):
python -c "
from main import GameEngine
engine = GameEngine()
engine.initialize()
print('✓ Init OK')

# Test podstawowych komend
engine.process_command('look')
print('✓ Look OK')
engine.process_command('inventory')
print('✓ Inventory OK')
engine.process_command('status')
print('✓ Status OK')

# Test save/load
from persistence.save_manager import SaveManager
SaveManager.save_game(engine.game_state, 'test_slot')
print('✓ Save OK')
SaveManager.load_game('test_slot')
print('✓ Load OK')

print('🟢 SMOKE TEST PASSED!')
"
```

### System-Specific Tests
```bash
# Po zmianie QUESTÓW:
python tests/test_quest_system.py -k test_quest_completion

# Po zmianie WALKI:
python tests/test_combat_demo.py

# Po zmianie NPCów:
python tests/test_npc_ai.py

# Po zmianie EKONOMII:
python tests/test_enhanced_economy.py
```

## 🐛 CZĘSTE PUŁAPKI I ROZWIĄZANIA

### Problem 1: "NPC nie reaguje na event"
```python
# DIAGNOSIS:
grep "subscribe.*EVENT_NAME" npcs/*.py

# FIX: Sprawdź czy handler jest zarejestrowany:
@event_bus.subscribe(EventType.YOUR_EVENT)  # Dekorator!
def handler(data):
    ...
```

### Problem 2: "Circular import error"
```python
# DIAGNOSIS:
python -c "import sys; sys.path.insert(0, '.'); from module import *"

# FIX: Przenieś import do wnętrza funkcji:
def my_function():
    from other_module import something  # Import lokalny
```

### Problem 3: "Save nie wczytuje się"
```python
# DIAGNOSIS:
python -c "
from persistence.save_manager import SaveManager
save = SaveManager.load_raw('slot_1')
print(save.get('version', 'NO VERSION'))
"

# FIX: Dodaj migrację dla nowej wersji w save_manager.py
```

### Problem 4: "GameState ma dziwny stan"
```python
# DIAGNOSIS - sprawdź czy nie tworzysz nowej instancji:
grep -r "GameState()" --include="*.py" .  # Powinno być 0!

# FIX: Używaj singleton import:
from core.game_state import game_state  # NIE GameState!
```

## 📋 METRYKI JAKOŚCI (Monitor Daily)

### Code Health Indicators
```bash
# Circular dependencies (should be 0):
python -m pycycle . 2>/dev/null | wc -l

# TODO/FIXME count (should decrease):
grep -r "TODO\|FIXME" --include="*.py" . | wc -l

# Test coverage (should be >80%):
pytest --cov=. --cov-report=term | tail -1

# Function complexity (no function >10):
python -m mccabe --min 10 **/*.py

# Duplicate code (should be minimal):
python -m pylint --disable=all --enable=duplicate-code **/*.py
```

## 🚀 DEPLOYMENT CHECKLIST

### Before Pushing to GitHub:
```bash
# [ ] All smoke tests pass
# [ ] No new circular dependencies  
# [ ] Save/load compatibility verified
# [ ] Event chains tested end-to-end
# [ ] No hardcoded absolute paths
# [ ] No debug print() statements
# [ ] No exposed credentials/tokens
# [ ] README.md updated if needed
# [ ] Version bumped if breaking changes
```

## 💡 GOLDEN RULES

1. **"Każda zmiana w event emisji wymaga sprawdzenia WSZYSTKICH subscriberów"**
2. **"Nigdy nie modyfikuj GameState bez sprawdzenia całego update chain"**
3. **"Zmiany w NPC wymagają sprawdzenia questów i ekonomii"**
4. **"Modyfikacja save format = migration required"**
5. **"W razie wątpliwości - uruchom test_all.py"**

## 🆘 EMERGENCY PROCEDURES

### System Not Starting:
```bash
# 1. Check for syntax errors:
python -m py_compile **/*.py

# 2. Check imports:
python -c "from main import *"

# 3. Reset to last known good:
git stash && git checkout main
```

### Broken Save Files:
```bash
# Force migration:
python -c "
from persistence.save_manager import SaveManager
SaveManager.force_migrate_all_saves()
"
```

### Event System Frozen:
```bash
# Clear event queue:
python -c "
from core.event_bus import event_bus
event_bus.clear_all_handlers()
event_bus.reset()
"
```

---

## 📌 REMEMBER

> **"Holistyczne myślenie przed lokalną zmianą"**
> 
> Każda linia kodu jest częścią większego systemu.
> Jedna nieuważna zmiana może zepsuć 10 innych miejsc.
> 
> **ZAWSZE sprawdzaj integrację. BEZ WYJĄTKÓW.**

**Last Updated**: 2025-09-01
**Version**: 2.0 - Full Integration Safety Protocol
**Maintainer**: Claude AI Assistant
**Project**: Droga Szamana RPG

🟢 **SYSTEM READY** - Follow this protocol for ZERO integration errors!