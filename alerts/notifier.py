"""
Notification module for sending alerts
Supports SMS (via SIM800L), console, and multiple notifiers
"""

import time
from typing import List, Optional
from abc import ABC, abstractmethod


class Notifier(ABC):
    """Base class for all notifiers"""
    
    @abstractmethod
    def send(self, message: str, priority: str = "normal") -> bool:
        """Send notification"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return notifier name"""
        pass


class ConsoleNotifier(Notifier):
    """Console notifier for testing/debugging"""
    
    def __init__(self):
        self.sent_count = 0
    
    def send(self, message: str, priority: str = "normal") -> bool:
        self.sent_count += 1
        prefix = "🔴" if priority == "critical" else "🟡" if priority == "warning" else "🔵"
        print(f"{prefix} [CONSOLE] {message}")
        return True
    
    def get_name(self) -> str:
        return "console"


class SMSNotifier(Notifier):
    """
    SMS notifier using SIM800L module over serial
    """
    
    def __init__(self, port: str = "/dev/ttyS0", baudrate: int = 9600, 
                 phone_number: Optional[str] = None):
        self.port = port
        self.baudrate = baudrate
        self.phone_number = phone_number
        self.serial_connection = None
        self.available = False
        self._connect()
    
    def _connect(self):
        """Connect to SIM800L over serial"""
        try:
            import serial
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(1)
            
            # Test AT commands
            self.serial_connection.write(b'AT\r\n')
            response = self.serial_connection.read(50)
            
            if b'OK' in response:
                self.available = True
                print(f"✅ SIM800L connected on {self.port}")
                # Set SMS text mode
                self.serial_connection.write(b'AT+CMGF=1\r\n')
                time.sleep(0.5)
            else:
                print(f"⚠️ SIM800L not responding on {self.port}")
                self.available = False
                
        except ImportError:
            print("⚠️ PySerial not installed. SMS notifier disabled.")
            self.available = False
        except Exception as e:
            print(f"⚠️ Failed to connect to SIM800L: {e}")
            self.available = False
    
    def set_phone_number(self, phone_number: str):
        """Set recipient phone number"""
        self.phone_number = phone_number
    
    def send(self, message: str, priority: str = "normal") -> bool:
        """Send SMS via SIM800L"""
        if not self.available:
            print(f"📱 [MOCK SMS] Would send: {message[:100]}...")
            return True
        
        if not self.phone_number:
            print("❌ No phone number set for SMS")
            return False
        
        try:
            # Send AT command to set recipient
            cmd = f'AT+CMGS="{self.phone_number}"\r\n'
            self.serial_connection.write(cmd.encode())
            time.sleep(1)
            
            # Send message
            self.serial_connection.write((message + '\x1A').encode())
            time.sleep(3)
            
            return True
        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")
            return False
    
    def get_name(self) -> str:
        return "sms"


class MultiNotifier(Notifier):
    """Composite notifier that sends to multiple channels"""
    
    def __init__(self, notifiers: List[Notifier]):
        self.notifiers = notifiers
    
    def add_notifier(self, notifier: Notifier):
        """Add a notifier to the list"""
        self.notifiers.append(notifier)
    
    def send(self, message: str, priority: str = "normal") -> bool:
        """Send to all registered notifiers"""
        success = True
        for notifier in self.notifiers:
            if not notifier.send(message, priority):
                success = False
        return success
    
    def get_name(self) -> str:
        names = [n.get_name() for n in self.notifiers]
        return f"multi({','.join(names)})"


class RateLimitedNotifier(Notifier):
    """Wrapper that rate-limits notifications to prevent spam"""
    
    def __init__(self, notifier: Notifier, cooldown_seconds: int = 3600):
        self.notifier = notifier
        self.cooldown = cooldown_seconds
        self.last_sent = {}
        self.last_message = ""
    
    def send(self, message: str, priority: str = "normal") -> bool:
        current_time = time.time()
        
        # Critical alerts bypass rate limit
        if priority == "critical":
            return self.notifier.send(message, priority)
        
        # Check cooldown
        if message in self.last_sent:
            if current_time - self.last_sent[message] < self.cooldown:
                print(f"⏱️ Rate limited: '{message[:50]}...' (cooldown {self.cooldown}s)")
                return False
        
        # Check if same as last message
        if message == self.last_message:
            if current_time - self.last_sent.get(message, 0) < self.cooldown / 2:
                print(f"⏱️ Rate limited: duplicate message")
                return False
        
        self.last_sent[message] = current_time
        self.last_message = message
        return self.notifier.send(message, priority)
    
    def get_name(self) -> str:
        return f"rate_limited({self.notifier.get_name()})"


if __name__ == "__main__":
    print("=== Notifier Test ===")
    
    # Test console notifier
    console = ConsoleNotifier()
    console.send("Test message from console notifier")
    
    # Test multi-notifier
    multi = MultiNotifier([console])
    multi.send("Test from multi-notifier")
    
    # Test rate-limited notifier
    limited = RateLimitedNotifier(console, cooldown_seconds=5)
    limited.send("First message")
    limited.send("First message")  # Should be rate limited
    print("Wait 6 seconds...")
    time.sleep(6)
    limited.send("First message")  # Should go through after cooldown