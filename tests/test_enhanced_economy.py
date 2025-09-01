"""
Comprehensive test suite for the enhanced economy system in Droga Szamana RPG
Tests all components: events, production chains, merchant AI, and market dynamics
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mechanics.economy import EnhancedEconomy, Economy, QualityTier, Item
from mechanics.economic_events import EconomicEventManager, EconomicEvent, EventType
from mechanics.production_chains import ProductionChainManager, ProductionChain, ProductionStep
from mechanics.merchant_ai import MerchantAI, MerchantMood, NegotiationStyle


class TestEconomicEvents(unittest.TestCase):
    """Test suite for economic events system"""
    
    def setUp(self):
        self.event_manager = EconomicEventManager()
    
    def test_event_creation(self):
        """Test creating and managing economic events"""
        # Check that templates are loaded
        self.assertGreater(len(self.event_manager.szablony_wydarzen), 0)
        self.assertIn('krach_rynkowy', self.event_manager.szablony_wydarzen)
        self.assertIn('niedobor_metalu', self.event_manager.szablony_wydarzen)
    
    def test_event_forcing(self):
        """Test manually forcing events"""
        current_time = 1000
        success = self.event_manager.force_event('niedobor_metalu', current_time)
        self.assertTrue(success)
        
        # Check that event is now active
        active_events = self.event_manager.get_active_events()
        self.assertEqual(len(active_events), 1)
        self.assertEqual(active_events[0].typ, EventType.NIEDOBOR_ZASOBOW)
    
    def test_price_modifiers(self):
        """Test event price modifiers"""
        current_time = 1000
        self.event_manager.force_event('niedobor_metalu', current_time)
        
        # Metal should be more expensive
        metal_modifier = self.event_manager.get_price_modifier_for_item('metal')
        self.assertGreater(metal_modifier, 2.0)  # Should be 2.5x more expensive
        
        # Regular items should be unaffected
        bread_modifier = self.event_manager.get_price_modifier_for_item('chleb')
        self.assertEqual(bread_modifier, 1.0)
    
    def test_supply_demand_changes(self):
        """Test event effects on supply and demand"""
        current_time = 1000
        self.event_manager.force_event('karawana_przybyla', current_time)
        
        # Cheese supply should increase
        cheese_supply_change = self.event_manager.get_supply_change_for_item('ser')
        self.assertGreater(cheese_supply_change, 0)
    
    def test_event_expiration(self):
        """Test that events expire correctly"""
        current_time = 1000
        self.event_manager.force_event('niedobor_metalu', current_time)
        
        # Event should be active
        self.assertEqual(len(self.event_manager.get_active_events()), 1)
        
        # Fast forward past expiration
        future_time = current_time + 800  # 800 minutes later (event lasts 720 minutes)
        self.event_manager.update(future_time, {})
        
        # Event should be expired
        self.assertEqual(len(self.event_manager.get_active_events()), 0)
    
    def test_save_load_state(self):
        """Test saving and loading event manager state"""
        current_time = 1000
        self.event_manager.force_event('niedobor_metalu', current_time)
        
        # Save state
        saved_state = self.event_manager.save_state()
        self.assertIn('aktywne_wydarzenia', saved_state)
        self.assertEqual(len(saved_state['aktywne_wydarzenia']), 1)
        
        # Create new manager and load state
        new_manager = EconomicEventManager()
        new_manager.load_state(saved_state)
        
        # Should have same active events
        self.assertEqual(len(new_manager.get_active_events()), 1)
        self.assertEqual(new_manager.get_price_modifier_for_item('metal'), 2.5)


class TestProductionChains(unittest.TestCase):
    """Test suite for production chains system"""
    
    def setUp(self):
        self.production_manager = ProductionChainManager()
    
    def test_chain_loading(self):
        """Test that production chains are loaded correctly"""
        self.assertGreater(len(self.production_manager.chains), 0)
        self.assertIn('miecz_stalowy', self.production_manager.chains)
        self.assertIn('luk_kompozytowy', self.production_manager.chains)
    
    def test_chain_properties(self):
        """Test production chain properties"""
        sword_chain = self.production_manager.get_chain('miecz_stalowy')
        self.assertIsNotNone(sword_chain)
        self.assertEqual(sword_chain.produkt_koncowy, 'miecz')
        self.assertGreater(len(sword_chain.kroki), 0)
        self.assertGreater(sword_chain.oblicz_calkowity_czas(), 0)
    
    def test_resource_requirements(self):
        """Test calculating resource requirements"""
        sword_chain = self.production_manager.get_chain('miecz_stalowy')
        resources = sword_chain.get_wszystkie_surowce()
        self.assertIsInstance(resources, dict)
        self.assertGreater(len(resources), 0)
    
    def test_skill_requirements(self):
        """Test skill requirements"""
        sword_chain = self.production_manager.get_chain('miecz_stalowy')
        skills = sword_chain.get_wszystkie_umiejetnosci()
        self.assertIsInstance(skills, list)
        self.assertIn('kowalstwo', skills)
    
    def test_available_chains_filtering(self):
        """Test filtering chains by player skills"""
        player_skills = {
            'kowalstwo': 60,
            'stolarstwo': 30,
            'hutnictwo': 40
        }
        
        available = self.production_manager.get_available_chains(player_skills, 0.5)
        self.assertIsInstance(available, list)
        # Should return some chains that match skill levels
        
    def test_production_simulation(self):
        """Test simulating production"""
        player_skills = {
            'kowalstwo': 60,
            'stolarstwo': 40,
            'hutnictwo': 50
        }
        tool_qualities = {
            'mlotek_kowala': 70,
            'kowadlo': 65
        }
        
        result = self.production_manager.simulate_production('miecz_stalowy', player_skills, tool_qualities)
        self.assertIsInstance(result, dict)
        self.assertIn('sukces', result)
        self.assertIn('calkowity_czas', result)
        self.assertIn('kroki_szczegoly', result)
    
    def test_resource_extraction(self):
        """Test resource extraction from nodes"""
        player_skills = {'górnictwo': 35}
        result = self.production_manager.extract_from_node('kamieniołom', player_skills, 60)
        
        self.assertIsInstance(result, dict)
        self.assertIn('sukces', result)
        if result['sukces']:
            self.assertIn('zasoby', result)
            self.assertIn('czas', result)


class TestMerchantAI(unittest.TestCase):
    """Test suite for merchant AI system"""
    
    def setUp(self):
        self.merchant = MerchantAI("test_merchant", "Test Merchant", "greedy")
    
    def test_merchant_initialization(self):
        """Test merchant AI initialization"""
        self.assertEqual(self.merchant.name, "Test Merchant")
        self.assertEqual(self.merchant.personality, "greedy")
        self.assertIsInstance(self.merchant.mood, MerchantMood)
        self.assertIsInstance(self.merchant.negotiation_style, NegotiationStyle)
        self.assertGreater(len(self.merchant.specializations), 0)
    
    def test_price_calculation(self):
        """Test price calculation logic"""
        market_data = {
            'category': 'weapons',
            'current_stock': 5,
            'optimal_stock': 10,
            'demand_factor': 1.2,
            'competition_factor': 0.9
        }
        
        selling_price = self.merchant.calculate_selling_price("miecz", 50.0, "player1", market_data)
        buying_price = self.merchant.calculate_buying_price("miecz", 60.0, "player1", market_data)
        
        self.assertIsInstance(selling_price, float)
        self.assertIsInstance(buying_price, float)
        self.assertGreater(selling_price, 0)
        self.assertGreater(buying_price, 0)
        self.assertGreater(selling_price, buying_price)  # Should sell for more than buy
    
    def test_negotiation(self):
        """Test negotiation system"""
        offered_price = 40.0
        current_price = 50.0
        
        result = self.merchant.negotiate("player1", "miecz", offered_price, current_price, False)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('final_price', result)
        self.assertIn('reason', result)
        self.assertIn('reputation_change', result)
        
        if result['success']:
            # Final price should be between offered and current
            final_price = result['final_price']
            self.assertGreaterEqual(final_price, min(offered_price, current_price))
            self.assertLessEqual(final_price, max(offered_price, current_price))
    
    def test_transaction_processing(self):
        """Test transaction processing and memory"""
        self.merchant.process_transaction("player1", "miecz", 1, 50.0, "sale")
        
        # Check that transaction was recorded
        player_transactions = self.merchant.memory.player_transactions.get("player1", [])
        self.assertEqual(len(player_transactions), 1)
        self.assertEqual(player_transactions[0]['item_id'], "miecz")
        self.assertEqual(player_transactions[0]['amount'], 50.0)
    
    def test_reputation_system(self):
        """Test reputation tracking"""
        initial_reputation = self.merchant.memory.get_player_reputation("player1")
        self.assertEqual(initial_reputation, 0.0)
        
        # Adjust reputation
        self.merchant.memory.adjust_reputation("player1", 10.0, "good deal")
        new_reputation = self.merchant.memory.get_player_reputation("player1")
        self.assertEqual(new_reputation, 10.0)
        
        # Test bounds
        self.merchant.memory.adjust_reputation("player1", 150.0, "amazing")
        capped_reputation = self.merchant.memory.get_player_reputation("player1")
        self.assertEqual(capped_reputation, 100.0)
    
    def test_attitude_calculation(self):
        """Test attitude calculation towards players"""
        # Start with neutral
        attitude = self.merchant.get_attitude_towards_player("player1")
        self.assertEqual(attitude['customer_tier'], 'New')
        
        # Process some transactions to build history
        self.merchant.process_transaction("player1", "miecz", 1, 100.0, "sale")
        self.merchant.process_transaction("player1", "kilof", 1, 50.0, "sale")
        
        new_attitude = self.merchant.get_attitude_towards_player("player1")
        self.assertEqual(new_attitude['customer_tier'], 'Regular')
        self.assertGreater(new_attitude['total_spent'], 0)
    
    def test_save_load_state(self):
        """Test saving and loading merchant state"""
        # Add some data
        self.merchant.process_transaction("player1", "miecz", 1, 50.0, "sale")
        self.merchant.memory.adjust_reputation("player1", 15.0, "good customer")
        
        # Save state
        saved_state = self.merchant.save_state()
        self.assertIn('merchant_id', saved_state)
        self.assertIn('memory', saved_state)
        
        # Create new merchant and load state
        new_merchant = MerchantAI("test_merchant", "Test Merchant", "greedy")
        new_merchant.load_state(saved_state)
        
        # Check that data was loaded correctly
        self.assertEqual(new_merchant.memory.get_player_reputation("player1"), 15.0)
        self.assertEqual(len(new_merchant.memory.player_transactions.get("player1", [])), 1)


class TestEnhancedEconomy(unittest.TestCase):
    """Test suite for the enhanced economy system"""
    
    def setUp(self):
        self.economy = EnhancedEconomy()
    
    def test_economy_initialization(self):
        """Test enhanced economy initialization"""
        self.assertIsNotNone(self.economy.event_manager)
        self.assertIsNotNone(self.economy.production_manager)
        self.assertIsInstance(self.economy.merchant_ais, dict)
        self.assertIn('prison', self.economy.markets)
    
    def test_merchant_ai_integration(self):
        """Test adding and using merchant AIs"""
        self.economy.add_merchant_ai("bjorn", "Bjorn Ironsmith", "greedy")
        
        self.assertIn("bjorn", self.economy.merchant_ais)
        self.assertIn("bjorn", self.economy.npcs)
        
        # Test getting enhanced prices
        price = self.economy.get_enhanced_price("miecz", "prison", 50, "bjorn", "player1")
        self.assertIsInstance(price, float)
        self.assertGreater(price, 0)
    
    def test_negotiation_integration(self):
        """Test negotiation through economy system"""
        self.economy.add_merchant_ai("bjorn", "Bjorn Ironsmith", "greedy")
        
        result = self.economy.negotiate_price("bjorn", "player1", "miecz", 40.0, 50.0, False)
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
    
    def test_enhanced_trading(self):
        """Test enhanced trading with AI merchants"""
        self.economy.add_merchant_ai("bjorn", "Bjorn Ironsmith", "greedy")
        
        # Test player buying from merchant
        result = self.economy.process_enhanced_trade("bjorn", "player", "miecz", 1)
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('message', result)
    
    def test_economic_events_integration(self):
        """Test integration with economic events"""
        # Force an event
        if self.economy.event_manager:
            self.economy.event_manager.force_event('niedobor_metalu', 1000)
            
            # Get active events
            events = self.economy.get_active_events()
            self.assertGreater(len(events), 0)
            
            # Prices should be affected
            metal_price = self.economy.get_enhanced_price("metal", "prison", 10)
            normal_price = self.economy.get_enhanced_price("chleb", "prison", 5)
            
            # Metal should be more expensive due to shortage
            self.assertGreater(metal_price, 10)
    
    def test_production_chains_integration(self):
        """Test integration with production chains"""
        chains = self.economy.get_production_chains("weapons")
        self.assertIsInstance(chains, list)
        
        if len(chains) > 0:
            # Test production simulation
            player_skills = {'kowalstwo': 50, 'hutnictwo': 40}
            result = self.economy.simulate_production(chains[0]['id'], player_skills)
            self.assertIsInstance(result, dict)
    
    def test_seasonal_effects(self):
        """Test seasonal price modifiers"""
        # Force seasonal update
        self.economy._update_seasonal_modifiers()
        
        self.assertIsInstance(self.economy.seasonal_modifiers, dict)
        # Should have some seasonal modifiers
    
    def test_economic_indicators(self):
        """Test economic indicators tracking"""
        indicators = self.economy.economic_indicators
        
        self.assertIn('inflation_rate', indicators)
        self.assertIn('market_stability', indicators)
        self.assertGreaterEqual(indicators['inflation_rate'], 0)
        self.assertGreaterEqual(indicators['market_stability'], 0)
        self.assertLessEqual(indicators['market_stability'], 1.0)
    
    def test_update_system(self):
        """Test the enhanced update system"""
        # Add some merchants
        self.economy.add_merchant_ai("bjorn", "Bjorn Ironsmith", "greedy")
        
        # Run updates for several time periods
        for time_period in [60, 120, 1440]:  # 1h, 2h, 1 day
            try:
                self.economy.update_enhanced(time_period)
            except Exception as e:
                self.fail(f"Update failed at time {time_period}: {e}")
    
    def test_merchant_attitude_tracking(self):
        """Test merchant attitude system"""
        self.economy.add_merchant_ai("bjorn", "Bjorn Ironsmith", "greedy")
        
        attitude = self.economy.get_merchant_attitude("bjorn", "player1")
        self.assertIsInstance(attitude, dict)
        self.assertIn('attitude', attitude)
        self.assertIn('customer_tier', attitude)
        self.assertIn('reputation', attitude)
    
    def test_save_load_enhanced_state(self):
        """Test saving and loading enhanced economy state"""
        # Set up some state
        self.economy.add_merchant_ai("bjorn", "Bjorn Ironsmith", "greedy")
        self.economy.add_merchant_ai("helga", "Helga Trader", "generous")
        
        if self.economy.event_manager:
            self.economy.event_manager.force_event('niedobor_metalu', 1000)
        
        # Save state
        saved_state = self.economy.save_enhanced_state()
        
        self.assertIn('merchant_ais', saved_state)
        self.assertIn('economic_indicators', saved_state)
        self.assertEqual(len(saved_state['merchant_ais']), 2)
        
        # Create new economy and load state
        new_economy = EnhancedEconomy()
        new_economy.load_enhanced_state(saved_state)
        
        # Verify state was loaded
        self.assertEqual(len(new_economy.merchant_ais), 2)
        self.assertIn('bjorn', new_economy.merchant_ais)
        self.assertIn('helga', new_economy.merchant_ais)


class TestQualitySystem(unittest.TestCase):
    """Test suite for item quality system"""
    
    def test_quality_tier_classification(self):
        """Test quality tier classification"""
        self.assertEqual(QualityTier.get_tier(10), QualityTier.OKROPNA)
        self.assertEqual(QualityTier.get_tier(30), QualityTier.SŁABA)
        self.assertEqual(QualityTier.get_tier(50), QualityTier.PRZECIĘTNA)
        self.assertEqual(QualityTier.get_tier(70), QualityTier.DOBRA)
        self.assertEqual(QualityTier.get_tier(90), QualityTier.DOSKONAŁA)
    
    def test_item_value_calculation(self):
        """Test item value calculation with quality"""
        item = Item(
            id="test_item",
            nazwa="Test Item",
            typ="weapon",
            opis="Test description",
            waga=1.0,
            bazowa_wartosc=100,
            trwalosc=200,
            kategoria="weapon",
            efekty={},
            jakosc=80,
            obecna_trwalosc=200
        )
        
        # Quality 80 should give 1.5x multiplier, full durability = 1.0x
        expected_value = 100 * 1.5 * 1.0  # base * quality * durability
        self.assertEqual(item.aktualna_wartosc, expected_value)
    
    def test_item_durability_effects(self):
        """Test durability effects on value"""
        item = Item(
            id="test_item",
            nazwa="Test Item", 
            typ="weapon",
            opis="Test description",
            waga=1.0,
            bazowa_wartosc=100,
            trwalosc=100,
            kategoria="weapon",
            efekty={},
            jakosc=50,  # Average quality = 1.0x multiplier
            obecna_trwalosc=50  # Half durability = 0.5x multiplier
        )
        
        expected_value = 100 * 1.0 * 0.5  # base * quality * durability
        self.assertEqual(item.aktualna_wartosc, expected_value)
    
    def test_item_repair(self):
        """Test item repair functionality"""
        item = Item(
            id="test_item",
            nazwa="Test Item",
            typ="tool",
            opis="Test description", 
            waga=1.0,
            bazowa_wartosc=50,
            trwalosc=100,
            kategoria="tool",
            efekty={},
            obecna_trwalosc=30
        )
        
        # Repair item
        item.napraw(40)
        self.assertEqual(item.obecna_trwalosc, 70)
        
        # Can't repair beyond max
        item.napraw(50)
        self.assertEqual(item.obecna_trwalosc, 100)
    
    def test_item_usage(self):
        """Test item usage and durability loss"""
        item = Item(
            id="test_item",
            nazwa="Test Item",
            typ="tool",
            opis="Test description",
            waga=1.0,
            bazowa_wartosc=50,
            trwalosc=100,
            kategoria="tool",
            efekty={},
            obecna_trwalosc=100
        )
        
        # Use item
        item.zuzyj(20)
        self.assertEqual(item.obecna_trwalosc, 80)
        self.assertFalse(item.czy_zepsute())
        
        # Use until broken
        item.zuzyj(100)
        self.assertEqual(item.obecna_trwalosc, 0)
        self.assertTrue(item.czy_zepsute())


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete economy system"""
    
    def setUp(self):
        self.economy = EnhancedEconomy()
        
        # Set up a complete economic scenario
        self.economy.add_merchant_ai("bjorn", "Bjorn Ironsmith", "greedy")
        self.economy.add_merchant_ai("helga", "Helga Trader", "generous")
        self.economy.add_merchant_ai("erik", "Erik Woodworker", "normal")
    
    def test_complete_economic_cycle(self):
        """Test a complete economic cycle with multiple merchants"""
        # Initial state check
        self.assertEqual(len(self.economy.merchant_ais), 3)
        
        # Simulate player interactions with each merchant
        for merchant_id in ["bjorn", "helga", "erik"]:
            # Get prices
            sword_price = self.economy.get_enhanced_price("miecz", "prison", 50, merchant_id, "player1")
            self.assertGreater(sword_price, 0)
            
            # Attempt negotiation
            negotiation = self.economy.negotiate_price(merchant_id, "player1", "miecz", 
                                                     sword_price * 0.8, sword_price, False)
            self.assertIsInstance(negotiation, dict)
            
            # Process trade
            trade = self.economy.process_enhanced_trade(merchant_id, "player", "miecz", 1)
            self.assertIsInstance(trade, dict)
    
    def test_economic_events_impact(self):
        """Test how economic events impact the entire system"""
        if not self.economy.event_manager:
            self.skipTest("Economic events not available")
        
        # Force a metal shortage event
        self.economy.event_manager.force_event('niedobor_metalu', 1000)
        
        # Check impact on different merchants
        for merchant_id in ["bjorn", "helga", "erik"]:
            metal_price = self.economy.get_enhanced_price("metal", "prison", 10, merchant_id, "player1")
            bread_price = self.economy.get_enhanced_price("chleb", "prison", 3, merchant_id, "player1")
            
            # Metal should be more expensive, bread should be normal
            self.assertGreater(metal_price, 15)  # Should be increased due to shortage
    
    def test_market_dynamics_over_time(self):
        """Test market dynamics over multiple time periods"""
        initial_prices = {}
        
        # Record initial prices
        for item in ["miecz", "chleb", "metal"]:
            initial_prices[item] = self.economy.get_enhanced_price(item, "prison", 10, "bjorn", "player1")
        
        # Simulate time passing with updates
        for day in range(1, 4):
            self.economy.update_enhanced(day * 1440)  # Each day = 1440 minutes
            
            # Check that prices can change
            current_prices = {}
            for item in ["miecz", "chleb", "metal"]:
                current_prices[item] = self.economy.get_enhanced_price(item, "prison", 10, "bjorn", "player1")
            
            # Prices should still be positive
            for price in current_prices.values():
                self.assertGreater(price, 0)
    
    def test_merchant_relationship_development(self):
        """Test how merchant relationships develop over time"""
        merchant_id = "bjorn"
        player_id = "test_player"
        
        # Initial attitude
        initial_attitude = self.economy.get_merchant_attitude(merchant_id, player_id)
        self.assertEqual(initial_attitude['customer_tier'], 'New')
        
        # Simulate multiple successful transactions
        for i in range(5):
            trade_result = self.economy.process_enhanced_trade(merchant_id, "player", "chleb", 1)
            if trade_result['success']:
                # Process through merchant AI
                if merchant_id in self.economy.merchant_ais:
                    merchant_ai = self.economy.merchant_ais[merchant_id]
                    merchant_ai.memory.adjust_reputation(player_id, 2.0, "successful trade")
        
        # Check attitude development
        final_attitude = self.economy.get_merchant_attitude(merchant_id, player_id)
        self.assertGreaterEqual(final_attitude['reputation'], initial_attitude['reputation'])


def run_comprehensive_tests():
    """Run all tests and provide summary"""
    print("=== COMPREHENSIVE ECONOMIC SYSTEM TESTS ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestEconomicEvents,
        TestProductionChains,
        TestMerchantAI,
        TestEnhancedEconomy,
        TestQualitySystem,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n=== TEST SUMMARY ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0] if 'AssertionError:' in traceback else 'Unknown failure'}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\\n')[-2] if traceback else 'Unknown error'}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run comprehensive tests
    success = run_comprehensive_tests()
    
    if success:
        print("\n🎉 All tests passed! Economic system is ready for production.")
    else:
        print("\n❌ Some tests failed. Please review and fix issues before deployment.")
    
    exit(0 if success else 1)