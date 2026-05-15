"""
Environmental sensor module for temperature and humidity
Supports DHT22 on Raspberry Pi GPIO and Mock for testing
"""

import time
from typing import Tuple, Optional
from dataclasses import dataclass

# Try to import numpy for variation (optional)
try:
    import numpy as np
except ImportError:
    np = None
    import math


@dataclass
class EnvironmentalData:
    """Environmental sensor readings"""
    temperature_celsius: float
    humidity_percent: float
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class EnvironmentalSensor:
    """Base class for environmental sensors"""
    
    def read_temperature(self) -> float:
        """Read temperature in Celsius"""
        raise NotImplementedError
    
    def read_humidity(self) -> float:
        """Read relative humidity percentage"""
        raise NotImplementedError
    
    def read_all(self) -> EnvironmentalData:
        """Read all environmental data"""
        return EnvironmentalData(
            temperature_celsius=self.read_temperature(),
            humidity_percent=self.read_humidity(),
            timestamp=time.time()
        )


class DHT22Sensor(EnvironmentalSensor):
    """
    DHT22 temperature/humidity sensor for Raspberry Pi
    Requires Adafruit_DHT library
    """
    
    def __init__(self, pin: int = 4):
        self.pin = pin
        self.sensor_available = False
        
        try:
            import Adafruit_DHT
            self.dht = Adafruit_DHT
            self.sensor_available = True
            print(f"✅ DHT22 sensor initialized on GPIO pin {pin}")
        except ImportError:
            print("⚠️ Adafruit_DHT not installed. Run: pip install Adafruit_DHT")
            print("   Using fallback mock values")
    
    def read_temperature(self) -> float:
        """Read temperature from DHT22"""
        if not self.sensor_available:
            return 25.0  # Fallback value
        
        try:
            humidity, temperature = self.dht.read_retry(self.dht.DHT22, self.pin)
            if temperature is not None:
                return temperature
            return 25.0
        except Exception as e:
            print(f"Error reading temperature: {e}")
            return 25.0
    
    def read_humidity(self) -> float:
        """Read humidity from DHT22"""
        if not self.sensor_available:
            return 60.0  # Fallback value
        
        try:
            humidity, temperature = self.dht.read_retry(self.dht.DHT22, self.pin)
            if humidity is not None:
                return humidity
            return 60.0
        except Exception as e:
            print(f"Error reading humidity: {e}")
            return 60.0


class MockSensor(EnvironmentalSensor):
    """Mock sensor for testing without hardware"""
    
    def __init__(self, fixed_temp: float = 25.0, fixed_humidity: float = 60.0):
        self.fixed_temp = fixed_temp
        self.fixed_humidity = fixed_humidity
        self.vary = False
        self.start_time = time.time()
        print("✅ Mock sensor initialized (for testing)")
    
    def enable_variation(self, amplitude_temp: float = 2.0, amplitude_humidity: float = 10.0):
        """Enable simulated daily variation for testing"""
        self.vary = True
        self.amplitude_temp = amplitude_temp
        self.amplitude_humidity = amplitude_humidity
    
    def _sin(self, x):
        """Sine function that works with or without numpy"""
        if np is not None:
            return np.sin(x)
        return math.sin(x)
    
    def read_temperature(self) -> float:
        if self.vary:
            # Simulate diurnal variation (24 hour cycle)
            hour = (time.time() - self.start_time) / 3600 % 24
            variation = self.amplitude_temp * self._sin(2 * 3.14159 * hour / 24)
            return self.fixed_temp + variation
        return self.fixed_temp
    
    def read_humidity(self) -> float:
        if self.vary:
            # Humidity inverse to temperature
            hour = (time.time() - self.start_time) / 3600 % 24
            variation = self.amplitude_humidity * self._sin(2 * 3.14159 * hour / 24 + 3.14159)
            result = self.fixed_humidity + variation
            # Clamp to realistic range
            return max(20, min(85, result))
        return self.fixed_humidity


# For testing
if __name__ == "__main__":
    print("=== Environmental Sensor Test ===")
    
    # Test MockSensor
    mock = MockSensor()
    print(f"Mock - Temp: {mock.read_temperature():.1f}°C, Humidity: {mock.read_humidity():.1f}%")
    
    # Test with variation
    mock.enable_variation()
    for i in range(5):
        time.sleep(0.5)
        print(f"Mock (varying) - Temp: {mock.read_temperature():.1f}°C, Humidity: {mock.read_humidity():.1f}%")
    
    # Test read_all
    data = mock.read_all()
    print(f"\nread_all() - Temp: {data.temperature_celsius:.1f}°C, Humidity: {data.humidity_percent:.1f}%")
    
    print("\n✅ Sensor module ready")