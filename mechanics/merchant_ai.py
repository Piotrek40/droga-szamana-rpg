"""
Inteligentny system AI dla handlarzy w Droga Szamana RPG
Implementuje zaawansowane zachowania NPCów handlarzy z pamięcią, strategią i emocjami
"""

import random
import math
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class MerchantMood(Enum):
    """Nastrój handlarza wpływający na ceny i zachowanie"""
    ROZPACZLIWY = ("rozpaczliwy", 0.6, 1.4, "Desperacko potrzebuje pieniędzy")
    ZMARTWIONY = ("zmartwiony", 0.8, 1.2, "Jest zaniepokojony interesami")
    NEUTRALNY = ("neutralny", 1.0, 1.0, "Spokojny i zrównoważony")
    PEWNY_SIEBIE = ("pewny_siebie", 1.2, 0.8, "Czuje się pewnie w biznesie")
    ZACHŁANNY = ("zachłanny", 1.4, 0.6, "Chce maksymalnych zysków")
    
    def __init__(self, nazwa, sell_modifier, buy_modifier, opis):
        self.nazwa = nazwa
        self.sell_modifier = sell_modifier  # Jak chciwie sprzedaje
        self.buy_modifier = buy_modifier    # Jak hojnie kupuje
        self.opis = opis


class NegotiationStyle(Enum):
    """Style negocjacji handlarzy"""
    AGRESYWNY = ("agresywny", 0.7, "Twardo trzyma się swoich cen")
    ELASTYCZNY = ("elastyczny", 1.3, "Łatwo przystaje na kompromisy")
    OSTROŻNY = ("ostrożny", 0.9, "Rozważnie podchodzi do negocjacji")
    IMPULSYWNY = ("impulsywny", 1.1, "Szybko podejmuje decyzje")
    
    def __init__(self, nazwa, negotiation_modifier, opis):
        self.nazwa = nazwa
        self.modifier = negotiation_modifier
        self.opis = opis


@dataclass
class MarketKnowledge:
    """Wiedza handlarza o rynku"""
    item_price_history: Dict[str, List[float]] = field(default_factory=dict)
    competitor_prices: Dict[str, Dict[str, float]] = field(default_factory=dict)  # competitor_id -> item_prices
    demand_patterns: Dict[str, List[int]] = field(default_factory=dict)  # Historia popytu
    supply_sources: Dict[str, List[str]] = field(default_factory=dict)  # item_id -> list of supplier_names
    seasonal_trends: Dict[str, Dict[str, float]] = field(default_factory=dict)  # season -> item_modifiers
    
    def add_price_observation(self, item_id: str, price: float):
        """Dodaje obserwację ceny do wiedzy"""
        if item_id not in self.item_price_history:
            self.item_price_history[item_id] = []
        
        self.item_price_history[item_id].append(price)
        if len(self.item_price_history[item_id]) > 20:  # Pamiętaj tylko ostatnie 20 cen
            self.item_price_history[item_id].pop(0)
    
    def get_price_trend(self, item_id: str) -> float:
        """Zwraca trend cenowy (-1 do 1, gdzie -1 to spadek, 1 to wzrost)"""
        if item_id not in self.item_price_history or len(self.item_price_history[item_id]) < 3:
            return 0.0
        
        recent_prices = self.item_price_history[item_id][-3:]
        if recent_prices[-1] > recent_prices[0]:
            return min(1.0, (recent_prices[-1] - recent_prices[0]) / recent_prices[0])
        else:
            return max(-1.0, (recent_prices[-1] - recent_prices[0]) / recent_prices[0])
    
    def estimate_fair_price(self, item_id: str) -> Optional[float]:
        """Estymuje sprawiedliwą cenę na podstawie historii"""
        if item_id not in self.item_price_history or not self.item_price_history[item_id]:
            return None
        
        # Średnia ważona z większym naciskiem na nowsze ceny
        prices = self.item_price_history[item_id]
        weights = [i + 1 for i in range(len(prices))]
        weighted_avg = sum(p * w for p, w in zip(prices, weights)) / sum(weights)
        
        return weighted_avg


@dataclass
class MerchantMemory:
    """Pamięć handlarza o transakcjach i graczach"""
    player_transactions: Dict[str, List[Dict]] = field(default_factory=dict)  # player_id -> transactions
    player_reputation: Dict[str, float] = field(default_factory=dict)  # player_id -> reputation (-100 to 100)
    successful_negotiations: Dict[str, int] = field(default_factory=dict)  # player_id -> count
    failed_negotiations: Dict[str, int] = field(default_factory=dict)  # player_id -> count
    last_interaction: Dict[str, int] = field(default_factory=dict)  # player_id -> timestamp
    grudges: Dict[str, str] = field(default_factory=dict)  # player_id -> reason
    favors: Dict[str, str] = field(default_factory=dict)  # player_id -> reason
    
    def add_transaction(self, player_id: str, transaction_data: Dict):
        """Dodaje transakcję do pamięci"""
        if player_id not in self.player_transactions:
            self.player_transactions[player_id] = []
        
        transaction_data['timestamp'] = int(time.time())
        self.player_transactions[player_id].append(transaction_data)
        
        # Ogranicz do ostatnich 50 transakcji na gracza
        if len(self.player_transactions[player_id]) > 50:
            self.player_transactions[player_id].pop(0)
    
    def get_player_reputation(self, player_id: str) -> float:
        """Pobiera reputację gracza"""
        return self.player_reputation.get(player_id, 0.0)
    
    def adjust_reputation(self, player_id: str, change: float, reason: str = ""):
        """Zmienia reputację gracza"""
        current = self.player_reputation.get(player_id, 0.0)
        new_reputation = max(-100.0, min(100.0, current + change))
        self.player_reputation[player_id] = new_reputation
        
        # Dodaj urazę lub łaskę przy ekstremalnych zmianach
        if change <= -20 and reason:
            self.grudges[player_id] = reason
        elif change >= 20 and reason:
            self.favors[player_id] = reason
    
    def get_total_spent(self, player_id: str) -> float:
        """Zwraca całkowitą kwotę wydaną przez gracza"""
        if player_id not in self.player_transactions:
            return 0.0

        total = 0.0
        for transaction in self.player_transactions[player_id]:
            # 'sale' = handlarz sprzedał = gracz kupił = gracz wydał pieniądze
            if transaction['type'] == 'sale':
                total += transaction['amount']

        return total
    
    def get_interaction_frequency(self, player_id: str, current_time: int) -> float:
        """Oblicza częstotliwość interakcji z graczem"""
        if player_id not in self.last_interaction:
            return 0.0
        
        time_since = current_time - self.last_interaction[player_id]
        days_since = time_since / (24 * 60)  # Zakładając, że czas to minuty
        
        transaction_count = len(self.player_transactions.get(player_id, []))
        return transaction_count / max(1.0, days_since)


@dataclass
class MerchantStrategy:
    """Strategia biznesowa handlarza"""
    target_profit_margin: float = 0.3  # Docelowa marża (30%)
    min_profit_margin: float = 0.1     # Minimalna marża (10%)
    max_discount: float = 0.2          # Maksymalny rabat (20%)
    inventory_turnover_target: float = 0.7  # Cel obrotu zapasami (70% tygodniowo)
    cash_reserve_ratio: float = 0.3    # Procent gotówki do wartości zapasów
    
    risk_tolerance: float = 0.5        # Tolerancja ryzyka (0-1)
    market_aggressiveness: float = 0.5  # Agresywność rynkowa (0-1)
    relationship_importance: float = 0.3  # Waga relacji w decyzjach (0-1)
    
    def calculate_target_price(self, base_cost: float, market_conditions: Dict[str, Any]) -> float:
        """Oblicza cenę docelową na podstawie strategii"""
        target_markup = 1.0 + self.target_profit_margin
        
        # Uwzględnij warunki rynkowe
        demand_factor = market_conditions.get('demand_factor', 1.0)
        competition_factor = market_conditions.get('competition_factor', 1.0)
        
        adjusted_markup = target_markup * demand_factor / competition_factor
        return base_cost * adjusted_markup
    
    def should_accept_offer(self, offered_price: float, item_cost: float, 
                           market_position: float) -> bool:
        """Decyduje czy przyjąć ofertę"""
        min_acceptable = item_cost * (1.0 + self.min_profit_margin)
        
        # Uwzględnij pozycję rynkową
        position_modifier = 1.0 + (market_position - 0.5) * self.market_aggressiveness
        adjusted_min = min_acceptable * position_modifier
        
        return offered_price >= adjusted_min


class MerchantAI:
    """Główna klasa AI handlarza"""

    def __init__(self, merchant_id: str, name: str, personality: str = "neutral", npc_reference: Any = None):
        self.merchant_id = merchant_id
        self.name = name
        self.personality = personality
        self.npc_reference = npc_reference  # Opcjonalna referencja do NPC dla synchronizacji pamięci

        # Komponenty AI
        self.mood = self._determine_initial_mood()
        self.negotiation_style = self._determine_negotiation_style()
        self.market_knowledge = MarketKnowledge()
        self.memory = MerchantMemory()
        self.strategy = self._create_strategy()

        # Stan handlarza
        self.energy = 100  # Wpływa na jakość decyzji
        self.stress = 0    # Wpływa na nastrój i ceny
        self.daily_revenue = 0.0
        self.daily_transactions = 0

        # Specjalizacje i preferencje
        self.specializations = self._determine_specializations()
        self.preferred_customers = []  # Typy klientów preferowanych
        self.blacklist = []  # Gracze na czarnej liście
        
    def _determine_initial_mood(self) -> MerchantMood:
        """Określa początkowy nastrój handlarza"""
        if self.personality == "greedy":
            return MerchantMood.ZACHŁANNY
        elif self.personality == "generous":
            return MerchantMood.NEUTRALNY
        elif self.personality == "desperate":
            return MerchantMood.ROZPACZLIWY
        else:
            return random.choice(list(MerchantMood))
    
    def _determine_negotiation_style(self) -> NegotiationStyle:
        """Określa styl negocjacji"""
        if self.personality == "aggressive":
            return NegotiationStyle.AGRESYWNY
        elif self.personality == "flexible":
            return NegotiationStyle.ELASTYCZNY
        else:
            return random.choice(list(NegotiationStyle))
    
    def _create_strategy(self) -> MerchantStrategy:
        """Tworzy strategię biznesową"""
        strategy = MerchantStrategy()
        
        # Dostosuj strategię do osobowości
        if self.personality == "greedy":
            strategy.target_profit_margin = 0.5
            strategy.min_profit_margin = 0.2
            strategy.max_discount = 0.1
        elif self.personality == "generous":
            strategy.target_profit_margin = 0.2
            strategy.min_profit_margin = 0.05
            strategy.max_discount = 0.3
        elif self.personality == "risk_averse":
            strategy.risk_tolerance = 0.2
            strategy.cash_reserve_ratio = 0.5
        elif self.personality == "aggressive":
            strategy.risk_tolerance = 0.8
            strategy.market_aggressiveness = 0.9
        
        return strategy
    
    def _determine_specializations(self) -> List[str]:
        """Określa specjalizacje handlarza"""
        all_specializations = [
            "weapons", "armor", "tools", "food", "materials", 
            "luxury", "potions", "books", "jewelry"
        ]
        
        # Każdy handlarz ma 1-3 specjalizacje
        num_specs = random.randint(1, 3)
        return random.sample(all_specializations, num_specs)
    
    def update_mood(self, current_time: int):
        """Aktualizuje nastrój handlarza"""
        # Podstawowe czynniki wpływające na nastrój
        revenue_factor = min(2.0, max(0.5, self.daily_revenue / 100.0))  # Przychód vs cel
        stress_factor = 1.0 - (self.stress / 100.0)
        energy_factor = self.energy / 100.0
        
        # Oblicz ogólny wskaźnik zadowolenia
        satisfaction = (revenue_factor + stress_factor + energy_factor) / 3.0
        
        # Ustaw nastrój na podstawie zadowolenia
        if satisfaction < 0.3:
            self.mood = MerchantMood.ROZPACZLIWY
        elif satisfaction < 0.5:
            self.mood = MerchantMood.ZMARTWIONY
        elif satisfaction < 0.7:
            self.mood = MerchantMood.NEUTRALNY
        elif satisfaction < 0.9:
            self.mood = MerchantMood.PEWNY_SIEBIE
        else:
            self.mood = MerchantMood.ZACHŁANNY
    
    def calculate_selling_price(self, item_id: str, base_cost: float,
                               player_id: str, market_data: Dict[str, Any]) -> float:
        """Oblicza cenę sprzedaży dla gracza"""
        # Bazowa cena strategiczna
        base_price = self.strategy.calculate_target_price(base_cost, market_data)

        # Modyfikator nastroju
        mood_modifier = self.mood.sell_modifier

        # Modyfikator reputacji gracza (z MerchantMemory)
        reputation = self.memory.get_player_reputation(player_id)
        reputation_modifier = 1.0 - (reputation / 200.0)  # -50% do +50%
        reputation_modifier = max(0.5, min(1.5, reputation_modifier))

        # Modyfikator relacji z NPC (z Relationship.get_overall_disposition)
        relationship_modifier = 1.0
        if self.npc_reference and hasattr(self.npc_reference, 'relationships'):
            rel = self.npc_reference.relationships.get(player_id)
            if rel and hasattr(rel, 'get_overall_disposition'):
                disposition = rel.get_overall_disposition()  # -100 do 100
                # Dobra relacja = niższa cena (do -10%), zła = wyższa (+10%)
                relationship_modifier = 1.0 - (disposition / 1000.0)
                relationship_modifier = max(0.9, min(1.1, relationship_modifier))
        
        # Modyfikator specjalizacji
        specialization_modifier = 1.0
        item_category = market_data.get('category', 'unknown')
        if item_category in self.specializations:
            specialization_modifier = 0.9  # 10% taniej dla specjalizacji
        
        # Modyfikator konkurencji (jeśli wie o cenach konkurencji)
        competition_modifier = 1.0
        if item_id in self.market_knowledge.competitor_prices:
            avg_competitor_price = sum(self.market_knowledge.competitor_prices[item_id].values())
            avg_competitor_price /= len(self.market_knowledge.competitor_prices[item_id])
            
            # Ustaw cenę blisko konkurencji, ale z własnym nastawieniem
            if base_price > avg_competitor_price * 1.2:
                competition_modifier = 0.9  # Obniż cenę jeśli jesteś za drogi
            elif base_price < avg_competitor_price * 0.8:
                competition_modifier = 1.1  # Podnieś cenę jeśli jesteś za tani
        
        # Modyfikator stresu i energii
        performance_modifier = (self.energy / 100.0) * (1.0 - self.stress / 200.0)
        performance_modifier = max(0.8, min(1.2, performance_modifier))
        
        # Finalna cena (z uwzględnieniem relationship_modifier)
        final_price = (base_price * mood_modifier * reputation_modifier * relationship_modifier *
                      specialization_modifier * competition_modifier * performance_modifier)

        # Zaokrąglij do rozsądnej wartości
        return round(final_price, 2)

    def calculate_buying_price(self, item_id: str, item_value: float,
                              player_id: str, market_data: Dict[str, Any]) -> float:
        """Oblicza cenę zakupu od gracza"""
        # Bazowa cena (zwykle 60-80% wartości rynkowej)
        base_buy_ratio = 0.7

        # Modyfikator nastroju
        mood_modifier = self.mood.buy_modifier

        # Modyfikator reputacji gracza
        reputation = self.memory.get_player_reputation(player_id)
        reputation_modifier = 1.0 + (reputation / 300.0)  # -33% do +33%
        reputation_modifier = max(0.4, min(1.4, reputation_modifier))

        # Modyfikator relacji z NPC (z Relationship.get_overall_disposition)
        relationship_modifier = 1.0
        if self.npc_reference and hasattr(self.npc_reference, 'relationships'):
            rel = self.npc_reference.relationships.get(player_id)
            if rel and hasattr(rel, 'get_overall_disposition'):
                disposition = rel.get_overall_disposition()  # -100 do 100
                # Dobra relacja = wyższa cena skupu (do +10%), zła = niższa (-10%)
                relationship_modifier = 1.0 + (disposition / 1000.0)
                relationship_modifier = max(0.9, min(1.1, relationship_modifier))
        
        # Modyfikator potrzeby przedmiotu
        need_modifier = 1.0
        current_stock = market_data.get('current_stock', 5)
        optimal_stock = market_data.get('optimal_stock', 10)
        
        if current_stock < optimal_stock * 0.3:
            need_modifier = 1.3  # Desperacko potrzebuje
        elif current_stock < optimal_stock * 0.6:
            need_modifier = 1.1  # Potrzebuje
        elif current_stock > optimal_stock * 1.5:
            need_modifier = 0.7  # Ma za dużo
        
        # Modyfikator specjalizacji
        specialization_modifier = 1.0
        item_category = market_data.get('category', 'unknown')
        if item_category in self.specializations:
            specialization_modifier = 1.2  # 20% więcej za specjalizację
        
        # Finalna cena (z uwzględnieniem relationship_modifier)
        final_price = (item_value * base_buy_ratio * mood_modifier * relationship_modifier *
                      reputation_modifier * need_modifier * specialization_modifier)

        return round(final_price, 2)
    
    def negotiate(self, player_id: str, item_id: str, offered_price: float, 
                  current_merchant_price: float, is_buying: bool = True) -> Dict[str, Any]:
        """Proces negocjacji z graczem"""
        # Pobierz dane o graczu
        reputation = self.memory.get_player_reputation(player_id)
        negotiation_history = self.memory.successful_negotiations.get(player_id, 0)
        failed_negotiations = self.memory.failed_negotiations.get(player_id, 0)
        
        # Oblicz bazową szansę na sukces negocjacji
        price_difference = abs(offered_price - current_merchant_price) / current_merchant_price
        
        base_success_chance = 0.5  # 50% bazowa szansa
        
        # Modyfikatory szansy
        reputation_factor = (reputation + 100) / 200.0  # 0.0 - 1.0
        experience_factor = min(1.0, negotiation_history / 10.0)  # Doświadczenie w negocjacjach
        style_factor = self.negotiation_style.modifier
        mood_factor = 0.5 + (self.mood.sell_modifier - 1.0)  # Nastrój wpływa na elastyczność
        
        # Im większa różnica cen, tym trudniej
        price_factor = max(0.1, 1.0 - price_difference)
        
        # Specjalny bonus dla stałych klientów
        loyalty_bonus = min(0.2, self.memory.get_total_spent(player_id) / 1000.0)
        
        # Kara za poprzednie nieudane negocjacje
        failure_penalty = min(0.3, failed_negotiations * 0.05)
        
        final_success_chance = (base_success_chance * reputation_factor * style_factor * 
                              mood_factor * price_factor + experience_factor + 
                              loyalty_bonus - failure_penalty)
        
        final_success_chance = max(0.05, min(0.95, final_success_chance))
        
        # Wykonaj test negocjacji
        success = random.random() < final_success_chance
        
        result = {
            "success": success,
            "final_price": current_merchant_price,
            "reason": "",
            "reputation_change": 0
        }
        
        if success:
            # Negocjacja udana - znajdź kompromis
            compromise_ratio = 0.3 + (reputation_factor * 0.4)  # 30-70% w stronę gracza
            if is_buying:  # Gracz sprzedaje handlarzowi
                result["final_price"] = current_merchant_price + (offered_price - current_merchant_price) * compromise_ratio
            else:  # Gracz kupuje od handlarza
                result["final_price"] = current_merchant_price - (current_merchant_price - offered_price) * compromise_ratio
            
            result["reason"] = self._get_negotiation_success_message()
            result["reputation_change"] = random.randint(1, 3)
            
            # Aktualizuj statystyki
            self.memory.successful_negotiations[player_id] = negotiation_history + 1
            
        else:
            # Negocjacja nieudana
            result["reason"] = self._get_negotiation_failure_message()
            result["reputation_change"] = random.randint(-2, -1)
            
            # Aktualizuj statystyki
            self.memory.failed_negotiations[player_id] = failed_negotiations + 1
        
        # Dodaj stres z negocjacji
        self.stress = min(100, self.stress + random.randint(2, 5))
        
        return result
    
    def _get_negotiation_success_message(self) -> str:
        """Zwraca wiadomość przy udanej negocjacji"""
        messages = [
            "W porządku, w porządku... można się dogadać.",
            "Jesteś twardym negocjatorem. Respektuję to.",
            "Dobra, ale to moja ostateczna oferta!",
            "Dla ciebie zrobię wyjątek.",
            "Przekonałeś mnie. Umowa stoi."
        ]
        return random.choice(messages)
    
    def _get_negotiation_failure_message(self) -> str:
        """Zwraca wiadomość przy nieudanej negocjacji"""
        messages = [
            "Przykro mi, ale nie mogę zejść niżej.",
            "Ta cena jest nie do negocjacji.",
            "Chyba żartujesz z tą ofertą!",
            "Muszę jednak na siebie zarobić.",
            "Nie, nie... to za mało."
        ]
        return random.choice(messages)
    
    def process_transaction(self, player_id: str, item_id: str, quantity: int, 
                          total_price: float, transaction_type: str):
        """Przetwarza transakcję i aktualizuje pamięć"""
        # Zapisz transakcję
        transaction_data = {
            "type": transaction_type,  # "purchase" lub "sale"
            "item_id": item_id,
            "quantity": quantity,
            "amount": total_price,
            "price_per_unit": total_price / quantity
        }
        
        self.memory.add_transaction(player_id, transaction_data)
        self.memory.last_interaction[player_id] = int(time.time())

        # Synchronizuj z pamięcią NPC jeśli dostępna
        if self.npc_reference and hasattr(self.npc_reference, 'memory'):
            self.npc_reference.memory.add_episodic_memory(
                event_type='trade_transaction',
                description=f"{transaction_type} {quantity}x {item_id} za {total_price} złota",
                emotional_impact={'satisfaction': 0.2 if transaction_type == 'sale' else 0.1},
                related_entities=[player_id]
            )

        # Aktualizuj wiedzę rynkową
        unit_price = total_price / quantity
        self.market_knowledge.add_price_observation(item_id, unit_price)
        
        # Aktualizuj statystyki dnia
        if transaction_type == "sale":  # Handlarz sprzedał
            self.daily_revenue += total_price
        else:  # Handlarz kupił
            self.daily_revenue -= total_price  # Koszt zakupu
        
        self.daily_transactions += 1
        
        # Zmień energię i stres
        self.energy = max(0, self.energy - random.randint(1, 3))
        self.stress = max(0, self.stress - random.randint(0, 2))  # Transakcje mogą redukować stres
    
    def daily_reset(self):
        """Resetuje dzienne statystyki"""
        self.daily_revenue = 0.0
        self.daily_transactions = 0
        self.energy = min(100, self.energy + random.randint(30, 50))  # Odnowa po odpoczynku
        self.stress = max(0, self.stress - random.randint(10, 20))   # Odpoczynek redukuje stres
    
    def get_attitude_towards_player(self, player_id: str) -> Dict[str, Any]:
        """Zwraca stosunek handlarza do gracza"""
        reputation = self.memory.get_player_reputation(player_id)
        total_spent = self.memory.get_total_spent(player_id)
        
        # Określ kategorię klienta
        if total_spent > 500:
            customer_tier = "VIP"
        elif total_spent > 200:
            customer_tier = "Valued"
        elif total_spent > 50:
            customer_tier = "Regular"
        else:
            customer_tier = "New"
        
        # Określ stosunek na podstawie reputacji
        if reputation >= 50:
            attitude = "Bardzo Przyjazny"
        elif reputation >= 20:
            attitude = "Przyjazny"
        elif reputation >= -20:
            attitude = "Neutralny"
        elif reputation >= -50:
            attitude = "Nieufny"
        else:
            attitude = "Wrogi"
        
        return {
            "attitude": attitude,
            "customer_tier": customer_tier,
            "reputation": reputation,
            "total_spent": total_spent,
            "has_grudge": player_id in self.memory.grudges,
            "has_favor": player_id in self.memory.favors
        }
    
    def save_state(self) -> Dict[str, Any]:
        """Zapisuje stan AI handlarza"""
        return {
            "merchant_id": self.merchant_id,
            "name": self.name,
            "personality": self.personality,
            "mood": self.mood.nazwa,
            "negotiation_style": self.negotiation_style.nazwa,
            "energy": self.energy,
            "stress": self.stress,
            "daily_revenue": self.daily_revenue,
            "daily_transactions": self.daily_transactions,
            "specializations": self.specializations,
            "market_knowledge": {
                "item_price_history": self.market_knowledge.item_price_history,
                "competitor_prices": self.market_knowledge.competitor_prices,
                "demand_patterns": self.market_knowledge.demand_patterns
            },
            "memory": {
                "player_transactions": self.memory.player_transactions,
                "player_reputation": self.memory.player_reputation,
                "successful_negotiations": self.memory.successful_negotiations,
                "failed_negotiations": self.memory.failed_negotiations,
                "last_interaction": self.memory.last_interaction,
                "grudges": self.memory.grudges,
                "favors": self.memory.favors
            },
            "strategy": {
                "target_profit_margin": self.strategy.target_profit_margin,
                "min_profit_margin": self.strategy.min_profit_margin,
                "max_discount": self.strategy.max_discount,
                "risk_tolerance": self.strategy.risk_tolerance
            }
        }
    
    def load_state(self, data: Dict[str, Any]):
        """Wczytuje stan AI handlarza"""
        self.merchant_id = data["merchant_id"]
        self.name = data["name"]
        self.personality = data["personality"]
        self.energy = data["energy"]
        self.stress = data["stress"]
        self.daily_revenue = data["daily_revenue"]
        self.daily_transactions = data["daily_transactions"]
        self.specializations = data["specializations"]
        
        # Wczytaj nastrój
        for mood in MerchantMood:
            if mood.nazwa == data["mood"]:
                self.mood = mood
                break
        
        # Wczytaj styl negocjacji
        for style in NegotiationStyle:
            if style.nazwa == data["negotiation_style"]:
                self.negotiation_style = style
                break
        
        # Wczytaj wiedzę rynkową
        if "market_knowledge" in data:
            mk_data = data["market_knowledge"]
            self.market_knowledge.item_price_history = mk_data.get("item_price_history", {})
            self.market_knowledge.competitor_prices = mk_data.get("competitor_prices", {})
            self.market_knowledge.demand_patterns = mk_data.get("demand_patterns", {})
        
        # Wczytaj pamięć
        if "memory" in data:
            mem_data = data["memory"]
            self.memory.player_transactions = mem_data.get("player_transactions", {})
            self.memory.player_reputation = mem_data.get("player_reputation", {})
            self.memory.successful_negotiations = mem_data.get("successful_negotiations", {})
            self.memory.failed_negotiations = mem_data.get("failed_negotiations", {})
            self.memory.last_interaction = mem_data.get("last_interaction", {})
            self.memory.grudges = mem_data.get("grudges", {})
            self.memory.favors = mem_data.get("favors", {})
        
        # Wczytaj strategię
        if "strategy" in data:
            strat_data = data["strategy"]
            self.strategy.target_profit_margin = strat_data.get("target_profit_margin", 0.3)
            self.strategy.min_profit_margin = strat_data.get("min_profit_margin", 0.1)
            self.strategy.max_discount = strat_data.get("max_discount", 0.2)
            self.strategy.risk_tolerance = strat_data.get("risk_tolerance", 0.5)


if __name__ == "__main__":
    # Test systemu AI handlarza
    print("=== TEST SYSTEMU AI HANDLARZA ===")
    
    # Stwórz handlarza
    merchant = MerchantAI("bjorn_zelazny", "Bjorn Żelazny", "greedy")
    
    print(f"Handlarz: {merchant.name}")
    print(f"Osobowość: {merchant.personality}")
    print(f"Nastrój: {merchant.mood.nazwa} - {merchant.mood.opis}")
    print(f"Styl negocjacji: {merchant.negotiation_style.nazwa}")
    print(f"Specjalizacje: {', '.join(merchant.specializations)}")
    
    # Symuluj kilka transakcji
    market_data = {
        'category': 'weapons',
        'current_stock': 3,
        'optimal_stock': 8
    }
    
    print(f"\n=== SYMULACJA TRANSAKCJI ===")
    
    # Test cen
    selling_price = merchant.calculate_selling_price("miecz", 80.0, "player1", market_data)
    buying_price = merchant.calculate_buying_price("miecz", 100.0, "player1", market_data)
    
    print(f"Cena sprzedaży miecza: {selling_price:.2f} zł")
    print(f"Cena zakupu miecza: {buying_price:.2f} zł")
    
    # Test negocjacji
    negotiation_result = merchant.negotiate("player1", "miecz", 70.0, selling_price, False)
    print(f"\nNegocjacja (oferta 70 zł vs cena {selling_price:.2f} zł):")
    print(f"Sukces: {negotiation_result['success']}")
    print(f"Finalna cena: {negotiation_result['final_price']:.2f} zł")
    print(f"Odpowiedź: {negotiation_result['reason']}")
    
    # Przetestuj transakcję
    if negotiation_result['success']:
        merchant.process_transaction("player1", "miecz", 1, negotiation_result['final_price'], "sale")
        print(f"\nTransakcja przeprowadzona!")
        
        # Sprawdź stosunek do gracza
        attitude = merchant.get_attitude_towards_player("player1")
        print(f"Stosunek do gracza: {attitude['attitude']}")
        print(f"Kategoria klienta: {attitude['customer_tier']}")
        print(f"Reputacja: {attitude['reputation']}")
    
    print(f"\nStan handlarza po transakcji:")
    print(f"Energia: {merchant.energy}")
    print(f"Stres: {merchant.stress}")
    print(f"Dzienny przychód: {merchant.daily_revenue:.2f} zł")