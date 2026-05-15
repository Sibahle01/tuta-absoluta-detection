"""
Data models / schemas for the IPM system
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime
import time


class AlertLevel(Enum):
    """Alert severity levels"""
    NONE = "none"
    MONITOR = "monitor"
    WARNING = "warning"
    CRITICAL = "critical"


class ChemicalClass(Enum):
    """Chemical classes for resistance management"""
    SPINOSYN = "spinosyn"
    DIAMIDE = "diamide"
    BIOLOGICAL = "biological"
    PYRETHROID = "pyrethroid"
    ORGANOPHOSPHATE = "organophosphate"


@dataclass
class Detection:
    """Single detection result from YOLO"""
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)
    timestamp: float = field(default_factory=time.time)


@dataclass
class EnvironmentalData:
    """Environmental sensor readings"""
    temperature_celsius: float
    humidity_percent: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class DecisionOutput:
    """Output from decision engine"""
    action: str  # 'spray', 'warning', 'monitor', 'none'
    alert_level: AlertLevel
    pest_pressure_index: float
    pest_count: int
    temperature_factor: float
    humidity_factor: float
    trend_factor: float
    message: str
    recommended_chemical: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ChemicalApplication:
    """Record of a chemical application"""
    chemical_name: str
    chemical_class: str
    date: datetime
    pest_count_at_application: int
    efficacy_estimate: float = 0.9


@dataclass
class SystemState:
    """Complete system state for logging/debugging"""
    pest_count: int
    temperature: float
    humidity: float
    ppi: float
    action: str
    alert_level: str
    message: str
    detection_confidence_mean: float = 0.0
    application_history: List[ChemicalApplication] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)