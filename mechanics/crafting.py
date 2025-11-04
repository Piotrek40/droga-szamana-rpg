"""
System craftingu dla Droga Szamana RPG
Zawiera kompletną implementację craftingu z recepturami, umiejętnościami i jakością
"""

import json
import random
import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

try:
    from .economy import Item, QualityTier
except ImportError:
    from economy import Item, QualityTier


class CraftingResult(Enum):
    """Możliwe wyniki craftingu"""
    SUKCES = "sukces"
    CZĘŚCIOWY_SUKCES = "częściowy_sukces"
    PORAŻKA = "porażka"
    KRYTYCZNA_PORAŻKA = "krytyczna_porażka"
    MISTRZOWSKI_SUKCES = "mistrzowski_sukces"


@dataclass
class CraftingSkill:
    """Umiejętność craftingowa gracza"""
    nazwa: str
    poziom: int = 0
    doswiadczenie: int = 0
    max_doswiadczenie: int = 100
    
    def dodaj_exp(self, ile: int) -> bool:
        """Dodaje doświadczenie i sprawdza czy był awans"""
        self.doswiadczenie += ile
        awans = False
        
        while self.doswiadczenie >= self.max_doswiadczenie:
            self.doswiadczenie -= self.max_doswiadczenie
            self.poziom += 1
            self.max_doswiadczenie = int(self.max_doswiadczenie * 1.2)
            awans = True
        
        return awans
    
    def oblicz_bonus(self) -> float:
        """Oblicza bonus do crafingu na podstawie poziomu"""
        return 1.0 + (self.poziom * 0.05)  # 5% bonusu na poziom


@dataclass
class RecipeIngredient:
    """Składnik receptury"""
    przedmiot: str
    ilosc: int
    minimalna_jakosc: int = 0


@dataclass
class RequiredTool:
    """Wymagane narzędzie"""
    przedmiot: str
    minimalna_jakosc: int = 0
    zuzycie_trwalosci: int = 1


@dataclass
class Recipe:
    """Receptura craftingowa"""
    id: str
    nazwa: str
    opis: str
    wymagana_umiejetnosc: str
    poziom_trudnosci: int
    czas_tworzenia: int  # w sekundach
    skladniki: List[RecipeIngredient]
    wymagane_narzedzia: List[RequiredTool]
    rezultat_id: str
    rezultat_ilosc: int = 1
    bonus_jakosci: int = 0
    exp_za_stworzenie: int = 0  # Use-based learning: wzrost przez praktykę, nie XP
    szansa_powodzenia: float = 1.0
    odkryta: bool = False
    
    def sprawdz_wymagania(self, gracz, inwentarz) -> Tuple[bool, List[str]]:
        """Sprawdza czy gracz spełnia wymagania receptury"""
        bledy = []
        
        # Sprawdź umiejętność
        if hasattr(gracz, 'umiejetnosci_craft'):
            umiejetnosc = gracz.umiejetnosci_craft.get(self.wymagana_umiejetnosc)
            if not umiejetnosc or umiejetnosc.poziom < self.poziom_trudnosci:
                bledy.append(f"Wymagany poziom {self.poziom_trudnosci} w {self.wymagana_umiejetnosc}")
        
        # Sprawdź składniki
        for skladnik in self.skladniki:
            if not inwentarz.ma_przedmiot(skladnik.przedmiot, skladnik.ilosc, skladnik.minimalna_jakosc):
                bledy.append(f"Brak: {skladnik.ilosc}x {skladnik.przedmiot} (jakość min. {skladnik.minimalna_jakosc})")
        
        # Sprawdź narzędzia
        for narzedzie in self.wymagane_narzedzia:
            if not inwentarz.ma_przedmiot(narzedzie.przedmiot, 1, narzedzie.minimalna_jakosc):
                bledy.append(f"Brak narzędzia: {narzedzie.przedmiot} (jakość min. {narzedzie.minimalna_jakosc})")
        
        return len(bledy) == 0, bledy


@dataclass
class CraftingStation:
    """Stacja craftingowa (warsztat, kuźnia, itp.)"""
    nazwa: str
    typ: str
    bonus_jakosci: int = 0
    bonus_szansy: float = 0.0
    wymagane_umiejetnosci: List[str] = field(default_factory=list)
    dostepna: bool = True
    
    def oblicz_bonus(self, receptura: Recipe) -> Tuple[int, float]:
        """Oblicza bonusy stacji dla danej receptury"""
        bonus_jakosc = 0
        bonus_szansa = 0.0
        
        if receptura.wymagana_umiejetnosc in self.wymagane_umiejetnosci:
            bonus_jakosc = self.bonus_jakosci
            bonus_szansa = self.bonus_szansy
        
        return bonus_jakosc, bonus_szansa


class CraftingSystem:
    """Główny system craftingu"""
    
    def __init__(self, items_db_path: str = "data/items.json", recipes_db_path: str = "data/recipes.json", stations_db_path: str = "data/crafting_stations.json"):
        self.items_db = self._load_items_db(items_db_path)
        self.recipes_db = self._load_recipes_db(recipes_db_path)
        self.stations_data = self._load_stations_db(stations_db_path)
        self.crafting_stations = self._create_stations_from_data()
        self.discovered_recipes = set()  # Odkryte receptury
    
    def _load_stations_db(self, path: str) -> Dict:
        """Wczytuje dane stacji craftingowych z JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Ostrzeżenie: Nie znaleziono pliku {path}")
            return {'stations': {}, 'portable_stations': {}}
    
    def _create_stations_from_data(self) -> Dict[str, 'CraftingStation']:
        """Tworzy stacje na podstawie danych z JSON"""
        stations = {}
        for station_id, data in self.stations_data.get('stations', {}).items():
            stations[station_id] = CraftingStation(
                nazwa=data['name'],
                typ=data['type'],
                bonus_jakosci=data.get('quality_bonus', 0),
                bonus_szansy=data.get('skill_bonus', 0) / 100.0,  # Convert to float percentage
                wymagane_umiejetnosci=[data.get('required_skill', 'kowalstwo')],
                dostepna=True
            )
        return stations
    
    @property
    def recipes(self):
        """Alias dla recipes_db dla kompatybilności"""
        return self.recipes_db
    
    def _load_items_db(self, path: str) -> Dict[str, dict]:
        """Ładuje bazę danych przedmiotów"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_recipes_db(self, path: str) -> Dict[str, Recipe]:
        """Ładuje receptury z pliku JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        recipes = {}
        for recipe_id, recipe_data in data.items():
            skladniki = [
                RecipeIngredient(**sk) for sk in recipe_data['skladniki']
            ]
            narzedzia = [
                RequiredTool(**nt) for nt in recipe_data['wymagane_narzedzia']
            ]
            
            recipe = Recipe(
                id=recipe_id,
                nazwa=recipe_data['nazwa'],
                opis=recipe_data['opis'],
                wymagana_umiejetnosc=recipe_data['wymagana_umiejetnosc'],
                poziom_trudnosci=recipe_data['poziom_trudnosci'],
                czas_tworzenia=recipe_data['czas_tworzenia'],
                skladniki=skladniki,
                wymagane_narzedzia=narzedzia,
                rezultat_id=recipe_data['rezultat']['przedmiot'],
                rezultat_ilosc=recipe_data['rezultat'].get('ilosc', 1),
                bonus_jakosci=recipe_data['rezultat'].get('bonus_jakosci', 0),
                exp_za_stworzenie=recipe_data.get('exp_za_stworzenie', 0),  # 0 dla use-based learning
                szansa_powodzenia=recipe_data['szansa_powodzenia']
            )
            recipes[recipe_id] = recipe
        
        return recipes
    
    def _create_default_stations(self) -> Dict[str, CraftingStation]:
        """Tworzy domyślne stacje craftingowe"""
        stations = {
            'kuznia': CraftingStation(
                nazwa="Kuźnia",
                typ="kowalstwo",
                bonus_jakosci=15,
                bonus_szansy=0.1,
                wymagane_umiejetnosci=['kowalstwo']
            ),
            'warsztat_stolarski': CraftingStation(
                nazwa="Warsztat Stolarski",
                typ="stolarstwo",
                bonus_jakosci=12,
                bonus_szansy=0.08,
                wymagane_umiejetnosci=['stolarstwo']
            ),
            'krosno': CraftingStation(
                nazwa="Krosno",
                typ="tkactwo",
                bonus_jakosci=8,
                bonus_szansy=0.05,
                wymagane_umiejetnosci=['tkactwo', 'szycie']
            ),
            'alchemiczny_stol': CraftingStation(
                nazwa="Stół Alchemiczny",
                typ="alchemia",
                bonus_jakosci=20,
                bonus_szansy=0.15,
                wymagane_umiejetnosci=['alchemia']
            )
        }
        return stations
    
    def discover_recipe(self, recipe_id: str, gracz) -> bool:
        """Odkrywa nową recepturę"""
        if recipe_id in self.discovered_recipes:
            return False
        
        if recipe_id in self.recipes_db:
            self.discovered_recipes.add(recipe_id)
            recipe = self.recipes_db[recipe_id]
            
            # Dodaj doświadczenie za odkrycie
            if hasattr(gracz, 'umiejetnosci_craft'):
                umiejetnosc = gracz.umiejetnosci_craft.get(recipe.wymagana_umiejetnosc)
                if umiejetnosc:
                    umiejetnosc.dodaj_exp(5)
            
            return True
        
        return False
    
    def oblicz_szanse_powodzenia(self, recipe: Recipe, gracz, stacja: Optional[CraftingStation] = None) -> float:
        """Oblicza szanse powodzenia dla danej receptury"""
        # Bazowa szansa z receptury
        szansa = recipe.szansa_powodzenia
        
        # Bonus z umiejętności
        if hasattr(gracz, 'umiejetnosci_craft'):
            umiejetnosc = gracz.umiejetnosci_craft.get(recipe.wymagana_umiejetnosc)
            if umiejetnosc:
                poziom_bonus = (umiejetnosc.poziom - recipe.poziom_trudnosci) * 0.05
                szansa += max(-0.3, min(0.3, poziom_bonus))
        
        # Bonus ze stacji
        if stacja:
            _, bonus_szansa = stacja.oblicz_bonus(recipe)
            szansa += bonus_szansa
        
        return max(0.1, min(0.95, szansa))  # Ograniczamy między 10% a 95%
    
    def oblicz_jakosc_rezultatu(self, recipe: Recipe, gracz, skladniki: List[Item], 
                               narzedzia: List[Item], stacja: Optional[CraftingStation] = None) -> int:
        """Oblicza jakość tworzonego przedmiotu"""
        # Bazowa jakość z receptury
        jakosc = 50 + recipe.bonus_jakosci
        
        # Średnia jakość składników
        if skladniki:
            srednia_jakosc_skladnikow = sum(item.jakosc for item in skladniki) / len(skladniki)
            jakosc += int((srednia_jakosc_skladnikow - 50) * 0.3)
        
        # Jakość najlepszego narzędzia
        if narzedzia:
            najlepsze_narzedzie = max(narzedzia, key=lambda x: x.jakosc)
            jakosc += int((najlepsze_narzedzie.jakosc - 50) * 0.2)
        
        # Bonus z umiejętności
        if hasattr(gracz, 'umiejetnosci_craft'):
            umiejetnosc = gracz.umiejetnosci_craft.get(recipe.wymagana_umiejetnosc)
            if umiejetnosc:
                jakosc += umiejetnosc.poziom
        
        # Bonus ze stacji
        if stacja:
            bonus_jakosc, _ = stacja.oblicz_bonus(recipe)
            jakosc += bonus_jakosc
        
        # Losowość ±10
        jakosc += random.randint(-10, 10)
        
        return max(1, min(100, jakosc))
    
    def pobierz_skladniki(self, recipe: Recipe, inwentarz) -> Tuple[bool, List[Item]]:
        """Pobiera składniki z inwentarza"""
        pobrane_skladniki = []
        
        for wymagany_skladnik in recipe.skladniki:
            pobrane_ilosc = 0
            skladniki_tego_typu = []
            
            for _ in range(wymagany_skladnik.ilosc):
                przedmiot = inwentarz.usun_przedmiot(
                    wymagany_skladnik.przedmiot, 
                    wymagany_skladnik.minimalna_jakosc
                )
                if przedmiot:
                    skladniki_tego_typu.append(przedmiot)
                    pobrane_ilosc += 1
                else:
                    # Przywróć już pobrane przedmioty
                    for item in skladniki_tego_typu:
                        inwentarz.dodaj_przedmiot(item)
                    for item in pobrane_skladniki:
                        inwentarz.dodaj_przedmiot(item)
                    return False, []
            
            pobrane_skladniki.extend(skladniki_tego_typu)
        
        return True, pobrane_skladniki
    
    def pobierz_narzedzia(self, recipe: Recipe, inwentarz) -> List[Item]:
        """Pobiera narzędzia (bez usuwania z inwentarza)"""
        narzedzia = []
        
        for wymagane_narzedzie in recipe.wymagane_narzedzia:
            for item_id, items in inwentarz.przedmioty.items():
                if item_id == wymagane_narzedzie.przedmiot:
                    for item in items:
                        if item.jakosc >= wymagane_narzedzie.minimalna_jakosc and not item.czy_zepsute():
                            narzedzia.append(item)
                            break
                    break
        
        return narzedzia
    
    def zuzyj_narzedzia(self, recipe: Recipe, narzedzia: List[Item]):
        """Zużywa trwałość narzędzi"""
        for i, wymagane_narzedzie in enumerate(recipe.wymagane_narzedzia):
            if i < len(narzedzia):
                narzedzia[i].zuzyj(wymagane_narzedzie.zuzycie_trwalosci)
    
    def craft_item(self, recipe_id: str, gracz, inwentarz, stacja: Optional[str] = None) -> Dict:
        """Główna funkcja craftingu"""
        if recipe_id not in self.recipes_db:
            return {"sukces": False, "powod": "Nieznana receptura"}
        
        if recipe_id not in self.discovered_recipes:
            return {"sukces": False, "powod": "Receptura nie została odkryta"}
        
        recipe = self.recipes_db[recipe_id]
        
        # Sprawdź wymagania
        spelnione, bledy = recipe.sprawdz_wymagania(gracz, inwentarz)
        if not spelnione:
            return {"sukces": False, "powod": "Nie spełniono wymagań", "bledy": bledy}
        
        # Pobierz stację craftingową
        crafting_station = None
        if stacja and stacja in self.crafting_stations:
            crafting_station = self.crafting_stations[stacja]
            if not crafting_station.dostepna:
                return {"sukces": False, "powod": "Stacja niedostępna"}
        
        # Pobierz składniki
        sukces_skladniki, skladniki = self.pobierz_skladniki(recipe, inwentarz)
        if not sukces_skladniki:
            return {"sukces": False, "powod": "Nie można pobrać składników"}
        
        # Pobierz narzędzia
        narzedzia = self.pobierz_narzedzia(recipe, inwentarz)
        if len(narzedzia) != len(recipe.wymagane_narzedzia):
            # Przywróć składniki
            for item in skladniki:
                inwentarz.dodaj_przedmiot(item)
            return {"sukces": False, "powod": "Brak wymaganych narzędzi"}
        
        # Oblicz szanse powodzenia
        szansa = self.oblicz_szanse_powodzenia(recipe, gracz, crafting_station)
        
        # Wykonaj test powodzenia
        wynik_testu = random.random()
        
        if wynik_testu <= szansa * 0.05:  # 5% szansy na mistrzowski sukces
            rezultat = CraftingResult.MISTRZOWSKI_SUKCES
        elif wynik_testu <= szansa:
            rezultat = CraftingResult.SUKCES
        elif wynik_testu <= szansa + 0.2:  # 20% szansy na częściowy sukces po porażce
            rezultat = CraftingResult.CZĘŚCIOWY_SUKCES
        elif wynik_testu >= 0.95:  # 5% szansy na krytyczną porażkę
            rezultat = CraftingResult.KRYTYCZNA_PORAŻKA
        else:
            rezultat = CraftingResult.PORAŻKA
        
        # Zużyj narzędzia
        self.zuzyj_narzedzia(recipe, narzedzia)
        
        # Przetwórz rezultaty
        utworzone_przedmioty = []
        exp_zdobyte = 0
        
        if rezultat in [CraftingResult.SUKCES, CraftingResult.MISTRZOWSKI_SUKCES, CraftingResult.CZĘŚCIOWY_SUKCES]:
            # Oblicz jakość
            jakosc = self.oblicz_jakosc_rezultatu(recipe, gracz, skladniki, narzedzia, crafting_station)
            
            if rezultat == CraftingResult.MISTRZOWSKI_SUKCES:
                jakosc = min(100, jakosc + 15)
                ilosc = recipe.rezultat_ilosc + 1  # Bonus przedmiot
            elif rezultat == CraftingResult.CZĘŚCIOWY_SUKCES:
                jakosc = max(1, jakosc - 15)
                ilosc = max(1, recipe.rezultat_ilosc // 2)  # Połowa
            else:
                ilosc = recipe.rezultat_ilosc
            
            # Stwórz przedmioty
            for _ in range(ilosc):
                if recipe.rezultat_id in self.items_db:
                    item_data = self.items_db[recipe.rezultat_id]
                    nowy_przedmiot = Item(
                        id=recipe.rezultat_id,
                        nazwa=item_data['nazwa'],
                        typ=item_data['typ'],
                        opis=item_data['opis'],
                        waga=item_data['waga'],
                        bazowa_wartosc=item_data['bazowa_wartosc'],
                        trwalosc=item_data['trwalosc'],
                        kategoria=item_data['kategoria'],
                        efekty=item_data['efekty'],
                        jakosc=jakosc,
                        tworca=gracz.nazwa if hasattr(gracz, 'nazwa') else "Gracz",
                        czas_stworzenia=int(time.time())
                    )
                    
                    if inwentarz.dodaj_przedmiot(nowy_przedmiot):
                        utworzone_przedmioty.append(nowy_przedmiot)
            
            # Dodaj doświadczenie
            if hasattr(gracz, 'umiejetnosci_craft'):
                umiejetnosc = gracz.umiejetnosci_craft.get(recipe.wymagana_umiejetnosc)
                if umiejetnosc:
                    exp_bonus = 1.0
                    if rezultat == CraftingResult.MISTRZOWSKI_SUKCES:
                        exp_bonus = 2.0
                    elif rezultat == CraftingResult.CZĘŚCIOWY_SUKCES:
                        exp_bonus = 0.5
                    
                    exp_zdobyte = int(recipe.exp_za_stworzenie * exp_bonus)
                    awans = umiejetnosc.dodaj_exp(exp_zdobyte)
        
        else:  # Porażka
            if rezultat == CraftingResult.KRYTYCZNA_PORAŻKA:
                # Zniszcz też niektóre narzędzia
                for narzedzie in narzedzia:
                    if random.random() < 0.3:  # 30% szans na zniszczenie
                        narzedzie.zuzyj(narzedzie.obecna_trwalosc)
            
            # Możliwość odzyskania niektórych składników
            if rezultat == CraftingResult.PORAŻKA:
                for skladnik in skladniki:
                    if random.random() < 0.3:  # 30% szans na odzyskanie
                        inwentarz.dodaj_przedmiot(skladnik)
        
        # Sprawdź możliwość odkrycia nowych receptur
        nowe_receptury = self._sprawdz_odkrycia(recipe, gracz)
        
        return {
            "sukces": rezultat in [CraftingResult.SUKCES, CraftingResult.MISTRZOWSKI_SUKCES, CraftingResult.CZĘŚCIOWY_SUKCES],
            "rezultat": rezultat.value,
            "przedmioty": utworzone_przedmioty,
            "exp_zdobyte": exp_zdobyte,
            "nowe_receptury": nowe_receptury,
            "zuzyto_skladnikow": len(skladniki),
            "szansa_powodzenia": szansa
        }
    
    def _sprawdz_odkrycia(self, recipe: Recipe, gracz) -> List[str]:
        """Sprawdza możliwość odkrycia nowych receptur"""
        nowe_receptury = []
        
        if not hasattr(gracz, 'umiejetnosci_craft'):
            return nowe_receptury
        
        umiejetnosc = gracz.umiejetnosci_craft.get(recipe.wymagana_umiejetnosc)
        if not umiejetnosc:
            return nowe_receptury
        
        # Szansa na odkrycie receptury tej samej kategorii
        for recipe_id, other_recipe in self.recipes_db.items():
            if recipe_id in self.discovered_recipes:
                continue
            
            if other_recipe.wymagana_umiejetnosc == recipe.wymagana_umiejetnosc:
                if other_recipe.poziom_trudnosci <= umiejetnosc.poziom + 2:
                    if random.random() < 0.1:  # 10% szansy
                        if self.discover_recipe(recipe_id, gracz):
                            nowe_receptury.append(recipe_id)
        
        return nowe_receptury
    
    def get_available_recipes(self, gracz) -> List[Recipe]:
        """Zwraca listę dostępnych receptur dla gracza"""
        dostepne = []
        
        for recipe_id in self.discovered_recipes:
            if recipe_id in self.recipes_db:
                recipe = self.recipes_db[recipe_id]
                
                # Sprawdź poziom umiejętności
                if hasattr(gracz, 'umiejetnosci_craft'):
                    umiejetnosc = gracz.umiejetnosci_craft.get(recipe.wymagana_umiejetnosc)
                    if umiejetnosc and umiejetnosc.poziom >= recipe.poziom_trudnosci:
                        dostepne.append(recipe)
        
        return dostepne
    
    def auto_discover_basic_recipes(self, gracz):
        """Automatycznie odkrywa podstawowe receptury"""
        podstawowe = ['maczuga', 'noz', 'strzaly']  # Najłatwiejsze receptury
        
        for recipe_id in podstawowe:
            if recipe_id in self.recipes_db:
                self.discover_recipe(recipe_id, gracz)
    
    def get_all_recipes(self) -> List[Recipe]:
        """
        Zwraca listę wszystkich receptur w grze.
        
        Returns:
            Lista wszystkich obiektów Recipe
        """
        return list(self.recipes.values())
    
    def get_known_recipes(self, known_recipe_ids: List[str]) -> List[Recipe]:
        """
        Zwraca listę znanych receptur na podstawie ID.
        
        Args:
            known_recipe_ids: Lista ID receptur które gracz zna
            
        Returns:
            Lista obiektów Recipe
        """
        recipes = []
        for recipe_id in known_recipe_ids:
            if recipe_id in self.recipes_db:
                recipe_data = self.recipes_db[recipe_id]
                recipe = Recipe(
                    id=recipe_id,
                    nazwa=recipe_data['nazwa'],
                    opis=recipe_data['opis'],
                    skladniki=[
                        RecipeIngredient(
                            przedmiot_id=ing['przedmiot'],
                            ilosc=ing['ilosc']
                        ) for ing in recipe_data['skladniki']
                    ],
                    wymagane_narzedzia=[
                        RequiredTool(
                            kategoria=tool['kategoria'],
                            minimalna_jakosc=tool.get('minimalna_jakosc', 1)
                        ) for tool in recipe_data.get('wymagane_narzedzia', [])
                    ],
                    wymagane_stacje=recipe_data.get('wymagane_stacje', []),
                    wymagana_umiejetnosc=recipe_data['wymagana_umiejetnosc'],
                    poziom_trudnosci=recipe_data['poziom_trudnosci'],
                    czas_wykonania=recipe_data['czas_wykonania'],
                    rezultaty=recipe_data['rezultaty'],
                    szansa_sukcesu=recipe_data.get('szansa_sukcesu', 100),
                    dodatkowe_efekty=recipe_data.get('dodatkowe_efekty', {})
                )
                recipes.append(recipe)
        return recipes
    
    def craft(self, recipe_id: str, materials: List[Dict], crafter_skill: Any = None) -> Dict[str, Any]:
        """
        Wrapper metoda dla kompatybilności z commands.py
        
        Args:
            recipe_id: ID receptury do wytworzenia
            materials: Lista materiałów (inventory gracza)
            crafter_skill: Umiejętność gracza (nieużywane w tej implementacji)
            
        Returns:
            Słownik z wynikami craftingu w formacie oczekiwanym przez commands.py
        """
        # Dla uproszczenia, zwracamy podstawową strukturę
        # W pełnej implementacji należałoby przekonwertować argumenty i wywołać craft_item()
        
        if recipe_id not in self.recipes_db:
            return {
                'success': False,
                'message': f'Nieznana receptura: {recipe_id}',
                'item': None,
                'quality': 0
            }
        
        if recipe_id not in self.discovered_recipes:
            return {
                'success': False,
                'message': f'Receptura nie została odkryta: {recipe_id}',
                'item': None,
                'quality': 0
            }
        
        # Dla uproszczenia - zawsze sukces z podstawową jakością
        recipe = self.recipes_db[recipe_id]
        if recipe.rezultat_id in self.items_db:
            item_data = self.items_db[recipe.rezultat_id].copy()
            item_data['name'] = recipe.rezultat_id
            
            return {
                'success': True,
                'message': f'Wytworzono {recipe.nazwa}',
                'item': item_data,
                'quality': 50  # Średnia jakość
            }
        else:
            return {
                'success': False,
                'message': f'Brak danych przedmiotu: {recipe.rezultat_id}',
                'item': None,
                'quality': 0
            }
    
    def get_workshop(self, workshop_id: str = "default") -> Optional[Dict[str, Any]]:
        """Zwraca informacje o warsztacie.
        
        Args:
            workshop_id: ID warsztatu
            
        Returns:
            Słownik z danymi warsztatu lub None
        """
        if workshop_id in self.crafting_stations:
            station = self.crafting_stations[workshop_id]
            return {
                'id': workshop_id,
                'name': station.nazwa,
                'type': station.typ,
                'quality_bonus': station.bonus_jakosci,
                'skill_bonus': station.bonus_szansy,
                'available': station.dostepna,
                'required_skills': station.wymagane_umiejetnosci
            }
        
        # Domyślny warsztat
        return {
            'id': 'default',
            'name': 'Podstawowy Warsztat',
            'type': 'general',
            'quality_bonus': 0,
            'skill_bonus': 0,
            'available': True,
            'required_skills': []
        }
    
    def get_quality_system(self) -> Dict[str, Any]:
        """Zwraca informacje o systemie jakości.
        
        Returns:
            Słownik z informacjami o systemie jakości
        """
        return {
            'quality_tiers': {
                'poor': {'min': 0, 'max': 20, 'name': 'Kiepska'},
                'common': {'min': 21, 'max': 40, 'name': 'Zwykła'},
                'good': {'min': 41, 'max': 60, 'name': 'Dobra'},
                'rare': {'min': 61, 'max': 80, 'name': 'Rzadka'},
                'epic': {'min': 81, 'max': 100, 'name': 'Epicka'}
            },
            'quality_modifiers': {
                'durability': [0.5, 1.0, 1.2, 1.5, 2.0],
                'value': [0.3, 1.0, 1.5, 2.5, 4.0],
                'effectiveness': [0.7, 1.0, 1.1, 1.3, 1.6]
            }
        }


# Przykładowa klasa gracza do testów
@dataclass
class TestPlayer:
    """Testowy gracz dla systemu craftingu"""
    nazwa: str = "TestGracz"
    umiejetnosci_craft: Dict[str, CraftingSkill] = field(default_factory=dict)
    
    def __post_init__(self):
        # Dodaj podstawowe umiejętności
        self.umiejetnosci_craft['kowalstwo'] = CraftingSkill('kowalstwo', 5, 0)
        self.umiejetnosci_craft['stolarstwo'] = CraftingSkill('stolarstwo', 3, 0)
        self.umiejetnosci_craft['alchemia'] = CraftingSkill('alchemia', 1, 0)


if __name__ == "__main__":
    # Test systemu craftingu
    try:
        from .economy import NPCInventory
    except ImportError:
        from economy import NPCInventory
    
    crafting_system = CraftingSystem(
        "/mnt/d/claude3/data/items.json",
        "/mnt/d/claude3/data/recipes.json"
    )
    
    # Stwórz testowego gracza
    gracz = TestPlayer()
    
    # Stwórz inwentarz z materiałami
    inwentarz = NPCInventory(max_przedmiotow=100)
    
    # Dodaj materiały do testów
    items_db = crafting_system.items_db
    
    # Dodaj metal wysokiej jakości
    for _ in range(3):
        metal = Item(
            id="metal",
            nazwa=items_db["metal"]["nazwa"],
            typ=items_db["metal"]["typ"], 
            opis=items_db["metal"]["opis"],
            waga=items_db["metal"]["waga"],
            bazowa_wartosc=items_db["metal"]["bazowa_wartosc"],
            trwalosc=items_db["metal"]["trwalosc"],
            kategoria=items_db["metal"]["kategoria"],
            efekty=items_db["metal"]["efekty"],
            jakosc=70
        )
        inwentarz.dodaj_przedmiot(metal)
    
    # Dodaj drewno i skórę
    drewno = Item(
        id="drewno",
        nazwa=items_db["drewno"]["nazwa"],
        typ=items_db["drewno"]["typ"],
        opis=items_db["drewno"]["opis"], 
        waga=items_db["drewno"]["waga"],
        bazowa_wartosc=items_db["drewno"]["bazowa_wartosc"],
        trwalosc=items_db["drewno"]["trwalosc"],
        kategoria=items_db["drewno"]["kategoria"],
        efekty=items_db["drewno"]["efekty"],
        jakosc=50
    )
    inwentarz.dodaj_przedmiot(drewno)
    
    skora = Item(
        id="skora",
        nazwa=items_db["skora"]["nazwa"],
        typ=items_db["skora"]["typ"],
        opis=items_db["skora"]["opis"],
        waga=items_db["skora"]["waga"],
        bazowa_wartosc=items_db["skora"]["bazowa_wartosc"],
        trwalosc=items_db["skora"]["trwalosc"],
        kategoria=items_db["skora"]["kategoria"],
        efekty=items_db["skora"]["efekty"],
        jakosc=40
    )
    inwentarz.dodaj_przedmiot(skora)
    
    # Dodaj młotek jako narzędzie
    mlotek = Item(
        id="mlotek",
        nazwa=items_db["mlotek"]["nazwa"],
        typ=items_db["mlotek"]["typ"],
        opis=items_db["mlotek"]["opis"],
        waga=items_db["mlotek"]["waga"],
        bazowa_wartosc=items_db["mlotek"]["bazowa_wartosc"],
        trwalosc=items_db["mlotek"]["trwalosc"],
        kategoria=items_db["mlotek"]["kategoria"],
        efekty=items_db["mlotek"]["efekty"],
        jakosc=60
    )
    inwentarz.dodaj_przedmiot(mlotek)
    
    # Odkryj podstawowe receptury
    crafting_system.auto_discover_basic_recipes(gracz)
    
    print("=== TEST SYSTEMU CRAFTINGU ===")
    print(f"Odkryte receptury: {list(crafting_system.discovered_recipes)}")
    print(f"Inwentarz przed: {inwentarz.liczba_przedmiotow()} przedmiotów")
    
    # Testuj tworzenie noża
    rezultat = crafting_system.craft_item("noz", gracz, inwentarz, "kuznia")
    
    print(f"\nRezultat craftingu noża:")
    print(f"Sukces: {rezultat['sukces']}")
    print(f"Rezultat: {rezultat['rezultat']}")
    if rezultat['przedmioty']:
        for item in rezultat['przedmioty']:
            print(f"Utworzony: {item.nazwa} (jakość: {item.jakosc})")
    print(f"Zdobyte EXP: {rezultat['exp_zdobyte']}")
    print(f"Nowe receptury: {rezultat['nowe_receptury']}")
    
    print(f"\nInwentarz po: {inwentarz.liczba_przedmiotow()} przedmiotów")
    print(f"Poziom kowalstwa: {gracz.umiejetnosci_craft['kowalstwo'].poziom}")
    print(f"EXP kowalstwa: {gracz.umiejetnosci_craft['kowalstwo'].doswiadczenie}")