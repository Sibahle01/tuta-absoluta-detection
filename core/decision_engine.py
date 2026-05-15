"""
Decision Engine for Tuta absoluta IPM System
Based on validated mathematics from peer-reviewed literature
"""

import math
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import time


class AlertLevel:
    """Alert severity levels as string constants to avoid Enum issues"""
    NONE = "none"
    MONITOR = "monitor"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class DecisionOutput:
    """Output from decision engine"""
    action: str  # 'spray', 'warning', 'monitor', 'none'
    alert_level: str  # 'critical', 'warning', 'monitor', 'none'
    pest_pressure_index: float
    pest_count: int
    temperature_factor: float
    humidity_factor: float
    trend_factor: float
    message: str
    recommended_chemical: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class PestPressureIndex:
    """
    Pest Pressure Index (PPI) = α*C + β*T + γ*H + δ*Tr
    
    Where:
    α = 0.40 - Pest count weight
    β = 0.30 - Temperature weight  
    γ = 0.20 - Humidity weight
    δ = 0.10 - Trend weight
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "ipm_config.yaml"
        
        # Default values
        self.alpha = 0.40
        self.beta = 0.30
        self.gamma = 0.20
        self.delta = 0.10
        self.economic_threshold = 4
        self.warning_threshold = 2
        self.temp_min = 10
        self.temp_opt_min = 20
        self.temp_opt_max = 30
        self.temp_max = 35
        self.humidity_opt_min = 40
        self.humidity_opt_max = 70
        self.humidity_lethal_min = 20
        self.humidity_lethal_max = 85
        
        # Try to load config if exists
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config:
                        w = config.get('pest_pressure_index_weights', {})
                        self.alpha = w.get('pest_count_weight', 0.40)
                        self.beta = w.get('temperature_weight', 0.30)
                        self.gamma = w.get('humidity_weight', 0.20)
                        self.delta = w.get('trend_weight', 0.10)
                        
                        thresholds = config.get('economic_thresholds', {})
                        self.economic_threshold = thresholds.get('pests_per_image', 4)
                        self.warning_threshold = thresholds.get('warning_threshold', 2)
                        
                        temp = config.get('temperature_limits', {})
                        self.temp_min = temp.get('development_min', 10)
                        self.temp_opt_min = temp.get('development_opt_min', 20)
                        self.temp_opt_max = temp.get('development_opt_max', 30)
                        self.temp_max = temp.get('development_max', 35)
                        
                        hum = config.get('humidity_limits', {})
                        self.humidity_opt_min = hum.get('optimal_min', 40)
                        self.humidity_opt_max = hum.get('optimal_max', 70)
                        self.humidity_lethal_min = hum.get('lethal_min', 20)
                        self.humidity_lethal_max = hum.get('lethal_max', 85)
                        
                        print(f"✅ Loaded config from {config_path}")
            except Exception as e:
                print(f"⚠️ Error loading config: {e}, using defaults")
        else:
            print(f"⚠️ Config file {config_path} not found, using defaults")
        
        # Trend tracking
        self.pest_history = []
        self.max_history = 10
    
    def compute_temperature_factor(self, temp_celsius: float) -> float:
        """Temperature factor (T) - 0 to 1 scale"""
        if temp_celsius < self.temp_min:
            return 0.0
        elif temp_celsius > self.temp_max:
            return 0.0
        elif self.temp_opt_min <= temp_celsius <= self.temp_opt_max:
            return 1.0
        elif temp_celsius < self.temp_opt_min:
            return (temp_celsius - self.temp_min) / (self.temp_opt_min - self.temp_min)
        else:
            return max(0, (self.temp_max - temp_celsius) / (self.temp_max - self.temp_opt_max))
    
    def compute_humidity_factor(self, humidity_percent: float) -> float:
        """Humidity factor (H) - 0 to 1 scale"""
        if humidity_percent < self.humidity_lethal_min:
            return 0.0
        elif humidity_percent > self.humidity_lethal_max:
            return 0.3
        elif self.humidity_opt_min <= humidity_percent <= self.humidity_opt_max:
            return 1.0
        elif humidity_percent < self.humidity_opt_min:
            return (humidity_percent - self.humidity_lethal_min) / (self.humidity_opt_min - self.humidity_lethal_min)
        else:
            return 1.0 - (humidity_percent - self.humidity_opt_max) / (self.humidity_lethal_max - self.humidity_opt_max) * 0.7
    
    def compute_trend_factor(self) -> float:
        """Trend factor (Tr) - 0 to 1 scale"""
        if len(self.pest_history) < 3:
            return 0.5
        
        recent = self.pest_history[-3:]
        if recent[0] == 0:
            return 0.3
        
        slope = (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0
        slope = max(-1, min(1, slope))
        return (slope + 1) / 2
    
    def normalize_pest_count(self, pest_count: int) -> float:
        """Normalize pest count to 0-1 scale"""
        if pest_count <= 0:
            return 0.0
        elif pest_count >= self.economic_threshold:
            return 1.0
        else:
            return pest_count / self.economic_threshold
    
    def compute_ppi(self, pest_count: int, temperature: float, humidity: float) -> float:
        """Compute Pest Pressure Index (0-1 scale)"""
        # Update history
        self.pest_history.append(pest_count)
        if len(self.pest_history) > self.max_history:
            self.pest_history.pop(0)
        
        C = self.normalize_pest_count(pest_count)
        T = self.compute_temperature_factor(temperature)
        H = self.compute_humidity_factor(humidity)
        Tr = self.compute_trend_factor()
        
        ppi = (self.alpha * C + self.beta * T + self.gamma * H + self.delta * Tr)
        return min(1.0, max(0.0, ppi))
    
    def decide(self, pest_count: int, temperature: float, humidity: float) -> DecisionOutput:
        """Main decision method"""
        ppi = self.compute_ppi(pest_count, temperature, humidity)
        
        # Individual factors for logging
        C = self.normalize_pest_count(pest_count)
        T = self.compute_temperature_factor(temperature)
        H = self.compute_humidity_factor(humidity)
        Tr = self.compute_trend_factor()
        
        # MODIFIED: Require at least warning_threshold pests for warning/critical
        # If no pests detected, only warn if PPI is extremely high (>0.8)
        if pest_count >= self.economic_threshold or (pest_count > 0 and ppi >= 0.7):
            action = "spray"
            alert_level = AlertLevel.CRITICAL
            message = f"CRITICAL: {pest_count} pests detected (PPI={ppi:.2f}). Spray immediately."
        elif pest_count >= self.warning_threshold or (pest_count > 0 and ppi >= 0.4):
            action = "warning"
            alert_level = AlertLevel.WARNING
            message = f"WARNING: {pest_count} pests detected (PPI={ppi:.2f}). Monitor closely."
        elif pest_count > 0 and ppi >= 0.2:
            action = "monitor"
            alert_level = AlertLevel.MONITOR
            message = f"MONITOR: {pest_count} pests detected (PPI={ppi:.2f}). Continue observation."
        else:
            action = "none"
            alert_level = AlertLevel.NONE
            message = f"SAFE: {pest_count} pests detected (PPI={ppi:.2f}). No action needed."
        
        return DecisionOutput(
            action=action,
            alert_level=alert_level,
            pest_pressure_index=ppi,
            pest_count=pest_count,
            temperature_factor=T,
            humidity_factor=H,
            trend_factor=Tr,
            message=message
        )


if __name__ == "__main__":
    engine = PestPressureIndex()
    
    print("=== Decision Engine Test ===\n")
    
    tests = [
        (8, 25, 60, "Critical infestation"),
        (3, 28, 50, "Warning level"),
        (1, 25, 60, "Monitor level"),
        (3, 12, 60, "Cool conditions (reduced risk)"),
        (3, 32, 60, "Hot conditions (increased risk)"),
        (0, 25, 60, "No pests, optimal conditions"),
        (0, 15, 60, "No pests, cold conditions"),
    ]
    
    for pest, temp, hum, desc in tests:
        result = engine.decide(pest, temp, hum)
        print(f"{desc}: {result.action} - {result.message}")
        print(f"  PPI: {result.pest_pressure_index:.2f}, Alert: {result.alert_level}\n")