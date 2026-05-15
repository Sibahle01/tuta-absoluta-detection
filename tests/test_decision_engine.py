"""
Unit tests for decision engine
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.decision_engine import PestPressureIndex
from simulation.scenarios import ALL_SCENARIOS


class TestDecisionEngine(unittest.TestCase):
    """Test cases for PestPressureIndex"""
    
    def setUp(self):
        self.engine = PestPressureIndex()
    
    def test_economic_threshold(self):
        """Test that economic threshold triggers spray action"""
        # Below threshold
        result = self.engine.decide(3, 25, 60)
        self.assertNotEqual(result.action, "spray")
        
        # At threshold
        result = self.engine.decide(4, 25, 60)
        self.assertEqual(result.action, "spray")
        
        # Above threshold
        result = self.engine.decide(8, 25, 60)
        self.assertEqual(result.action, "spray")
    
    def test_temperature_factor(self):
        """Test temperature factor calculation"""
        # Cold - factor should be low
        factor_cold = self.engine.compute_temperature_factor(5)
        self.assertLess(factor_cold, 0.1)
        
        # Optimal - factor should be 1
        factor_opt = self.engine.compute_temperature_factor(25)
        self.assertEqual(factor_opt, 1.0)
        
        # Hot - factor should decrease
        factor_hot = self.engine.compute_temperature_factor(38)
        self.assertLess(factor_hot, 0.5)
    
    def test_humidity_factor(self):
        """Test humidity factor calculation"""
        # Too dry
        factor_dry = self.engine.compute_humidity_factor(10)
        self.assertEqual(factor_dry, 0.0)
        
        # Optimal
        factor_opt = self.engine.compute_humidity_factor(55)
        self.assertEqual(factor_opt, 1.0)
        
        # Too wet
        factor_wet = self.engine.compute_humidity_factor(90)
        self.assertLess(factor_wet, 0.5)
    
    def test_normalize_pest_count(self):
        """Test pest count normalization"""
        self.assertEqual(self.engine.normalize_pest_count(0), 0.0)
        self.assertEqual(self.engine.normalize_pest_count(4), 1.0)  # At threshold
        self.assertEqual(self.engine.normalize_pest_count(2), 0.5)  # Half threshold
        self.assertEqual(self.engine.normalize_pest_count(8), 1.0)  # Above threshold caps at 1
    
    def test_ppi_range(self):
        """Test PPI stays within 0-1 range"""
        # Test various inputs
        test_cases = [
            (0, 25, 60),
            (10, 25, 60),
            (4, 35, 60),
            (4, 25, 10),
            (4, 25, 90),
            (0, 5, 60),
        ]
        
        for pest, temp, hum in test_cases:
            ppi = self.engine.compute_ppi(pest, temp, hum)
            self.assertGreaterEqual(ppi, 0.0)
            self.assertLessEqual(ppi, 1.0)
    
    def test_trend_factor(self):
        """Test trend factor calculation"""
        # Reset history
        self.engine.pest_history = []
        
        # Not enough history - should be neutral
        factor = self.engine.compute_trend_factor()
        self.assertEqual(factor, 0.5)
        
        # Add history
        for count in [1, 2, 3, 4]:
            self.engine.compute_ppi(count, 25, 60)
        
        # Should be above neutral (increasing)
        factor = self.engine.compute_trend_factor()
        self.assertGreater(factor, 0.5)
    
    def test_scenario_validation(self):
        """Test against all literature scenarios"""
        for scenario in ALL_SCENARIOS:
            result = self.engine.decide(
                scenario.pest_count,
                scenario.temperature,
                scenario.humidity
            )
            
            # Check that result makes sense for this scenario
            if scenario.expected_action == "spray":
                self.assertIn(result.action, ["spray"], 
                             f"Failed: {scenario.name} expected spray, got {result.action}")
            elif scenario.expected_action == "warning":
                self.assertIn(result.action, ["warning", "spray"],
                             f"Failed: {scenario.name} expected warning, got {result.action}")
            elif scenario.expected_action == "monitor":
                self.assertIn(result.action, ["monitor", "warning", "spray"],
                             f"Failed: {scenario.name} expected monitor, got {result.action}")


if __name__ == "__main__":
    unittest.main()