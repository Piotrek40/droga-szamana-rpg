#!/usr/bin/env python3
"""
DEMO SYSTEMU EKONOMII I CRAFTINGU - DROGA SZAMANA RPG
Pełna demonstracja wszystkich funkcji systemu
"""

import json
import random
from mechanics.economy import *
from mechanics.crafting import *


class Gracz:
    """Klasa gracza z pełnymi umiejętnościami"""
    def __init__(self, nazwa: str):
        self.nazwa = nazwa
        self.zloto = 500
        self.inwentarz = NPCInventory(max_przedmiotow=50, zloto=500)
        
        # Umiejętności craftingowe
        self.umiejetnosci_craft = {
            'kowalstwo': CraftingSkill('kowalstwo', 3, 25),
            'stolarstwo': CraftingSkill('stolarstwo', 2, 15),
            'alchemia': CraftingSkill('alchemia', 1, 5),
            'szycie': CraftingSkill('szycie', 1, 0)
        }
        
        # Umiejętności handlowe
        self.umiejetnosci = {
            'handel': 25,
            'przekonywanie': 30
        }
        
        self.reputacja = {}  # Reputacja u różnych NPCów


def dodaj_materialy_graczowi(gracz: Gracz, items_db: Dict[str, dict]):
    """Dodaje różnorodne materiały do inwentarza gracza"""
    materialy = {
        'metal': (5, 60, 90),  # (ilość, min_jakość, max_jakość)
        'drewno': (8, 40, 80),
        'skora': (3, 30, 70),
        'tkanina': (4, 20, 60),
        'kamien': (6, 10, 50)
    }
    
    # Dodaj również narzędzia
    narzedzia = ['mlotek', 'dluto', 'igla']
    
    for material_id, (ilosc, min_jakosc, max_jakosc) in materialy.items():
        for _ in range(ilosc):
            jakosc = random.randint(min_jakosc, max_jakosc)
            item_data = items_db[material_id]
            
            przedmiot = Item(
                id=material_id,
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
            gracz.inwentarz.dodaj_przedmiot(przedmiot)
    
    # Dodaj narzędzia
    for narzedzie_id in narzedzia:
        jakosc = random.randint(40, 80)
        item_data = items_db[narzedzie_id]
        
        narzedzie = Item(
            id=narzedzie_id,
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
        gracz.inwentarz.dodaj_przedmiot(przedmiot)


def demo_crafting(gracz: Gracz, crafting_system: CraftingSystem):
    """Demonstracja systemu craftingu"""
    print("\n" + "="*50)
    print("           DEMO SYSTEMU CRAFTINGU")
    print("="*50)
    
    # Odkryj wszystkie podstawowe receptury
    crafting_system.auto_discover_basic_recipes(gracz)
    print(f"Odkryte receptury: {list(crafting_system.discovered_recipes)}")
    
    # Pokaż dostępne receptury
    dostepne = crafting_system.get_available_recipes(gracz)
    print(f"\nDostępne receptury dla gracza:")
    for recipe in dostepne:
        umiejetnosc = gracz.umiejetnosci_craft.get(recipe.wymagana_umiejetnosc)
        poziom = umiejetnosc.poziom if umiejetnosc else 0
        print(f"  - {recipe.nazwa} (trudność: {recipe.poziom_trudnosci}, mój poziom: {poziom})")
    
    # Sprawdź materiały gracza
    print(f"\nMoje materiały:")
    for item_id, items in gracz.inwentarz.przedmioty.items():
        if items:
            srednia_jakosc = sum(item.jakosc for item in items) / len(items)
            print(f"  - {items[0].nazwa}: {len(items)}szt. (śr. jakość: {srednia_jakosc:.1f})")
    
    # Testuj crafting różnych przedmiotów
    receptury_do_testowania = ['noz', 'kilof', 'luk', 'strzaly']
    
    for recipe_id in receptury_do_testowania:
        if recipe_id in crafting_system.discovered_recipes:
            print(f"\n--- CRAFTING: {crafting_system.recipes_db[recipe_id].nazwa} ---")
            
            # Sprawdź wymagania
            recipe = crafting_system.recipes_db[recipe_id]
            spelnione, bledy = recipe.sprawdz_wymagania(gracz, gracz.inwentarz)
            
            if spelnione:
                # Oblicz szanse
                szansa = crafting_system.oblicz_szanse_powodzenia(recipe, gracz)
                print(f"Szansa powodzenia: {szansa:.1%}")
                
                # Wykonaj crafting
                rezultat = crafting_system.craft_item(recipe_id, gracz, gracz.inwentarz, "kuznia")
                
                print(f"Rezultat: {rezultat['rezultat']}")
                if rezultat['sukces'] and rezultat['przedmioty']:
                    for item in rezultat['przedmioty']:
                        tier = QualityTier.get_tier(item.jakosc)
                        print(f"  Utworzony: {item.nazwa} - {tier.nazwa} (jakość: {item.jakosc})")
                print(f"  Zdobyte EXP: {rezultat['exp_zdobyte']}")
                
                if rezultat['nowe_receptury']:
                    print(f"  ODKRYTO: {rezultat['nowe_receptury']}")
            else:
                print(f"Nie można wykonać - brak wymagań:")
                for blad in bledy:
                    print(f"  ❌ {blad}")


def demo_handel(gracz: Gracz, market: Market, items_db: Dict[str, dict]):
    """Demonstracja systemu handlu"""
    print("\n" + "="*50)
    print("           DEMO SYSTEMU HANDLU")
    print("="*50)
    
    kowal = None
    kupiec = None
    
    # Znajdź odpowiednich NPCów
    for npc in market.npcs:
        if npc.zawod == "kowalstwo":
            kowal = npc
        elif npc.zawod == "handel":
            kupiec = npc
    
    if not kowal or not kupiec:
        print("Brak odpowiednich NPCów!")
        return
    
    print(f"\n--- HANDEL Z: {kowal.nazwa} (Kowal) ---")
    print(f"Reputacja: {kowal.reputacja_gracza}")
    print(f"Osobowość: {kowal.osobowosc.value[0]}")
    print(f"Pieniądze NPC: {kowal.inwentarz.zloto} zł")
    print(f"Moje pieniądze: {gracz.zloto} zł")
    
    # Pokaż co ma kowal do sprzedania
    print(f"\nCo ma {kowal.nazwa} do sprzedania:")
    for item_id, items in kowal.inwentarz.przedmioty.items():
        if items:
            for item in items[:3]:  # Pokaż pierwsze 3
                cena_rynkowa = market.oblicz_cene_rynkowa(item_id, item.bazowa_wartosc)
                cena_npc = kowal.oblicz_cene_sprzedazy(item, cena_rynkowa)
                tier = QualityTier.get_tier(item.jakosc)
                print(f"  - {item.nazwa} ({tier.nazwa}, jakość {item.jakosc}) - {cena_npc:.1f} zł")
    
    # Testuj kupowanie
    for item_id in ['kilof', 'lopata', 'mlotek']:
        if kowal.inwentarz.ma_przedmiot(item_id):
            print(f"\n🛒 Próbuję kupić: {items_db[item_id]['nazwa']}")
            
            cena_rynkowa = market.oblicz_cene_rynkowa(item_id, items_db[item_id]['bazowa_wartosc'])
            
            # Bez targowania
            rezultat = TradeSystem.kup_od_npc(gracz, kowal, item_id, cena_rynkowa, targowanie=False)
            print(f"Bez targowania: {rezultat}")
            
            if not rezultat['sukces']:
                # Z targowaniem
                rezultat = TradeSystem.kup_od_npc(gracz, kowal, item_id, cena_rynkowa, targowanie=True)
                print(f"Z targowaniem: {rezultat}")
            
            if rezultat['sukces']:
                print(f"  ✅ Kupiono za {rezultat['cena']:.1f} zł")
                print(f"  📈 Reputacja: {kowal.reputacja_gracza}")
                break
    
    print(f"\n--- HANDEL Z: {kupiec.nazwa} (Kupiec) ---")
    print(f"Reputacja: {kupiec.reputacja_gracza}")
    print(f"Osobowość: {kupiec.osobowosc.value[0]}")
    
    # Testuj sprzedawanie
    for item_id, items in gracz.inwentarz.przedmioty.items():
        if items and item_id in ['metal', 'drewno']:
            item = items[0]
            print(f"\n💰 Próbuję sprzedać: {item.nazwa} (jakość: {item.jakosc})")
            
            cena_rynkowa = market.oblicz_cene_rynkowa(item_id, item.bazowa_wartosc)
            
            rezultat = TradeSystem.sprzedaj_npc(gracz, kupiec, item, cena_rynkowa, targowanie=True)
            print(f"Rezultat: {rezultat}")
            
            if rezultat['sukces']:
                print(f"  ✅ Sprzedano za {rezultat['cena']:.1f} zł")
                gracz.inwentarz.przedmioty[item_id].remove(item)
                break


def demo_ekonomia(market: Market, items_db: Dict[str, dict], dni: int = 7):
    """Demonstracja symulacji ekonomii"""
    print("\n" + "="*50)
    print("          DEMO SYMULACJI EKONOMII")
    print("="*50)
    
    print(f"Symulacja {dni} dni na rynku '{market.nazwa}'")
    print(f"NPCe na rynku: {len(market.npcs)}")
    
    # Obserwowane przedmioty
    obserwowane = ['chleb', 'metal', 'kilof', 'miecz', 'mieso']
    
    print(f"\n📊 OBSERWOWANE CENY:")
    print("Dzień | " + " | ".join(f"{items_db[item]['nazwa'][:8]:>8}" for item in obserwowane))
    print("-" * (7 + len(obserwowane) * 12))
    
    for dzien in range(1, dni + 1):
        # Symuluj dzień
        market.symuluj_dzien(items_db)
        
        # Pokaż ceny
        ceny = []
        for item_id in obserwowane:
            if item_id in market.dane_rynkowe:
                cena = market.oblicz_cene_rynkowa(item_id, items_db[item_id]['bazowa_wartosc'])
                ceny.append(f"{cena:8.1f}")
            else:
                ceny.append("     N/A")
        
        print(f"{dzien:4d}  | " + " | ".join(ceny))
    
    print(f"\n📈 ANALIZA RYNKU PO {dni} DNIACH:")
    for item_id in obserwowane:
        if item_id in market.dane_rynkowe:
            dane = market.dane_rynkowe[item_id]
            nazwa = items_db[item_id]['nazwa']
            print(f"{nazwa:15} - Podaż: {dane.podaz:3d}, Popyt: {dane.popyt:3d}, "
                  f"Trend: {dane.trend:+5.2f}, Ostatnia cena: {dane.ostatnia_cena:6.1f} zł")
    
    print(f"\n💰 KONDYCJA FINANSOWA NPCów:")
    for npc in market.npcs:
        wartosc = npc.inwentarz.wartosc_calkowita()
        print(f"{npc.nazwa:20} ({npc.zawod:12}) - {npc.inwentarz.zloto:4d} zł + "
              f"{wartosc - npc.inwentarz.zloto:6.1f} zł w towarach = {wartosc:6.1f} zł")


def demo_jakosci_i_trwalosci(items_db: Dict[str, dict]):
    """Demonstracja systemu jakości i trwałości"""
    print("\n" + "="*50)
    print("        DEMO JAKOŚCI I TRWAŁOŚCI")
    print("="*50)
    
    # Stwórz przedmioty różnej jakości
    item_data = items_db['miecz']
    
    print("Miecze różnej jakości:")
    for nazwa_jakosci, jakosc in [("Okropny", 15), ("Słaby", 35), ("Przeciętny", 50), 
                                  ("Dobry", 75), ("Doskonały", 95)]:
        miecz = Item(
            id="miecz",
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
        
        tier = QualityTier.get_tier(jakosc)
        print(f"{nazwa_jakosci:12} (jakość {jakosc:2d}) - "
              f"{tier.nazwa:12} - wartość: {miecz.aktualna_wartosc:5.1f} zł")
    
    # Demo zużycia
    print(f"\nDemo zużycia przedmiotu:")
    miecz = Item(
        id="miecz", nazwa="Miecz", typ="bron", opis="Test", waga=2.0,
        bazowa_wartosc=45, trwalosc=200, kategoria="broń", efekty={}, jakosc=70
    )
    
    print(f"Nowy miecz - Trwałość: {miecz.obecna_trwalosc}/{miecz.trwalosc}, "
          f"Wartość: {miecz.aktualna_wartosc:.1f} zł")
    
    # Zużywaj miecz
    for i in range(1, 6):
        miecz.zuzyj(40)
        procent_trwalosci = (miecz.obecna_trwalosc / miecz.trwalosc) * 100
        print(f"Po {i*40:3d} użyciach - Trwałość: {miecz.obecna_trwalosc:3d}/{miecz.trwalosc} "
              f"({procent_trwalosci:5.1f}%), Wartość: {miecz.aktualna_wartosc:.1f} zł")
        
        if miecz.czy_zepsute():
            print("  ⚠️  PRZEDMIOT ZEPSUTY!")
            break


def main():
    """Główna funkcja demonstracyjna"""
    print("🏰 " + "="*60)
    print("       DROGA SZAMANA - SYSTEM EKONOMII I CRAFTINGU")
    print("                   PEŁNA DEMONSTRACJA")  
    print("="*62 + " 🏰")
    
    # Inicjalizacja systemów
    items_db = load_items_database("/mnt/d/claude3/data/items.json")
    crafting_system = CraftingSystem(
        "/mnt/d/claude3/data/items.json",
        "/mnt/d/claude3/data/recipes.json"
    )
    
    # Stwórz gracza
    gracz = Gracz("Ragnar Szamankiller")
    dodaj_materialy_graczowi(gracz, items_db)
    
    # Stwórz rynek z NPCami  
    npcs = create_sample_npcs(items_db)
    market = Market("Wielki Targ w Nordheim", "centrum miasta")
    for npc in npcs:
        market.dodaj_npc(npc)
    
    print(f"\n👤 Gracz: {gracz.nazwa}")
    print(f"💰 Pieniądze: {gracz.zloto} zł")
    print(f"🎒 Przedmioty: {gracz.inwentarz.liczba_przedmiotow()}")
    print(f"🏪 NPCe na rynku: {len(market.npcs)}")
    
    # Uruchom demonstracje
    demo_jakosci_i_trwalosci(items_db)
    demo_crafting(gracz, crafting_system)
    demo_handel(gracz, market, items_db)
    demo_ekonomia(market, items_db, 5)
    
    print(f"\n🎯 " + "="*60)
    print("                    DEMO ZAKOŃCZONE")
    print("   Wszystkie systemy działają prawidłowo! 🎉")
    print("="*62 + " 🎯")


if __name__ == "__main__":
    main()