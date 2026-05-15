"""
Resistance Manager for Insecticide Resistance Management (IRM)
Based on Van den Berg et al. 2022
"""

import yaml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChemicalApplication:
    """Record of a chemical application"""
    chemical_name: str
    chemical_class: str
    date: datetime
    pest_count_at_application: int
    efficacy_estimate: float = 0.9


@dataclass
class ChemicalRecommendation:
    """Recommended chemical for application"""
    chemical_name: str
    chemical_class: str
    reason: str
    confidence: float
    rotation_index: int


class ResistanceManager:
    """
    Manages chemical rotation to prevent resistance development
    Implements rotation strategy from Van den Berg et al. 2022
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "chemicals.yaml"
        
        # Default values (will be used if config file doesn't exist or is invalid)
        self.schedule = [
            {'name': 'spinosad', 'class': 'Spinosyns', 'max_applications_per_season': 3, 'resistance_risk': 'moderate'},
            {'name': 'chlorantraniliprole', 'class': 'Diamides', 'max_applications_per_season': 2, 'resistance_risk': 'high'},
            {'name': 'Bacillus thuringiensis', 'class': 'Biological', 'max_applications_per_season': 999, 'resistance_risk': 'low'}
        ]
        self.rotation_required_after = 2
        self.resistance_thresholds = {'warning': 0.6, 'critical': 0.4}
        
        # Try to load config file if it exists
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                if config and 'chemical_rotation' in config:
                    self.schedule = config['chemical_rotation'].get('schedule', self.schedule)
                    self.rotation_required_after = config['chemical_rotation'].get('rotation_required_after_applications', self.rotation_required_after)
                    self.resistance_thresholds = config['chemical_rotation'].get('resistance_thresholds', self.resistance_thresholds)
                    print(f"✅ Loaded chemical config from {config_path}")
                else:
                    print(f"⚠️ Config file {config_path} has invalid structure, using defaults")
            except Exception as e:
                print(f"⚠️ Error loading config: {e}, using defaults")
        else:
            print(f"⚠️ Config file {config_path} not found, using defaults")
        
        # Application history
        self.applications: List[ChemicalApplication] = []
        self.current_index = 0
    
    def get_chemical_by_name(self, name: str) -> Optional[Dict]:
        """Get chemical details by name"""
        for chem in self.schedule:
            if chem['name'].lower() == name.lower():
                return chem
        return None
    
    def record_application(self, chemical_name: str, pest_count: int, efficacy: float = 0.9):
        """Record a chemical application"""
        chem = self.get_chemical_by_name(chemical_name)
        if chem:
            application = ChemicalApplication(
                chemical_name=chemical_name,
                chemical_class=chem['class'],
                date=datetime.now(),
                pest_count_at_application=pest_count,
                efficacy_estimate=efficacy
            )
            self.applications.append(application)
            
            # Update rotation index
            if len(self.applications) >= self.rotation_required_after:
                self.current_index = (self.current_index + 1) % len(self.schedule)
            
            return application
        return None
    
    def get_next_chemical(self, current_efficacy: float = 0.9) -> ChemicalRecommendation:
        """
        Recommend next chemical based on rotation schedule and efficacy
        """
        # Ensure current_index is valid
        if self.current_index >= len(self.schedule):
            self.current_index = 0
        
        # Check if rotation is needed due to low efficacy
        if current_efficacy < self.resistance_thresholds['critical']:
            # Force rotation immediately
            self.current_index = (self.current_index + 1) % len(self.schedule)
            next_chem = self.schedule[self.current_index]
            reason = f"Critical efficacy drop ({current_efficacy:.0%}) - rotated to {next_chem['name']}"
        elif current_efficacy < self.resistance_thresholds['warning']:
            # Warning level - recommend rotation but don't force
            next_chem = self.schedule[self.current_index]
            reason = f"Efficacy drop ({current_efficacy:.0%}) - consider rotating to different class"
        else:
            # Normal operation
            next_chem = self.schedule[self.current_index]
            reason = f"Continuing with {next_chem['name']} from rotation schedule"
        
        return ChemicalRecommendation(
            chemical_name=next_chem['name'],
            chemical_class=next_chem['class'],
            reason=reason,
            confidence=0.9 if current_efficacy > 0.7 else 0.7,
            rotation_index=self.current_index
        )
    
    def get_application_summary(self) -> Dict:
        """Get summary of recent applications"""
        return {
            'total_applications': len(self.applications),
            'applications_by_class': self._count_by_class(),
            'last_application': self.applications[-1] if self.applications else None,
            'next_recommended': self.schedule[self.current_index]['name'] if self.schedule and self.current_index < len(self.schedule) else None
        }
    
    def _count_by_class(self) -> Dict:
        """Count applications by chemical class"""
        counts = {}
        for app in self.applications:
            counts[app.chemical_class] = counts.get(app.chemical_class, 0) + 1
        return counts
    
    def estimate_resistance_risk(self) -> float:
        """
        Estimate resistance risk based on application history
        Returns risk score 0-1 (0 = low, 1 = high)
        """
        if not self.applications:
            return 0.0
        
        recent_apps = self.applications[-5:]
        class_counts = {}
        for app in recent_apps:
            class_counts[app.chemical_class] = class_counts.get(app.chemical_class, 0) + 1
        
        max_consecutive = max(class_counts.values()) if class_counts else 0
        frequency_risk = min(1.0, max_consecutive / 3) * 0.5
        
        avg_efficacy = sum(a.efficacy_estimate for a in recent_apps) / len(recent_apps) if recent_apps else 0.9
        efficacy_risk = max(0, (0.9 - avg_efficacy) / 0.5) * 0.5
        
        return min(1.0, frequency_risk + efficacy_risk)


if __name__ == "__main__":
    print("=== Resistance Manager Test ===\n")
    
    manager = ResistanceManager()
    
    # Test 1: Initial recommendation
    rec = manager.get_next_chemical()
    print(f"1. Initial recommendation: {rec.chemical_name} ({rec.chemical_class})")
    print(f"   Reason: {rec.reason}")
    
    # Test 2: Record an application
    manager.record_application("spinosad", pest_count=5)
    print(f"\n2. After spinosad application: {len(manager.applications)} application(s) recorded")
    
    # Test 3: Next recommendation
    rec = manager.get_next_chemical()
    print(f"\n3. Next recommendation: {rec.chemical_name}")
    
    # Test 4: Force rotation due to low efficacy
    rec = manager.get_next_chemical(current_efficacy=0.35)
    print(f"\n4. Low efficacy (35%) recommendation: {rec.chemical_name}")
    print(f"   Reason: {rec.reason}")
    
    # Test 5: Resistance risk
    risk = manager.estimate_resistance_risk()
    print(f"\n5. Estimated resistance risk: {risk:.1%}")
    
    print("\n✅ Resistance Manager test complete!")