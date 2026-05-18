"""
Test your trained YOLO model on the dataset test images
No camera needed - uses your 1,799 test images
"""

import cv2
import os
from pathlib import Path
from ultralytics import YOLO

# Paths
MODEL_PATH = r"D:\yolov8m_final\weights\best.pt"
DATASET_PATH = r"D:\tuta-absoluta-detection-1\test\images"

print("=" * 60)
print("TESTING YOLO MODEL ON DATASET TEST IMAGES")
print("=" * 60)

# Load model
print(f"\n📷 Loading model: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

# Get all test images
test_images = list(Path(DATASET_PATH).glob("*.jpg")) + list(Path(DATASET_PATH).glob("*.png"))
print(f"📸 Found {len(test_images)} test images")

# Test parameters
CONF_THRESHOLD = 0.5
results_summary = {
    'total_images': 0,
    'images_with_pests': 0,
    'total_pests_detected': 0,
    'max_pests_in_one_image': 0,
    'confidence_scores': []
}

print(f"\n🔬 Running detection (conf threshold: {CONF_THRESHOLD})...")
print("-" * 60)

for i, img_path in enumerate(test_images[:50]):  # Test first 50 images (change to run all)
    # Run detection
    results = model(str(img_path), conf=CONF_THRESHOLD, verbose=False)
    
    # Count Tuta absoluta detections (class 0)
    pest_count = 0
    confidences = []
    
    if len(results) > 0 and results[0].boxes is not None:
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            
            if class_id == 0:  # tuta_absoluta
                pest_count += 1
                confidences.append(confidence)
    
    # Update summary
    results_summary['total_images'] += 1
    results_summary['total_pests_detected'] += pest_count
    results_summary['confidence_scores'].extend(confidences)
    
    if pest_count > 0:
        results_summary['images_with_pests'] += 1
        results_summary['max_pests_in_one_image'] = max(
            results_summary['max_pests_in_one_image'], 
            pest_count
        )
    
    # Print progress every 10 images
    if (i + 1) % 10 == 0:
        print(f"   Processed {i+1}/{len(test_images[:50])} images...")

# Print results
print("\n" + "=" * 60)
print("TEST RESULTS")
print("=" * 60)
print(f"\n📊 Summary (on {results_summary['total_images']} test images):")
print(f"   Images with pests detected: {results_summary['images_with_pests']}")
print(f"   Total pests detected: {results_summary['total_pests_detected']}")
print(f"   Max pests in one image: {results_summary['max_pests_in_one_image']}")
print(f"   Average pests per image: {results_summary['total_pests_detected'] / results_summary['total_images']:.2f}")

if results_summary['confidence_scores']:
    print(f"\n📈 Confidence scores:")
    print(f"   Min: {min(results_summary['confidence_scores']):.3f}")
    print(f"   Max: {max(results_summary['confidence_scores']):.3f}")
    print(f"   Avg: {sum(results_summary['confidence_scores']) / len(results_summary['confidence_scores']):.3f}")

print("\n✅ Test complete!")