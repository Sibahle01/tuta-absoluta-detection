"""
Validation framework for the Tuta absoluta IPM Decision Support System.

Three-level validation:
    Level 1 — Literature Alignment  (scenarios vs published papers)
    Level 2 — Sensitivity Analysis  (mathematical integrity checks)
    Level 3 — Performance Benchmark (latency and throughput)

Run from project root:
    python simulation/validator.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass, field

from core.decision_engine import IPMDecisionEngine
from core.models import (
    DetectionResult, EnvironmentalReading,
    CropStage, SprayRecord, DecisionZone, ActionType
)


# ================================================================
# LITERATURE-DERIVED TEST SCENARIOS
# Each scenario is traceable to a specific published paper
# ================================================================

@dataclass
class TestScenario:
    """A single validation scenario derived from literature"""
    name: str
    description: str
    source: str
    pest_count: int
    temperature: float
    humidity: float
    crop_stage: CropStage
    spray_history: List[SprayRecord]
    expected_action: str        # 'none', 'warning', 'spray', 'emergency'
    expected_zone: str          # 'GREEN', 'YELLOW', 'ORANGE', 'RED'
    expected_chemical_not: str = ""  # Chemical that should NOT be selected


@dataclass
class ValidationResult:
    """Result of a single validation test"""
    scenario: TestScenario
    actual_action: str
    expected_action: str
    actual_zone: str
    expected_zone: str
    passed: bool
    ppi_score: float
    message: str
    details: Dict = field(default_factory=dict)


def build_scenarios() -> List[TestScenario]:
    """
    Build all literature-derived test scenarios.
    Each scenario maps directly to a finding in a cited paper.
    """
    now = datetime.now()

    return [
        TestScenario(
            name="S1_Below_Threshold",
            description="Low pest count — below economic injury level",
            source="Rostami et al. (2021)",
            pest_count=0,
            temperature=22.0,
            humidity=65.0,
            crop_stage=CropStage.VEGETATIVE,
            spray_history=[],
            expected_action="none",
            expected_zone="GREEN"
        ),
        TestScenario(
            name="S2_Approaching_Threshold",
            description="Two pests — approaching action threshold",
            source="Rostami et al. (2021)",
            pest_count=2,
            temperature=22.0,
            humidity=65.0,
            crop_stage=CropStage.VEGETATIVE,
            spray_history=[],
            expected_action="warning",
            expected_zone="YELLOW"
        ),
        TestScenario(
            name="S3_At_Action_Threshold",
            description="Three pests at 75% EIL — prepare to spray",
            source="Rostami et al. (2021)",
            pest_count=3,
            temperature=25.0,
            humidity=68.0,
            crop_stage=CropStage.FRUIT_SET,
            spray_history=[],
            expected_action="spray",
            expected_zone="ORANGE"
        ),
        TestScenario(
            name="S4_At_EIL",
            description="Four pests at economic injury level — spray immediately",
            source="Rostami et al. (2021)",
            pest_count=4,
            temperature=26.0,
            humidity=70.0,
            crop_stage=CropStage.FRUIT_SET,
            spray_history=[],
            expected_action="spray",
            expected_zone="RED"
        ),
        TestScenario(
            name="S5_High_Temperature_Acceleration",
            description="High temperature accelerates P. absoluta development",
            source="Maake & Sibisi (2026); Cuthbertson et al. (2013)",
            pest_count=2,
            temperature=32.0,    # Hot KZN summer day
            humidity=85.0,
            crop_stage=CropStage.FRUIT_SET,
            spray_history=[],
            expected_action="warning",
            expected_zone="YELLOW"
        ),
        TestScenario(
            name="S6_Resistance_Rotation",
            description="System avoids recently used chemical",
            source="Van den Berg et al. (2022)",
            pest_count=5,
            temperature=25.0,
            humidity=68.0,
            crop_stage=CropStage.FRUIT_DEVELOPMENT,
            spray_history=[
                SprayRecord(
                    timestamp=now - timedelta(days=14),
                    chemical_id="spinosad",
                    chemical_name="Spinosad",
                    dose_ml_per_litre=0.8,
                    area_m2=1000,
                    ppi_at_time=0.72,
                    pest_count_at_time=4
                ),
                SprayRecord(
                    timestamp=now - timedelta(days=7),
                    chemical_id="spinosad",
                    chemical_name="Spinosad",
                    dose_ml_per_litre=0.9,
                    area_m2=1000,
                    ppi_at_time=0.81,
                    pest_count_at_time=6
                )
            ],
            expected_action="spray",
            expected_zone="RED",
            expected_chemical_not="spinosad"
        ),
        TestScenario(
            name="S7_Critical_Infestation",
            description="Critical infestation — 80-100% crop loss risk",
            source="Desneux et al. (2010); Maake & Sibisi (2026)",
            pest_count=9,
            temperature=28.0,
            humidity=72.0,
            crop_stage=CropStage.FRUIT_SET,
            spray_history=[],
            expected_action="spray",
            expected_zone="RED"
        ),
    ]


# ================================================================
# VALIDATOR — THREE LEVELS
# ================================================================

class IPMValidator:
    """
    Formal three-level validation framework.

    Level 1 — Literature Alignment
    Level 2 — Sensitivity Analysis
    Level 3 — Performance Benchmarking
    """

    def __init__(self):
        self.scenarios = build_scenarios()
        self.level1_results: List[ValidationResult] = []
        print("✅ IPM Validator initialised")
        print(f"   {len(self.scenarios)} literature scenarios loaded")

    # ============================================================
    # LEVEL 1 — LITERATURE ALIGNMENT
    # ============================================================

    def validate_literature_alignment(self) -> Dict:
        """
        Test each scenario against expected outcomes from literature.
        Target: ≥80% alignment accuracy.
        """
        print("\n" + "=" * 60)
        print("LEVEL 1: LITERATURE ALIGNMENT VALIDATION")
        print("=" * 60)

        self.level1_results = []
        passed = 0

        for scenario in self.scenarios:
            # Fresh engine per scenario for isolation
            engine = IPMDecisionEngine()

            # Build detection result
            detection = DetectionResult(
                timestamp=datetime.now(),
                image_path=f"test/{scenario.name}.jpg",
                tuta_absoluta_count=scenario.pest_count,
                insect_count=0,
                confidence_scores=[0.85] * max(1, scenario.pest_count),
                mean_confidence=0.85,
                inference_time_ms=4.7
            )

            # Build environment reading
            environment = EnvironmentalReading(
                timestamp=datetime.now(),
                temperature_celsius=scenario.temperature,
                humidity_percent=scenario.humidity
            )

            # Calculate PPI
            ppi = engine.calculate_ppi(detection, environment, scenario.crop_stage)

            # Determine actual action from zone
            actual_action = self._zone_to_action(ppi.zone)
            actual_zone = ppi.zone.value

            # Check zone match
            zone_match = actual_zone == scenario.expected_zone

            # Check action match (allow higher severity to pass)
            action_match = self._action_passes(
                scenario.expected_action, actual_action
            )

            # Chemical rotation check
            chemical_ok = True
            if scenario.expected_chemical_not:
                from core.resistance_manager import ResistanceManager
                rm = ResistanceManager()
                selected = rm.select_chemical(scenario.spray_history, ppi.ppi_score)
                if selected:
                    chemical_ok = selected['id'] != scenario.expected_chemical_not

            scenario_passed = zone_match and action_match and chemical_ok
            if scenario_passed:
                passed += 1

            result = ValidationResult(
                scenario=scenario,
                actual_action=actual_action,
                expected_action=scenario.expected_action,
                actual_zone=actual_zone,
                expected_zone=scenario.expected_zone,
                passed=scenario_passed,
                ppi_score=ppi.ppi_score,
                message=f"Expected {scenario.expected_zone}/{scenario.expected_action} "
                        f"→ Got {actual_zone}/{actual_action}",
                details={
                    'components': ppi.component_breakdown,
                    'zone_match': zone_match,
                    'action_match': action_match,
                    'chemical_ok': chemical_ok
                }
            )
            self.level1_results.append(result)

            status = "✅ PASS" if scenario_passed else "❌ FAIL"
            print(f"\n{status} | {scenario.name}")
            print(f"   Source:   {scenario.source}")
            print(f"   Input:    {scenario.pest_count} pests | "
                  f"{scenario.temperature}°C | {scenario.crop_stage.value}")
            print(f"   Expected: {scenario.expected_zone} / {scenario.expected_action}")
            print(f"   Actual:   {actual_zone} / {actual_action} (PPI={ppi.ppi_score:.4f})")
            if not chemical_ok:
                print(f"   ⚠️  Chemical rotation check FAILED")

        accuracy = (passed / len(self.scenarios)) * 100
        print(f"\n{'=' * 60}")
        print(f"Literature Alignment: {passed}/{len(self.scenarios)} = {accuracy:.1f}%")
        print(f"Target: ≥80% | Status: {'✅ PASSED' if accuracy >= 80 else '❌ NEEDS REVIEW'}")

        return {
            'level': 1,
            'name': 'Literature Alignment',
            'passed': passed,
            'total': len(self.scenarios),
            'accuracy_percent': accuracy,
            'target_met': accuracy >= 80.0,
            'results': [
                {
                    'scenario': r.scenario.name,
                    'source': r.scenario.source,
                    'ppi': r.ppi_score,
                    'expected_zone': r.expected_zone,
                    'actual_zone': r.actual_zone,
                    'passed': r.passed
                }
                for r in self.level1_results
            ]
        }

    def _zone_to_action(self, zone: DecisionZone) -> str:
        mapping = {
            DecisionZone.GREEN: "none",
            DecisionZone.YELLOW: "warning",
            DecisionZone.ORANGE: "spray",
            DecisionZone.RED: "spray"
        }
        return mapping.get(zone, "none")

    def _action_passes(self, expected: str, actual: str) -> bool:
        """Higher severity than expected still passes"""
        severity = {"none": 0, "warning": 1, "spray": 2, "emergency": 3}
        return severity.get(actual, 0) >= severity.get(expected, 0)

    # ============================================================
    # LEVEL 2 — SENSITIVITY ANALYSIS
    # ============================================================

    def run_sensitivity_analysis(self) -> Dict:
        """
        Vary each input independently and verify PPI responds correctly.
        Validates that mathematical weights produce proportional responses.
        """
        print("\n" + "=" * 60)
        print("LEVEL 2: SENSITIVITY ANALYSIS")
        print("=" * 60)

        results = {}

        # --- Test 1: Pest count monotonicity ---
        print("\nTest 1: Pest count → PPI should increase monotonically")
        pest_counts = [0, 1, 2, 3, 4, 5, 7, 10]
        ppi_by_count = []

        for count in pest_counts:
            engine = IPMDecisionEngine()
            det = self._make_detection(count)
            env = self._make_environment(22.0, 65.0)
            ppi = engine.calculate_ppi(det, env, CropStage.VEGETATIVE)
            ppi_by_count.append(ppi.ppi_score)
            print(f"   {count:>3} pests → PPI={ppi.ppi_score:.4f} | {ppi.zone.value}")

        monotonic = all(
            ppi_by_count[i] <= ppi_by_count[i+1]
            for i in range(len(ppi_by_count)-1)
        )
        results['count_monotonic'] = monotonic
        print(f"   Monotonic increase: {'✅ PASS' if monotonic else '❌ FAIL'}")

        # --- Test 2: Temperature effect ---
        print("\nTest 2: Temperature → higher temp should increase PPI")
        temperatures = [10, 15, 20, 25, 28, 32, 35]
        ppi_by_temp = []

        for temp in temperatures:
            engine = IPMDecisionEngine()
            det = self._make_detection(3)
            env = self._make_environment(temp, 65.0)
            ppi = engine.calculate_ppi(det, env, CropStage.VEGETATIVE)
            ppi_by_temp.append(ppi.ppi_score)
            print(f"   {temp:>3}°C → PPI={ppi.ppi_score:.4f}")

        temp_increases = ppi_by_temp[4] > ppi_by_temp[0]
        results['temperature_increases_ppi'] = temp_increases
        print(f"   Temperature increases PPI: {'✅ PASS' if temp_increases else '❌ FAIL'}")

        # --- Test 3: Crop stage vulnerability ---
        print("\nTest 3: Crop stage → fruit set should have highest PPI")
        stages = [
            CropStage.SEEDLING, CropStage.VEGETATIVE, CropStage.FLOWERING,
            CropStage.FRUIT_SET, CropStage.FRUIT_DEVELOPMENT, CropStage.HARVEST
        ]
        stage_ppis = {}

        for stage in stages:
            engine = IPMDecisionEngine()
            det = self._make_detection(3)
            env = self._make_environment(25.0, 68.0)
            ppi = engine.calculate_ppi(det, env, stage)
            stage_ppis[stage.value] = ppi.ppi_score
            print(f"   {stage.value:<20} → PPI={ppi.ppi_score:.4f}")

        fruit_set_highest = (
            stage_ppis['fruit_set'] >= max(stage_ppis.values()) * 0.95
        )
        results['fruit_set_highest'] = fruit_set_highest
        print(f"   Fruit set highest PPI: {'✅ PASS' if fruit_set_highest else '❌ FAIL'}")

        # --- Test 4: Zero pest gate ---
        print("\nTest 4: Zero pest gate → 0 pests must always be GREEN")
        zero_cases = [
            (10.0, 30.0, CropStage.SEEDLING),
            (22.0, 65.0, CropStage.FRUIT_SET),
            (35.0, 90.0, CropStage.FRUIT_SET),   # Worst case conditions
        ]
        zero_gate_passes = []

        for temp, humidity, stage in zero_cases:
            engine = IPMDecisionEngine()
            det = self._make_detection(0)
            env = self._make_environment(temp, humidity)
            ppi = engine.calculate_ppi(det, env, stage)
            gate_pass = ppi.zone == DecisionZone.GREEN
            zero_gate_passes.append(gate_pass)
            print(f"   {temp}°C, {stage.value:<20} → PPI={ppi.ppi_score:.4f} "
                  f"Zone={ppi.zone.value} {'✅' if gate_pass else '❌'}")

        all_zero_gate = all(zero_gate_passes)
        results['zero_pest_gate'] = all_zero_gate
        print(f"   Zero pest gate: {'✅ ALL PASS' if all_zero_gate else '❌ FAIL'}")

        # --- Test 5: Weight sum ---
        print("\nTest 5: PPI weights must sum to exactly 1.0")
        engine = IPMDecisionEngine()
        weight_sum = sum(engine.weights.values())
        weights_valid = abs(weight_sum - 1.0) < 1e-6
        results['weights_sum_to_one'] = weights_valid
        print(f"   α+β+γ+δ = {weight_sum:.8f} | {'✅ PASS' if weights_valid else '❌ FAIL'}")

        # Summary
        all_passed = all(results.values())
        print(f"\nSensitivity Analysis: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")

        return {
            'level': 2,
            'name': 'Sensitivity Analysis',
            'all_passed': all_passed,
            'results': results,
            'data': {
                'pest_counts': pest_counts,
                'ppi_by_count': ppi_by_count,
                'temperatures': temperatures,
                'ppi_by_temp': ppi_by_temp,
                'stage_ppis': stage_ppis
            }
        }

    def _make_detection(self, pest_count: int) -> DetectionResult:
        return DetectionResult(
            timestamp=datetime.now(),
            image_path='test/benchmark.jpg',
            tuta_absoluta_count=pest_count,
            insect_count=0,
            confidence_scores=[0.85] * max(1, pest_count),
            mean_confidence=0.85,
            inference_time_ms=4.7
        )

    def _make_environment(self, temp: float, humidity: float) -> EnvironmentalReading:
        return EnvironmentalReading(
            timestamp=datetime.now(),
            temperature_celsius=temp,
            humidity_percent=humidity
        )

    # ============================================================
    # LEVEL 3 — PERFORMANCE BENCHMARKING
    # ============================================================

    def run_performance_benchmarks(self, n_iterations: int = 1000) -> Dict:
        """
        Measure decision engine latency and throughput.
        Target: mean latency <100ms (Raspberry Pi compatible).
        """
        print("\n" + "=" * 60)
        print(f"LEVEL 3: PERFORMANCE BENCHMARKING ({n_iterations} iterations)")
        print("=" * 60)

        det = self._make_detection(3)
        env = self._make_environment(25.0, 68.0)
        latencies = []

        for _ in range(n_iterations):
            engine = IPMDecisionEngine()
            start = time.perf_counter()
            engine.calculate_ppi(det, env, CropStage.FRUIT_SET)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        arr = np.array(latencies)
        mean_ms = float(np.mean(arr))
        rpi_safe = mean_ms < 100.0

        print(f"\n   Mean latency:    {mean_ms:.3f} ms")
        print(f"   Median latency:  {np.median(arr):.3f} ms")
        print(f"   Std deviation:   {np.std(arr):.3f} ms")
        print(f"   Min latency:     {np.min(arr):.3f} ms")
        print(f"   Max latency:     {np.max(arr):.3f} ms")
        print(f"   95th percentile: {np.percentile(arr, 95):.3f} ms")
        print(f"   Throughput:      {1000/mean_ms:.1f} decisions/second")
        print(f"\n   Raspberry Pi compatible (<100ms): {'✅ YES' if rpi_safe else '❌ NO'}")

        return {
            'level': 3,
            'name': 'Performance Benchmarking',
            'iterations': n_iterations,
            'mean_ms': round(mean_ms, 3),
            'median_ms': round(float(np.median(arr)), 3),
            'std_ms': round(float(np.std(arr)), 3),
            'min_ms': round(float(np.min(arr)), 3),
            'max_ms': round(float(np.max(arr)), 3),
            'p95_ms': round(float(np.percentile(arr, 95)), 3),
            'throughput': round(1000 / mean_ms, 1),
            'rpi_compatible': rpi_safe,
            'latency_distribution': latencies
        }

    # ============================================================
    # FULL VALIDATION SUITE
    # ============================================================

    def run_full_validation(self, save_plots: bool = True) -> Dict:
        """
        Run all three validation levels and generate report.
        """
        print("\n" + "=" * 60)
        print("  TUTA ABSOLUTA IPM DECISION SUPPORT SYSTEM")
        print("  FULL VALIDATION SUITE")
        print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)

        level1 = self.validate_literature_alignment()
        level2 = self.run_sensitivity_analysis()
        level3 = self.run_performance_benchmarks()

        overall = (
            level1['accuracy_percent'] >= 80.0 and
            level2['all_passed'] and
            level3['rpi_compatible']
        )

        report = {
            'timestamp': datetime.now().isoformat(),
            'system': 'Tuta absoluta IPM Decision Support System v1.0',
            'overall_pass': overall,
            'level1': level1,
            'level2': level2,
            'level3': {k: v for k, v in level3.items() if k != 'latency_distribution'}
        }

        # Save JSON report
        with open('validation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print("\n✅ Saved: validation_report.json")

        # Generate plots
        if save_plots:
            self._generate_plots(level1, level2, level3)
            print("✅ Saved: ipm_validation_results.png")

        # Final summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"  Level 1 — Literature Alignment : "
              f"{level1['accuracy_percent']:.1f}% "
              f"({'✅' if level1['target_met'] else '❌'})")
        print(f"  Level 2 — Sensitivity Analysis : "
              f"{'All passed ✅' if level2['all_passed'] else 'Issues found ❌'}")
        print(f"  Level 3 — Performance          : "
              f"{level3['mean_ms']:.2f}ms mean "
              f"({'✅ RPi ready' if level3['rpi_compatible'] else '❌ Too slow'})")
        print(f"\n  OVERALL STATUS: {'✅ SYSTEM VALIDATED' if overall else '❌ REVIEW REQUIRED'}")
        print("=" * 60)

        return report

    # ============================================================
    # VISUALISATION
    # ============================================================

    def _generate_plots(self, level1: Dict, level2: Dict, level3: Dict):
        """Generate publication-quality 9-panel validation figure"""

        fig = plt.figure(figsize=(18, 14))
        fig.suptitle(
            'IPM Decision Support System — Full Validation Results\n'
            'Phthorimaea absoluta | South African Smallholder Tomato Farming',
            fontsize=13, fontweight='bold', y=0.98
        )

        data = level2['data']

        # ---- Plot 1: Literature scenarios PPI ----
        ax1 = fig.add_subplot(3, 3, 1)
        names = [r['scenario'].replace('S', 'S\n', 1)
                 for r in level1['results']]
        ppis = [r['ppi'] for r in level1['results']]
        colors = ['#2ecc71' if r['passed'] else '#e74c3c'
                  for r in level1['results']]
        ax1.bar(range(len(names)), ppis, color=colors,
                alpha=0.85, edgecolor='black', linewidth=0.8)
        ax1.axhline(0.55, color='orange', linestyle='--',
                    linewidth=1.5, label='YELLOW (0.55)')
        ax1.axhline(0.75, color='red', linestyle='--',
                    linewidth=1.5, label='ORANGE (0.75)')
        ax1.axhline(0.85, color='darkred', linestyle='--',
                    linewidth=1.5, label='RED (0.85)')
        ax1.set_xticks(range(len(names)))
        ax1.set_xticklabels(names, fontsize=6)
        ax1.set_ylabel('PPI Score')
        ax1.set_ylim(0, 1.05)
        ax1.set_title(
            f"Literature Alignment\n"
            f"{level1['passed']}/{level1['total']} passed "
            f"({level1['accuracy_percent']:.0f}%)",
            fontweight='bold'
        )
        ax1.legend(fontsize=6)
        ax1.grid(True, alpha=0.3, axis='y')

        # ---- Plot 2: Pass/Fail summary ----
        ax2 = fig.add_subplot(3, 3, 2)
        passed_n = level1['passed']
        failed_n = level1['total'] - level1['passed']
        ax2.pie(
            [passed_n, failed_n],
            labels=[f'Passed\n({passed_n})', f'Failed\n({failed_n})'],
            colors=['#2ecc71', '#e74c3c'],
            autopct='%1.0f%%',
            startangle=90,
            textprops={'fontsize': 10}
        )
        ax2.set_title('Literature Alignment\nPass/Fail', fontweight='bold')

        # ---- Plot 3: Pest count sensitivity ----
        ax3 = fig.add_subplot(3, 3, 3)
        counts = data['pest_counts']
        ppi_c = data['ppi_by_count']
        ax3.plot(counts, ppi_c, 'o-', color='#3498db',
                 linewidth=2.5, markersize=7, label='PPI')
        ax3.fill_between(counts, 0, ppi_c, alpha=0.15, color='#3498db')
        ax3.axhline(0.30, color='green', linestyle=':', alpha=0.8, label='GREEN')
        ax3.axhline(0.55, color='orange', linestyle=':', alpha=0.8, label='YELLOW')
        ax3.axhline(0.75, color='red', linestyle=':', alpha=0.8, label='ORANGE')
        ax3.axhline(0.85, color='darkred', linestyle=':', alpha=0.8, label='RED')
        ax3.axvline(4, color='purple', linestyle='--',
                    linewidth=1.5, label='EIL (Rostami 2021)')
        ax3.set_xlabel('Pest Count (pests/image)')
        ax3.set_ylabel('PPI Score')
        ax3.set_title('PPI vs Pest Count\n(Sensitivity — Rostami 2021)',
                      fontweight='bold')
        ax3.legend(fontsize=6)
        ax3.grid(True, alpha=0.3)

        # ---- Plot 4: Temperature sensitivity ----
        ax4 = fig.add_subplot(3, 3, 4)
        temps = data['temperatures']
        ppi_t = data['ppi_by_temp']
        ax4.plot(temps, ppi_t, 's-', color='#e74c3c',
                 linewidth=2.5, markersize=7)
        ax4.fill_between(temps, min(ppi_t), ppi_t, alpha=0.15, color='#e74c3c')
        ax4.axvline(10, color='blue', linestyle=':',
                    alpha=0.8, label='T_base=10°C')
        ax4.axvline(25, color='orange', linestyle=':',
                    alpha=0.8, label='High urgency=25°C')
        ax4.set_xlabel('Temperature (°C)')
        ax4.set_ylabel('PPI Score')
        ax4.set_title('PPI vs Temperature\n(Degree-Day Model — Cuthbertson 2013)',
                      fontweight='bold')
        ax4.legend(fontsize=7)
        ax4.grid(True, alpha=0.3)

        # ---- Plot 5: Crop stage vulnerability ----
        ax5 = fig.add_subplot(3, 3, 5)
        stage_data = data['stage_ppis']
        stage_names = [s.replace('_', '\n') for s in stage_data.keys()]
        stage_vals = list(stage_data.values())
        stage_colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(stage_names)))
        bars = ax5.bar(range(len(stage_names)), stage_vals,
                       color=stage_colors, edgecolor='black', linewidth=0.8)
        ax5.set_xticks(range(len(stage_names)))
        ax5.set_xticklabels(stage_names, fontsize=7)
        ax5.set_ylabel('PPI Score')
        ax5.set_ylim(0, 1.05)
        ax5.set_title('PPI by Crop Stage\n(Seasonal Vulnerability — Rostami 2021)',
                      fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='y')

        # ---- Plot 6: Dose optimisation curve ----
        ax6 = fig.add_subplot(3, 3, 6)
        ppi_range = np.linspace(0, 1, 200)
        D_min, D_max, AT = 1.5, 3.0, 0.55
        doses = [
            D_min + (D_max - D_min) * max(0, (p - AT) / (1 - AT))
            if p > AT else D_min
            for p in ppi_range
        ]
        ax6.plot(ppi_range, doses, color='#1abc9c', linewidth=2.5)
        ax6.fill_between(ppi_range, D_min, doses,
                         alpha=0.2, color='#1abc9c')
        ax6.axvline(AT, color='orange', linestyle='--',
                    linewidth=1.5, label=f'Action threshold ({AT})')
        ax6.axvline(0.85, color='darkred', linestyle='--',
                    linewidth=1.5, label='RED zone (0.85)')
        ax6.set_xlabel('PPI Score')
        ax6.set_ylabel('Dose (ml/L)')
        ax6.set_title('Dose Optimisation\n(Bt thuringiensis — Van den Berg 2022)',
                      fontweight='bold')
        ax6.legend(fontsize=7)
        ax6.grid(True, alpha=0.3)

        # ---- Plot 7: Latency distribution ----
        ax7 = fig.add_subplot(3, 3, 7)
        latencies = level3['latency_distribution']
        ax7.hist(latencies, bins=50, color='#9b59b6',
                 alpha=0.75, edgecolor='white', linewidth=0.5)
        ax7.axvline(np.mean(latencies), color='red', linestyle='--',
                    linewidth=2,
                    label=f"Mean: {level3['mean_ms']:.2f}ms")
        ax7.axvline(np.percentile(latencies, 95), color='orange',
                    linestyle='--', linewidth=2,
                    label=f"P95: {level3['p95_ms']:.2f}ms")
        ax7.axvline(100, color='green', linestyle='-',
                    linewidth=1.5, alpha=0.7, label='RPi limit (100ms)')
        ax7.set_xlabel('Latency (ms)')
        ax7.set_ylabel('Frequency')
        ax7.set_title('Decision Engine Latency\n(1000 iterations)',
                      fontweight='bold')
        ax7.legend(fontsize=7)
        ax7.grid(True, alpha=0.3)

        # ---- Plot 8: Zone distribution ----
        ax8 = fig.add_subplot(3, 3, 8)
        zone_counts = {'GREEN': 0, 'YELLOW': 0, 'ORANGE': 0, 'RED': 0}
        for r in level1['results']:
            z = r['actual_zone']
            zone_counts[z] = zone_counts.get(z, 0) + 1
        zone_colors = {
            'GREEN': '#2ecc71', 'YELLOW': '#f1c40f',
            'ORANGE': '#e67e22', 'RED': '#e74c3c'
        }
        non_zero = {k: v for k, v in zone_counts.items() if v > 0}
        ax8.pie(
            list(non_zero.values()),
            labels=list(non_zero.keys()),
            colors=[zone_colors[k] for k in non_zero.keys()],
            autopct='%1.0f%%',
            startangle=90,
            textprops={'fontsize': 9}
        )
        ax8.set_title('Decision Zone Distribution\n(Literature Scenarios)',
                      fontweight='bold')

        # ---- Plot 9: Summary dashboard ----
        ax9 = fig.add_subplot(3, 3, 9)
        ax9.axis('off')

        l1_status = '✓ PASSED' if level1['target_met'] else '✗ REVIEW'
        l2_status = '✓ PASSED' if level2['all_passed'] else '✗ REVIEW'
        l3_status = '✓ PASSED' if level3['rpi_compatible'] else '✗ REVIEW'
        overall = level1['target_met'] and level2['all_passed'] and level3['rpi_compatible']

        summary = (
            f"VALIDATION SUMMARY\n"
            f"{'─'*32}\n\n"
            f"System:\n"
            f"  Tuta absoluta IPM DSS v1.0\n"
            f"  SA Smallholder Context\n\n"
            f"Level 1 — Literature Alignment\n"
            f"  Accuracy : {level1['accuracy_percent']:.0f}%\n"
            f"  Scenarios: {level1['passed']}/{level1['total']}\n"
            f"  Status   : {l1_status}\n\n"
            f"Level 2 — Sensitivity Analysis\n"
            f"  Status   : {l2_status}\n\n"
            f"Level 3 — Performance\n"
            f"  Mean     : {level3['mean_ms']:.2f} ms\n"
            f"  P95      : {level3['p95_ms']:.2f} ms\n"
            f"  RPi Safe : {l3_status}\n\n"
            f"{'─'*32}\n"
            f"OVERALL: {'✓ VALIDATED' if overall else '✗ REVIEW'}\n"
            f"{'─'*32}"
        )

        ax9.text(
            0.05, 0.97, summary,
            transform=ax9.transAxes,
            fontsize=9, verticalalignment='top',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.9)
        )

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig('ipm_validation_results.png', dpi=150, bbox_inches='tight')
        plt.show()


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    validator = IPMValidator()
    report = validator.run_full_validation(save_plots=True)