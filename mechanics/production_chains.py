"""
System łańcuchów produkcji dla Droga Szamana RPG
Implementuje realistyczne łańcuchy od surowców do gotowych produktów
"""

import json
import random
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class ResourceType(Enum):
    """Typy zasobów w łańcuchu produkcji"""
    SUROWIEC_PIERWOTNY = "surowiec_pierwotny"  # Ruda, drewno surowe
    SUROWIEC_PRZETWORZONY = "surowiec_przetworzony"  # Żelazo, deski
    KOMPONENET = "komponent"  # Części, elementy
    PRODUKT_GOTOWY = "produkt_gotowy"  # Broń, narzędzia
    PRODUKT_ZLOZONY = "produkt_zlozony"  # Zbroje, maszyny


@dataclass
class ResourceQuality:
    """System jakości surowców i produktów"""
    wartosc: int  # 1-100
    nazwa: str = ""
    mnoznik_ceny: float = 1.0
    mnoznik_wydajnosci: float = 1.0
    mnoznik_trwalosci: float = 1.0
    
    def __post_init__(self):
        if not self.nazwa:
            if self.wartosc <= 20:
                self.nazwa = "Okropna"
                self.mnoznik_ceny = 0.5
                self.mnoznik_wydajnosci = 0.7
                self.mnoznik_trwalosci = 0.6
            elif self.wartosc <= 40:
                self.nazwa = "Słaba"
                self.mnoznik_ceny = 0.75
                self.mnoznik_wydajnosci = 0.85
                self.mnoznik_trwalosci = 0.8
            elif self.wartosc <= 60:
                self.nazwa = "Przeciętna"
                self.mnoznik_ceny = 1.0
                self.mnoznik_wydajnosci = 1.0
                self.mnoznik_trwalosci = 1.0
            elif self.wartosc <= 80:
                self.nazwa = "Dobra"
                self.mnoznik_ceny = 1.5
                self.mnoznik_wydajnosci = 1.15
                self.mnoznik_trwalosci = 1.3
            else:
                self.nazwa = "Doskonała"
                self.mnoznik_ceny = 2.0
                self.mnoznik_wydajnosci = 1.3
                self.mnoznik_trwalosci = 1.6


@dataclass
class ProductionStep:
    """Pojedynczy krok w łańcuchu produkcji"""
    nazwa: str
    wymagane_surowce: Dict[str, int]  # resource_id -> quantity
    wymagane_narzedzia: List[str]  # tool_ids
    wymagana_stacja: Optional[str]  # station_id
    wymagana_umiejetnosc: str  # skill_name
    poziom_trudnosci: int  # 1-100
    czas_produkcji: int  # w minutach
    wydajnosc_bazowa: int  # ile sztuk produkuje
    szansa_powodzenia: float  # 0.0 - 1.0
    szansa_jakosci_premium: float = 0.1  # szansa na wyższą jakość
    
    def oblicz_wymaganą_jakosc_narzędzi(self) -> int:
        """Oblicza minimalną jakość narzędzi potrzebnych"""
        return max(10, self.poziom_trudnosci - 20)
    
    def oblicz_czas_z_modyfikatorami(self, skill_level: int, tool_quality: int) -> int:
        """Oblicza rzeczywisty czas produkcji"""
        skill_modifier = max(0.5, 1.0 - (skill_level - self.poziom_trudnosci) * 0.02)
        tool_modifier = max(0.7, 1.0 - (tool_quality - 50) * 0.005)
        return int(self.czas_produkcji * skill_modifier * tool_modifier)


@dataclass
class ProductionChain:
    """Kompletny łańcuch produkcji"""
    id: str
    nazwa: str
    opis: str
    kategoria: str  # weapons, tools, food, textiles
    kroki: List[ProductionStep]
    produkt_koncowy: str  # item_id
    poziom_zaawansowania: int  # 1-10
    
    def get_wszystkie_surowce(self) -> Dict[str, int]:
        """Zwraca wszystkie surowce potrzebne w całym łańcuchu"""
        wszystkie_surowce = {}
        for krok in self.kroki:
            for resource_id, quantity in krok.wymagane_surowce.items():
                wszystkie_surowce[resource_id] = wszystkie_surowce.get(resource_id, 0) + quantity
        return wszystkie_surowce
    
    def get_wszystkie_umiejetnosci(self) -> List[str]:
        """Zwraca wszystkie umiejętności potrzebne w łańcuchu"""
        return list(set(krok.wymagana_umiejetnosc for krok in self.kroki))
    
    def oblicz_calkowity_czas(self) -> int:
        """Oblicza całkowity czas produkcji (bez modyfikatorów)"""
        return sum(krok.czas_produkcji for krok in self.kroki)


class ProductionChainManager:
    """Manager łańcuchów produkcji"""
    
    def __init__(self):
        self.chains = self._create_production_chains()
        self.resource_nodes = self._create_resource_nodes()
        
    def _create_resource_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Tworzy węzły zasobów (miejsca wydobycia/zbierania)"""
        nodes = {
            # Węzły surowców pierwotnych
            'kamieniołom': {
                'nazwa': 'Kamieniołom',
                'opis': 'Stare wyrobisko w skale więzienia',
                'zasoby': {
                    'ruda_zelaza': {'szansa': 0.3, 'ilosc': (1, 3), 'jakosc': (20, 60)},
                    'kamien': {'szansa': 0.8, 'ilosc': (2, 5), 'jakosc': (30, 70)}
                },
                'wymagane_narzedzie': 'kilof',
                'wymagana_umiejetnosc': 'górnictwo',
                'czas_wydobycia': 30,
                'wyczerpywalny': True,
                'zapas': 100
            },
            
            'stary_sad': {
                'nazwa': 'Stary Sad',
                'opis': 'Opuszczony sad za więzieniem',
                'zasoby': {
                    'drewno_surowe': {'szansa': 0.4, 'ilosc': (1, 4), 'jakosc': (25, 75)},
                    'jablko': {'szansa': 0.6, 'ilosc': (2, 6), 'jakosc': (40, 80)}
                },
                'wymagane_narzedzie': 'siekiera',
                'wymagana_umiejetnosc': 'leśnictwo',
                'czas_wydobycia': 25,
                'wyczerpywalny': False,  # Odnawia się
                'tempo_odnowy': 60  # minuty
            },
            
            'podziemny_strumien': {
                'nazwa': 'Podziemny Strumień',
                'opis': 'Ukryty strumień pod więzieniem',
                'zasoby': {
                    'woda': {'szansa': 0.9, 'ilosc': (3, 8), 'jakosc': (60, 90)},
                    'glina': {'szansa': 0.3, 'ilosc': (1, 3), 'jakosc': (30, 60)}
                },
                'wymagane_narzedzie': None,  # Można zbierać ręcznie
                'wymagana_umiejetnosc': None,
                'czas_wydobycia': 10,
                'wyczerpywalny': False,
                'tempo_odnowy': 30
            },
            
            'sekretna_pracownia': {
                'nazwa': 'Sekretna Pracownia',
                'opis': 'Ukryta pracownia alchemiczna',
                'zasoby': {
                    'zioła': {'szansa': 0.5, 'ilosc': (1, 2), 'jakosc': (50, 90)},
                    'substancje_alchemiczne': {'szansa': 0.2, 'ilosc': (1, 1), 'jakosc': (70, 95)}
                },
                'wymagane_narzedzie': None,
                'wymagana_umiejetnosc': 'alchemia',
                'czas_wydobycia': 45,
                'wyczerpywalny': True,
                'zapas': 50
            }
        }
        return nodes
    
    def _create_production_chains(self) -> Dict[str, ProductionChain]:
        """Tworzy łańcuchy produkcji"""
        chains = {}
        
        # === ŁAŃCUCH PRODUKCJI MIECZA ===
        chains['miecz_stalowy'] = ProductionChain(
            id='miecz_stalowy',
            nazwa='Produkcja Stalowego Miecza',
            opis='Kompletny proces od rudy do gotowego miecza',
            kategoria='weapons',
            poziom_zaawansowania=6,
            produkt_koncowy='miecz',
            kroki=[
                # Krok 1: Przetworzenie rudy na żelazo
                ProductionStep(
                    nazwa='Wytapianie Żelaza',
                    wymagane_surowce={'ruda_zelaza': 3, 'węgiel': 2},
                    wymagane_narzedzia=['piec_hutniczy', 'miech'],
                    wymagana_stacja='huta',
                    wymagana_umiejetnosc='hutnictwo',
                    poziom_trudnosci=40,
                    czas_produkcji=120,
                    wydajnosc_bazowa=2,  # 2 sztabki żelaza
                    szansa_powodzenia=0.7,
                    szansa_jakosci_premium=0.15
                ),
                
                # Krok 2: Kucie stali z żelaza
                ProductionStep(
                    nazwa='Kucie Stali',
                    wymagane_surowce={'zelazo': 2, 'węgiel': 1},
                    wymagane_narzedzia=['mlotek_kowala', 'kowadlo'],
                    wymagana_stacja='kuznia',
                    wymagana_umiejetnosc='kowalstwo',
                    poziom_trudnosci=50,
                    czas_produkcji=90,
                    wydajnosc_bazowa=1,  # 1 sztabka stali
                    szansa_powodzenia=0.75,
                    szansa_jakosci_premium=0.2
                ),
                
                # Krok 3: Wykuwanie klingi
                ProductionStep(
                    nazwa='Wykuwanie Klingi',
                    wymagane_surowce={'stal': 1},
                    wymagane_narzedzia=['mlotek_precyzyjny', 'kowadlo', 'pilniki'],
                    wymagana_stacja='kuznia_mistrzowska',
                    wymagana_umiejetnosc='kowalstwo',
                    poziom_trudnosci=65,
                    czas_produkcji=150,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.6,
                    szansa_jakosci_premium=0.25
                ),
                
                # Krok 4: Wykonanie rękojeści
                ProductionStep(
                    nazwa='Wykonanie Rękojeści',
                    wymagane_surowce={'drewno_twardym': 1, 'skora': 1},
                    wymagane_narzedzia=['dluto', 'noz_rzezbarski'],
                    wymagana_stacja='warsztat_stolarski',
                    wymagana_umiejetnosc='stolarstwo',
                    poziom_trudnosci=35,
                    czas_produkcji=80,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.8,
                    szansa_jakosci_premium=0.1
                ),
                
                # Krok 5: Montaż finalny
                ProductionStep(
                    nazwa='Montaż Miecza',
                    wymagane_surowce={'klinga_stalowa': 1, 'rekojeść': 1, 'nitowanie': 3},
                    wymagane_narzedzia=['mlotek', 'wiertło', 'pilniki'],
                    wymagana_stacja='kuznia',
                    wymagana_umiejetnosc='kowalstwo',
                    poziom_trudnosci=45,
                    czas_produkcji=100,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.85,
                    szansa_jakosci_premium=0.15
                )
            ]
        )
        
        # === ŁAŃCUCH PRODUKCJI ŁUKU ===
        chains['luk_kompozytowy'] = ProductionChain(
            id='luk_kompozytowy',
            nazwa='Produkcja Łuku Kompozytowego',
            opis='Zaawansowany łuk z kilku rodzajów drewna',
            kategoria='weapons',
            poziom_zaawansowania=4,
            produkt_koncowy='luk',
            kroki=[
                # Krok 1: Przygotowanie drewna
                ProductionStep(
                    nazwa='Sezonowanie Drewna',
                    wymagane_surowce={'drewno_cis': 1, 'drewno_brzoza': 1},
                    wymagane_narzedzia=['noz', 'dluto'],
                    wymagana_stacja='suszarnia',
                    wymagana_umiejetnosc='stolarstwo',
                    poziom_trudnosci=30,
                    czas_produkcji=240,  # Długi proces
                    wydajnosc_bazowa=2,  # 2 elementy drewna
                    szansa_powodzenia=0.9,
                    szansa_jakosci_premium=0.2
                ),
                
                # Krok 2: Formowanie ramion łuku
                ProductionStep(
                    nazwa='Formowanie Ramion',
                    wymagane_surowce={'drewno_sezonowane': 2},
                    wymagane_narzedzia=['noz_rzezbarski', 'dluto', 'szablony'],
                    wymagana_stacja='warsztat_lukmistrza',
                    wymagana_umiejetnosc='lukmistrzostwo',
                    poziom_trudnosci=55,
                    czas_produkcji=180,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.7,
                    szansa_jakosci_premium=0.3
                ),
                
                # Krok 3: Wykonanie cięciwy
                ProductionStep(
                    nazwa='Skręcanie Cięciwy',
                    wymagane_surowce={'len': 3, 'wosk': 1},
                    wymagane_narzedzia=['kołowrotek'],
                    wymagana_stacja=None,
                    wymagana_umiejetnosc='sznurnictwo',
                    poziom_trudnosci=25,
                    czas_produkcji=45,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.9,
                    szansa_jakosci_premium=0.1
                ),
                
                # Krok 4: Montaż finalny
                ProductionStep(
                    nazwa='Montaż i Strojenie',
                    wymagane_surowce={'ramiona_luku': 1, 'cieciwa': 1, 'uchwyty': 2},
                    wymagane_narzedzia=['noz', 'pilniki'],
                    wymagana_stacja='warsztat_lukmistrza',
                    wymagana_umiejetnosc='lukmistrzostwo',
                    poziom_trudnosci=40,
                    czas_produkcji=90,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.8,
                    szansa_jakosci_premium=0.2
                )
            ]
        )
        
        # === ŁAŃCUCH PRODUKCJI ZBROI ===
        chains['zbroja_skorzana'] = ProductionChain(
            id='zbroja_skorzana',
            nazwa='Produkcja Zbroi Skórzanej',
            opis='Elastyczna zbroja z wygarbowanej skóry',
            kategoria='armor',
            poziom_zaawansowania=5,
            produkt_koncowy='zbroja_skorzana',
            kroki=[
                # Krok 1: Garbowanie skór
                ProductionStep(
                    nazwa='Garbowanie Skór',
                    wymagane_surowce={'skora_surowa': 4, 'kora_debowa': 2, 'sol': 1},
                    wymagane_narzedzia=['kadzie', 'mieszadła'],
                    wymagana_stacja='garbarnia',
                    wymagana_umiejetnosc='garbarstwo',
                    poziom_trudnosci=35,
                    czas_produkcji=360,  # Bardzo długi proces
                    wydajnosc_bazowa=3,  # 3 kawałki skóry
                    szansa_powodzenia=0.8,
                    szansa_jakosci_premium=0.15
                ),
                
                # Krok 2: Krojenie elementów
                ProductionStep(
                    nazwa='Krojenie Elementów Zbroi',
                    wymagane_surowce={'skora_garbowana': 3},
                    wymagane_narzedzia=['noz_krawiecki', 'szablon'],
                    wymagana_stacja='warsztat_krawiecki',
                    wymagana_umiejetnosc='krawiectwo',
                    poziom_trudnosci=40,
                    czas_produkcji=120,
                    wydajnosc_bazowa=1,  # Komplet elementów
                    szansa_powodzenia=0.85,
                    szansa_jakosci_premium=0.1
                ),
                
                # Krok 3: Szycie i montaż
                ProductionStep(
                    nazwa='Szycie i Montaż',
                    wymagane_surowce={'elementy_zbroi': 1, 'nici': 5, 'klamry': 8},
                    wymagane_narzedzia=['igla', 'szylo', 'szczypce'],
                    wymagana_stacja='warsztat_krawiecki',
                    wymagana_umiejetnosc='krawiectwo',
                    poziom_trudnosci=50,
                    czas_produkcji=200,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.75,
                    szansa_jakosci_premium=0.2
                ),
                
                # Krok 4: Wzmocnienia i wykończenia
                ProductionStep(
                    nazwa='Wzmacnianie Zbroi',
                    wymagane_surowce={'zbroja_podstawowa': 1, 'blaszki_metalowe': 6, 'nitowanie': 12},
                    wymagane_narzedzia=['mlotek', 'szczypce', 'wiertło'],
                    wymagana_stacja='warsztat_panercerski',
                    wymagana_umiejetnosc='pancernictwo',
                    poziom_trudnosci=45,
                    czas_produkcji=150,
                    wydajnosc_bazowa=1,
                    szansa_powodzenia=0.8,
                    szansa_jakosci_premium=0.25
                )
            ]
        )
        
        # === ŁAŃCUCH PRODUKCJI ELIKSIRU ===
        chains['eliksir_leczniczy'] = ProductionChain(
            id='eliksir_leczniczy',
            nazwa='Warzenie Eliksiru Leczniczego',
            opis='Potężny eliksir przywracający zdrowie',
            kategoria='alchemy',
            poziom_zaawansowania=7,
            produkt_koncowy='eliksir_leczniczy',
            kroki=[
                # Krok 1: Przygotowanie składników roślinnych
                ProductionStep(
                    nazwa='Przygotowanie Ziół',
                    wymagane_surowce={'ziola_lecznicze': 3, 'korzen_zywokrwi': 1, 'liscie_szalwii': 2},
                    wymagane_narzedzia=['moździerz', 'noz_alchemiczny'],
                    wymagana_stacja='pracownia_alchemiczna',
                    wymagana_umiejetnosc='zielarstwo',
                    poziom_trudnosci=30,
                    czas_produkcji=60,
                    wydajnosc_bazowa=1,  # Mieszanka ziół
                    szansa_powodzenia=0.85,
                    szansa_jakosci_premium=0.2
                ),
                
                # Krok 2: Destylacja bazowa
                ProductionStep(
                    nazwa='Destylacja Esencji',
                    wymagane_surowce={'mieszanka_ziol': 1, 'alkohol': 2, 'woda_destylowana': 3},
                    wymagane_narzedzia=['alembik', 'probowki'],
                    wymagana_stacja='laboratorium_alchemiczne',
                    wymagana_umiejetnosc='alchemia',
                    poziom_trudnosci=60,
                    czas_produkcji=180,
                    wydajnosc_bazowa=2,  # 2 dawki esencji
                    szansa_powodzenia=0.7,
                    szansa_jakosci_premium=0.3
                ),
                
                # Krok 3: Warzenie finalne
                ProductionStep(
                    nazwa='Warzenie Eliksiru',
                    wymagane_surowce={'esencja': 2, 'miod': 1, 'kryształ_magiczny': 1},
                    wymagane_narzedzia=['kocioł_alchemiczny', 'mieszadło_runiczne'],
                    wymagana_stacja='laboratorium_mistrzowskie',
                    wymagana_umiejetnosc='alchemia',
                    poziom_trudnosci=75,
                    czas_produkcji=240,
                    wydajnosc_bazowa=3,  # 3 fiolki eliksiru
                    szansa_powodzenia=0.6,
                    szansa_jakosci_premium=0.4
                )
            ]
        )
        
        return chains
    
    def get_chain(self, chain_id: str) -> Optional[ProductionChain]:
        """Zwraca łańcuch produkcji o danym ID"""
        return self.chains.get(chain_id)
    
    def get_chains_by_category(self, category: str) -> List[ProductionChain]:
        """Zwraca łańcuchy z danej kategorii"""
        return [chain for chain in self.chains.values() if chain.kategoria == category]
    
    def get_chains_for_skill(self, skill_name: str) -> List[ProductionChain]:
        """Zwraca łańcuchy wymagające danej umiejętności"""
        result = []
        for chain in self.chains.values():
            if skill_name in chain.get_wszystkie_umiejetnosci():
                result.append(chain)
        return result
    
    def get_available_chains(self, player_skills: Dict[str, int], min_success_chance: float = 0.3) -> List[ProductionChain]:
        """Zwraca łańcuchy dostępne dla gracza o danych umiejętnościach"""
        available = []
        
        for chain in self.chains.values():
            can_produce = True
            total_success = 1.0
            
            for step in chain.kroki:
                skill_level = player_skills.get(step.wymagana_umiejetnosc, 0)
                skill_diff = skill_level - step.poziom_trudnosci
                
                # Oblicz szanse sukcesu tego kroku
                step_success = step.szansa_powodzenia + (skill_diff / 100.0)
                step_success = max(0.1, min(0.95, step_success))
                
                total_success *= step_success
                
                # Jeśli umiejętność jest zbyt niska
                if skill_level < step.poziom_trudnosci - 30:
                    can_produce = False
                    break
            
            if can_produce and total_success >= min_success_chance:
                available.append(chain)
        
        return available
    
    def calculate_production_cost(self, chain_id: str, material_prices: Dict[str, float]) -> float:
        """Oblicza koszt produkcji dla całego łańcucha"""
        chain = self.get_chain(chain_id)
        if not chain:
            return 0.0
        
        total_cost = 0.0
        for resource_id, quantity in chain.get_wszystkie_surowce().items():
            price = material_prices.get(resource_id, 10.0)  # Domyślna cena
            total_cost += price * quantity
        
        return total_cost
    
    def calculate_production_time(self, chain_id: str, player_skills: Dict[str, int], 
                                  tool_qualities: Dict[str, int]) -> int:
        """Oblicza rzeczywisty czas produkcji"""
        chain = self.get_chain(chain_id)
        if not chain:
            return 0
        
        total_time = 0
        for step in chain.kroki:
            skill_level = player_skills.get(step.wymagana_umiejetnosc, 0)
            
            # Średnia jakość narzędzi dla tego kroku
            avg_tool_quality = 50
            tool_count = 0
            for tool in step.wymagane_narzedzia:
                if tool in tool_qualities:
                    avg_tool_quality += tool_qualities[tool]
                    tool_count += 1
            if tool_count > 0:
                avg_tool_quality //= (tool_count + 1)
            
            step_time = step.oblicz_czas_z_modyfikatorami(skill_level, avg_tool_quality)
            total_time += step_time
        
        return total_time
    
    def simulate_production(self, chain_id: str, player_skills: Dict[str, int], 
                           tool_qualities: Dict[str, int]) -> Dict[str, Any]:
        """Symuluje cały proces produkcji"""
        chain = self.get_chain(chain_id)
        if not chain:
            return {"sukces": False, "powod": "Nieznany łańcuch produkcji"}
        
        results = {
            "sukces": True,
            "produkt_koncowy": chain.produkt_koncowy,
            "calkowity_czas": 0,
            "jakosci_produktow": {},
            "kroki_szczegoly": [],
            "calkowita_szansa": 1.0
        }
        
        for i, step in enumerate(chain.kroki):
            skill_level = player_skills.get(step.wymagana_umiejetnosc, 0)
            
            # Oblicz szanse sukcesu
            skill_diff = skill_level - step.poziom_trudnosci
            success_chance = step.szansa_powodzenia + (skill_diff / 100.0)
            success_chance = max(0.1, min(0.95, success_chance))
            
            # Symuluj wykonanie kroku
            step_success = random.random() < success_chance
            
            # Oblicz jakość produktu
            base_quality = 50 + skill_diff
            quality_roll = random.randint(-15, 15)
            quality = max(1, min(100, base_quality + quality_roll))
            
            # Szansa na premium jakość
            if step_success and random.random() < step.szansa_jakosci_premium:
                quality = min(100, quality + 20)
            
            step_time = step.oblicz_czas_z_modyfikatorami(skill_level, 
                                                         tool_qualities.get(step.wymagane_narzedzia[0], 50))
            
            results["kroki_szczegoly"].append({
                "krok": step.nazwa,
                "sukces": step_success,
                "jakosc": quality,
                "czas": step_time,
                "szansa": success_chance
            })
            
            results["calkowity_czas"] += step_time
            results["calkowita_szansa"] *= success_chance
            
            if not step_success:
                results["sukces"] = False
                results["powod"] = f"Niepowodzenie w kroku: {step.nazwa}"
                break
        
        # Oblicz finalną jakość produktu
        if results["sukces"]:
            avg_quality = sum(detail["jakosc"] for detail in results["kroki_szczegoly"])
            avg_quality //= len(results["kroki_szczegoly"])
            results["jakosc_koncowa"] = avg_quality
        
        return results
    
    def get_resource_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Zwraca węzeł zasobów"""
        return self.resource_nodes.get(node_id)
    
    def extract_from_node(self, node_id: str, player_skills: Dict[str, int], 
                          tool_quality: int = 50) -> Dict[str, Any]:
        """Wydobywa zasoby z węzła"""
        node = self.get_resource_node(node_id)
        if not node:
            return {"sukces": False, "powod": "Nieznany węzeł zasobów"}
        
        # Sprawdź czy węzeł jest wyczerpany
        if node.get('wyczerpywalny') and node.get('zapas', 0) <= 0:
            return {"sukces": False, "powod": "Źródło zasobów wyczerpane"}
        
        # Sprawdź wymagania
        required_skill = node.get('wymagana_umiejetnosc')
        if required_skill and player_skills.get(required_skill, 0) < 10:
            return {"sukces": False, "powod": f"Wymagana umiejętność: {required_skill}"}
        
        results = {
            "sukces": True,
            "czas": node['czas_wydobycia'],
            "zasoby": {}
        }
        
        # Dla każdego możliwego zasobu
        for resource_id, resource_data in node['zasoby'].items():
            if random.random() < resource_data['szansa']:
                quantity_range = resource_data['ilosc']
                quantity = random.randint(quantity_range[0], quantity_range[1])
                
                quality_range = resource_data['jakosc']
                base_quality = random.randint(quality_range[0], quality_range[1])
                
                # Modyfikacje przez umiejętności i narzędzia
                skill_bonus = 0
                if required_skill:
                    skill_level = player_skills.get(required_skill, 0)
                    skill_bonus = (skill_level - 25) // 10  # Bonus co 10 poziomów
                
                tool_bonus = (tool_quality - 50) // 10
                final_quality = max(1, min(100, base_quality + skill_bonus + tool_bonus))
                
                results["zasoby"][resource_id] = {
                    "ilosc": quantity,
                    "jakosc": final_quality
                }
        
        # Zmniejsz zapas jeśli węzeł wyczerpywalny
        if node.get('wyczerpywalny'):
            node['zapas'] = max(0, node['zapas'] - 1)
        
        return results


if __name__ == "__main__":
    # Test systemu łańcuchów produkcji
    manager = ProductionChainManager()
    
    print("=== TEST SYSTEMU ŁAŃCUCHÓW PRODUKCJI ===")
    
    # Pokaż dostępne łańcuchy
    print(f"Liczba łańcuchów: {len(manager.chains)}")
    for chain_id, chain in manager.chains.items():
        print(f"\n{chain.nazwa} (poziom: {chain.poziom_zaawansowania})")
        print(f"  Produkt: {chain.produkt_koncowy}")
        print(f"  Kroki: {len(chain.kroki)}")
        print(f"  Całkowity czas: {chain.oblicz_calkowity_czas()} minut")
        print(f"  Umiejętności: {', '.join(chain.get_wszystkie_umiejetnosci())}")
    
    # Test symulacji produkcji miecza
    print(f"\n=== SYMULACJA PRODUKCJI MIECZA ===")
    player_skills = {
        'hutnictwo': 45,
        'kowalstwo': 60,
        'stolarstwo': 40
    }
    tool_qualities = {
        'mlotek_kowala': 70,
        'kowadlo': 65,
        'dluto': 55
    }
    
    result = manager.simulate_production('miecz_stalowy', player_skills, tool_qualities)
    print(f"Sukces: {result['sukces']}")
    print(f"Całkowity czas: {result['calkowity_czas']} minut")
    print(f"Szansa powodzenia: {result['calkowita_szansa']:.2%}")
    
    if result['sukces']:
        print(f"Jakość końcowa: {result['jakosc_koncowa']}")
    
    print("\nSzczegóły kroków:")
    for detail in result['kroki_szczegoly']:
        print(f"  {detail['krok']}: {'✓' if detail['sukces'] else '✗'} "
              f"(jakość: {detail['jakosc']}, czas: {detail['czas']}min)")
    
    # Test wydobycia zasobów
    print(f"\n=== TEST WYDOBYCIA ZASOBÓW ===")
    extraction = manager.extract_from_node('kamieniołom', {'górnictwo': 35}, 60)
    print(f"Wydobycie z kamieniołomu: {extraction['sukces']}")
    if extraction['sukces']:
        print(f"Czas: {extraction['czas']} minut")
        print("Zasoby:")
        for resource, data in extraction['zasoby'].items():
            print(f"  {resource}: {data['ilosc']} sztuk (jakość: {data['jakosc']})")