#!/usr/bin/env python3
"""
Skrypt do konsolidacji wszystkich plików NPC w jeden spójny plik.
Łączy dane z npcs.json, npc_unified.json, npc_mapping.json i npc_schedules.json
"""

import json
import os
from typing import Dict, Any

def load_json(filepath: str) -> Dict:
    """Bezpiecznie wczytuje plik JSON"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def merge_npc_data():
    """Merguje wszystkie pliki NPC w jeden"""
    
    # Wczytaj wszystkie pliki
    npcs_data = load_json('data/npcs.json')
    unified_data = load_json('data/npc_unified.json')
    mapping_data = load_json('data/npc_mapping.json')
    schedules_data = load_json('data/npc_schedules.json')
    
    # Struktura docelowa
    complete_data = {
        "version": "1.0",
        "comment": "Kompletne dane NPCów - skonsolidowane z 4 plików",
        "npcs": {},
        "schedule_templates": schedules_data.get("schedule_templates", {}),
        "dialogue_mappings": {}
    }
    
    # Najpierw przetwórz dane z npcs.json (podstawowe dane)
    for npc in npcs_data.get("npcs", []):
        npc_id = npc["id"]
        complete_data["npcs"][npc_id] = {
            "id": npc_id,
            "name": npc.get("name"),
            "display_name": npc.get("name"),  # domyślnie to samo co name
            "role": npc.get("role"),
            "location": npc.get("location"),
            "spawn_location": npc.get("location"),  # domyślnie ta sama lokacja
            "personality": npc.get("personality", []),
            "quirks": npc.get("quirks", []),
            "stats": {
                "health": npc.get("health", 100),
                "max_health": npc.get("max_health", 100),
                "energy": npc.get("energy", 100),
                "max_energy": npc.get("max_energy", 100),
                "strength": npc.get("strength", 50),
                "agility": npc.get("agility", 50),
                "intelligence": npc.get("intelligence", 50)
            },
            "inventory": npc.get("inventory", {}),
            "gold": npc.get("gold", 0),
            "schedule": npc.get("schedule", {}),
            "schedule_template": None,  # będzie uzupełnione
            "schedule_overrides": {},
            "dialogue_tree": npc_id,  # domyślnie ID jako dialogue_tree
            "dialogue_id": npc_id,
            "memories": npc.get("memories", []),
            "relationships": npc.get("relationships", {}),
            "goals": npc.get("goals", []),
            "description": ""  # będzie uzupełnione z mapping
        }
    
    # Dodaj/aktualizuj dane z npc_unified.json
    for npc_id, npc_data in unified_data.get("npcs", {}).items():
        if npc_id not in complete_data["npcs"]:
            # Nowy NPC którego nie było w npcs.json
            complete_data["npcs"][npc_id] = {
                "id": npc_id,
                "name": npc_data.get("name"),
                "display_name": npc_data.get("display_name", npc_data.get("name")),
                "role": npc_data.get("role"),
                "location": npc_data.get("default_location"),
                "spawn_location": npc_data.get("default_location"),
                "personality": npc_data.get("personality", []),
                "quirks": [],
                "stats": npc_data.get("stats", {
                    "health": 100,
                    "max_health": 100,
                    "energy": 100,
                    "max_energy": 100,
                    "strength": 50,
                    "agility": 50,
                    "intelligence": 50
                }),
                "inventory": npc_data.get("inventory", {}),
                "gold": npc_data.get("gold", 0),
                "schedule": {},
                "schedule_template": npc_data.get("schedule_template"),
                "schedule_overrides": npc_data.get("schedule_overrides", {}),
                "dialogue_tree": npc_data.get("dialogue_tree", npc_id),
                "dialogue_id": npc_id,
                "memories": [],
                "relationships": {},
                "goals": [],
                "description": ""
            }
        else:
            # Aktualizuj istniejące dane
            existing = complete_data["npcs"][npc_id]
            if "display_name" in npc_data:
                existing["display_name"] = npc_data["display_name"]
            if "schedule_template" in npc_data:
                existing["schedule_template"] = npc_data["schedule_template"]
            if "schedule_overrides" in npc_data:
                existing["schedule_overrides"] = npc_data["schedule_overrides"]
            if "dialogue_tree" in npc_data:
                existing["dialogue_tree"] = npc_data["dialogue_tree"]
            if "cell" in npc_data:
                existing["cell"] = npc_data["cell"]
    
    # Dodaj dane z npc_mapping.json
    for map_id, map_data in mapping_data.get("npc_mapping", {}).get("mappings", {}).items():
        # Znajdź odpowiadającego NPCa
        npc_found = None
        
        # Szukaj po różnych możliwych ID
        if map_id in complete_data["npcs"]:
            npc_found = map_id
        else:
            # Szukaj po dialogue_id
            dialogue_id = map_data.get("dialogue_id")
            for npc_id, npc in complete_data["npcs"].items():
                if npc.get("dialogue_id") == dialogue_id or npc.get("dialogue_tree") == dialogue_id:
                    npc_found = npc_id
                    break
        
        if npc_found:
            npc = complete_data["npcs"][npc_found]
            if "display_name" in map_data:
                npc["display_name"] = map_data["display_name"]
            if "dialogue_id" in map_data:
                npc["dialogue_id"] = map_data["dialogue_id"]
            if "spawn_location" in map_data:
                npc["spawn_location"] = map_data["spawn_location"]
            if "description" in map_data:
                npc["description"] = map_data["description"]
        
        # Dodaj do dialogue_mappings dla szybkiego dostępu
        complete_data["dialogue_mappings"][map_data.get("dialogue_id", map_id)] = {
            "npc_id": npc_found or map_id,
            "display_name": map_data.get("display_name", ""),
            "description": map_data.get("description", "")
        }
    
    # Przypisz domyślne schedule_template jeśli brak
    for npc_id, npc in complete_data["npcs"].items():
        if not npc.get("schedule_template"):
            if npc.get("role") == "prisoner":
                npc["schedule_template"] = "prisoner_standard"
            elif npc.get("role") == "guard":
                npc["schedule_template"] = "guard_standard"
            elif npc.get("role") == "warden":
                npc["schedule_template"] = "warden_schedule"
    
    # Sortuj NPCów alfabetycznie dla czytelności
    complete_data["npcs"] = dict(sorted(complete_data["npcs"].items()))
    
    return complete_data

def validate_data(data: Dict) -> bool:
    """Waliduje kompletność danych"""
    errors = []
    
    for npc_id, npc in data["npcs"].items():
        if not npc.get("id"):
            errors.append(f"NPC {npc_id}: brak ID")
        if not npc.get("name"):
            errors.append(f"NPC {npc_id}: brak name")
        if not npc.get("role"):
            errors.append(f"NPC {npc_id}: brak role")
        if not npc.get("location") and not npc.get("spawn_location"):
            errors.append(f"NPC {npc_id}: brak location")
    
    if errors:
        print("Znalezione błędy:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

def main():
    """Główna funkcja"""
    print("Konsolidacja plików NPC...")
    
    # Merguj dane
    complete_data = merge_npc_data()
    
    # Walidacja
    if not validate_data(complete_data):
        print("Walidacja nieudana! Sprawdź błędy.")
        return
    
    # Zapisz do nowego pliku
    output_file = 'data/npc_complete.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, ensure_ascii=False, indent=2)
    
    # Statystyki
    print(f"\n✅ Sukces! Skonsolidowano dane do {output_file}")
    print(f"📊 Statystyki:")
    print(f"  - NPCs: {len(complete_data['npcs'])}")
    print(f"  - Schedule templates: {len(complete_data['schedule_templates'])}")
    print(f"  - Dialogue mappings: {len(complete_data['dialogue_mappings'])}")
    
    # Lista NPCów
    print(f"\n📋 Lista NPCów:")
    for npc_id, npc in complete_data["npcs"].items():
        print(f"  - {npc_id}: {npc.get('display_name', npc.get('name'))} ({npc.get('role')})")

if __name__ == "__main__":
    main()