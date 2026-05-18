"""
Live Camera Preview with YOLO Detection
Run this to see exactly what your camera sees and what the model detects.

Usage:
    python camera_preview.py

Controls:
    Q - Quit
    S - Save current frame
    + - Increase confidence threshold
    - - Decrease confidence threshold
"""

import cv2
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ultralytics import YOLO

# ============================================================
# CONFIGURATION — adjust these if needed
# ============================================================
MODEL_PATH = r"D:\yolov8m_final\weights\best.pt"
CAMERA_ID  = 0          # Try 0, 1, 2 if camera not found
CONF_THRESHOLD = 0.60   # Balanced threshold
IMG_SIZE   = 640

# Class names from your trained model
CLASS_NAMES = {0: "tuta_absoluta", 1: "insect"}
CLASS_COLORS = {
    "tuta_absoluta": (0, 255, 0),    # Green
    "insect":        (0, 165, 255),  # Orange
}

# ============================================================
# LOAD MODEL
# ============================================================
print(f"Loading model from: {MODEL_PATH}")
if not Path(MODEL_PATH).exists():
    print(f"Model not found at {MODEL_PATH}")
    print("Check the path and try again.")
    sys.exit(1)

model = YOLO(MODEL_PATH)
print("Model loaded.")

# ============================================================
# OPEN CAMERA
# ============================================================
print(f"Opening camera {CAMERA_ID}...")
cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)  # Use DSHOW backend on Windows

if not cap.isOpened():
    print(f"Could not open camera {CAMERA_ID}")
    print("Try changing CAMERA_ID to 1 or 2 at the top of this script")
    sys.exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Camera resolution: {actual_w}x{actual_h}")
print()
print("=" * 50)
print("LIVE PREVIEW RUNNING")
print("  Q     = Quit")
print("  S     = Save current frame")
print("  +/-   = Adjust confidence threshold")
print("=" * 50)

# ============================================================
# DETECTION LOOP
# ============================================================
conf = CONF_THRESHOLD
frame_count = 0
tuta_total = 0
fps_start = time.time()
fps = 0.0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame_count += 1

    # Run YOLO detection
    results = model(frame, conf=conf, imgsz=IMG_SIZE, verbose=False)

    # Count detections
    tuta_count = 0
    insect_count = 0
    annotated = frame.copy()

    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue

        for box in boxes:
            cls_id    = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            class_name = CLASS_NAMES.get(cls_id, f"class_{cls_id}")
            color = CLASS_COLORS.get(class_name, (255, 255, 255))

            if class_name == "tuta_absoluta":
                tuta_count += 1
            else:
                insect_count += 1

            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Label background
            label = f"{class_name} {confidence:.2f}"
            (lw, lh), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            cv2.rectangle(
                annotated,
                (x1, y1 - lh - 6), (x1 + lw, y1),
                color, -1
            )
            cv2.putText(
                annotated, label, (x1, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 0, 0), 1
            )

    tuta_total += tuta_count

    # Calculate FPS every 30 frames
    if frame_count % 30 == 0:
        fps = 30 / (time.time() - fps_start)
        fps_start = time.time()

    # ---- OVERLAY: status panel - UPDATED THRESHOLDS ----
    # Spray at 2+ pests, Warning at 2, Monitor at 1
    if tuta_count == 0:
        zone_text  = "GREEN — No pests"
        zone_color = (0, 200, 0)
        action_text = "NONE"
        action_color = (100, 100, 100)
    elif tuta_count == 1:
        zone_text  = "GREEN — Below threshold"
        zone_color = (0, 200, 0)
        action_text = "MONITOR"
        action_color = (0, 200, 255)
    elif tuta_count == 2:
        zone_text  = "ORANGE — Warning"
        zone_color = (0, 140, 255)
        action_text = "WARNING — Prepare to spray"
        action_color = (0, 140, 255)
    else:  # tuta_count >= 3
        zone_text  = "RED — SPRAY NOW"
        zone_color = (0, 0, 255)
        action_text = "SPRAY — Activating"
        action_color = (0, 0, 255)

    # Semi-transparent top banner
    overlay = annotated.copy()
    cv2.rectangle(overlay, (0, 0), (actual_w, 110), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)

    # Text lines
    cv2.putText(annotated,
        f"Tuta absoluta IPM System — LIVE PREVIEW",
        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.putText(annotated,
        f"Tuta: {tuta_count}   Other: {insect_count}   Conf: {conf:.2f}   FPS: {fps:.1f}",
        (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.putText(annotated,
        f"Zone: {zone_text}",
        (10, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55, zone_color, 2)

    cv2.putText(annotated,
        f"Action: {action_text}",
        (10, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.55, action_color, 2)

    # Bottom instruction bar
    cv2.rectangle(annotated, (0, actual_h - 25), (actual_w, actual_h),
                  (30, 30, 30), -1)
    cv2.putText(annotated,
        "Q=Quit   S=Save   +=Higher conf   -=Lower conf",
        (10, actual_h - 8),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    # Show frame
    cv2.imshow("Tuta absoluta IPM — Live Detection", annotated)

    # Print to terminal when pests detected
    if tuta_count > 0:
        print(f"[{time.strftime('%H:%M:%S')}] "
              f"DETECTED: {tuta_count} Tuta absoluta | {zone_text} | {action_text}")

    # Keyboard input
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q') or key == 27:   # Q or ESC
        print("Quitting preview.")
        break

    elif key == ord('s'):              # Save frame
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename  = f"preview_capture_{timestamp}.jpg"
        cv2.imwrite(filename, annotated)
        print(f"Frame saved: {filename}")

    elif key == ord('+') or key == ord('='):
        conf = min(0.95, conf + 0.05)
        print(f"Confidence threshold: {conf:.2f}")

    elif key == ord('-'):
        conf = max(0.05, conf - 0.05)
        print(f"Confidence threshold: {conf:.2f}")

# ============================================================
# CLEANUP
# ============================================================
cap.release()
cv2.destroyAllWindows()
print(f"\nSession summary:")
print(f"  Frames processed : {frame_count}")
print(f"  Total detections : {tuta_total}")