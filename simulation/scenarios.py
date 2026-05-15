"""
Test scenarios based on peer-reviewed literature
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class TestScenario:
    """Single test scenario"""
    name: str
    description: str
    pest_count: int
    temperature: float
    humidity: float
    expected_action: str
    source: str


# Scenarios from Rostami et al. 2021
ROSTAMI_SCENARIOS = [
    TestScenario(
        name="rostami_low",
        description="Low infestation (2 eggs/plant)",
        pest_count=2,
        temperature=25,
        humidity=60,
        expected_action="warning",
        source="Rostami et al. 2021 - Low infestation"
    ),
    TestScenario(
        name="rostami_medium",
        description="Medium infestation (8 eggs/plant)",
        pest_count=8,
        temperature=25,
        humidity=60,
        expected_action="spray",
        source="Rostami et al. 2021 - Economic threshold exceeded"
    ),
    TestScenario(
        name="rostami_high",
        description="High infestation (16 eggs/plant → 47% fruit loss)",
        pest_count=16,
        temperature=25,
        humidity=60,
        expected_action="spray",
        source="Rostami et al. 2021 - Critical infestation"
    ),
]

# Scenarios from Cuthbertson et al. 2013 (temperature effects)
TEMPERATURE_SCENARIOS = [
    TestScenario(
        name="temp_cold",
        description="Cold temperature slows development",
        pest_count=3,
        temperature=12,
        humidity=60,
        expected_action="monitor",
        source="Cuthbertson 2013 - Below development threshold"
    ),
    TestScenario(
        name="temp_optimal",
        description="Optimal temperature for development",
        pest_count=3,
        temperature=25,
        humidity=60,
        expected_action="warning",
        source="Cuthbertson 2013 - Optimal development"
    ),
    TestScenario(
        name="temp_hot",
        description="Hot temperature increases development rate",
        pest_count=3,
        temperature=32,
        humidity=60,
        expected_action="warning",
        source="Cuthbertson 2013 - Above optimal"
    ),
]

# Scenarios from Van den Berg et al. 2022 (resistance context)
RESISTANCE_SCENARIOS = [
    TestScenario(
        name="resistance_warning",
        description="Moderate infestation with resistance context",
        pest_count=4,
        temperature=28,
        humidity=65,
        expected_action="spray",
        source="Van den Berg 2022 - Resistance management required"
    ),
]

# All scenarios combined
ALL_SCENARIOS = ROSTAMI_SCENARIOS + TEMPERATURE_SCENARIOS + RESISTANCE_SCENARIOS


if __name__ == "__main__":
    print("=== Test Scenarios ===")
    for scenario in ALL_SCENARIOS:
        print(f"\n{scenario.name}: {scenario.description}")
        print(f"  Pests: {scenario.pest_count}, Temp: {scenario.temperature}°C, Humidity: {scenario.humidity}%")
        print(f"  Expected: {scenario.expected_action} ({scenario.source})")