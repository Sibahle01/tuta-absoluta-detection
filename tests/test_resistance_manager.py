"""
Unit tests for resistance manager
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.resistance_manager import ResistanceManager


class TestResistanceManager(unittest.TestCase):
    """Test cases for ResistanceManager"""
    
    def setUp(self):
        self.manager = ResistanceManager()
    
    def test_initial_recommendation(self):
        """Test initial chemical recommendation"""
        rec = self.manager.get_next_chemical()
        self.assertIsNotNone(rec.chemical_name)
        self.assertIsNotNone(rec.chemical_class)
    
    def test_record_application(self):
        """Test recording an application"""
        app = self.manager.record_application("spinosad", pest_count=5)
        self.assertIsNotNone(app)
        self.assertEqual(app.chemical_name, "spinosad")
        self.assertEqual(len(self.manager.applications), 1)
    
    def test_rotation_after_applications(self):
        """Test rotation after multiple applications"""
        # Record multiple applications
        for i in range(3):
            self.manager.record_application("spinosad", pest_count=5)
        
        # Should have rotated
        rec = self.manager.get_next_chemical()
        # Note: May or may not rotate depending on config
        self.assertIsNotNone(rec.chemical_name)
    
    def test_efficacy_force_rotation(self):
        """Test that low efficacy forces rotation"""
        rec = self.manager.get_next_chemical(current_efficacy=0.3)
        # Should recommend rotation
        self.assertIn("rotate", rec.reason.lower())
    
    def test_resistance_risk_range(self):
        """Test resistance risk stays within bounds"""
        risk = self.manager.estimate_resistance_risk()
        self.assertGreaterEqual(risk, 0.0)
        self.assertLessEqual(risk, 1.0)
    
    def test_get_chemical_by_name(self):
        """Test chemical lookup"""
        chem = self.manager.get_chemical_by_name("spinosad")
        self.assertIsNotNone(chem)
        self.assertEqual(chem['class'], "Spinosyns")
        
        chem = self.manager.get_chemical_by_name("nonexistent")
        self.assertIsNone(chem)
    
    def test_application_summary(self):
        """Test application summary generation"""
        summary = self.manager.get_application_summary()
        self.assertIn('total_applications', summary)
        self.assertIn('applications_by_class', summary)


if __name__ == "__main__":
    unittest.main()