"""
Plugin systemu handlu dla Smart Interface.
Dodaje inteligentne akcje handlowe, porównywanie cen i podpowiedzi ekonomiczne.
"""

from typing import List, Dict, Any, Callable, Optional
from ui.smart_interface import PluginInterface, ContextualAction, ActionType


class TradePlugin(PluginInterface):
    """Plugin rozszerzający interfejs o funkcje handlowe."""
    
    def __init__(self):
        self.price_history = {}  # Śledzi historię cen
        self.merchant_reputation = {}  # Reputacja u kupców
        self.last_trades = []  # Ostatnie transakcje
        self.market_trends = {}  # Trendy rynkowe
        
    def register_actions(self) -> List[ContextualAction]:
        """Rejestruje akcje handlowe."""
        actions = []
        
        # Handel z NPC
        actions.append(ContextualAction(
            id="trade",
            name="Handluj",
            description="Rozpocznij handel z kupcem",
            type=ActionType.TRADE,
            command="handluj",
            icon="🤝",
            hotkey="t",
            condition=lambda ctx: self._has_merchant_nearby(ctx),
            priority=85,
            category="trade"
        ))
        
        # Sprawdź ceny
        actions.append(ContextualAction(
            id="check_prices",
            name="Sprawdź ceny",
            description="Zobacz aktualne ceny towarów",
            type=ActionType.TRADE,
            command="ceny",
            icon="💰",
            hotkey="c",
            condition=lambda ctx: self._has_merchant_nearby(ctx),
            priority=80,
            category="trade"
        ))
        
        # Kup przedmiot
        actions.append(ContextualAction(
            id="buy",
            name="Kup przedmiot",
            description="Zakup wybrany towar",
            type=ActionType.TRADE,
            command="kup",
            icon="🛒",
            condition=lambda ctx: self._in_trade_mode(ctx),
            priority=90,
            category="trade"
        ))
        
        # Sprzedaj przedmiot
        actions.append(ContextualAction(
            id="sell",
            name="Sprzedaj przedmiot",
            description="Sprzedaj przedmiot z ekwipunku",
            type=ActionType.TRADE,
            command="sprzedaj",
            icon="💸",
            condition=lambda ctx: self._in_trade_mode(ctx) and self._has_items_to_sell(ctx),
            priority=89,
            category="trade"
        ))
        
        # Negocjuj cenę
        actions.append(ContextualAction(
            id="negotiate",
            name="Negocjuj cenę",
            description="Próbuj wynegocjować lepszą cenę",
            type=ActionType.TRADE,
            command="negocjuj",
            icon="🗣️",
            hotkey="n",
            condition=lambda ctx: self._in_trade_mode(ctx) and self._can_negotiate(ctx),
            priority=75,
            category="trade"
        ))
        
        # Sprawdź jakość
        actions.append(ContextualAction(
            id="inspect_quality",
            name="Sprawdź jakość towaru",
            description="Dokładnie zbadaj jakość przedmiotu",
            type=ActionType.TRADE,
            command="zbadaj_jakość",
            icon="🔍",
            condition=lambda ctx: self._in_trade_mode(ctx),
            priority=70,
            category="trade"
        ))
        
        # Porównaj ceny
        actions.append(ContextualAction(
            id="compare_prices",
            name="Porównaj ceny",
            description="Porównaj ceny z innymi kupcami",
            type=ActionType.TRADE,
            command="porównaj_ceny",
            icon="📊",
            condition=lambda ctx: len(self.price_history) > 0,
            priority=65,
            category="trade"
        ))
        
        # Masowa transakcja
        actions.append(ContextualAction(
            id="bulk_trade",
            name="Handel hurtowy",
            description="Kup/sprzedaj wiele przedmiotów naraz",
            type=ActionType.TRADE,
            command="hurt",
            icon="📦",
            condition=lambda ctx: self._in_trade_mode(ctx) and self._has_bulk_items(ctx),
            priority=72,
            category="trade"
        ))
        
        # Wymiana barterowa
        actions.append(ContextualAction(
            id="barter",
            name="Wymiana barterowa",
            description="Wymień przedmioty bez użycia złota",
            type=ActionType.TRADE,
            command="wymień",
            icon="🔄",
            condition=lambda ctx: self._in_trade_mode(ctx) and self._merchant_accepts_barter(ctx),
            priority=68,
            category="trade"
        ))
        
        # Sprawdź reputację
        actions.append(ContextualAction(
            id="check_reputation",
            name="Sprawdź reputację handlową",
            description="Zobacz swoją reputację u kupców",
            type=ActionType.TRADE,
            command="reputacja_handlowa",
            icon="⭐",
            condition=lambda ctx: len(self.merchant_reputation) > 0,
            priority=60,
            category="trade"
        ))
        
        return actions
    
    def register_status_widgets(self) -> List[Callable]:
        """Dodaje widgety handlowe do status bara."""
        widgets = []
        
        def gold_widget(game_state):
            """Widget pokazujący ilość złota."""
            if hasattr(game_state.player, 'gold'):
                gold = game_state.player.gold
                if gold > 1000:
                    return f"💰 {gold//1000}k{gold%1000:03d}zł"
                return f"💰 {gold}zł"
            return "💰 0zł"
        
        def market_trend_widget(game_state):
            """Widget pokazujący trend rynkowy."""
            if not self.market_trends:
                return ""
            
            # Pokaż najważniejszy trend
            best_trend = max(self.market_trends.items(), key=lambda x: abs(x[1]))
            item, trend = best_trend
            
            if trend > 0.2:
                arrow = "📈"
            elif trend < -0.2:
                arrow = "📉"
            else:
                arrow = "➡️"
            
            return f"{arrow} {item[:8]}: {int(trend*100):+d}%"
        
        def trade_status_widget(game_state):
            """Widget statusu handlu."""
            if hasattr(game_state, 'in_trade') and game_state.in_trade:
                merchant = getattr(game_state, 'current_merchant', 'Kupiec')
                discount = self._calculate_discount(merchant)
                if discount > 0:
                    return f"🤝 Handel (-{discount}%)"
                return "🤝 Handel"
            return ""
        
        widgets.append(gold_widget)
        widgets.append(market_trend_widget)
        widgets.append(trade_status_widget)
        
        return widgets
    
    def register_parsers(self) -> Dict[str, Callable]:
        """Dodaje parsery dla komend handlowych."""
        parsers = {}
        
        def parse_trade_command(text: str, context: Dict) -> Optional[str]:
            """Parser dla komend handlowych."""
            text = text.lower()
            
            # "kup miecz od kowala" -> "kup miecz kowal"
            if text.startswith("kup "):
                parts = text.split()
                if "od" in parts:
                    od_index = parts.index("od")
                    item = " ".join(parts[1:od_index])
                    merchant = " ".join(parts[od_index+1:])
                    return f"kup {item} {merchant}"
                elif len(parts) > 1:
                    return f"kup {' '.join(parts[1:])}"
            
            # "sprzedaj wszystkie skóry" -> "sprzedaj skóra wszystko"
            if text.startswith("sprzedaj wszystkie "):
                item = text[18:]
                return f"sprzedaj {item} wszystko"
            
            # "ile kosztuje chleb" -> "cena chleb"
            if text.startswith("ile kosztuje "):
                item = text[13:]
                return f"cena {item}"
            
            # "pokaż mi twoje towary" -> "sklep"
            shop_phrases = ["pokaż towary", "co masz", "co sprzedajesz", "sklep"]
            if any(phrase in text for phrase in shop_phrases):
                return "sklep"
            
            return None
        
        def parse_price_query(text: str, context: Dict) -> Optional[str]:
            """Parser dla zapytań o ceny."""
            text = text.lower()
            
            # "czy miecz jest drogi?" -> analiza ceny
            if "drogi" in text or "tani" in text or "opłaca" in text:
                # Znajdź przedmiot
                items = ["miecz", "zbroja", "mikstura", "chleb", "woda"]
                for item in items:
                    if item in text:
                        return f"analiza_ceny {item}"
            
            # "jaka jest cena żelaza?" -> "cena żelazo"
            if "jaka jest cena" in text or "ile kosztuje" in text:
                words = text.split()
                if words:
                    item = words[-1].rstrip("?")
                    return f"cena {item}"
            
            return None
        
        parsers["trade"] = parse_trade_command
        parsers["price"] = parse_price_query
        
        return parsers
    
    def on_action_executed(self, action: str, result: Any):
        """Reaguje na wykonane akcje."""
        # Śledź transakcje
        if "kupił" in str(result) or "sprzedał" in str(result):
            self.last_trades.append({
                "action": action,
                "result": result,
                "timestamp": self._get_game_time()
            })
            if len(self.last_trades) > 20:
                self.last_trades.pop(0)
            
            # Aktualizuj historię cen
            self._update_price_history(action, result)
            
            # Aktualizuj reputację
            self._update_reputation(action, result)
        
        # Śledź trendy rynkowe
        if "cena" in action.lower():
            self._analyze_market_trends(result)
    
    def _has_merchant_nearby(self, context: Dict) -> bool:
        """Sprawdza czy jest kupiec w pobliżu."""
        if "npcs" in context:
            merchant_roles = ["kupiec", "handlarz", "kowal", "alchemik", "karczmarz"]
            for npc in context["npcs"]:
                if any(role in npc.get("role", "").lower() for role in merchant_roles):
                    return True
        return False
    
    def _in_trade_mode(self, context: Dict) -> bool:
        """Sprawdza czy jesteśmy w trybie handlu."""
        game_state = context.get("game_state")
        if game_state and hasattr(game_state, "in_trade"):
            return game_state.in_trade
        return False
    
    def _has_items_to_sell(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma przedmioty do sprzedania."""
        if "player" in context and hasattr(context["player"], "inventory"):
            return len(context["player"].inventory) > 0
        return False
    
    def _can_negotiate(self, context: Dict) -> bool:
        """Sprawdza czy można negocjować."""
        # Można negocjować jeśli ma się odpowiednią umiejętność lub reputację
        player = context.get("player")
        if player:
            # Sprawdź umiejętność handlu
            if hasattr(player, "skills"):
                from player.skills import SkillName
                trade_skill = player.skills.get_skill(SkillName.HANDEL)
                if trade_skill and trade_skill.level > 20:
                    return True
            
            # Sprawdź reputację u tego kupca
            game_state = context.get("game_state")
            current_merchant = getattr(game_state, "current_merchant", None) if game_state else None
            if current_merchant and self.merchant_reputation.get(current_merchant, 0) > 30:
                return True
        
        return False
    
    def _has_bulk_items(self, context: Dict) -> bool:
        """Sprawdza czy gracz ma przedmioty do handlu hurtowego."""
        if "player" in context and hasattr(context["player"], "inventory"):
            # Zlicz duplikaty
            item_counts = {}
            for item in context["player"].inventory:
                item_name = item.get("name", "")
                item_counts[item_name] = item_counts.get(item_name, 0) + 1
            
            # Jeśli ma więcej niż 5 sztuk czegokolwiek
            return any(count >= 5 for count in item_counts.values())
        return False
    
    def _merchant_accepts_barter(self, context: Dict) -> bool:
        """Sprawdza czy kupiec akceptuje wymianę barterową."""
        # Niektórzy kupcy preferują barter
        game_state = context.get("game_state")
        current_merchant = getattr(game_state, "current_merchant", "") if game_state else ""
        barter_merchants = ["koczownik", "przemytnik", "zbieracz"]
        return any(merchant in current_merchant.lower() for merchant in barter_merchants) if current_merchant else False
    
    def _calculate_discount(self, merchant: str) -> int:
        """Oblicza zniżkę na podstawie reputacji."""
        reputation = self.merchant_reputation.get(merchant, 0)
        if reputation > 80:
            return 20  # 20% zniżki
        elif reputation > 50:
            return 10  # 10% zniżki
        elif reputation > 20:
            return 5   # 5% zniżki
        return 0
    
    def _update_price_history(self, action: str, result: Any):
        """Aktualizuje historię cen."""
        # Parsuj cenę z rezultatu
        import re
        price_match = re.search(r'(\d+)\s*(?:złot|zł|gold)', str(result))
        if price_match:
            price = int(price_match.group(1))
            
            # Znajdź przedmiot
            item_match = re.search(r'(kupił|sprzedał)\s+(\w+)', str(result))
            if item_match:
                item = item_match.group(2)
                
                if item not in self.price_history:
                    self.price_history[item] = []
                
                self.price_history[item].append({
                    "price": price,
                    "action": "buy" if "kupił" in str(result) else "sell",
                    "time": self._get_game_time()
                })
                
                # Ogranicz historię
                if len(self.price_history[item]) > 50:
                    self.price_history[item].pop(0)
    
    def _update_reputation(self, action: str, result: Any):
        """Aktualizuje reputację u kupców."""
        if "sukces" in str(result).lower():
            # Znajdź kupca
            merchant = self._extract_merchant_name(result)
            if merchant:
                if merchant not in self.merchant_reputation:
                    self.merchant_reputation[merchant] = 0
                
                # Zwiększ reputację za udane transakcje
                self.merchant_reputation[merchant] += 1
                
                # Max 100
                self.merchant_reputation[merchant] = min(100, self.merchant_reputation[merchant])
    
    def _analyze_market_trends(self, result: Any):
        """Analizuje trendy rynkowe."""
        # Parsuj ceny i porównaj z historią
        for item, history in self.price_history.items():
            if len(history) >= 3:
                # Oblicz trend na podstawie ostatnich 3 cen
                recent_prices = [h["price"] for h in history[-3:]]
                avg_recent = sum(recent_prices) / len(recent_prices)
                
                if len(history) >= 6:
                    older_prices = [h["price"] for h in history[-6:-3]]
                    avg_older = sum(older_prices) / len(older_prices)
                    
                    if avg_older > 0:
                        trend = (avg_recent - avg_older) / avg_older
                        self.market_trends[item] = trend
    
    def _extract_merchant_name(self, result: Any) -> Optional[str]:
        """Wyciąga nazwę kupca z rezultatu."""
        # Note: Implementacja parsowania nazwy kupca
        return "kupiec"
    
    def _get_game_time(self) -> str:
        """Pobiera czas gry."""
        # Note: Integracja z systemem czasu
        return "00:00"
    
    def get_trade_hints(self, context: Dict) -> List[str]:
        """Zwraca kontekstowe podpowiedzi handlowe."""
        hints = []
        
        # Podpowiedzi o cenach
        if self.market_trends:
            for item, trend in self.market_trends.items():
                if trend > 0.3:
                    hints.append(f"📈 Ceny {item} rosną! Lepiej kupić teraz.")
                elif trend < -0.3:
                    hints.append(f"📉 Ceny {item} spadają! Warto poczekać z zakupem.")
        
        # Podpowiedzi o reputacji
        game_state = context.get("game_state")
        current_merchant = getattr(game_state, "current_merchant", None) if game_state else None
        if current_merchant:
            rep = self.merchant_reputation.get(current_merchant, 0)
            if rep > 50:
                hints.append(f"⭐ Masz dobrą reputację u tego kupca - możesz negocjować!")
            elif rep < 10:
                hints.append(f"💭 Zbuduj reputację przez częste transakcje.")
        
        # Podpowiedzi o jakości
        if self._in_trade_mode(context):
            hints.append("💡 Sprawdź jakość przed zakupem - wpływa na trwałość!")
        
        return hints