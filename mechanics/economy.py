"""
System ekonomiczny dla Droga Szamana RPG
Zawiera kompletną implementację dynamicznej ekonomii z NPCami, handlem i reputacją
"""

import json
import random
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class QualityTier(Enum):
    """Poziomy jakości przedmiotów"""
    OKROPNA = (1, 20, "Okropna", 0.5)
    SŁABA = (21, 40, "Słaba", 0.75)
    PRZECIĘTNA = (41, 60, "Przeciętna", 1.0)
    DOBRA = (61, 80, "Dobra", 1.5)
    DOSKONAŁA = (81, 100, "Doskonała", 2.0)
    
    def __init__(self, min_val, max_val, nazwa, multiplier):
        self.min_val = min_val
        self.max_val = max_val
        self.nazwa = nazwa
        self.multiplier = multiplier
    
    @classmethod
    def get_tier(cls, quality: int):
        """Zwraca poziom jakości dla danej wartości"""
        for tier in cls:
            if tier.min_val <= quality <= tier.max_val:
                return tier
        return cls.PRZECIĘTNA


@dataclass
class Item:
    """Klasa reprezentująca przedmiot w grze"""
    id: str
    nazwa: str
    typ: str
    opis: str
    waga: float
    bazowa_wartosc: int
    trwalosc: int
    kategoria: str
    efekty: Dict[str, int]
    jakosc: int = 50
    obecna_trwalosc: Optional[int] = None
    tworca: Optional[str] = None
    czas_stworzenia: Optional[int] = None
    
    def __post_init__(self):
        if self.obecna_trwalosc is None:
            self.obecna_trwalosc = self.trwalosc
    
    @property
    def quality_tier(self) -> QualityTier:
        """Zwraca poziom jakości przedmiotu"""
        return QualityTier.get_tier(self.jakosc)
    
    @property
    def aktualna_wartosc(self) -> float:
        """Oblicza aktualną wartość przedmiotu bazując na jakości i trwałości"""
        quality_multiplier = self.quality_tier.multiplier
        durability_multiplier = max(0.1, self.obecna_trwalosc / self.trwalosc)
        return self.bazowa_wartosc * quality_multiplier * durability_multiplier
    
    def zuzyj(self, ile: int = 1):
        """Zmniejsza trwałość przedmiotu"""
        self.obecna_trwalosc = max(0, self.obecna_trwalosc - ile)
    
    def napraw(self, ile: int):
        """Naprawia przedmiot"""
        self.obecna_trwalosc = min(self.trwalosc, self.obecna_trwalosc + ile)
    
    def czy_zepsute(self) -> bool:
        """Sprawdza czy przedmiot jest zepsuty"""
        return self.obecna_trwalosc <= 0


@dataclass
class MarketData:
    """Dane rynkowe dla przedmiotu"""
    item_id: str = ""
    podaz: int = 0
    popyt: int = 0
    historia_cen: List[float] = field(default_factory=list)
    ostatnia_cena: float = 0.0
    trend: float = 0.0  # -1 do 1, gdzie -1 to spadek, 1 to wzrost
    
    def dodaj_cene(self, cena: float):
        """Dodaje cenę do historii"""
        self.historia_cen.append(cena)
        if len(self.historia_cen) > 50:  # Przechowujemy tylko ostatnie 50 cen
            self.historia_cen.pop(0)
        self.ostatnia_cena = cena
        self.oblicz_trend()
    
    def oblicz_trend(self):
        """Oblicza trend cenowy"""
        if len(self.historia_cen) < 3:
            self.trend = 0.0
            return
        
        ostatnie_3 = self.historia_cen[-3:]
        if ostatnie_3[-1] > ostatnie_3[0]:
            self.trend = min(1.0, (ostatnie_3[-1] - ostatnie_3[0]) / ostatnie_3[0])
        else:
            self.trend = max(-1.0, (ostatnie_3[-1] - ostatnie_3[0]) / ostatnie_3[0])


@dataclass
class NPCInventory:
    """Inwentarz NPC-a"""
    przedmioty: Dict[str, List[Item]] = field(default_factory=dict)
    zloto: int = 100
    max_przedmiotow: int = 50
    
    def dodaj_przedmiot(self, przedmiot: Item) -> bool:
        """Dodaje przedmiot do inwentarza"""
        if self.liczba_przedmiotow() >= self.max_przedmiotow:
            return False
        
        if przedmiot.id not in self.przedmioty:
            self.przedmioty[przedmiot.id] = []
        
        self.przedmioty[przedmiot.id].append(przedmiot)
        return True
    
    def usun_przedmiot(self, item_id: str, jakosc_min: int = 0) -> Optional[Item]:
        """Usuwa przedmiot z inwentarza"""
        if item_id not in self.przedmioty or not self.przedmioty[item_id]:
            return None
        
        # Znajdź przedmiot o odpowiedniej jakości
        for i, przedmiot in enumerate(self.przedmioty[item_id]):
            if przedmiot.jakosc >= jakosc_min:
                return self.przedmioty[item_id].pop(i)
        
        return None
    
    def ma_przedmiot(self, item_id: str, ilosc: int = 1, jakosc_min: int = 0) -> bool:
        """Sprawdza czy ma wystarczającą ilość przedmiotów"""
        if item_id not in self.przedmioty:
            return False
        
        odpowiednie = [p for p in self.przedmioty[item_id] if p.jakosc >= jakosc_min]
        return len(odpowiednie) >= ilosc
    
    def liczba_przedmiotow(self) -> int:
        """Zwraca całkowitą liczbę przedmiotów"""
        return sum(len(items) for items in self.przedmioty.values())
    
    def wartosc_calkowita(self) -> float:
        """Oblicza całkowitą wartość inwentarza"""
        wartosc = self.zloto
        for items in self.przedmioty.values():
            wartosc += sum(item.aktualna_wartosc for item in items)
        return wartosc


class NPCPersonality(Enum):
    """Typy osobowości NPCów wpływających na handel"""
    ZACHŁANNY = ("zachłanny", 1.3, 0.7, "Bardzo chce zysku")
    UCZCIWY = ("uczciwy", 1.1, 0.9, "Sprawiedliwe ceny")
    HOJNY = ("hojny", 0.9, 1.1, "Lubi pomagać")
    SKĄPY = ("skąpy", 1.2, 0.8, "Nie lubi wydawać")
    IMPULSYWNY = ("impulsywny", 1.0, 1.0, "Nieprzewidywalny")


@dataclass
class NPC:
    """Klasa reprezentująca NPC w systemie ekonomicznym"""
    nazwa: str
    zawod: str
    reputacja_gracza: int  # -100 do 100
    osobowosc: NPCPersonality
    inwentarz: NPCInventory
    umiejetnosci: Dict[str, int] = field(default_factory=dict)
    produkcja: Dict[str, int] = field(default_factory=dict)  # Co i ile produkuje
    konsumpcja: Dict[str, int] = field(default_factory=dict)  # Co i ile zużywa
    ostatnia_produkcja: int = 0
    
    def oblicz_cene_kupna(self, przedmiot: Item, cena_rynkowa: float) -> float:
        """Oblicza cenę kupna od gracza"""
        mod_reputacji = 1.0 + (self.reputacja_gracza / 200.0)  # 0.5 do 1.5
        mod_osobowosci = self.osobowosc.value[2]  # Jak hojnie płaci
        
        # Sprawdź czy NPC potrzebuje tego przedmiotu
        mod_potrzeby = 1.0
        if przedmiot.id in self.konsumpcja:
            ile_ma = len(self.inwentarz.przedmioty.get(przedmiot.id, []))
            ile_potrzebuje = self.konsumpcja[przedmiot.id]
            if ile_ma < ile_potrzebuje:
                mod_potrzeby = 1.5  # Płaci więcej za potrzebne rzeczy
        
        return cena_rynkowa * mod_reputacji * mod_osobowosci * mod_potrzeby
    
    def oblicz_cene_sprzedazy(self, przedmiot: Item, cena_rynkowa: float) -> float:
        """Oblicza cenę sprzedaży do gracza"""
        mod_reputacji = 1.0 - (self.reputacja_gracza / 300.0)  # 0.67 do 1.33
        mod_osobowosci = self.osobowosc.value[1]  # Jak chciwie sprzedaje
        
        return cena_rynkowa * max(0.5, mod_reputacji) * mod_osobowosci
    
    def produkuj(self, items_db: Dict[str, dict]) -> List[Item]:
        """Produkuje przedmioty zgodnie z zawodem"""
        wyprodukowane = []
        
        for item_id, ilosc in self.produkcja.items():
            if item_id not in items_db:
                continue
                
            for _ in range(ilosc):
                # Jakość zależy od umiejętności
                umiejetnosc = self.umiejetnosci.get(self.zawod, 10)
                jakosc = min(100, max(1, umiejetnosc + random.randint(-20, 20)))
                
                item_data = items_db[item_id]
                nowy_przedmiot = Item(
                    id=item_id,
                    nazwa=item_data['nazwa'],
                    typ=item_data['typ'],
                    opis=item_data['opis'],
                    waga=item_data['waga'],
                    bazowa_wartosc=item_data['bazowa_wartosc'],
                    trwalosc=item_data['trwalosc'],
                    kategoria=item_data['kategoria'],
                    efekty=item_data['efekty'],
                    jakosc=jakosc,
                    tworca=self.nazwa
                )
                
                if self.inwentarz.dodaj_przedmiot(nowy_przedmiot):
                    wyprodukowane.append(nowy_przedmiot)
        
        return wyprodukowane
    
    def konsumuj(self) -> List[str]:
        """Konsumuje potrzebne przedmioty"""
        skonsumowane = []
        
        for item_id, ilosc in self.konsumpcja.items():
            for _ in range(min(ilosc, len(self.inwentarz.przedmioty.get(item_id, [])))):
                przedmiot = self.inwentarz.usun_przedmiot(item_id)
                if przedmiot:
                    skonsumowane.append(item_id)
        
        return skonsumowane


@dataclass
class Market:
    """Rynek/targ gdzie odbywa się handel"""
    nazwa: str
    lokalizacja: str
    npcs: List[NPC] = field(default_factory=list)
    dane_rynkowe: Dict[str, MarketData] = field(default_factory=dict)
    modyfikator_cen: float = 1.0  # Globalny modyfikator dla tego rynku
    
    def dodaj_npc(self, npc: NPC):
        """Dodaje NPC-a do rynku"""
        self.npcs.append(npc)
    
    def oblicz_cene_rynkowa(self, item_id: str, bazowa_wartosc: float) -> float:
        """Oblicza aktualną cenę rynkową przedmiotu"""
        if item_id not in self.dane_rynkowe:
            self.dane_rynkowe[item_id] = MarketData()
        
        dane = self.dane_rynkowe[item_id]
        
        # Oblicz stosunek popytu do podaży
        if dane.podaz == 0:
            ratio = 2.0  # Bardzo drogo gdy nie ma podaży
        else:
            ratio = dane.popyt / dane.podaz
            ratio = max(0.2, min(5.0, ratio))  # Ograniczamy ekstremalne ceny
        
        # Uwzględnij trend
        trend_modifier = 1.0 + (dane.trend * 0.1)
        
        cena = bazowa_wartosc * ratio * trend_modifier * self.modyfikator_cen
        dane.dodaj_cene(cena)
        
        return cena
    
    def aktualizuj_podaz_popyt(self, items_db: Dict[str, dict]):
        """Aktualizuje podaż i popyt na podstawie inwentarzy NPCów"""
        # Resetuj dane
        for dane in self.dane_rynkowe.values():
            dane.podaz = 0
            dane.popyt = 0
        
        # Policz podaż (co NPCe mają)
        for npc in self.npcs:
            for item_id, items in npc.inwentarz.przedmioty.items():
                if item_id not in self.dane_rynkowe:
                    self.dane_rynkowe[item_id] = MarketData()
                self.dane_rynkowe[item_id].podaz += len(items)
        
        # Policz popyt (czego NPCe potrzebują)
        for npc in self.npcs:
            for item_id, ilosc_potrzebna in npc.konsumpcja.items():
                if item_id not in self.dane_rynkowe:
                    self.dane_rynkowe[item_id] = MarketData()
                
                ile_ma = len(npc.inwentarz.przedmioty.get(item_id, []))
                brakuje = max(0, ilosc_potrzebna - ile_ma)
                self.dane_rynkowe[item_id].popyt += brakuje
    
    def handel_miedzy_npcami(self, items_db: Dict[str, dict]):
        """Symuluje handel między NPCami"""
        for i, kupujacy in enumerate(self.npcs):
            for j, sprzedajacy in enumerate(self.npcs):
                if i == j:
                    continue
                
                # Sprawdź czy kupujący potrzebuje czegoś co ma sprzedający
                for item_id, potrzeba in kupujacy.konsumpcja.items():
                    ile_ma = len(kupujacy.inwentarz.przedmioty.get(item_id, []))
                    if ile_ma >= potrzeba:
                        continue
                    
                    if not sprzedajacy.inwentarz.ma_przedmiot(item_id):
                        continue
                    
                    # Sprawdź czy kupujący ma pieniądze
                    if item_id not in items_db:
                        continue
                    
                    cena = self.oblicz_cene_rynkowa(item_id, items_db[item_id]['bazowa_wartosc'])
                    
                    if kupujacy.inwentarz.zloto >= cena:
                        przedmiot = sprzedajacy.inwentarz.usun_przedmiot(item_id)
                        if przedmiot and kupujacy.inwentarz.dodaj_przedmiot(przedmiot):
                            kupujacy.inwentarz.zloto -= int(cena)
                            sprzedajacy.inwentarz.zloto += int(cena)
    
    def symuluj_dzien(self, items_db: Dict[str, dict]):
        """Symuluje jeden dzień na rynku"""
        # NPCe produkują
        for npc in self.npcs:
            npc.produkuj(items_db)
        
        # NPCe konsumują
        for npc in self.npcs:
            npc.konsumuj()
        
        # Handel między NPCami
        self.handel_miedzy_npcami(items_db)
        
        # Aktualizuj podaż i popyt
        self.aktualizuj_podaz_popyt(items_db)


class TradeSystem:
    """System handlu z graczem"""
    
    @staticmethod
    def targuj_sie(gracz_cena: float, npc_cena: float, npc: NPC, umiejetnosc_gracza: int) -> Tuple[bool, float, int]:
        """
        Targowanie się z NPCem
        Zwraca: (sukces, finalna_cena, zmiana_reputacji)
        """
        roznica = abs(gracz_cena - npc_cena) / npc_cena
        
        # Bazowa szansa sukcesu
        szansa = 0.5 + (umiejetnosc_gracza / 200.0)  # 50-100%
        
        # Modyfikacje
        if roznica > 0.5:  # Zbyt duża różnica
            szansa *= 0.3
        elif roznica > 0.2:
            szansa *= 0.7
        
        # Reputacja wpływa na szanse
        szansa += npc.reputacja_gracza / 500.0  # -0.2 do +0.2
        
        # Osobowość NPCa
        if npc.osobowosc == NPCPersonality.IMPULSYWNY:
            szansa += random.uniform(-0.3, 0.3)
        elif npc.osobowosc == NPCPersonality.ZACHŁANNY:
            szansa *= 0.8 if gracz_cena < npc_cena else 1.2
        
        sukces = random.random() < max(0.1, min(0.9, szansa))
        
        if sukces:
            # Negocjacja udana - cena pośrodku
            finalna_cena = (gracz_cena + npc_cena) / 2
            zmiana_reputacji = random.randint(1, 3)
        else:
            # Negocjacja nieudana
            finalna_cena = npc_cena
            zmiana_reputacji = random.randint(-2, -1)
        
        return sukces, finalna_cena, zmiana_reputacji
    
    @staticmethod
    def kup_od_npc(gracz, npc: NPC, item_id: str, cena_rynkowa: float, targowanie: bool = False) -> Dict:
        """Kupuje przedmiot od NPCa"""
        if not npc.inwentarz.ma_przedmiot(item_id):
            return {"sukces": False, "powod": "NPC nie ma tego przedmiotu"}
        
        przedmiot = npc.inwentarz.przedmioty[item_id][0]  # Pierwszy dostępny
        cena_npc = npc.oblicz_cene_sprzedazy(przedmiot, cena_rynkowa)
        
        finalna_cena = cena_npc
        zmiana_reputacji = 0
        
        if targowanie and hasattr(gracz, 'umiejetnosci'):
            umiejetnosc = gracz.umiejetnosci.get('handel', 0)
            # Gracz proponuje niższą cenę
            propozycja = cena_npc * random.uniform(0.7, 0.9)
            
            sukces, finalna_cena, zmiana_reputacji = TradeSystem.targuj_sie(
                propozycja, cena_npc, npc, umiejetnosc
            )
        
        if hasattr(gracz, 'zloto') and gracz.zloto >= finalna_cena:
            przedmiot_kupiony = npc.inwentarz.usun_przedmiot(item_id)
            if przedmiot_kupiony:
                gracz.zloto -= int(finalna_cena)
                npc.inwentarz.zloto += int(finalna_cena)
                npc.reputacja_gracza += zmiana_reputacji
                
                return {
                    "sukces": True,
                    "przedmiot": przedmiot_kupiony,
                    "cena": finalna_cena,
                    "zmiana_reputacji": zmiana_reputacji
                }
        
        return {"sukces": False, "powod": "Brak środków"}
    
    @staticmethod
    def sprzedaj_npc(gracz, npc: NPC, przedmiot: Item, cena_rynkowa: float, targowanie: bool = False) -> Dict:
        """Sprzedaje przedmiot NPCowi"""
        if npc.inwentarz.liczba_przedmiotow() >= npc.inwentarz.max_przedmiotow:
            return {"sukces": False, "powod": "NPC ma pełny inwentarz"}
        
        cena_npc = npc.oblicz_cene_kupna(przedmiot, cena_rynkowa)
        
        finalna_cena = cena_npc
        zmiana_reputacji = 0
        
        if targowanie and hasattr(gracz, 'umiejetnosci'):
            umiejetnosc = gracz.umiejetnosci.get('handel', 0)
            # Gracz proponuje wyższą cenę
            propozycja = cena_npc * random.uniform(1.1, 1.3)
            
            sukces, finalna_cena, zmiana_reputacji = TradeSystem.targuj_sie(
                propozycja, cena_npc, npc, umiejetnosc
            )
        
        if npc.inwentarz.zloto >= finalna_cena:
            if npc.inwentarz.dodaj_przedmiot(przedmiot):
                if hasattr(gracz, 'zloto'):
                    gracz.zloto += int(finalna_cena)
                npc.inwentarz.zloto -= int(finalna_cena)
                npc.reputacja_gracza += zmiana_reputacji
                
                return {
                    "sukces": True,
                    "cena": finalna_cena,
                    "zmiana_reputacji": zmiana_reputacji
                }
        
        return {"sukces": False, "powod": "NPC nie ma środków"}


def create_sample_npcs(items_db: Dict[str, dict]) -> List[NPC]:
    """Tworzy przykładowych NPCów do systemu"""
    npcs = []
    
    # Kowal
    kowal = NPC(
        nazwa="Bjorn Żelazny",
        zawod="kowalstwo",
        reputacja_gracza=0,
        osobowosc=NPCPersonality.UCZCIWY,
        inwentarz=NPCInventory(zloto=200, max_przedmiotow=30),
        umiejetnosci={"kowalstwo": 60},
        produkcja={"kilof": 1, "lopata": 1, "mlotek": 1},
        konsumpcja={"metal": 3, "drewno": 2, "chleb": 1}
    )
    
    # Stolarz
    stolarz = NPC(
        nazwa="Erik Drewniak",
        zawod="stolarstwo", 
        reputacja_gracza=0,
        osobowosc=NPCPersonality.HOJNY,
        inwentarz=NPCInventory(zloto=150, max_przedmiotow=25),
        umiejetnosci={"stolarstwo": 55},
        produkcja={"luk": 1, "strzaly": 2, "maczuga": 1},
        konsumpcja={"drewno": 4, "metal": 1, "ser": 1}
    )
    
    # Kupiec żywności
    kupiec = NPC(
        nazwa="Helga Handlarka",
        zawod="handel",
        reputacja_gracza=0,
        osobowosc=NPCPersonality.ZACHŁANNY,
        inwentarz=NPCInventory(zloto=300, max_przedmiotow=40),
        umiejetnosci={"handel": 70},
        produkcja={"chleb": 3, "ser": 2},
        konsumpcja={"woda": 1, "mieso": 1}
    )
    
    # Myśliwy
    mysliwy = NPC(
        nazwa="Ragnar Łowca",
        zawod="polowanie",
        reputacja_gracza=0,
        osobowosc=NPCPersonality.SKĄPY,
        inwentarz=NPCInventory(zloto=120, max_przedmiotow=20),
        umiejetnosci={"polowanie": 65, "stolarstwo": 30},
        produkcja={"mieso": 2, "skora": 2},
        konsumpcja={"strzaly": 3, "chleb": 1, "woda": 1}
    )
    
    # Rolnik
    rolnik = NPC(
        nazwa="Olaf Ziemny",
        zawod="rolnictwo",
        reputacja_gracza=0,
        osobowosc=NPCPersonality.IMPULSYWNY,
        inwentarz=NPCInventory(zloto=80, max_przedmiotow=35),
        umiejetnosci={"rolnictwo": 50},
        produkcja={"jablko": 4, "tkanina": 1},
        konsumpcja={"lopata": 1, "woda": 2}
    )
    
    npcs.extend([kowal, stolarz, kupiec, mysliwy, rolnik])
    
    # Dodaj początkowe przedmioty do inwentarzy
    for npc in npcs:
        for item_id in list(items_db.keys()):
            if random.random() < 0.3:  # 30% szans na każdy przedmiot
                item_data = items_db[item_id]
                jakosc = random.randint(20, 80)
                
                przedmiot = Item(
                    id=item_id,
                    nazwa=item_data['nazwa'],
                    typ=item_data['typ'],
                    opis=item_data['opis'],
                    waga=item_data['waga'],
                    bazowa_wartosc=item_data['bazowa_wartosc'],
                    trwalosc=item_data['trwalosc'],
                    kategoria=item_data['kategoria'],
                    efekty=item_data['efekty'],
                    jakosc=jakosc
                )
                
                npc.inwentarz.dodaj_przedmiot(przedmiot)
    
    return npcs


def load_items_database(filepath: str) -> Dict[str, dict]:
    """Ładuje bazę danych przedmiotów"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


class Economy:
    """Główna klasa systemu ekonomicznego - wrapper dla Market i TradeSystem."""
    
    def __init__(self):
        """Inicjalizacja systemu ekonomicznego."""
        self.markets = {}  # market_id -> Market
        self.npcs = {}  # npc_id -> dict with NPC data
        self.trade_system = TradeSystem()
        
        # Dodaj atrybuty dla testów
        self.market_data = {}  # Dane rynkowe dla testów
        self.economic_events = []  # Lista wydarzeń ekonomicznych
        
        # Utwórz główny rynek więzienia
        self.markets['prison'] = Market("Więzienny Czarny Rynek", "dziedziniec")
        
        # Inicjalizuj podstawowe dane rynkowe
        self._initialize_market_data()
    
    def _initialize_market_data(self):
        """Inicjalizuje podstawowe dane rynkowe."""
        basic_items = ['chleb', 'woda', 'mięso', 'ser', 'jabłko', 'metal', 'drewno']
        for item_id in basic_items:
            self.market_data[item_id] = {
                'base_price': 10 + random.randint(0, 20),
                'supply': random.randint(5, 20),
                'demand': random.randint(5, 20),
                'volatility': random.uniform(0.1, 0.3)
            }
    
    def generate_economic_event(self):
        """Generuje losowe wydarzenie ekonomiczne."""
        events = [
            "Przybył karawana kupców - ceny spadają o 10%",
            "Niedobór surowców - ceny rosną o 15%",
            "Święto więzienne - wzrost popytu na jedzenie",
            "Nowa dostawa broni - ceny broni spadają",
            "Korupcja strażników - czarny rynek kwitnie",
            "Inspekcja - handel ograniczony",
            "Bunt więźniów - chaos na rynku",
            "Przybycie przemytników - nowe towary dostępne"
        ]
        
        event = random.choice(events)
        self.economic_events.append({
            'description': event,
            'time': 0,  # Będzie ustawiony przez game_state
            'impact': random.uniform(-0.2, 0.2)  # Wpływ na ceny
        })
        
        # Zastosuj wpływ wydarzenia na ceny
        for item_id in self.market_data:
            if 'impact' in self.economic_events[-1]:
                impact = self.economic_events[-1]['impact']
                self.market_data[item_id]['base_price'] *= (1 + impact)
        
        return event
    
    def update(self, game_time: int = 1):
        """Aktualizuje system ekonomiczny.
        
        Args:
            game_time: Czas gry w minutach
        """
        # Aktualizuj rynki co godzinę
        if game_time % 60 == 0:
            for market_id, market in self.markets.items():
                # Symuluj aktywność rynku
                if hasattr(market, 'dane_rynkowe'):
                    for item_id, dane in market.dane_rynkowe.items():
                        # Niewielkie wahania podaży i popytu
                        if random.random() < 0.1:
                            dane.podaz = max(0, dane.podaz + random.randint(-2, 2))
                        if random.random() < 0.1:
                            dane.popyt = max(0, dane.popyt + random.randint(-2, 2))
    
    def add_npc(self, npc_id: str, profession: str, personality: str, starting_gold: int = 100):
        """Dodaj NPCa do systemu ekonomicznego.
        
        Args:
            npc_id: ID NPCa
            profession: Profesja (merchant, guard, prisoner, etc.)
            personality: Osobowość (normal, greedy, generous, etc.)
            starting_gold: Początkowe złoto
        """
        personality_map = {
            'normal': NPCPersonality.UCZCIWY,
            'greedy': NPCPersonality.ZACHŁANNY,
            'generous': NPCPersonality.HOJNY,
            'stingy': NPCPersonality.SKĄPY,
            'impulsive': NPCPersonality.IMPULSYWNY
        }
        
        npc_personality = personality_map.get(personality, NPCPersonality.UCZCIWY)
        
        self.npcs[npc_id] = {
            'profession': profession,
            'personality': npc_personality.value,  # Zapisz jako string, nie enum
            'gold': starting_gold,
            'inventory': {},
            'reputation': 0
        }
    
    def get_price(self, item_id: str, market_id: str = 'prison', base_price: Optional[int] = None) -> float:
        """Pobierz aktualną cenę przedmiotu na rynku.
        
        Args:
            item_id: ID przedmiotu
            market_id: ID rynku
            base_price: Bazowa cena (jeśli nie podano, użyj 10)
            
        Returns:
            Aktualna cena rynkowa
        """
        if market_id not in self.markets:
            return base_price or 10
        
        market = self.markets[market_id]
        return market.oblicz_cene_rynkowa(item_id, base_price or 10)
    
    def calculate_price(self, item_id: str, market_id: str, base_price: int) -> float:
        """Alias dla get_price dla kompatybilności."""
        return self.get_price(item_id, market_id, base_price)
    
    def execute_trade(self, seller_id: str, buyer_id: str, item_id: str, 
                     quantity: int = 1, agreed_price: Optional[int] = None) -> Dict:
        """Wykonaj transakcję między NPCami lub graczem.
        
        Args:
            seller_id: ID sprzedawcy
            buyer_id: ID kupującego
            item_id: ID przedmiotu
            quantity: Ilość
            agreed_price: Uzgodniona cena
            
        Returns:
            Słownik z wynikiem transakcji
        """
        # Sprawdź czy sprzedawca ma przedmiot
        if seller_id in self.npcs:
            seller = self.npcs[seller_id]
            if item_id not in seller['inventory'] or seller['inventory'][item_id]['quantity'] < quantity:
                return {'success': False, 'message': 'Sprzedawca nie ma przedmiotu'}
        
        # Sprawdź czy kupujący ma złoto
        if buyer_id in self.npcs:
            buyer = self.npcs[buyer_id]
            price = agreed_price or self.get_price(item_id)
            total_cost = price * quantity
            
            if buyer['gold'] < total_cost:
                return {'success': False, 'message': 'Kupujący nie ma wystarczająco złota'}
            
            # Wykonaj transakcję
            buyer['gold'] -= total_cost
            
            if seller_id in self.npcs:
                seller['gold'] += total_cost
                seller['inventory'][item_id]['quantity'] -= quantity
                if seller['inventory'][item_id]['quantity'] <= 0:
                    del seller['inventory'][item_id]
            
            if item_id not in buyer['inventory']:
                buyer['inventory'][item_id] = {'quantity': 0, 'quality': 50}
            buyer['inventory'][item_id]['quantity'] += quantity
            
            return {'success': True, 'message': f'Transakcja zakończona', 'price': total_cost}
        
        return {'success': False, 'message': 'Nieznany błąd transakcji'}
    
    def simulate_day(self):
        """Symuluj dzień handlu na wszystkich rynkach."""
        for market in self.markets.values():
            # Podstawowa symulacja - zmień ceny losowo
            for item_id in ['chleb', 'woda', 'mięso', 'metal', 'drewno']:
                if item_id not in market.dane_rynkowe:
                    market.dane_rynkowe[item_id] = MarketData(item_id=item_id, podaz=10, popyt=10)
                
                # Losowa zmiana podaży i popytu
                data = market.dane_rynkowe[item_id]
                data.podaz = max(1, data.podaz + random.randint(-5, 5))
                data.popyt = max(1, data.popyt + random.randint(-5, 5))
    
    def get_average_prices(self) -> Dict[str, float]:
        """Pobierz średnie ceny wszystkich przedmiotów.
        
        Returns:
            Słownik item_id -> średnia cena
        """
        prices = {}
        for item_id in ['chleb', 'woda', 'mięso', 'ser', 'jabłko']:
            prices[item_id] = self.get_price(item_id)
        return prices
    
    def save_state(self) -> Dict:
        """Zapisz stan ekonomii.
        
        Returns:
            Słownik ze stanem ekonomii
        """
        return {
            'npcs': self.npcs,
            'markets': {
                market_id: {
                    'name': market.nazwa,
                    'data': {
                        item_id: {
                            'supply': data.podaz,
                            'demand': data.popyt
                        }
                        for item_id, data in market.dane_rynkowe.items()
                    }
                }
                for market_id, market in self.markets.items()
            }
        }
    
    def load_state(self, data: Dict):
        """Wczytaj stan ekonomii.
        
        Args:
            data: Dane ekonomii
        """
        if 'npcs' in data:
            self.npcs = data['npcs']
        
        if 'markets' in data:
            for market_id, market_data in data['markets'].items():
                if market_id not in self.markets:
                    self.markets[market_id] = Market(market_data['name'])
                
                market = self.markets[market_id]
                for item_id, item_data in market_data.get('data', {}).items():
                    market.dane_rynkowe[item_id] = MarketData(
                        item_id,
                        item_data['supply'],
                        item_data['demand']
                    )
    
    def can_afford(self, buyer_id: str, amount: float) -> bool:
        """Sprawdź czy kupujący może sobie pozwolić na daną kwotę.
        
        Args:
            buyer_id: ID kupującego
            amount: Kwota do sprawdzenia
            
        Returns:
            True jeśli kupujący ma wystarczającą ilość złota
        """
        if buyer_id in self.npcs:
            return self.npcs[buyer_id]['gold'] >= amount
        return False


class EnhancedEconomy(Economy):
    """Rozszerzona klasa systemu ekonomicznego z pełną funkcjonalnością"""
    
    def __init__(self):
        super().__init__()
        
        # Import rozszerzonych modułów
        try:
            from .economic_events import EconomicEventManager
            from .production_chains import ProductionChainManager
            from .merchant_ai import MerchantAI
            self.event_manager = EconomicEventManager()
            self.production_manager = ProductionChainManager()
            self.merchant_ais = {}  # merchant_id -> MerchantAI
        except ImportError:
            # Fallback jeśli moduły nie są dostępne
            self.event_manager = None
            self.production_manager = None
            self.merchant_ais = {}
        
        # Rozszerzone dane
        self.seasonal_modifiers = {}
        self.market_events = []
        self.production_nodes = {}  # location_id -> resource_node
        
        # Statystyki ekonomiczne
        self.economic_indicators = {
            'inflation_rate': 0.02,  # 2% rocznie
            'unemployment_rate': 0.1,
            'gdp_growth': 0.03,
            'market_stability': 0.8
        }
    
    def add_merchant_ai(self, npc_id: str, name: str, personality: str = "neutral"):
        """Dodaje AI handlarza"""
        if self.merchant_ais is not None:
            try:
                from .merchant_ai import MerchantAI
                merchant_ai = MerchantAI(npc_id, name, personality)
                self.merchant_ais[npc_id] = merchant_ai
                
                # Dodaj też do podstawowego systemu NPCów
                self.add_npc(npc_id, "merchant", personality, 200)
            except ImportError:
                print(f"Warning: Cannot create MerchantAI for {npc_id} - module not available")
    
    def get_enhanced_price(self, item_id: str, market_id: str = 'prison', 
                          base_price: Optional[int] = None, npc_id: Optional[str] = None,
                          player_id: Optional[str] = None) -> float:
        """Pobiera cenę z uwzględnieniem wydarzeń ekonomicznych i AI handlarza"""
        base_price = base_price or 10
        
        # Bazowa cena rynkowa
        market_price = self.get_price(item_id, market_id, base_price)
        
        # Modyfikacja przez wydarzenia ekonomiczne
        if self.event_manager:
            event_modifier = self.event_manager.get_price_modifier_for_item(item_id)
            market_price *= event_modifier
        
        # Modyfikacja przez sezon
        seasonal_modifier = self.seasonal_modifiers.get(item_id, 1.0)
        market_price *= seasonal_modifier
        
        # Jeśli podano NPC i gracza, uwzględnij AI handlarza
        if npc_id and player_id and npc_id in self.merchant_ais:
            merchant_ai = self.merchant_ais[npc_id]
            market_data = {
                'category': self._get_item_category(item_id),
                'current_stock': self._get_npc_stock(npc_id, item_id),
                'optimal_stock': 10,
                'demand_factor': self._calculate_demand_factor(item_id),
                'competition_factor': self._calculate_competition_factor(item_id)
            }
            
            ai_price = merchant_ai.calculate_selling_price(item_id, base_price, player_id, market_data)
            return ai_price
        
        return market_price
    
    def negotiate_price(self, npc_id: str, player_id: str, item_id: str, 
                       offered_price: float, current_price: float, is_buying: bool = True) -> Dict[str, Any]:
        """Negocjuje cenę z AI handlarzem"""
        if npc_id not in self.merchant_ais:
            return {
                'success': False,
                'final_price': current_price,
                'reason': 'NPC nie obsługuje negocjacji',
                'reputation_change': 0
            }
        
        merchant_ai = self.merchant_ais[npc_id]
        return merchant_ai.negotiate(player_id, item_id, offered_price, current_price, is_buying)
    
    def process_enhanced_trade(self, seller_id: str, buyer_id: str, item_id: str,
                              quantity: int = 1, negotiated: bool = False) -> Dict[str, Any]:
        """Wykonuje transakcję z pełną funkcjonalnością AI"""
        # Pobierz cenę z uwzględnieniem wszystkich czynników
        base_price = 10  # Domyślna
        
        if seller_id == 'player':
            # Gracz sprzedaje NPCowi
            if buyer_id in self.merchant_ais:
                merchant_ai = self.merchant_ais[buyer_id]
                market_data = {
                    'category': self._get_item_category(item_id),
                    'current_stock': self._get_npc_stock(buyer_id, item_id),
                    'optimal_stock': 10
                }
                
                price_per_unit = merchant_ai.calculate_buying_price(item_id, base_price, seller_id, market_data)
                total_price = price_per_unit * quantity
                
                # Wykonaj transakcję przez AI
                merchant_ai.process_transaction(seller_id, item_id, quantity, total_price, "purchase")
                
                return {
                    'success': True,
                    'message': f'Sprzedano {quantity}x {item_id} za {total_price:.2f} zł',
                    'price': total_price,
                    'price_per_unit': price_per_unit
                }
        
        elif buyer_id == 'player':
            # Gracz kupuje od NPCa
            if seller_id in self.merchant_ais:
                merchant_ai = self.merchant_ais[seller_id]
                market_data = {
                    'category': self._get_item_category(item_id),
                    'current_stock': self._get_npc_stock(seller_id, item_id),
                    'optimal_stock': 10
                }
                
                price_per_unit = merchant_ai.calculate_selling_price(item_id, base_price, buyer_id, market_data)
                total_price = price_per_unit * quantity
                
                # Wykonaj transakcję przez AI
                merchant_ai.process_transaction(buyer_id, item_id, quantity, total_price, "sale")
                
                return {
                    'success': True,
                    'message': f'Kupiono {quantity}x {item_id} za {total_price:.2f} zł',
                    'price': total_price,
                    'price_per_unit': price_per_unit
                }
        
        # Fallback do standardowej transakcji
        return self.execute_trade(seller_id, buyer_id, item_id, quantity)
    
    def update_enhanced(self, game_time: int = 1):
        """Rozszerzona aktualizacja systemu"""
        # Standardowa aktualizacja
        self.update(game_time)
        
        # Aktualizacja wydarzeń ekonomicznych
        if self.event_manager:
            market_data = {
                'total_npcs': len(self.npcs),
                'markets': list(self.markets.keys())
            }
            self.event_manager.update(game_time, market_data)
        
        # Aktualizacja AI handlarzy co godzinę
        if game_time % 60 == 0:
            for merchant_ai in self.merchant_ais.values():
                merchant_ai.update_mood(game_time)
        
        # Resetowanie dzienne (zakładając że dzień = 1440 minut)
        if game_time % 1440 == 0:
            self._daily_reset()
    
    def _daily_reset(self):
        """Codzienny reset systemu"""
        # Reset AI handlarzy
        for merchant_ai in self.merchant_ais.values():
            merchant_ai.daily_reset()
        
        # Aktualizuj sezonowe modyfikatory
        self._update_seasonal_modifiers()
        
        # Aktualizuj wskaźniki ekonomiczne
        self._update_economic_indicators()
    
    def _update_seasonal_modifiers(self):
        """Aktualizuje sezonowe modyfikatory cen"""
        # Przykład: jesienią jabłka są tańsze, drewno droższe
        season = self._get_current_season()
        
        if season == 'autumn':
            self.seasonal_modifiers = {
                'jablko': 0.7,
                'drewno': 1.2,
                'mieso': 0.9,
                'skora': 1.1
            }
        elif season == 'winter':
            self.seasonal_modifiers = {
                'drewno': 1.3,
                'mieso': 1.2,
                'tkanina': 1.1,
                'jablko': 1.4
            }
        elif season == 'spring':
            self.seasonal_modifiers = {
                'jablko': 1.1,
                'drewno': 0.9,
                'woda': 0.8
            }
        else:  # summer
            self.seasonal_modifiers = {
                'woda': 1.2,
                'mieso': 1.1,
                'ser': 0.9
            }
    
    def _get_current_season(self) -> str:
        """Określa aktualną porę roku"""
        # Uproszczona logika - można rozszerzyć
        import time
        month = time.localtime().tm_mon
        
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    def _update_economic_indicators(self):
        """Aktualizuje wskaźniki ekonomiczne"""
        # Symulacja inflacji
        self.economic_indicators['inflation_rate'] += random.uniform(-0.005, 0.005)
        self.economic_indicators['inflation_rate'] = max(0.0, min(0.1, self.economic_indicators['inflation_rate']))
        
        # Stabilność rynku
        num_events = len(self.event_manager.get_active_events()) if self.event_manager else 0
        event_impact = num_events * 0.1
        self.economic_indicators['market_stability'] = max(0.2, min(1.0, 0.8 - event_impact + random.uniform(-0.05, 0.05)))
    
    def _get_item_category(self, item_id: str) -> str:
        """Określa kategorię przedmiotu"""
        # Mapowanie przedmiotów na kategorie
        categories = {
            'miecz': 'weapons',
            'noz': 'weapons',
            'luk': 'weapons',
            'maczuga': 'weapons',
            'kilof': 'tools',
            'lopata': 'tools',
            'mlotek': 'tools',
            'dluto': 'tools',
            'igla': 'tools',
            'chleb': 'food',
            'mieso': 'food',
            'ser': 'food',
            'jablko': 'food',
            'woda': 'food',
            'metal': 'materials',
            'drewno': 'materials',
            'skora': 'materials',
            'tkanina': 'materials',
            'kamien': 'materials'
        }
        
        return categories.get(item_id, 'misc')
    
    def _get_npc_stock(self, npc_id: str, item_id: str) -> int:
        """Pobiera zapas przedmiotu u NPCa"""
        if npc_id in self.npcs:
            inventory = self.npcs[npc_id].get('inventory', {})
            return inventory.get(item_id, {}).get('quantity', 0)
        return 0
    
    def _calculate_demand_factor(self, item_id: str) -> float:
        """Oblicza czynnik popytu"""
        # Uproszczony czynnik popytu
        if self.event_manager:
            demand_change = self.event_manager.get_demand_change_for_item(item_id)
            return 1.0 + (demand_change / 20.0)  # Normalizacja
        return 1.0
    
    def _calculate_competition_factor(self, item_id: str) -> float:
        """Oblicza czynnik konkurencji"""
        # Liczba handlarzy sprzedających ten przedmiot
        sellers = 0
        for npc_id, npc_data in self.npcs.items():
            if item_id in npc_data.get('inventory', {}):
                sellers += 1
        
        if sellers == 0:
            return 1.5  # Brak konkurencji = wyższe ceny
        elif sellers == 1:
            return 1.0  # Normalny
        else:
            return max(0.7, 1.0 - (sellers - 1) * 0.1)  # Więcej konkurencji = niższe ceny
    
    def get_merchant_attitude(self, npc_id: str, player_id: str) -> Dict[str, Any]:
        """Pobiera stosunek handlarza do gracza"""
        if npc_id in self.merchant_ais:
            return self.merchant_ais[npc_id].get_attitude_towards_player(player_id)
        
        # Fallback dla zwykłych NPCów
        return {
            "attitude": "Neutralny",
            "customer_tier": "New",
            "reputation": 0,
            "total_spent": 0,
            "has_grudge": False,
            "has_favor": False
        }
    
    def get_active_events(self) -> List[str]:
        """Pobiera opisy aktywnych wydarzeń ekonomicznych"""
        if self.event_manager:
            return self.event_manager.get_event_descriptions()
        return []
    
    def get_production_chains(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Pobiera dostępne łańcuchy produkcji"""
        if not self.production_manager:
            return []
        
        if category:
            chains = self.production_manager.get_chains_by_category(category)
        else:
            chains = list(self.production_manager.chains.values())
        
        result = []
        for chain in chains:
            result.append({
                'id': chain.id,
                'name': chain.nazwa,
                'description': chain.opis,
                'category': chain.kategoria,
                'difficulty': chain.poziom_zaawansowania,
                'final_product': chain.produkt_koncowy,
                'steps': len(chain.kroki),
                'total_time': chain.oblicz_calkowity_czas(),
                'required_skills': chain.get_wszystkie_umiejetnosci()
            })
        
        return result
    
    def simulate_production(self, chain_id: str, player_skills: Dict[str, int], 
                          tool_qualities: Dict[str, int] = None) -> Dict[str, Any]:
        """Symuluje proces produkcji"""
        if not self.production_manager:
            return {'success': False, 'message': 'System produkcji niedostępny'}
        
        tool_qualities = tool_qualities or {}
        return self.production_manager.simulate_production(chain_id, player_skills, tool_qualities)
    
    def save_enhanced_state(self) -> Dict[str, Any]:
        """Zapisuje rozszerzony stan ekonomii"""
        base_state = self.save_state()
        
        enhanced_state = {
            **base_state,
            'economic_indicators': self.economic_indicators,
            'seasonal_modifiers': self.seasonal_modifiers,
            'merchant_ais': {
                npc_id: merchant_ai.save_state()
                for npc_id, merchant_ai in self.merchant_ais.items()
            }
        }
        
        if self.event_manager:
            enhanced_state['events'] = self.event_manager.save_state()
        
        return enhanced_state
    
    def load_enhanced_state(self, data: Dict[str, Any]):
        """Wczytuje rozszerzony stan ekonomii"""
        # Wczytaj podstawowy stan
        self.load_state(data)
        
        # Wczytaj rozszerzone dane
        self.economic_indicators = data.get('economic_indicators', self.economic_indicators)
        self.seasonal_modifiers = data.get('seasonal_modifiers', {})
        
        # Wczytaj AI handlarzy
        if 'merchant_ais' in data:
            try:
                from .merchant_ai import MerchantAI
                for npc_id, ai_data in data['merchant_ais'].items():
                    merchant_ai = MerchantAI(npc_id, ai_data['name'], ai_data['personality'])
                    merchant_ai.load_state(ai_data)
                    self.merchant_ais[npc_id] = merchant_ai
            except ImportError:
                print("Warning: MerchantAI not available for loading")
        
        # Wczytaj wydarzenia
        if 'events' in data and self.event_manager:
            self.event_manager.load_state(data['events'])


if __name__ == "__main__":
    # Test rozszerzonego systemu ekonomii
    print("=== TEST ROZSZERZONEGO SYSTEMU EKONOMII ===")
    
    economy = EnhancedEconomy()
    
    # Dodaj handlarzy AI
    economy.add_merchant_ai("bjorn", "Bjorn Żelazny", "greedy")
    economy.add_merchant_ai("helga", "Helga Handlarka", "generous")
    
    print(f"Dodano {len(economy.merchant_ais)} handlarzy AI")
    
    # Test cen z AI
    base_price = 50
    ai_price = economy.get_enhanced_price("miecz", "prison", base_price, "bjorn", "player1")
    print(f"Cena miecza (AI): {ai_price:.2f} zł (bazowa: {base_price} zł)")
    
    # Test negocjacji
    negotiation = economy.negotiate_price("bjorn", "player1", "miecz", 40.0, ai_price, False)
    print(f"Negocjacja: {'Sukces' if negotiation['success'] else 'Porażka'}")
    print(f"Finalna cena: {negotiation['final_price']:.2f} zł")
    print(f"Odpowiedź: {negotiation['reason']}")
    
    # Test transakcji
    trade_result = economy.process_enhanced_trade("bjorn", "player", "miecz", 1)
    print(f"Transakcja: {trade_result['message']}")
    
    # Sprawdź stosunek handlarza
    attitude = economy.get_merchant_attitude("bjorn", "player1")
    print(f"Stosunek Bjorna: {attitude['attitude']} ({attitude['customer_tier']})")
    
    # Pokaż aktywne wydarzenia
    events = economy.get_active_events()
    if events:
        print(f"\nAktywne wydarzenia:")
        for event in events:
            print(f"- {event}")
    else:
        print("\nBrak aktywnych wydarzeń ekonomicznych")
    
    # Pokaż dostępne łańcuchy produkcji
    chains = economy.get_production_chains("weapons")
    print(f"\nŁańcuchy produkcji broni ({len(chains)}):")
    for chain in chains[:3]:  # Pokaż pierwsze 3
        print(f"- {chain['name']}: {chain['steps']} kroków, {chain['total_time']} minut")
    
    print("\n=== SYMULACJA KILKU DNI ===")
    for day in range(1, 4):
        print(f"\nDzień {day}:")
        economy.update_enhanced(day * 1440)  # Symuluj pełne dni
        
        # Pokaż zmienione ceny
        new_price = economy.get_enhanced_price("miecz", "prison", 50, "bjorn", "player1")
        print(f"Nowa cena miecza: {new_price:.2f} zł")
        
        # Pokaż wskaźniki ekonomiczne
        indicators = economy.economic_indicators
        print(f"Stabilność rynku: {indicators['market_stability']:.2%}")
        print(f"Inflacja: {indicators['inflation_rate']:.2%}")


