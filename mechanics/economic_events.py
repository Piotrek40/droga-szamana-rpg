"""
System wydarzeń ekonomicznych dla Droga Szamana RPG
Implementuje dynamiczne wydarzenia wpływające na gospodarkę
"""

import random
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    """Typy wydarzeń ekonomicznych"""
    KRACH_RYNKOWY = "krach_rynkowy"
    NIEDOBOR_ZASOBOW = "niedobor_zasobow"
    KARAWANA_HANDLOWA = "karawana_handlowa"
    ZMIANA_SEZONOWA = "zmiana_sezonowa"
    EPIDEMIA = "epidemia"
    ODKRYCIE_ZASOBU = "odkrycie_zasobu"
    WOJNA_CENY = "wojna_ceny"
    STRAJK_PRODUCENTOW = "strajk_producentow"
    POŻAR_SKLADOW = "pozar_skladow"
    FESTIWAL_HANDLOWY = "festiwal_handlowy"
    EMBARGO = "embargo"
    NOWA_TECHNOLOGIA = "nowa_technologia"


@dataclass
class EconomicEvent:
    """Wydarzenie ekonomiczne"""
    id: str
    typ: EventType
    nazwa: str
    opis: str
    czas_trwania: int  # w minutach gry
    wplyw_na_ceny: Dict[str, float]  # item_id -> mnożnik ceny
    wplyw_na_podaz: Dict[str, int]  # item_id -> zmiana podaży
    wplyw_na_popyt: Dict[str, int]  # item_id -> zmiana popytu
    czas_rozpoczecia: int
    aktywne: bool = True
    prawdopodobienstwo: float = 0.1  # szansa na wystąpienie na dzień
    wymagania: Dict[str, Any] = field(default_factory=dict)  # warunki wystąpienia
    
    def is_expired(self, current_time: int) -> bool:
        """Sprawdza czy wydarzenie wygasło"""
        return current_time >= self.czas_rozpoczecia + self.czas_trwania
    
    def get_price_modifier(self, item_id: str) -> float:
        """Zwraca modyfikator ceny dla przedmiotu"""
        return self.wplyw_na_ceny.get(item_id, 1.0)
    
    def get_supply_change(self, item_id: str) -> int:
        """Zwraca zmianę podaży dla przedmiotu"""
        return self.wplyw_na_podaz.get(item_id, 0)
    
    def get_demand_change(self, item_id: str) -> int:
        """Zwraca zmianę popytu dla przedmiotu"""
        return self.wplyw_na_popyt.get(item_id, 0)


class EconomicEventManager:
    """Manager wydarzeń ekonomicznych"""
    
    def __init__(self):
        self.aktywne_wydarzenia = {}  # event_id -> EconomicEvent
        self.szablony_wydarzen = self._create_event_templates()
        self.ostatnia_aktualizacja = 0
        self.historia_wydarzen = []  # Ostatnie 50 wydarzeń
    
    def _create_event_templates(self) -> Dict[str, EconomicEvent]:
        """Tworzy szablony wydarzeń ekonomicznych"""
        szablony = {}
        
        # Krach rynkowy - wszystkie ceny spadają
        szablony['krach_rynkowy'] = EconomicEvent(
            id='krach_rynkowy',
            typ=EventType.KRACH_RYNKOWY,
            nazwa="Krach Rynkowy",
            opis="Panika wśród handlarzy powoduje gwałtowny spadek cen wszystkich towarów.",
            czas_trwania=480,  # 8 godzin
            wplyw_na_ceny={
                'all': 0.6  # Wszystkie ceny spadają do 60%
            },
            wplyw_na_podaz={},
            wplyw_na_popyt={},
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.05
        )
        
        # Niedobór metalu
        szablony['niedobor_metalu'] = EconomicEvent(
            id='niedobor_metalu',
            typ=EventType.NIEDOBOR_ZASOBOW,
            nazwa="Niedobór Metalu",
            opis="Problemy z dostawami metalu powodują wzrost cen metalowych przedmiotów.",
            czas_trwania=720,  # 12 godzin
            wplyw_na_ceny={
                'metal': 2.5,
                'miecz': 1.8,
                'kilof': 1.7,
                'mlotek': 1.6,
                'lopata': 1.5
            },
            wplyw_na_podaz={
                'metal': -5
            },
            wplyw_na_popyt={
                'metal': 8
            },
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.15
        )
        
        # Karawana handlowa
        szablony['karawana_przybyla'] = EconomicEvent(
            id='karawana_przybyla',
            typ=EventType.KARAWANA_HANDLOWA,
            nazwa="Przybycie Karawany",
            opis="Karawana przywiozła egzotyczne towary i luksusowe przedmioty.",
            czas_trwania=180,  # 3 godziny
            wplyw_na_ceny={
                'ser': 0.7,
                'jablko': 0.6,
                'tkanina': 0.8,
                'woda': 0.9
            },
            wplyw_na_podaz={
                'ser': 10,
                'jablko': 15,
                'tkanina': 8,
                'woda': 12
            },
            wplyw_na_popyt={},
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.2
        )
        
        # Zmiana sezonowa - jesień
        szablony['sezon_jesienni'] = EconomicEvent(
            id='sezon_jesienni',
            typ=EventType.ZMIANA_SEZONOWA,
            nazwa="Sezon Jesienny",
            opis="Jesienne zbiory wpływają na ceny żywności i materiałów.",
            czas_trwania=2160,  # 36 godzin (długotrwałe)
            wplyw_na_ceny={
                'jablko': 0.5,  # Tanie jabłka po zbiorach
                'drewno': 1.2,  # Droższe drewno przed zimą
                'skora': 1.3,   # Sezon polowań
                'mieso': 0.8
            },
            wplyw_na_podaz={
                'jablko': 20,
                'mieso': 5,
                'skora': 8
            },
            wplyw_na_popyt={
                'drewno': 12
            },
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.3
        )
        
        # Epidemia
        szablony['epidemia'] = EconomicEvent(
            id='epidemia',
            typ=EventType.EPIDEMIA,
            nazwa="Epidemia Choroby",
            opis="Choroba ogranicza produkcję i zwiększa popyt na leki i żywność.",
            czas_trwania=960,  # 16 godzin
            wplyw_na_ceny={
                'mieso': 1.5,
                'chleb': 1.4,
                'ser': 1.3,
                'woda': 1.6
            },
            wplyw_na_podaz={
                'all': -3  # Ogólnie mniej produkuje się
            },
            wplyw_na_popyt={
                'mieso': 8,
                'chleb': 10,
                'woda': 15
            },
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.08
        )
        
        # Odkrycie nowego źródła drewna
        szablony['odkrycie_lasu'] = EconomicEvent(
            id='odkrycie_lasu',
            typ=EventType.ODKRYCIE_ZASOBU,
            nazwa="Odkrycie Nowego Lasu",
            opis="Znaleziono nowe źródło wysokiej jakości drewna.",
            czas_trwania=1440,  # 24 godziny
            wplyw_na_ceny={
                'drewno': 0.7,
                'luk': 0.8,
                'maczuga': 0.75,
                'strzaly': 0.85
            },
            wplyw_na_podaz={
                'drewno': 25
            },
            wplyw_na_popyt={
                'drewno': -5
            },
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.12
        )
        
        # Wojna cenowa między kupcami
        szablony['wojna_ceny'] = EconomicEvent(
            id='wojna_ceny',
            typ=EventType.WOJNA_CENY,
            nazwa="Wojna Cenowa",
            opis="Kupcy konkurują ze sobą, obniżając drastycznie ceny.",
            czas_trwania=360,  # 6 godzin
            wplyw_na_ceny={
                'chleb': 0.4,
                'ser': 0.5,
                'mieso': 0.6,
                'woda': 0.3
            },
            wplyw_na_podaz={},
            wplyw_na_popyt={
                'chleb': 20,
                'ser': 15,
                'mieso': 18,
                'woda': 25
            },
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.15
        )
        
        # Strajk kowalów
        szablony['strajk_kowali'] = EconomicEvent(
            id='strajk_kowali',
            typ=EventType.STRAJK_PRODUCENTOW,
            nazwa="Strajk Kowalów",
            opis="Kowale protestują przeciwko niskim cenom, wstrzymując produkcję.",
            czas_trwania=480,  # 8 godzin
            wplyw_na_ceny={
                'miecz': 1.8,
                'kilof': 1.6,
                'mlotek': 1.7,
                'lopata': 1.5,
                'noz': 1.4
            },
            wplyw_na_podaz={
                'miecz': -8,
                'kilof': -6,
                'mlotek': -5,
                'lopata': -4,
                'noz': -3
            },
            wplyw_na_popyt={},
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.1
        )
        
        # Pożar składów
        szablony['pozar_skladow'] = EconomicEvent(
            id='pozar_skladow',
            typ=EventType.POŻAR_SKLADOW,
            nazwa="Pożar Składów",
            opis="Pożar zniszczył duże zapasy towarów, powodując niedobory.",
            czas_trwania=600,  # 10 godzin
            wplyw_na_ceny={
                'tkanina': 2.0,
                'skora': 1.8,
                'drewno': 1.6
            },
            wplyw_na_podaz={
                'tkanina': -15,
                'skora': -12,
                'drewno': -10
            },
            wplyw_na_popyt={
                'tkanina': 10,
                'skora': 8,
                'drewno': 12
            },
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.06
        )
        
        # Festiwal handlowy
        szablony['festiwal_handlowy'] = EconomicEvent(
            id='festiwal_handlowy',
            typ=EventType.FESTIWAL_HANDLOWY,
            nazwa="Festiwal Handlowy",
            opis="Wielki festiwal przyciąga handlarzy i zwiększa obroty.",
            czas_trwania=720,  # 12 godzin
            wplyw_na_ceny={
                'all': 0.9  # Lekki spadek cen przez konkurencję
            },
            wplyw_na_podaz={
                'all': 15  # Więcej towarów dostępnych
            },
            wplyw_na_popyt={
                'all': 10  # Więcej kupujących
            },
            czas_rozpoczecia=0,
            prawdopodobienstwo=0.25
        )
        
        return szablony
    
    def update(self, current_time: int, market_data: Dict[str, Any]):
        """Aktualizuje manager wydarzeń"""
        # Usuń wygasłe wydarzenia
        self._remove_expired_events(current_time)
        
        # Co godzinę sprawdź możliwość nowych wydarzeń
        if current_time - self.ostatnia_aktualizacja >= 60:  # Co godzinę
            self._check_new_events(current_time, market_data)
            self.ostatnia_aktualizacja = current_time
    
    def _remove_expired_events(self, current_time: int):
        """Usuwa wygasłe wydarzenia"""
        wygasle = []
        for event_id, event in self.aktywne_wydarzenia.items():
            if event.is_expired(current_time):
                wygasle.append(event_id)
                self.historia_wydarzen.append({
                    'event': event,
                    'czas_zakonczenia': current_time
                })
        
        for event_id in wygasle:
            del self.aktywne_wydarzenia[event_id]
        
        # Ogranicz historię do 50 wydarzeń
        if len(self.historia_wydarzen) > 50:
            self.historia_wydarzen = self.historia_wydarzen[-50:]
    
    def _check_new_events(self, current_time: int, market_data: Dict[str, Any]):
        """Sprawdza możliwość wystąpienia nowych wydarzeń"""
        for template_id, template in self.szablony_wydarzen.items():
            # Sprawdź czy wydarzenie już trwa
            if template_id in self.aktywne_wydarzenia:
                continue
            
            # Sprawdź prawdopodobieństwo
            if random.random() > template.prawdopodobienstwo:
                continue
            
            # Sprawdź wymagania
            if not self._check_requirements(template, market_data):
                continue
            
            # Stwórz nowe wydarzenie
            nowe_wydarzenie = EconomicEvent(
                id=f"{template_id}_{current_time}",
                typ=template.typ,
                nazwa=template.nazwa,
                opis=template.opis,
                czas_trwania=template.czas_trwania,
                wplyw_na_ceny=template.wplyw_na_ceny.copy(),
                wplyw_na_podaz=template.wplyw_na_podaz.copy(),
                wplyw_na_popyt=template.wplyw_na_popyt.copy(),
                czas_rozpoczecia=current_time,
                prawdopodobienstwo=template.prawdopodobienstwo
            )
            
            self.aktywne_wydarzenia[nowe_wydarzenie.id] = nowe_wydarzenie
            
            # Ogranicz liczbę równoczesnych wydarzeń
            if len(self.aktywne_wydarzenia) >= 3:
                break
    
    def _check_requirements(self, template: EconomicEvent, market_data: Dict[str, Any]) -> bool:
        """Sprawdza czy spełnione są wymagania dla wydarzenia"""
        # Na razie proste - wszystkie wydarzenia mogą wystąpić
        # Tutaj można dodać logikę sprawdzającą stan rynku, zapasy itp.
        return True
    
    def get_price_modifier_for_item(self, item_id: str) -> float:
        """Oblicza łączny modyfikator ceny dla przedmiotu"""
        total_modifier = 1.0
        
        for event in self.aktywne_wydarzenia.values():
            # Sprawdź modyfikator specyficzny dla przedmiotu
            if item_id in event.wplyw_na_ceny:
                total_modifier *= event.wplyw_na_ceny[item_id]
            # Sprawdź modyfikator globalny
            elif 'all' in event.wplyw_na_ceny:
                total_modifier *= event.wplyw_na_ceny['all']
        
        return total_modifier
    
    def get_supply_change_for_item(self, item_id: str) -> int:
        """Oblicza łączną zmianę podaży dla przedmiotu"""
        total_change = 0
        
        for event in self.aktywne_wydarzenia.values():
            # Sprawdź zmianę specyficzną dla przedmiotu
            if item_id in event.wplyw_na_podaz:
                total_change += event.wplyw_na_podaz[item_id]
            # Sprawdź zmianę globalną
            elif 'all' in event.wplyw_na_podaz:
                total_change += event.wplyw_na_podaz['all']
        
        return total_change
    
    def get_demand_change_for_item(self, item_id: str) -> int:
        """Oblicza łączną zmianę popytu dla przedmiotu"""
        total_change = 0
        
        for event in self.aktywne_wydarzenia.values():
            # Sprawdź zmianę specyficzną dla przedmiotu
            if item_id in event.wplyw_na_popyt:
                total_change += event.wplyw_na_popyt[item_id]
            # Sprawdź zmianę globalną
            elif 'all' in event.wplyw_na_popyt:
                total_change += event.wplyw_na_popyt['all']
        
        return total_change
    
    def get_active_events(self) -> List[EconomicEvent]:
        """Zwraca listę aktywnych wydarzeń"""
        return list(self.aktywne_wydarzenia.values())
    
    def get_event_descriptions(self) -> List[str]:
        """Zwraca opisy aktywnych wydarzeń"""
        return [f"{event.nazwa}: {event.opis}" for event in self.aktywne_wydarzenia.values()]
    
    def force_event(self, template_id: str, current_time: int) -> bool:
        """Wymusza wystąpienie wydarzenia (do testów)"""
        if template_id not in self.szablony_wydarzen:
            return False
        
        template = self.szablony_wydarzen[template_id]
        
        nowe_wydarzenie = EconomicEvent(
            id=f"{template_id}_{current_time}",
            typ=template.typ,
            nazwa=template.nazwa,
            opis=template.opis,
            czas_trwania=template.czas_trwania,
            wplyw_na_ceny=template.wplyw_na_ceny.copy(),
            wplyw_na_podaz=template.wplyw_na_podaz.copy(),
            wplyw_na_popyt=template.wplyw_na_popyt.copy(),
            czas_rozpoczecia=current_time
        )
        
        self.aktywne_wydarzenia[nowe_wydarzenie.id] = nowe_wydarzenie
        return True
    
    def save_state(self) -> Dict[str, Any]:
        """Zapisuje stan managera wydarzeń"""
        return {
            'aktywne_wydarzenia': {
                event_id: {
                    'id': event.id,
                    'typ': event.typ.value,
                    'nazwa': event.nazwa,
                    'opis': event.opis,
                    'czas_trwania': event.czas_trwania,
                    'wplyw_na_ceny': event.wplyw_na_ceny,
                    'wplyw_na_podaz': event.wplyw_na_podaz,
                    'wplyw_na_popyt': event.wplyw_na_popyt,
                    'czas_rozpoczecia': event.czas_rozpoczecia,
                    'aktywne': event.aktywne
                }
                for event_id, event in self.aktywne_wydarzenia.items()
            },
            'ostatnia_aktualizacja': self.ostatnia_aktualizacja
        }
    
    def load_state(self, data: Dict[str, Any]):
        """Wczytuje stan managera wydarzeń"""
        self.ostatnia_aktualizacja = data.get('ostatnia_aktualizacja', 0)
        
        for event_id, event_data in data.get('aktywne_wydarzenia', {}).items():
            event = EconomicEvent(
                id=event_data['id'],
                typ=EventType(event_data['typ']),
                nazwa=event_data['nazwa'],
                opis=event_data['opis'],
                czas_trwania=event_data['czas_trwania'],
                wplyw_na_ceny=event_data['wplyw_na_ceny'],
                wplyw_na_podaz=event_data['wplyw_na_podaz'],
                wplyw_na_popyt=event_data['wplyw_na_popyt'],
                czas_rozpoczecia=event_data['czas_rozpoczecia'],
                aktywne=event_data.get('aktywne', True)
            )
            self.aktywne_wydarzenia[event_id] = event


if __name__ == "__main__":
    # Test systemu wydarzeń
    manager = EconomicEventManager()
    
    print("=== TEST SYSTEMU WYDARZEŃ EKONOMICZNYCH ===")
    
    # Wymuś kilka wydarzeń
    current_time = int(time.time())
    manager.force_event('niedobor_metalu', current_time)
    manager.force_event('karawana_przybyla', current_time)
    
    print(f"Aktywne wydarzenia: {len(manager.get_active_events())}")
    for opis in manager.get_event_descriptions():
        print(f"- {opis}")
    
    # Test modyfikatorów
    print(f"\nModyfikator ceny metalu: {manager.get_price_modifier_for_item('metal'):.2f}")
    print(f"Modyfikator ceny sera: {manager.get_price_modifier_for_item('ser'):.2f}")
    print(f"Zmiana podaży metalu: {manager.get_supply_change_for_item('metal')}")
    print(f"Zmiana popytu na metal: {manager.get_demand_change_for_item('metal')}")
    
    # Test wygasania
    print(f"\nTest po czasie...")
    future_time = current_time + 200  # 3+ godzin później
    manager.update(future_time, {})
    print(f"Aktywne wydarzenia po czasie: {len(manager.get_active_events())}")