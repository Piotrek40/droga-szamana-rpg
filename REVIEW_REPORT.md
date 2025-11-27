# Przegląd projektowy – brakujące systemy i problemy testów

## Podsumowanie
Przegląd testów automatycznych (`pytest`) ujawnił brak kluczowych modułów rozszerzających walkę i systemy umiejętności oraz niezgodność API w systemie konsekwencji questów. W efekcie 8 z 128 testów kończy się błędami (NameError/TypeError). Poniżej znajdują się szczegóły i rekomendacje.

## Krytyczne braki
- **Brak modułów enhanced combat/skills** – Testy oczekują klas `EnhancedSkillSystem`, `EnhancedCombatSystem` i `CombatManager`, które nie istnieją w kodzie (`mechanics/enhanced_combat.py`, `player/enhanced_skills.py`, `mechanics/combat_integration.py` sugerowane w dokumentacji). W rezultacie testy `test_skill_progression`, `test_combat_with_pain`, `test_combat_techniques`, `test_environmental_combat`, `test_void_walker_abilities`, `test_npc_ai_combat` i `test_combat_integration` zgłaszają `NameError`.【F:tests/test_enhanced_combat.py†L94-L145】【F:docs/enhanced_combat_skills.md†L9-L66】

## Niezgodności API
- **ConsequenceTracker** – Testy integracyjne questów wołają `ConsequenceTracker.add_consequence(quest_id, event_type, data)` i oczekują zwrotu identyfikatora oraz generowania osi czasu. Obecna implementacja akceptuje tylko obiekt `Consequence` i nie zwraca wartości, przez co `test_consequences` kończy się `TypeError`. Wymagane jest dodanie overloadu/metody fabrycznej zgodnej z użyciem w testach oraz rozszerzenie o timeline/karę karmy zgodnie z oczekiwaniami testów.【F:tests/test_quest_system.py†L156-L206】【F:quests/consequences.py†L904-L979】

## Rekomendowane kolejne kroki
1. **Dostarczyć implementacje rozszerzonych systemów** – Zaimplementować lub przywrócić moduły `mechanics/enhanced_combat.py`, `player/enhanced_skills.py` i `mechanics/combat_integration.py` zgodnie z dokumentacją `docs/enhanced_combat_skills.md`, tak aby odpowiadały API używanemu w testach.
2. **Ujednolicić API ConsequenceTracker** – Dodać obsługę konstrukcji konsekwencji na podstawie danych słownikowych (quest_id, typ, struktura `effects`) oraz generowania identyfikatora i timeline, aby dopasować się do wywołań testowych.
3. **Ponownie uruchomić testy** – Po implementacji powyższych elementów zweryfikować zestaw `pytest`, aby upewnić się, że wszystkie 128 przypadków przechodzą.

## Log testów
- `pytest` (8 niepowodzeń na 128 testów) – szczegóły w powyższych sekcjach.【9f2d2b†L1-L63】
