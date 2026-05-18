"""
Spray Controller with Simulation/Production Mode
Cooldown: 60 seconds for simulation, 7 days for production
"""

import time
from datetime import datetime
from typing import Optional


class SprayController:
    """
    Spray controller with configurable cooldown
    - Simulation mode: 60 second cooldown (for testing)
    - Production mode: 7 day cooldown (for field deployment)
    """
    
    def __init__(self, spray_pin: int = 17, simulation_mode: bool = True):
        self.spray_pin = spray_pin
        self.simulation_mode = simulation_mode
        
        # Cooldown configuration
        if simulation_mode:
            self.cooldown_seconds = 60  # 1 minute for testing
            self.mode_label = "SIMULATION (60s cooldown)"
        else:
            self.cooldown_seconds = 7 * 24 * 3600  # 7 days for production
            self.mode_label = "PRODUCTION (7-day cooldown)"
        
        self.spray_duration = 2
        self.last_spray_time = 0
        self.is_spraying = False
        
        # Chemical rotation schedule
        self.schedule = [
            {'name': 'spinosad', 'class': 'Spinosyns'},
            {'name': 'chlorantraniliprole', 'class': 'Diamides'},
            {'name': 'Bacillus thuringiensis', 'class': 'Biological'}
        ]
        self.current_chemical_index = 0
        self.application_history = []
        
        print(f"✅ Spray controller initialized")
        print(f"   Mode: {self.mode_label}")
        print(f"   Spray duration: {self.spray_duration}s")
    
    def get_mode_label(self) -> str:
        """Return current mode for reporting"""
        return self.mode_label
    
    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds"""
        if self.last_spray_time == 0:
            return 0
        elapsed = time.time() - self.last_spray_time
        return max(0, self.cooldown_seconds - elapsed)
    
    def get_cooldown_human(self) -> str:
        """Get human-readable cooldown remaining"""
        remaining = self.get_cooldown_remaining()
        if self.simulation_mode:
            return f"{remaining:.0f}s"
        else:
            days = remaining / 86400
            return f"{days:.1f} days"
    
    def get_current_chemical(self) -> dict:
        """Get currently recommended chemical"""
        return self.schedule[self.current_chemical_index % len(self.schedule)]
    
    def should_rotate(self) -> bool:
        """Check if rotation needed"""
        if len(self.application_history) < 2:
            return False
        recent = self.application_history[-2:]
        return recent[0]['chemical_class'] == recent[1]['chemical_class']
    
    def rotate_chemical(self):
        """Move to next chemical"""
        old = self.get_current_chemical()
        self.current_chemical_index += 1
        new = self.get_current_chemical()
        print(f"🔄 Chemical rotation: {old['name']} → {new['name']}")
        return new
    
    def can_spray(self) -> bool:
        """Check if spray is allowed (cooldown check)"""
        if self.last_spray_time == 0:
            return True
        return (time.time() - self.last_spray_time) >= self.cooldown_seconds
    
    def spray(self, pest_count: int, force: bool = False) -> bool:
        """Activate spray if cooldown permits"""
        
        if not force and not self.can_spray():
            remaining = self.get_cooldown_remaining()
            print(f"⏱️ Spray cooldown active: {self.get_cooldown_human()} remaining")
            return False
        
        if self.should_rotate():
            self.rotate_chemical()
        
        chemical = self.get_current_chemical()
        
        print(f"\n💦 [SPRAY] ACTIVATED!")
        print(f"   Mode: {self.mode_label}")
        print(f"   Chemical: {chemical['name']} ({chemical['class']})")
        print(f"   Pest count: {pest_count}")
        print(f"   Duration: {self.spray_duration}s")
        
        # Simulate spray duration (in real hardware, this would trigger GPIO)
        if self.simulation_mode:
            for i in range(self.spray_duration):
                print(f"   Spraying... {i+1}/{self.spray_duration}s", end='\r')
                time.sleep(1)
            print(f"\n   Spray complete!                    ")
        else:
            # Production mode: actual GPIO control would go here
            print(f"   [PRODUCTION] GPIO {self.spray_pin} HIGH for {self.spray_duration}s")
            # GPIO.output(self.spray_pin, GPIO.HIGH)
            time.sleep(self.spray_duration)
            # GPIO.output(self.spray_pin, GPIO.LOW)
            print(f"   Spray complete")
        
        self.application_history.append({
            'timestamp': datetime.now().isoformat(),
            'chemical_name': chemical['name'],
            'chemical_class': chemical['class'],
            'pest_count': pest_count,
            'mode': self.mode_label
        })
        
        self.last_spray_time = time.time()
        
        print(f"✅ Total applications: {len(self.application_history)}")
        print(f"   Next spray available: {self.get_cooldown_human()}")
        return True
    
    def get_status(self) -> dict:
        """Get spray system status"""
        return {
            'mode': self.mode_label,
            'is_spraying': self.is_spraying,
            'cooldown_remaining_seconds': self.get_cooldown_remaining(),
            'cooldown_human': self.get_cooldown_human(),
            'total_applications': len(self.application_history),
            'current_chemical': self.get_current_chemical(),
            'rotation_needed': self.should_rotate(),
            'application_history': self.application_history[-5:]
        }
    
    def emergency_stop(self):
        """Emergency stop - cuts spray immediately"""
        self.is_spraying = False
        print("🛑 Emergency stop - spray deactivated")
    
    def cleanup(self):
        """Cleanup resources"""
        print(f"✅ Spray controller cleaned up (mode: {self.mode_label})")


# Test the zero-pest gate and cooldown modes
if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ZERO PEST GATE AND SPRAY COOLDOWN MODES")
    print("=" * 60)
    
    # Test decision engine with zero-pest gate
    from decision_engine import PestPressureIndex
    engine = PestPressureIndex()
    
    print("\n--- Zero Pest Gate Test ---")
    result = engine.decide(0, 35, 90)  # Extreme conditions, zero pests
    print(f"Zero pests, extreme heat+humidity:")
    print(f"  PPI: {result.pest_pressure_index:.3f}")
    print(f"  Zone: {result.zone}")
    print(f"  Action: {result.action}")
    print(f"  PASS: {result.zone == 'GREEN'}")
    
    # Test spray modes
    print("\n--- Spray Mode Tests ---")
    
    print("\n1. SIMULATION MODE (60s cooldown):")
    spray_sim = SprayController(simulation_mode=True)
    spray_sim.spray(pest_count=3)
    print(f"   Can spray again? {spray_sim.can_spray()}")
    print(f"   Status: {spray_sim.get_status()}")
    
    print("\n2. PRODUCTION MODE (7-day cooldown):")
    spray_prod = SprayController(simulation_mode=False)
    spray_prod.spray(pest_count=3)
    print(f"   Can spray again? {spray_prod.can_spray()}")
    print(f"   Cooldown: {spray_prod.get_cooldown_human()}")
    
    print("\n✅ All tests complete")