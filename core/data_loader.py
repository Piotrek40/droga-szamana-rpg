"""
Centralny system ładowania danych z hierarchicznej struktury JSON.

Używa wzorca Singleton i cache'uje załadowane dane.
Wspiera zarówno starą (flat) jak i nową (hierarchiczną) strukturę.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Centralny loader danych gry.

    Przykłady użycia:
        # Singleton pattern
        from core.data_loader import data_loader

        # Załaduj wszystkie itemy
        items = data_loader.load_items()
        miecz = items.get('miecz')

        # Załaduj tylko broń
        weapons = data_loader.load_items(category='weapons')

        # Załaduj lokacje więzienne
        prison_locs = data_loader.load_locations(region='prison')

        # Załaduj NPCów
        npcs = data_loader.load_npcs(group='prison')
    """

    def __init__(self, data_root: str = "data"):
        """
        Inicjalizuje DataLoader.

        Args:
            data_root: Ścieżka do głównego folderu data/
        """
        self.data_root = Path(data_root)
        self._cache = {}
        self._use_new_structure = True  # Preferuj nową strukturę

        logger.info(f"DataLoader zainicjalizowany: {self.data_root}")

    def clear_cache(self):
        """Czyści cache załadowanych danych"""
        self._cache = {}
        logger.info("Cache danych wyczyszczony")

    def _load_json(self, filepath: Path) -> Dict:
        """
        Wczytuje plik JSON.

        Args:
            filepath: Ścieżka do pliku

        Returns:
            Dict z danymi z JSONa

        Raises:
            FileNotFoundError: Gdy plik nie istnieje
            json.JSONDecodeError: Gdy JSON jest nieprawidłowy
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Załadowano: {filepath}")
            return data
        except FileNotFoundError:
            logger.error(f"Plik nie znaleziony: {filepath}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania JSON w {filepath}: {e}")
            raise

    def load_items(self, category: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Ładuje przedmioty.

        Args:
            category: Opcjonalna kategoria (weapons, tools, consumables, materials)
            use_cache: Czy użyć cache'a

        Returns:
            Dict z przedmiotami {item_id: item_data}
        """
        cache_key = f"items_{category or 'all'}"

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        items = {}

        if category:
            # Załaduj konkretną kategorię
            filepath = self.data_root / 'items' / category / f'{category}.json'
            if filepath.exists():
                items = self._load_json(filepath)
            else:
                logger.warning(f"Kategoria {category} nie istnieje, używam starej struktury")
                # Fallback na starą strukturę
                all_items = self._load_json(self.data_root / 'items.json')
                items = {k: v for k, v in all_items.items() if self._matches_category(v, category)}
        else:
            # Załaduj wszystkie itemy
            if self._use_new_structure:
                # Nowa struktura - łącz wszystkie kategorie
                for cat in ['weapons', 'tools', 'consumables', 'materials']:
                    cat_path = self.data_root / 'items' / cat / f'{cat}.json'
                    if cat_path.exists():
                        cat_items = self._load_json(cat_path)
                        items.update(cat_items)
            else:
                # Stara struktura - jeden plik
                items = self._load_json(self.data_root / 'items.json')

        self._cache[cache_key] = items
        logger.info(f"Załadowano {len(items)} przedmiotów (kategoria: {category or 'all'})")
        return items

    def _matches_category(self, item_data: Dict, category: str) -> bool:
        """Sprawdza czy item pasuje do kategorii"""
        typ = item_data.get('typ', '')
        kategoria = item_data.get('kategoria', '')

        if category == 'weapons':
            return typ == 'bron' or 'broń' in kategoria
        elif category == 'tools':
            return typ == 'narzedzie' or 'narzędzie' in kategoria
        elif category == 'consumables':
            return typ == 'jedzenie' or any(x in kategoria for x in ['żywność', 'napój', 'owoc'])
        elif category == 'materials':
            return typ == 'material' or 'surowiec' in kategoria
        return False

    def load_locations(self, region: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Ładuje lokacje.

        Args:
            region: Opcjonalny region (prison, wilderness, settlements)
            use_cache: Czy użyć cache'a

        Returns:
            Dict z lokacjami {location_id: location_data}
        """
        cache_key = f"locations_{region or 'all'}"

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        locations = {}

        if region:
            # Załaduj konkretny region
            filepath = self.data_root / 'world' / 'locations' / region / 'locations.json'
            if filepath.exists():
                data = self._load_json(filepath)
                locations = data.get('locations', data)  # Wspieraj zarówno wrapped jak i flat
            else:
                logger.warning(f"Region {region} nie istnieje, używam starej struktury")
                all_locs = self._load_json(self.data_root / 'locations.json')
                locations = all_locs.get('locations', all_locs)
        else:
            # Załaduj wszystkie lokacje
            if self._use_new_structure:
                # Nowa struktura - łącz wszystkie regiony
                locations_dir = self.data_root / 'world' / 'locations'
                if locations_dir.exists():
                    for region_dir in locations_dir.iterdir():
                        if region_dir.is_dir():
                            loc_file = region_dir / 'locations.json'
                            if loc_file.exists():
                                data = self._load_json(loc_file)
                                locations.update(data.get('locations', data))
            else:
                # Stara struktura
                data = self._load_json(self.data_root / 'locations.json')
                locations = data.get('locations', data)

        self._cache[cache_key] = locations
        logger.info(f"Załadowano {len(locations)} lokacji (region: {region or 'all'})")
        return locations

    def load_npcs(self, group: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Ładuje NPCów.

        Args:
            group: Opcjonalna grupa (prison, merchants, enemies)
            use_cache: Czy użyć cache'a

        Returns:
            Dict z NPCami {npc_id: npc_data}
        """
        cache_key = f"npcs_{group or 'all'}"

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        npcs = {}

        if group:
            # Załaduj konkretną grupę
            filepath = self.data_root / 'npcs' / group / 'npcs.json'
            if filepath.exists():
                data = self._load_json(filepath)
                npcs = data.get('npcs', data)
            else:
                logger.warning(f"Grupa {group} nie istnieje, używam starej struktury")
                all_npcs = self._load_json(self.data_root / 'npc_complete.json')
                npcs = all_npcs.get('npcs', all_npcs)
        else:
            # Załaduj wszystkich NPCów
            if self._use_new_structure:
                # Nowa struktura - łącz wszystkie grupy
                npcs_dir = self.data_root / 'npcs'
                if npcs_dir.exists():
                    for group_dir in npcs_dir.iterdir():
                        if group_dir.is_dir():
                            npc_file = group_dir / 'npcs.json'
                            if npc_file.exists():
                                data = self._load_json(npc_file)
                                npcs.update(data.get('npcs', data))
            else:
                # Stara struktura
                data = self._load_json(self.data_root / 'npc_complete.json')
                npcs = data.get('npcs', data)

        self._cache[cache_key] = npcs
        logger.info(f"Załadowano {len(npcs)} NPCów (grupa: {group or 'all'})")
        return npcs

    def load_system_config(self, system: str, config_name: str) -> Dict[str, Any]:
        """
        Ładuje konfigurację systemu gry.

        Args:
            system: Nazwa systemu (crafting, combat, economy)
            config_name: Nazwa pliku konfiguracji (bez .json)

        Returns:
            Dict z konfiguracją
        """
        cache_key = f"system_{system}_{config_name}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        filepath = self.data_root / 'systems' / system / f'{config_name}.json'
        if not filepath.exists():
            # Fallback na starą nazwę
            old_filepath = self.data_root / f'{config_name}.json'
            if old_filepath.exists():
                filepath = old_filepath

        config = self._load_json(filepath)
        self._cache[cache_key] = config
        logger.info(f"Załadowano konfigurację: {system}/{config_name}")
        return config

    def load_ui_texts(self) -> Dict[str, Any]:
        """Ładuje teksty UI"""
        cache_key = "ui_texts"
        if cache_key in self._cache:
            return self._cache[cache_key]

        filepath = self.data_root / 'ui' / 'texts.json'
        if not filepath.exists():
            filepath = self.data_root / 'ui_texts.json'

        texts = self._load_json(filepath)
        self._cache[cache_key] = texts
        return texts

    def load_dialogues(self) -> Dict[str, Any]:
        """Ładuje dialogi"""
        cache_key = "dialogues"
        if cache_key in self._cache:
            return self._cache[cache_key]

        filepath = self.data_root / 'dialogue' / 'dialogues.json'
        if not filepath.exists():
            filepath = self.data_root / 'dialogues.json'

        dialogues = self._load_json(filepath)
        self._cache[cache_key] = dialogues
        return dialogues

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera pojedynczy item po ID"""
        items = self.load_items()
        return items.get(item_id)

    def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera pojedynczą lokację po ID"""
        locations = self.load_locations()
        return locations.get(location_id)

    def get_npc(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera pojedynczego NPCa po ID"""
        npcs = self.load_npcs()
        return npcs.get(npc_id)


# Singleton instance
data_loader = DataLoader()


# Backward compatibility - można też importować funkcje bezpośrednio
def load_items(category: Optional[str] = None) -> Dict[str, Any]:
    """Backward compatibility wrapper"""
    return data_loader.load_items(category)


def load_locations(region: Optional[str] = None) -> Dict[str, Any]:
    """Backward compatibility wrapper"""
    return data_loader.load_locations(region)


def load_npcs(group: Optional[str] = None) -> Dict[str, Any]:
    """Backward compatibility wrapper"""
    return data_loader.load_npcs(group)
