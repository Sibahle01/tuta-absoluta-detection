# core/camera_manager.py
import cv2
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
import time


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    timestamp: float


class CameraManager:
    def __init__(self, model_path: str, camera_id: int = 0, conf_threshold: float = 0.5):
        self.model_path = Path(model_path)
        self.camera_id = camera_id
        self.conf_threshold = conf_threshold
        self.model = None
        self.cap = None
        self.camera_available = False
        
        self._load_model()
        self._init_camera()
    
    def _load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(str(self.model_path))
            print(f"✅ Loaded model from {self.model_path}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise
    
    def _init_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
                self.camera_available = True
                print(f"✅ Camera initialized (id={self.camera_id})")
            else:
                print(f"⚠️ Could not open camera {self.camera_id}")
                print(f"   Running in mock mode (no camera)")
                self.camera_available = False
        except Exception as e:
            print(f"⚠️ Camera error: {e}")
            self.camera_available = False
    
    def capture_frame(self):
        if not self.camera_available or self.cap is None:
            return None
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def detect_from_frame(self, frame):
        if self.model is None or frame is None:
            return [], frame
        
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        detections = []
        annotated = frame.copy()
        
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if class_id != 0:
                    continue
                
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                detections.append(Detection(
                    class_id=class_id,
                    class_name='tuta_absoluta',
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    timestamp=time.time()
                ))
                
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated, f"Tuta: {confidence:.2f}", (x1, y1-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return detections, annotated
    
    def detect_once(self):
        """Returns (pest_count, detections, annotated_frame)"""
        frame = self.capture_frame()
        if frame is None:
            # No camera - return mock data for testing
            return 0, [], None
        detections, annotated = self.detect_from_frame(frame)
        return len(detections), detections, annotated
    
    def test_model_on_image(self, image_path: str):
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not read: {image_path}")
            return 0, []
        detections, _ = self.detect_from_frame(image)
        print(f"Detected {len(detections)} Tuta absoluta")
        for d in detections:
            print(f"   Confidence: {d.confidence:.3f}")
        return len(detections), detections
    
    def release(self):
        if self.cap:
            self.cap.release()