#!/usr/bin/env python3
"""
Tuta absoluta IPM System - Main Entry Point
INTEGRATED WITH YOUR 98.5% MAP YOLO MODEL
"""

import argparse
import sys
import time
import signal
import cv2
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.decision_engine import PestPressureIndex
from core.resistance_manager import ResistanceManager
from core.camera_manager import CameraManager
from sensors.environmental import MockSensor, DHT22Sensor
from alerts.notifier import ConsoleNotifier, RateLimitedNotifier
from alerts.logger import JSONLogger, CSVLogger


class TutaIPMSystem:
    """Main system orchestrator with YOUR trained model"""
    
    def __init__(self, model_path: str, use_mocks: bool = True, 
                 camera_id: int = 0, phone_number: str = None):
        print("🚀 Starting Tuta absoluta IPM System")
        print("=" * 50)
        
        # Your YOLO Model
        print("📷 Loading YOUR trained model...")
        self.camera = CameraManager(model_path, camera_id=camera_id)
        
        # Decision components
        print("🧠 Initializing decision engine...")
        self.decision_engine = PestPressureIndex()
        
        print("💊 Initializing resistance manager...")
        self.resistance_manager = ResistanceManager()
        
        # Environmental sensors
        print("🌡️ Initializing environmental sensors...")
        if use_mocks:
            self.env_sensor = MockSensor()
            self.env_sensor.enable_variation()
        else:
            self.env_sensor = DHT22Sensor(pin=4)
        
        # Notifiers
        print("📱 Initializing notifiers...")
        console = ConsoleNotifier()
        self.notifier = RateLimitedNotifier(console, cooldown_seconds=60)
        
        # Loggers
        print("📝 Initializing loggers...")
        self.json_logger = JSONLogger()
        self.csv_logger = CSVLogger()
        
        print("✅ System ready with YOUR 98.5% mAP model!")
        print("=" * 50)
        
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Stats tracking
        self.total_detections = 0
        self.total_frames = 0
    
    def _signal_handler(self, signum, frame):
        print("\n🛑 Shutdown signal received...")
        self.running = False
    
    def run_once(self, save_image: bool = False) -> dict:
        """Single detection cycle using YOUR YOLO model"""
        
        # 1. Capture and detect with your model
        pest_count, detections, annotated_frame = self.camera.detect_once()
        
        self.total_frames += 1
        self.total_detections += pest_count
        
        # 2. Get environmental data
        env_data = self.env_sensor.read_all()
        temperature = env_data.temperature_celsius
        humidity = env_data.humidity_percent
        
        # 3. Run decision engine
        decision = self.decision_engine.decide(pest_count, temperature, humidity)
        
        # 4. Get chemical recommendation if needed
        chemical = None
        if decision.action == "spray":
            chemical = self.resistance_manager.get_next_chemical()
            decision.recommended_chemical = chemical.chemical_name
        
        # 5. Log event
        event = {
            'pest_count': pest_count,
            'detection_confidences': [d.confidence for d in detections],
            'temperature': temperature,
            'humidity': humidity,
            'ppi': decision.pest_pressure_index,
            'action': decision.action,
            'alert_level': decision.alert_level,
            'message': decision.message,
            'temperature_factor': decision.temperature_factor,
            'humidity_factor': decision.humidity_factor,
            'trend_factor': decision.trend_factor,
            'recommended_chemical': decision.recommended_chemical,
            'total_detections_so_far': self.total_detections
        }
        
        self.json_logger.log(event)
        self.csv_logger.log(event)
        
        # 6. Send notification if needed
        if decision.action in ['warning', 'spray']:
            self.notifier.send(decision.message, priority=decision.action)
        
        # 7. Save annotated image if requested
        if save_image and annotated_frame is not None and pest_count > 0:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            Path("detections").mkdir(exist_ok=True)
            cv2.imwrite(f"detections/detection_{timestamp}.jpg", annotated_frame)
        
        # 8. Print to console
        conf_str = ""
        if detections:
            confs = [d.confidence for d in detections]
            conf_str = f"[min:{min(confs):.2f}/max:{max(confs):.2f}]"
        print(f"🐛 Pests: {pest_count} {conf_str} | 🌡️ {temperature:.1f}°C | 💧 {humidity:.0f}% | "
              f"📊 PPI: {decision.pest_pressure_index:.2f} | {decision.action.upper()}")
        
        if decision.recommended_chemical:
            print(f"   💊 Recommended: {decision.recommended_chemical}")
        
        return event
    
    def run_continuous(self, interval_seconds: int = 60, save_images: bool = False):
        """Run detection continuously"""
        print(f"🔄 Running continuous mode (every {interval_seconds} seconds)")
        print("   Using YOUR trained YOLO model (98.5% mAP)")
        print("Press Ctrl+C to stop")
        print()
        
        cycle = 0
        while self.running:
            cycle += 1
            print(f"\n--- Cycle {cycle} @ {time.strftime('%H:%M:%S')} ---")
            
            start_time = time.time()
            self.run_once(save_image=save_images)
            
            # Print stats every 10 cycles
            if cycle % 10 == 0 and self.total_frames > 0:
                avg_detections = self.total_detections / self.total_frames
                print(f"\n📊 STATS: {self.total_frames} frames, "
                      f"{self.total_detections} total pests, "
                      f"avg {avg_detections:.2f}/frame")
            
            # Wait for next interval
            elapsed = time.time() - start_time
            wait_time = max(0, interval_seconds - elapsed)
            if wait_time > 0 and self.running:
                time.sleep(wait_time)
        
        self._shutdown()
    
    def run_test_on_image(self, image_path: str):
        """Test your model on a single image"""
        print(f"\n🔬 Testing model on: {image_path}")
        pest_count, detections = self.camera.test_model_on_image(image_path)
        
        print(f"\n📊 Decision for this image:")
        decision = self.decision_engine.decide(pest_count, 25, 60)
        print(f"   Action: {decision.action}")
        print(f"   Alert Level: {decision.alert_level}")
        print(f"   Message: {decision.message}")
    
    def _shutdown(self):
        """Clean shutdown"""
        print("\n📊 Final Statistics:")
        if self.total_frames > 0:
            avg = self.total_detections / self.total_frames
            print(f"   Total frames processed: {self.total_frames}")
            print(f"   Total Tuta detected: {self.total_detections}")
            print(f"   Average per frame: {avg:.2f}")
        
        self.camera.release()
        print("✅ System shutdown complete")


def main():
    parser = argparse.ArgumentParser(description='Tuta absoluta IPM System')
    parser.add_argument('--model', type=str, 
                        default=r"D:\yolov8m_final\weights\best.pt",
                        help='Path to your trained YOLO model')
    parser.add_argument('--mode', choices=['once', 'continuous', 'test_image'],
                        default='once', help='Run mode')
    parser.add_argument('--interval', type=int, default=60,
                        help='Seconds between checks')
    parser.add_argument('--camera', type=int, default=0,
                        help='Camera ID')
    parser.add_argument('--image', type=str,
                        help='Image path for test_image mode')
    parser.add_argument('--save-images', action='store_true',
                        help='Save annotated images when pests detected')
    parser.add_argument('--phone', type=str,
                        help='Phone number for SMS alerts')
    parser.add_argument('--no-mocks', action='store_true',
                        help='Use real hardware (DHT22, etc.)')
    
    args = parser.parse_args()
    
    # Check if model exists
    if not Path(args.model).exists():
        print(f"❌ Model not found at: {args.model}")
        print("   Update --model path to your best.pt file")
        sys.exit(1)
    
    # Create system with YOUR model
    system = TutaIPMSystem(
        model_path=args.model,
        use_mocks=not args.no_mocks,
        camera_id=args.camera,
        phone_number=args.phone
    )
    
    # Run requested mode
    if args.mode == 'once':
        system.run_once(save_image=args.save_images)
    elif args.mode == 'continuous':
        system.run_continuous(interval_seconds=args.interval, 
                             save_images=args.save_images)
    elif args.mode == 'test_image':
        if not args.image:
            print("❌ Please provide --image path")
            sys.exit(1)
        system.run_test_on_image(args.image)


if __name__ == "__main__":
    main()