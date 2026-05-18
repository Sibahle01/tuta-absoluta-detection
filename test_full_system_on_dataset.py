"""
Test the complete IPM system (detection + decision + spray) on dataset images
"""

import cv2
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ultralytics import YOLO
from core.decision_engine import PestPressureIndex
from core.spray_controller import SprayController  # Mock version for testing

# Paths
MODEL_PATH = r"D:\yolov8m_final\weights\best.pt"
DATASET_PATH = r"D:\tuta-absoluta-detection-1\test\images"

print("=" * 70)
print("FULL SYSTEM TEST ON DATASET IMAGES (Detection + Decision + Spray)")
print("=" * 70)

# Load model
print(f"\n📷 Loading model...")
model = YOLO(MODEL_PATH)

# Initialize decision engine
decision_engine = PestPressureIndex()

# Initialize spray (mock for testing)
spray = SprayController()
spray_enabled = True

print(f"\n🔬 Processing test images...")
print("-" * 70)

# Get test images
test_images = list(Path(DATASET_PATH).glob("*.jpg")) + list(Path(DATASET_PATH).glob("*.png"))
print(f"📸 Found {len(test_images)} test images\n")

# Results tracking
results = []
spray_count = 0
warning_count = 0
monitor_count = 0
safe_count = 0

CONF_THRESHOLD = 0.5

for i, img_path in enumerate(test_images[:100]):  # Test first 100 images
    # Read image
    image = cv2.imread(str(img_path))
    if image is None:
        continue
    
    # Detect pests
    detections = model(image, conf=CONF_THRESHOLD, verbose=False)
    
    # Count Tuta absoluta (class 0)
    pest_count = 0
    confidences = []
    
    if len(detections) > 0 and detections[0].boxes is not None:
        for box in detections[0].boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            if class_id == 0:
                pest_count += 1
                confidences.append(confidence)
    
    # Get environmental data (mock for testing)
    temperature = 25.0
    humidity = 60.0
    
    # Run decision engine
    decision = decision_engine.decide(pest_count, temperature, humidity)
    
    # Simulate spray if needed
    sprayed = False
    if decision.action == "spray" and spray_enabled and pest_count > 0:
        sprayed = spray.spray(pest_count=pest_count)
        if sprayed:
            spray_count += 1
    
    # Count actions
    if decision.action == "spray":
        spray_count += 1 if not sprayed else 0
    elif decision.action == "warning":
        warning_count += 1
    elif decision.action == "monitor":
        monitor_count += 1
    else:
        safe_count += 1
    
    # Store result
    results.append({
        'image': img_path.name,
        'pest_count': pest_count,
        'confidence_mean': sum(confidences)/len(confidences) if confidences else 0,
        'action': decision.action,
        'ppi': decision.pest_pressure_index,
        'sprayed': sprayed
    })
    
    # Print sample results
    if pest_count > 0 or i % 20 == 0:
        spray_symbol = "💦" if sprayed else "🔫" if decision.action == "spray" else "⬜"
        print(f"{spray_symbol} {img_path.name}: {pest_count} pests | "
              f"PPI={decision.pest_pressure_index:.2f} | {decision.action.upper()}")

# Print summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"\n📊 Total images processed: {len(results)}")
print(f"\n🎯 Decisions made:")
print(f"   🚨 SPRAY:  {spray_count} images")
print(f"   ⚠️ WARNING: {warning_count} images")
print(f"   👁️ MONITOR: {monitor_count} images")
print(f"   ✅ SAFE:    {safe_count} images")

print(f"\n🐛 Pest statistics:")
pest_counts = [r['pest_count'] for r in results]
print(f"   Images with pests: {sum(1 for c in pest_counts if c > 0)}")
print(f"   Total pests detected: {sum(pest_counts)}")
print(f"   Max pests in one image: {max(pest_counts)}")
print(f"   Average pests/image: {sum(pest_counts)/len(pest_counts):.2f}")

if spray_count > 0:
    print(f"\n💦 Spray would have been activated on {spray_count} images")

print("\n✅ System test complete!")