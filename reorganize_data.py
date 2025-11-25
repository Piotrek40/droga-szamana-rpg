#!/usr/bin/env python3
"""
Skrypt do reorganizacji struktury danych gry.
Dzieli items.json na kategorie i reorganizuje pliki.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

def load_json(filepath: str) -> Dict:
    """Wczytuje JSON z pliku"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath: str, data: Dict, indent: 2):
    """Zapisuje JSON do pliku z ładnym formatowaniem"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    print(f"✅ Zapisano: {filepath}")

def split_items(items_data: Dict) -> Dict[str, Dict]:
    """Dzieli items.json na kategorie"""
    categories = {
        'weapons': {},      # Broń
        'tools': {},        # Narzędzia
        'consumables': {},  # Jedzenie i napoje
        'materials': {}     # Materiały do craftingu
    }

    for item_id, item_data in items_data.items():
        item_type = item_data.get('typ', 'unknown')
        category = item_data.get('kategoria', '')

        if item_type == 'bron':
            categories['weapons'][item_id] = item_data
        elif item_type == 'narzedzie':
            categories['tools'][item_id] = item_data
        elif item_type == 'jedzenie':
            categories['consumables'][item_id] = item_data
        elif item_type == 'material':
            categories['materials'][item_id] = item_data
        else:
            # Fallback na kategorię
            if 'broń' in category:
                categories['weapons'][item_id] = item_data
            elif 'narzędzie' in category:
                categories['tools'][item_id] = item_data
            elif any(x in category for x in ['żywność', 'napój', 'owoc']):
                categories['consumables'][item_id] = item_data
            elif 'surowiec' in category:
                categories['materials'][item_id] = item_data
            else:
                # Default: materials
                categories['materials'][item_id] = item_data

    return categories

def split_locations(locations_data: Dict) -> Dict[str, Dict]:
    """Dzieli lokacje według typu"""
    prison_locations = {}

    for loc_id, loc_data in locations_data.get('locations', {}).items():
        loc_type = loc_data.get('type', 'unknown')

        # Na razie wszystko to więzienie
        if any(word in loc_id for word in ['cela', 'korytarz', 'zbrojownia', 'dziedziniec', 'kuchnia', 'biuro']):
            prison_locations[loc_id] = loc_data
        else:
            prison_locations[loc_id] = loc_data  # Domyślnie wszystko do więzienia

    return {'prison': prison_locations}

def split_npcs(npcs_data: Dict) -> Dict[str, Dict]:
    """Dzieli NPCs według typu"""
    prison_npcs = {}

    for npc_id, npc_data in npcs_data.get('npcs', {}).items():
        role = npc_data.get('role', 'unknown')

        # Na razie wszystko to więźniowie/strażnicy
        prison_npcs[npc_id] = npc_data

    return {'prison': prison_npcs}

def reorganize_data():
    """Główna funkcja reorganizująca dane"""
    base_path = Path('/home/user/droga-szamana-rpg/data')

    print("🚀 Rozpoczynam reorganizację danych...")
    print()

    # 1. Podziel items.json
    print("📦 Dzielenie items.json...")
    items = load_json(base_path / 'items.json')
    item_categories = split_items(items)

    for category, items_data in item_categories.items():
        if items_data:  # Tylko jeśli są jakieś itemy
            filepath = base_path / 'items' / category / f'{category}.json'
            save_json(str(filepath), items_data, indent=2)
            print(f"   ├─ {category}: {len(items_data)} itemów")

    print()

    # 2. Podziel locations.json
    print("🌍 Dzielenie locations.json...")
    locations = load_json(base_path / 'locations.json')
    location_regions = split_locations(locations)

    for region, locations_data in location_regions.items():
        if locations_data:
            filepath = base_path / 'world' / 'locations' / region / 'locations.json'
            wrapped_data = {'locations': locations_data}
            save_json(str(filepath), wrapped_data, indent=2)
            print(f"   ├─ {region}: {len(locations_data)} lokacji")

    print()

    # 3. Podziel NPCs
    print("👥 Dzielenie npc_complete.json...")
    npcs = load_json(base_path / 'npc_complete.json')
    npc_groups = split_npcs(npcs)

    for group, npcs_data in npc_groups.items():
        if npcs_data:
            filepath = base_path / 'npcs' / group / 'npcs.json'
            wrapped_data = {
                'version': npcs.get('version', '1.0'),
                'comment': f'NPCs z grupy: {group}',
                'npcs': npcs_data
            }
            save_json(str(filepath), wrapped_data, indent=2)
            print(f"   ├─ {group}: {len(npcs_data)} NPCów")

    print()

    # 4. Przenieś inne pliki do odpowiednich folderów
    print("📁 Przenoszenie pozostałych plików...")

    moves = [
        ('recipes.json', 'systems/crafting/recipes.json'),
        ('crafting_stations.json', 'systems/crafting/stations.json'),
        ('combat_mechanics.json', 'systems/combat/mechanics.json'),
        ('dialogues.json', 'dialogue/dialogues.json'),
        ('ui_texts.json', 'ui/texts.json'),
        ('commands.json', 'ui/commands.json'),
        ('world_data.json', 'world/world_metadata.json'),
    ]

    for src, dst in moves:
        src_path = base_path / src
        dst_path = base_path / dst

        if src_path.exists():
            data = load_json(str(src_path))
            save_json(str(dst_path), data, indent=2)
            print(f"   ├─ {src} → {dst}")

    print()
    print("✅ Reorganizacja zakończona!")
    print()
    print("📊 Nowa struktura:")
    print("   data/")
    print("   ├── items/")
    print("   │   ├── weapons/")
    print("   │   ├── tools/")
    print("   │   ├── consumables/")
    print("   │   └── materials/")
    print("   ├── world/")
    print("   │   └── locations/prison/")
    print("   ├── npcs/prison/")
    print("   ├── systems/")
    print("   │   ├── crafting/")
    print("   │   └── combat/")
    print("   ├── dialogue/")
    print("   └── ui/")

if __name__ == '__main__':
    reorganize_data()
