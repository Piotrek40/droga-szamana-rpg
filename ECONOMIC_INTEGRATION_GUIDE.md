# Przewodnik Integracji Rozszerzonego Systemu Ekonomicznego

Ten dokument opisuje, jak zintegrować kompletny system ekonomiczny z grą Droga Szamana RPG.

## 📋 Podsumowanie Systemu

Stworzony został kompleksowy system ekonomiczny składający się z:

### 🏭 Komponenty Systemu

1. **Enhanced Economy** (`mechanics/economy.py`)
   - Rozszerzona klasa `EnhancedEconomy` dziedzicząca po `Economy`
   - Integracja z AI handlarzy, wydarzeniami i łańcuchami produkcji
   - Pełna kompatybilność wsteczna

2. **Economic Events** (`mechanics/economic_events.py`)
   - 12 różnych typów wydarzeń ekonomicznych
   - Automatyczne generowanie i wygasanie wydarzeń
   - Wpływ na ceny, podaż i popyt

3. **Production Chains** (`mechanics/production_chains.py`)
   - Kompletne łańcuchy produkcji od surowców do produktów końcowych
   - System jakości surowców i narzędzi
   - Wydobywanie zasobów z węzłów

4. **Merchant AI** (`mechanics/merchant_ai.py`)
   - Inteligentni handlarze z pamięcią i emocjami
   - System negocjacji i reputacji
   - Różne style handlowe i osobowości

## 🔧 Instrukcje Integracji

### Krok 1: Aktualizacja Game State

```python
# W core/game_state.py dodaj:

from mechanics.economy import EnhancedEconomy

class GameState:
    def __init__(self):
        # ... istniejący kod ...
        
        # ZASTĄP standardową ekonomię rozszerzoną
        self.economy = EnhancedEconomy()
        
        # Dodaj handlarzy AI
        self._setup_merchant_ais()
    
    def _setup_merchant_ais(self):
        """Konfiguruje AI handlarzy na podstawie NPCów z gry"""
        # Dla każdego handlarza z data/npcs.json
        merchant_configs = [
            ("marek", "Marek Strażnik", "corruptible"),
            ("helga", "Helga Kucharka", "stingy"),
            ("olaf", "Olaf Kowal", "honest")
        ]
        
        for npc_id, name, personality in merchant_configs:
            self.economy.add_merchant_ai(npc_id, name, personality)
    
    def update(self, delta_time):
        """Aktualizuj stan gry"""
        # ... istniejący kod ...
        
        # DODAJ aktualizację ekonomii
        self.economy.update_enhanced(self.game_time)
```

### Krok 2: Aktualizacja Command Parser

```python
# W ui/commands.py dodaj nowe komendy handlowe:

def handle_trade_command(self, args, game_state):
    """Handel z NPCami z negocjacją"""
    if len(args) < 3:
        return "Użycie: handel [npc] [przedmiot] [ilość] [cena?]"
    
    npc_id, item_id = args[0], args[1]
    quantity = int(args[2]) if args[2].isdigit() else 1
    offered_price = float(args[3]) if len(args) > 3 else None
    
    # Sprawdź czy NPC istnieje
    if npc_id not in game_state.economy.merchant_ais:
        return f"NPC {npc_id} nie jest handlarzem."
    
    # Pobierz aktualną cenę
    current_price = game_state.economy.get_enhanced_price(
        item_id, "prison", 10, npc_id, "player"
    )
    
    # Jeśli podano cenę, rozpocznij negocjację
    if offered_price:
        negotiation = game_state.economy.negotiate_price(
            npc_id, "player", item_id, offered_price, current_price, False
        )
        
        if negotiation['success']:
            result = game_state.economy.process_enhanced_trade(
                npc_id, "player", item_id, quantity
            )
            return f"{negotiation['reason']} {result['message']}"
        else:
            return negotiation['reason']
    
    # Handel bez negocjacji
    result = game_state.economy.process_enhanced_trade(
        npc_id, "player", item_id, quantity
    )
    return result['message']

def handle_market_command(self, args, game_state):
    """Pokaż informacje o rynku"""
    economy = game_state.economy
    
    output = ["=== STAN RYNKU ==="]
    
    # Aktywne wydarzenia
    events = economy.get_active_events()
    if events:
        output.append("\n📈 WYDARZENIA EKONOMICZNE:")
        for event in events:
            output.append(f"• {event}")
    
    # Ceny wybranych przedmiotów
    output.append("\n💰 CENY RYNKOWE:")
    items = ["chleb", "miecz", "metal", "drewno"]
    for item_id in items:
        price = economy.get_enhanced_price(item_id, "prison", 10)
        output.append(f"• {item_id.title()}: {price:.1f} zł")
    
    # Wskaźniki ekonomiczne
    indicators = economy.economic_indicators
    output.append("\n📊 WSKAŹNIKI:")
    output.append(f"• Stabilność rynku: {indicators['market_stability']:.1%}")
    output.append(f"• Inflacja: {indicators['inflation_rate']:.2%}")
    
    return "\n".join(output)

def handle_craft_advanced_command(self, args, game_state):
    """Zaawansowany crafting z łańcuchami produkcji"""
    if not args:
        # Pokaż dostępne łańcuchy
        chains = game_state.economy.get_production_chains()
        if not chains:
            return "Brak dostępnych łańcuchów produkcji."
        
        output = ["=== ŁAŃCUCHY PRODUKCJI ==="]
        for chain in chains[:10]:  # Pokaż pierwsze 10
            output.append(f"• {chain['name']} ({chain['category']})")
            output.append(f"  Trudność: {chain['difficulty']}, Czas: {chain['total_time']} min")
        
        return "\n".join(output)
    
    chain_id = args[0]
    
    # Sprawdź umiejętności gracza (musisz dodać system umiejętności)
    player_skills = getattr(game_state.player, 'skills', {})
    
    # Symuluj produkcję
    result = game_state.economy.simulate_production(chain_id, player_skills)
    
    if result['success']:
        return f"✓ Udało się wyprodukować {result['produkt_koncowy']}! Jakość: {result['jakosc_koncowa']}"
    else:
        return f"✗ Produkcja nieudana: {result['powod']}"

# DODAJ te komendy do command_map:
self.command_map.update({
    'handel': self.handle_trade_command,
    'rynek': self.handle_market_command,
    'produkuj': self.handle_craft_advanced_command
})
```

### Krok 3: Aktualizacja GUI

```python
# W integrated_gui.py dodaj nowe panele:

def create_economy_panel(self, parent):
    """Panel ekonomiczny z informacjami o rynku"""
    economy_frame = tk.Frame(parent, bg=self.colors['panel'])
    economy_frame.grid(row=0, column=3, sticky='nsew', padx=2, pady=2)
    
    # Nagłówek
    tk.Label(economy_frame, text="EKONOMIA", 
             font=self.fonts['header'], 
             bg=self.colors['panel'], 
             fg=self.colors['text']).grid(row=0, column=0, sticky='ew', pady=2)
    
    # Wydarzenia ekonomiczne
    self.events_text = tk.Text(economy_frame, width=25, height=8,
                               font=self.fonts['small'], 
                               bg=self.colors['bg'], 
                               fg=self.colors['text'], wrap=tk.WORD)
    self.events_text.grid(row=1, column=0, sticky='ew', padx=2, pady=2)
    
    # Ceny rynkowe
    self.prices_text = tk.Text(economy_frame, width=25, height=8,
                               font=self.fonts['small'],
                               bg=self.colors['bg'],
                               fg=self.colors['text'], wrap=tk.WORD)
    self.prices_text.grid(row=2, column=0, sticky='ew', padx=2, pady=2)
    
    return economy_frame

def update_economy_display(self):
    """Aktualizuje wyświetlane informacje ekonomiczne"""
    if not hasattr(self, 'game_state') or not self.game_state.economy:
        return
    
    economy = self.game_state.economy
    
    # Aktualizuj wydarzenia
    self.events_text.delete(1.0, tk.END)
    events = economy.get_active_events()
    if events:
        self.events_text.insert(tk.END, "WYDARZENIA:\n")
        for event in events[:3]:  # Pokaż tylko 3 najważniejsze
            self.events_text.insert(tk.END, f"• {event}\n")
    else:
        self.events_text.insert(tk.END, "Brak aktywnych wydarzeń.")
    
    # Aktualizuj ceny
    self.prices_text.delete(1.0, tk.END)
    self.prices_text.insert(tk.END, "CENY RYNKOWE:\n")
    items = [("Chleb", "chleb"), ("Miecz", "miecz"), ("Metal", "metal")]
    for item_name, item_id in items:
        price = economy.get_enhanced_price(item_id, "prison", 10)
        self.prices_text.insert(tk.END, f"{item_name}: {price:.1f} zł\n")

def create_merchant_dialog(self, npc_id):
    """Okno dialogowe handlu z NPCem"""
    dialog = tk.Toplevel(self.root)
    dialog.title(f"Handel z {npc_id}")
    dialog.geometry("500x400")
    dialog.configure(bg=self.colors['bg'])
    
    # Informacje o handlarzu
    merchant_info = self.game_state.economy.get_merchant_attitude(npc_id, "player")
    
    info_label = tk.Label(dialog, 
                         text=f"Stosunek: {merchant_info['attitude']}\n"
                              f"Kategoria klienta: {merchant_info['customer_tier']}\n"
                              f"Reputacja: {merchant_info['reputation']}",
                         font=self.fonts['normal'],
                         bg=self.colors['bg'],
                         fg=self.colors['text'])
    info_label.pack(pady=10)
    
    # Lista przedmiotów do kupienia/sprzedaży
    # ... implementacja interfejsu handlowego ...
    
    return dialog

# DODAJ do main update loop:
def update_display(self):
    # ... istniejący kod ...
    
    # DODAJ aktualizację ekonomii
    self.update_economy_display()
```

### Krok 4: Konfiguracja NPCów

```python
# Dodaj do merge_npc_data.py lub podobnego pliku:

def setup_enhanced_npcs(game_state):
    """Konfiguruje NPCów z rozszerzonymi funkcjami ekonomicznymi"""
    
    # Dla każdego NPC określ specjalizację handlową
    npc_specializations = {
        "marek": {"personality": "corruptible", "specializations": ["contraband", "information"]},
        "brutus": {"personality": "aggressive", "specializations": ["weapons", "intimidation"]},
        "jozek": {"personality": "wise", "specializations": ["knowledge", "tools"]},
        "anna": {"personality": "calculating", "specializations": ["lockpicks", "escape_gear"]},
        "piotr": {"personality": "gossipy", "specializations": ["information", "rumors"]}
    }
    
    # Konfiguruj handlarzy
    for npc_id, config in npc_specializations.items():
        if npc_id in game_state.economy.merchant_ais:
            merchant_ai = game_state.economy.merchant_ais[npc_id]
            merchant_ai.specializations = config["specializations"]
```

## 📊 API Reference

### EnhancedEconomy

```python
economy = EnhancedEconomy()

# Dodanie handlarza AI
economy.add_merchant_ai("npc_id", "Nazwa", "personality")

# Pobieranie cen z pełnymi modyfikatorami
price = economy.get_enhanced_price("item_id", "market", base_price, "npc_id", "player_id")

# Negocjacje
result = economy.negotiate_price("npc_id", "player_id", "item_id", offered, current, is_buying)

# Transakcje
result = economy.process_enhanced_trade("seller_id", "buyer_id", "item_id", quantity)

# Informacje o wydarzeniach
events = economy.get_active_events()

# Łańcuchy produkcji
chains = economy.get_production_chains("category")
result = economy.simulate_production("chain_id", player_skills, tool_qualities)

# Stan handlarza
attitude = economy.get_merchant_attitude("npc_id", "player_id")
```

### Przykłady Użycia

```python
# Automatyczne wydarzenia co godzinę
if game_time % 60 == 0:
    economy.update_enhanced(game_time)

# Sprawdzenie czy gracz może negocjować
merchant_ai = economy.merchant_ais.get("marek")
if merchant_ai and merchant_ai.negotiation_style == NegotiationStyle.ELASTYCZNY:
    # Negocjacja ma większe szanse powodzenia

# Reakcja na wydarzenia ekonomiczne
events = economy.get_active_events()
for event_desc in events:
    if "niedobór metalu" in event_desc.lower():
        show_notification("Ceny metalowych przedmiotów wzrosły!")
```

## 🧪 Testowanie

Uruchom kompletny test suite:

```bash
python tests/test_enhanced_economy.py
```

Testy obejmują:
- Wydarzenia ekonomiczne
- Łańcuchy produkcji  
- AI handlarzy
- Integrację systemów
- System jakości
- Save/load compatibility

## 🔧 Rozwiązywanie Problemów

### Problem: ImportError dla nowych modułów
```python
# Rozwiązanie: Dodaj fallback w EnhancedEconomy.__init__
try:
    from .economic_events import EconomicEventManager
except ImportError:
    self.event_manager = None
    print("Economic events module not available")
```

### Problem: Ceny są za wysokie/niskie
```python
# Sprawdź aktywne wydarzenia ekonomiczne
events = economy.get_active_events()
print("Active events:", events)

# Sprawdź modyfikatory cen
for item in ["metal", "chleb"]:
    modifier = economy.event_manager.get_price_modifier_for_item(item)
    print(f"{item} price modifier: {modifier}")
```

### Problem: AI handlarze nie pamiętają transakcji
```python
# Sprawdź czy transakcje są przetwarzane przez AI
merchant_ai = economy.merchant_ais["marek"]
transactions = merchant_ai.memory.player_transactions.get("player", [])
print(f"Player transactions with Marek: {len(transactions)}")
```

## 📈 Dalszy Rozwój

System jest zaprojektowany do rozszerzania:

1. **Dodatkowe wydarzenia** - w `economic_events.py`
2. **Nowe łańcuchy produkcji** - w `production_chains.py`
3. **Więcej typów handlarzy** - w `merchant_ai.py`
4. **Sezonowość** - już wbudowana w `EnhancedEconomy`
5. **Międzynarodowy handel** - dodatkowe rynki w systemie

## 🎯 Podsumowanie

System ekonomiczny jest w pełni funkcjonalny i gotowy do integracji. Wszystkie komponenty są przetestowane i kompatybilne z istniejącym systemem gry. Save/load jest obsługiwane automatycznie.

**Kluczowe zalety:**
- ✅ Żywa ekonomia z AI handlarzami
- ✅ Wydarzenia wpływające na rynki  
- ✅ Realistyczne łańcuchy produkcji
- ✅ System jakości i trwałości
- ✅ Pełna kompatybilność wsteczna
- ✅ Comprehensive testing
- ✅ Polish language support

System jest gotowy do użycia w produkcji!