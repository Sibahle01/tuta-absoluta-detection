import sys, time, cv2, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ultralytics import YOLO
from core.decision_engine import PestPressureIndex
from core.resistance_manager import ResistanceManager

MODEL_PATH   = r"D:\yolov8m_final\weights\best.pt"
DATASET_PATH = r"D:\tuta-absoluta-detection-1\test\images"
CONF         = 0.50
DELAY_MS     = 2500

print("Loading model...")
model  = YOLO(MODEL_PATH)
engine = PestPressureIndex()
rm     = ResistanceManager()

images = list(Path(DATASET_PATH).glob("*.jpg"))
if not images:
    print(f"No images found at {DATASET_PATH}")
    sys.exit(1)

random.shuffle(images)
print(f"Found {len(images)} test images. Press Q to quit, SPACE to skip.")

zone_colors = {
    "GREEN":  (0, 200, 0),
    "YELLOW": (0, 200, 255),
    "ORANGE": (0, 140, 255),
    "RED":    (0, 0, 255)
}

for img_path in images:
    frame = cv2.imread(str(img_path))
    if frame is None:
        continue

    results = model(frame, conf=CONF, imgsz=640, verbose=False)
    tuta_count = 0
    annotated  = frame.copy()

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            if cls_id == 0:
                tuta_count += 1
                cv2.rectangle(annotated, (x1,y1), (x2,y2), (0,255,0), 3)
                cv2.putText(annotated, f"Tuta {conf:.2f}",
                    (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    decision = engine.decide(tuta_count, 25.0, 65.0)
    zone  = decision.zone
    color = zone_colors.get(zone, (255,255,255))

    chemical = ""
    if decision.action == "spray":
        chem = rm.get_next_chemical()
        if chem:
            chemical = f" | Apply: {chem.chemical_name}"

    h, w = annotated.shape[:2]
    cv2.rectangle(annotated, (0,0), (w,90), (20,20,20), -1)
    cv2.putText(annotated,
        f"Tuta absoluta detected: {tuta_count}  |  Zone: {zone}  |  Action: {decision.action.upper()}{chemical}",
        (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(annotated,
        f"PPI: {decision.pest_pressure_index:.3f}  |  {decision.message[:80]}",
        (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)

    icon = "GREEN" if zone=="GREEN" else "YELLOW" if zone=="YELLOW" else "ORANGE" if zone=="ORANGE" else "RED"
    print(f"[{icon}] Pests: {tuta_count} | PPI: {decision.pest_pressure_index:.3f} | {decision.action.upper()}{chemical}")

    cv2.imshow("Tuta absoluta IPM System - Dataset Demo", annotated)
    key = cv2.waitKey(DELAY_MS) & 0xFF
    if key == ord('q') or key == 27:
        break

cv2.destroyAllWindows()
print("Demo complete.")