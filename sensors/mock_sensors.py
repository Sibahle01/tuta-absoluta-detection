"""
Mock sensors for testing without hardware
"""

import time
import random
from typing import Tuple

from sensors.environmental import MockSensor


class SimulatedInfestation:
    """
    Simulates pest infestation over time for testing
    """
    
    def __init__(self, pest_name: str = "tuta_absoluta"):
        self.pest_name = pest_name
        self.base_count = 0
        self.start_time = time.time()
        self.outbreak_active = False
    
    def start_outbreak(self, peak_count: int = 10, duration_hours: float = 24):
        """Start a simulated outbreak"""
        self.outbreak_active = True
        self.outbreak_start = time.time()
        self.peak_count = peak_count
        self.duration = duration_hours * 3600
        print(f"🚨 Simulated outbreak started: {peak_count} pests expected")
    
    def get_pest_count(self) -> int:
        """Get current simulated pest count"""
        if not self.outbreak_active:
            return random.randint(0, 2)
        
        elapsed = time.time() - self.outbreak_start
        if elapsed > self.duration:
            self.outbreak_active = False
            return random.randint(0, 1)
        
        # Gaussian-like outbreak curve
        t = elapsed / self.duration  # 0 to 1
        factor = 4 * t * (1 - t)  # Peak at t=0.5, factor=1
        count = int(self.peak_count * factor)
        return max(0, min(self.peak_count, count))
    
    def reset(self):
        """Reset simulation"""
        self.outbreak_active = False
        self.base_count = 0


class MockCamera:
    """Mock camera for testing without hardware"""
    
    def __init__(self):
        self.image_counter = 0
        print("✅ Mock camera initialized")
    
    def capture(self) -> str:
        """Simulate capturing an image"""
        self.image_counter += 1
        return f"mock_frame_{self.image_counter}.jpg"


class MockGSM:
    """Mock GSM module for testing without hardware"""
    
    def __init__(self):
        self.messages_sent = []
        print("✅ Mock GSM initialized")
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """Simulate sending SMS"""
        self.messages_sent.append({
            'timestamp': time.time(),
            'phone': phone_number,
            'message': message
        })
        print(f"📱 [MOCK SMS] To: {phone_number}")
        print(f"   Message: {message[:100]}...")
        return True
    
    def get_message_count(self) -> int:
        return len(self.messages_sent)


if __name__ == "__main__":
    print("=== Mock Sensors Test ===")
    
    # Test outbreak simulation
    outbreak = SimulatedInfestation()
    print("\nSimulating outbreak:")
    for i in range(20):
        count = outbreak.get_pest_count()
        print(f"  Time {i}: {count} pests")
        if i == 5:
            outbreak.start_outbreak(peak_count=12)
    
    # Test mock GSM
    gsm = MockGSM()
    gsm.send_sms("+27123456789", "Test alert: Tuta absoluta detected!")
    print(f"\nMessages sent: {gsm.get_message_count()}")