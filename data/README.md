# 📁 Struktura Danych Gry - Droga Szamana RPG

> **Wersja**: 2.0
> **Data**: 2025-11-04
> **Status**: ✅ Produkcja

## 🎯 Przegląd

Dane gry są zorganizowane hierarchicznie w folderach tematycznych, co ułatwia:
- **Modowanie** - gracze mogą łatwo edytować JSON-y
- **Rozwój** - programiści wiedzą gdzie szukać konkretnych danych
- **Organizację** - każdy system ma swoje miejsce
- **Skalowanie** - łatwo dodawać nowe kategorie

## 📊 Struktura Folderów

```
data/
├── 📦 items/                    # PRZEDMIOTY
│   ├── weapons/                 # Broń (5 itemów)
│   │   └── weapons.json
│   ├── tools/                   # Narzędzia (5 itemów)
│   │   └── tools.json
│   ├── consumables/             # Jedzenie/napoje (5 itemów)
│   │   └── consumables.json
│   └── materials/               # Materiały (5 itemów)
│       └── materials.json
│
├── 🌍 world/                    # ŚWIAT GRY
│   ├── locations/               # Lokacje
│   │   └── prison/              # Więzienie (11 lokacji)
│   │       └── locations.json
│   └── world_metadata.json      # Metadata świata
│
├── 👥 npcs/                     # POSTACIE NPC
│   └── prison/                  # NPCe więzienne (10 postaci)
│       └── npcs.json
│
├── ⚙️ systems/                  # SYSTEMY GRY
│   ├── crafting/                # System craftingu
│   │   ├── recipes.json
│   │   └── stations.json
│   ├── combat/                  # System walki
│   │   └── mechanics.json
│   └── economy/                 # System ekonomii
│
├── 💬 dialogue/                 # DIALOGI
│   ├── npcs/                    # Dialogi per NPC
│   └── dialogues.json           # Główne dialogi
│
├── 🎨 ui/                       # INTERFEJS UŻYTKOWNIKA
│   ├── texts.json               # Teksty UI
│   └── commands.json            # Komendy gracza
│
├── 📜 quests/                   # QUESTY
│   └── (w przyszłości)
│
└── 🔧 config/                   # KONFIGURACJA
    └── (w przyszłości)
```

## 💻 Jak Używać - DataLoader

### Podstawowe Użycie

```python
# Import singleton instance
from core.data_loader import data_loader

# Załaduj wszystkie przedmioty
items = data_loader.load_items()
# Wynik: {'chleb': {...}, 'miecz': {...}, ...}

# Załaduj tylko broń
weapons = data_loader.load_items(category='weapons')
# Wynik: {'noz': {...}, 'miecz': {...}, 'luk': {...}, ...}

# Załaduj wszystkie lokacje
locations = data_loader.load_locations()

# Załaduj tylko lokacje więzienne
prison = data_loader.load_locations(region='prison')

# Załaduj NPCs
npcs = data_loader.load_npcs()
prison_npcs = data_loader.load_npcs(group='prison')
```

### Pobieranie Pojedynczych Obiektów

```python
# Pobierz konkretny item
miecz = data_loader.get_item('miecz')
# Wynik: {'nazwa': 'Miecz', 'typ': 'bron', ...}

# Pobierz konkretną lokację
cela = data_loader.get_location('cela_1')

# Pobierz konkretnego NPCa
piotr = data_loader.get_npc('gadatliwy_piotr')
```

### Zaawansowane

```python
# Załaduj konfigurację systemu
recipes = data_loader.load_system_config('crafting', 'recipes')
combat_mechanics = data_loader.load_system_config('combat', 'mechanics')

# Załaduj teksty UI
ui_texts = data_loader.load_ui_texts()

# Załaduj dialogi
dialogues = data_loader.load_dialogues()

# Wyczyść cache (np. po hot-reload)
data_loader.clear_cache()
```

## 📝 Format Danych

### Items (Przedmioty)

```json
{
  "item_id": {
    "nazwa": "Nazwa przedmiotu",
    "typ": "bron|narzedzie|jedzenie|material",
    "opis": "Opis przedmiotu",
    "waga": 2.5,
    "bazowa_wartosc": 100,
    "trwalosc": 200,
    "kategoria": "kategoria_szczegółowa",
    "efekty": {
      "obrazenia": 20,
      "bonus_blok": 2
    }
  }
}
```

**Kategorie itemów:**
- `weapons` - broń (typ: "bron")
- `tools` - narzędzia (typ: "narzedzie")
- `consumables` - jedzenie/napoje (typ: "jedzenie")
- `materials` - surowce (typ: "material")

### Locations (Lokacje)

```json
{
  "locations": {
    "location_id": {
      "name": "Krótka nazwa",
      "full_name": "Pełna nazwa lokacji",
      "type": "cell|corridor|room",
      "descriptions": {
        "day": "Opis w dzień",
        "night": "Opis w nocy"
      },
      "interactive_objects": ["obiekt1", "obiekt2"],
      "connections": {
        "wschód": "inna_lokacja"
      },
      "secrets": [...],
      "starting_items": ["item1", "item2"],
      "spawn_npcs": ["npc1"]
    }
  }
}
```

### NPCs (Postacie)

```json
{
  "npcs": {
    "npc_id": {
      "id": "npc_id",
      "name": "Imię NPC",
      "role": "prisoner|guard|merchant",
      "personality": {
        "friendly": 0.8,
        "talkative": 0.9
      },
      "quirks": ["cecha1", "cecha2"],
      "inventory": {...},
      "schedule": {...}
    }
  }
}
```

## 🔄 Kompatybilność Wsteczna

DataLoader wspiera **zarówno starą jak i nową strukturę**:

✅ **Stare pliki** (flat structure):
- `data/items.json` - nadal działa
- `data/locations.json` - nadal działa
- `data/npc_complete.json` - nadal działa

✅ **Nowe pliki** (hierarchical structure):
- `data/items/weapons/weapons.json` - preferowane
- `data/world/locations/prison/locations.json` - preferowane
- `data/npcs/prison/npcs.json` - preferowane

**DataLoader automatycznie wybiera nową strukturę jeśli istnieje, z fallbackiem na starą.**

## 📖 Przewodnik dla Modderów

### Jak dodać nowy przedmiot?

1. Otwórz odpowiedni plik w `data/items/[kategoria]/`
2. Dodaj nowy wpis:

```json
{
  "twoj_item_id": {
    "nazwa": "Twój Item",
    "typ": "bron",
    "opis": "Opis",
    "waga": 1.0,
    "bazowa_wartosc": 50,
    "trwalosc": 100,
    "kategoria": "broń_biała",
    "efekty": {
      "obrazenia": 15
    }
  }
}
```

3. Zapisz plik
4. Restart gry lub hot-reload

### Jak dodać nową lokację?

1. Otwórz `data/world/locations/prison/locations.json`
2. Dodaj nową lokację:

```json
{
  "locations": {
    "twoja_lokacja": {
      "name": "Nazwa",
      "full_name": "Pełna nazwa",
      "type": "room",
      "descriptions": {
        "day": "Opis dzienny",
        "night": "Opis nocny"
      },
      "connections": {
        "północ": "inna_lokacja"
      }
    }
  }
}
```

### Jak dodać nowego NPCa?

1. Otwórz `data/npcs/prison/npcs.json`
2. Dodaj nowego NPCa w sekcji `"npcs":`
3. Restart gry

## 🛠️ Dla Programistów

### Dodawanie nowych kategorii

Aby dodać nową kategorię przedmiotów (np. "armor"):

1. Utwórz folder: `data/items/armor/`
2. Utwórz plik: `data/items/armor/armor.json`
3. Aktualizuj `core/data_loader.py`:
   - Dodaj "armor" do listy kategorii w `load_items()`
   - Dodaj logikę rozpoznawania w `_matches_category()`

### Cache Management

DataLoader cachuje załadowane dane dla performance:

```python
# Cache jest automatycznie używany
items1 = data_loader.load_items()  # Ładuje z dysku
items2 = data_loader.load_items()  # Zwraca z cache (items1 is items2 == True)

# Wymuś przeładowanie
items3 = data_loader.load_items(use_cache=False)  # Zawsze z dysku

# Wyczyść cały cache
data_loader.clear_cache()
```

### Logging

DataLoader loguje wszystkie operacje:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Zobaczysz logi typu:
# INFO: Załadowano 20 przedmiotów (kategoria: all)
# DEBUG: Załadowano: /path/to/items/weapons/weapons.json
```

## ✅ Checklist Migracji

Jeśli migrujesz z starej struktury:

- [x] Utworzono nową strukturę folderów
- [x] Podzielono items.json na kategorie
- [x] Przeniesiono locations.json
- [x] Przeniesiono npc_complete.json
- [x] Utworzono DataLoader
- [ ] Zaktualizowano kod używający starych ścieżek
- [ ] Przetestowano wszystkie systemy
- [ ] Usunięto stare pliki (opcjonalnie)

## 📚 Dodatkowe Zasoby

- **DataLoader kod**: `core/data_loader.py`
- **Skrypt migracji**: `reorganize_data.py`
- **Backup starej struktury**: `data_backup/`
- **Testy**: `tests/test_data_loader.py` (TODO)

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'core'"

Upewnij się że uruchamiasz kod z głównego folderu projektu:
```bash
cd /path/to/droga-szamana-rpg
python your_script.py
```

### "FileNotFoundError" przy ładowaniu danych

1. Sprawdź czy folder `data/` istnieje
2. Sprawdź czy używasz poprawnych nazw kategorii/regionów
3. Włącz debug logging: `logging.basicConfig(level=logging.DEBUG)`

### Cache nie odświeża się

```python
# Wymuś reload bez cache
data_loader.load_items(use_cache=False)

# Lub wyczyść cały cache
data_loader.clear_cache()
```

## 📞 Kontakt

Masz pytania? Znalazłeś bug?
- GitHub Issues: [link do repo]
- Discord: [link do serwera]

---

**Wersja dokumentu**: 2.0
**Ostatnia aktualizacja**: 2025-11-04
**Status**: ✅ Aktywne
