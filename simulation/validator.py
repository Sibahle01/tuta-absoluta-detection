"""
Validation framework for testing system against literature scenarios
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass, field

from core.decision_engine import PestPressureIndex
from simulation.scenarios import TestScenario, ALL_SCENARIOS


@dataclass
class ValidationResult:
    """Result of a single validation test"""
    scenario: TestScenario
    actual_action: str
    expected_action: str
    passed: bool
    ppi: float
    message: str
    details: Dict = field(default_factory=dict)


class Validator:
    """Validates system against literature scenarios"""
    
    def __init__(self):
        self.engine = PestPressureIndex()
        self.results: List[ValidationResult] = []
    
    def validate_scenario(self, scenario: TestScenario) -> ValidationResult:
        """Validate a single scenario"""
        decision = self.engine.decide(
            scenario.pest_count,
            scenario.temperature,
            scenario.humidity
        )
        
        actual_action = decision.action
        expected = scenario.expected_action
        
        # Check if action matches expectation (allow "spray" for "critical" etc.)
        passed = False
        if expected == "spray" and actual_action == "spray":
            passed = True
        elif expected == "warning" and actual_action in ["warning", "spray"]:
            passed = True  # Warning or higher is acceptable
        elif expected == "monitor" and actual_action in ["monitor", "warning", "spray"]:
            passed = True  # Monitor or higher is acceptable
        elif expected == "none" and actual_action == "none":
            passed = True
        elif expected == actual_action:
            passed = True
        
        message = f"Expected {expected}, got {actual_action}"
        
        return ValidationResult(
            scenario=scenario,
            actual_action=actual_action,
            expected_action=expected,
            passed=passed,
            ppi=decision.pest_pressure_index,
            message=message,
            details={
                'temperature_factor': decision.temperature_factor,
                'humidity_factor': decision.humidity_factor,
                'trend_factor': decision.trend_factor,
                'full_message': decision.message
            }
        )
    
    def validate_all(self, scenarios: List[TestScenario] = None) -> List[ValidationResult]:
        """Validate all scenarios"""
        if scenarios is None:
            scenarios = ALL_SCENARIOS
        
        self.results = []
        for scenario in scenarios:
            result = self.validate_scenario(scenario)
            self.results.append(result)
        
        return self.results
    
    def get_summary(self) -> Dict:
        """Get validation summary"""
        if not self.results:
            return {'error': 'No results yet'}
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        passed_pct = (passed / total) * 100 if total > 0 else 0
        
        return {
            'total_scenarios': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed_pct,
            'action_distribution': self._get_action_distribution(),
            'failed_scenarios': [r.scenario.name for r in self.results if not r.passed]
        }
    
    def _get_action_distribution(self) -> Dict:
        """Get distribution of actual actions"""
        distribution = {}
        for result in self.results:
            action = result.actual_action
            distribution[action] = distribution.get(action, 0) + 1
        return distribution
    
    def print_report(self):
        """Print validation report"""
        print("\n" + "=" * 60)
        print("VALIDATION REPORT")
        print("=" * 60)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\n{status} | {result.scenario.name}")
            print(f"   Scenario: {result.scenario.description}")
            print(f"   Input: {result.scenario.pest_count} pests, "
                  f"{result.scenario.temperature}°C, {result.scenario.humidity}%")
            print(f"   Expected: {result.scenario.expected_action}")
            print(f"   Actual: {result.actual_action} (PPI={result.ppi:.3f})")
            print(f"   {result.message}")
        
        summary = self.get_summary()
        print("\n" + "-" * 40)
        print(f"SUMMARY: {summary['passed']}/{summary['total_scenarios']} passed "
              f"({summary['pass_rate']:.1f}%)")
        
        if summary['failed_scenarios']:
            print(f"Failed: {', '.join(summary['failed_scenarios'])}")
        print("=" * 60)


if __name__ == "__main__":
    validator = Validator()
    validator.validate_all()
    validator.print_report()