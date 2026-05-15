"""
Integration tests for the complete system
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.decision_engine import PestPressureIndex
from core.resistance_manager import ResistanceManager
from alerts.notifier import ConsoleNotifier
from alerts.logger import JSONLogger
from simulation.scenarios import ALL_SCENARIOS


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        self.decision_engine = PestPressureIndex()
        self.resistance_manager = ResistanceManager()
        self.notifier = ConsoleNotifier()
        self.logger = JSONLogger(log_dir="test_logs")
    
    def test_end_to_end_scenario(self):
        """Test complete flow: detection → decision → notification → logging"""
        
        # Simulate detection result
        pest_count = 5
        temperature = 28
        humidity = 65
        
        # Make decision
        decision = self.decision_engine.decide(pest_count, temperature, humidity)
        
        # Get chemical recommendation if needed
        chemical = None
        if decision.action == "spray":
            chemical = self.resistance_manager.get_next_chemical()
        
        # Log event
        self.logger.log({
            'pest_count': pest_count,
            'temperature': temperature,
            'humidity': humidity,
            'ppi': decision.pest_pressure_index,
            'action': decision.action,
            'message': decision.message,
            'recommended_chemical': chemical.chemical_name if chemical else None
        })
        
        # Verify
        self.assertEqual(decision.action, "spray")
        self.assertIsNotNone(chemical)
        self.assertGreater(len(self.logger.get_events()), 0)
    
    def test_all_scenarios_integration(self):
        """Test all literature scenarios through the system"""
        
        results = []
        for scenario in ALL_SCENARIOS:
            decision = self.decision_engine.decide(
                scenario.pest_count,
                scenario.temperature,
                scenario.humidity
            )
            
            results.append({
                'scenario': scenario.name,
                'action': decision.action,
                'ppi': decision.pest_pressure_index
            })
            
            # Log each scenario
            self.logger.log({
                'scenario': scenario.name,
                'pest_count': scenario.pest_count,
                'temperature': scenario.temperature,
                'humidity': scenario.humidity,
                'action': decision.action,
                'ppi': decision.pest_pressure_index
            })
        
        # Verify all scenarios processed
        self.assertEqual(len(results), len(ALL_SCENARIOS))
        
        # Verify logs created
        events = self.logger.get_events()
        self.assertGreaterEqual(len(events), len(ALL_SCENARIOS))
    
    def test_system_state_consistency(self):
        """Test that system state remains consistent across operations"""
        
        # Multiple decision calls should not cause errors
        for _ in range(10):
            decision = self.decision_engine.decide(3, 25, 60)
            self.assertIsNotNone(decision.action)
            
            # Record application if needed
            if decision.action == "spray":
                self.resistance_manager.record_application("spinosad", pest_count=3)
        
        # Should have recorded some applications
        summary = self.resistance_manager.get_application_summary()
        self.assertIsNotNone(summary)


if __name__ == "__main__":
    unittest.main()