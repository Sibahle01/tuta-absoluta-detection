"""
YOLO Detection Wrapper for Tuta absoluta
Optimized for Raspberry Pi 4B
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
import time


@dataclass
class Detection:
    """Single detection result"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2


class TutaDetector:
    """
    Wrapper for YOLO pest detection
    Supports both PyTorch and TFLite backends
    """
    
    def __init__(self, model_path: str, conf_threshold: float = 0.5):
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        self.model = None
        self.backend = None
        
        # Class mapping (from your dataset)
        self.class_names = {
            0: 'tuta_absoluta',
            1: 'insect'  # Other insects (non-target)
        }
        
        self._load_model()
    
    def _load_model(self):
        """Load model based on file extension"""
        if self.model_path.suffix == '.tflite':
            self._load_tflite()
        elif self.model_path.suffix in ['.pt', '.pth']:
            self._load_pytorch()
        else:
            raise ValueError(f"Unsupported model format: {self.model_path.suffix}")
    
    def _load_pytorch(self):
        """Load PyTorch model (Ultralytics YOLO)"""
        from ultralytics import YOLO
        self.model = YOLO(str(self.model_path))
        self.backend = 'pytorch'
        print(f"✅ Loaded PyTorch model from {self.model_path}")
    
    def _load_tflite(self):
        """Load TensorFlow Lite model for RPi optimization"""
        import tflite_runtime.interpreter as tflite
        self.interpreter = tflite.Interpreter(model_path=str(self.model_path))
        self.interpreter.allocate_tensors()
        self.backend = 'tflite'
        
        # Get input/output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_size = self.input_details[0]['shape'][1]  # 640 typically
        print(f"✅ Loaded TFLite model from {self.model_path}")
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for model input"""
        if self.backend == 'tflite':
            # Resize to model input size
            h, w = self.input_size, self.input_size
            resized = cv2.resize(image, (w, h))
            # Normalize to [0,1] and add batch dimension
            input_tensor = resized.astype(np.float32) / 255.0
            input_tensor = np.expand_dims(input_tensor, axis=0)
            return input_tensor
        else:
            # PyTorch model handles preprocessing internally
            return image
    
    def detect(self, image: np.ndarray) -> List[Detection]:
        """
        Run detection on single image
        Returns list of Detection objects (tuta_absoluta only by default)
        """
        if self.backend == 'pytorch':
            results = self.model(image, conf=self.conf_threshold, verbose=False)
            return self._parse_pytorch_results(results)
        else:
            return self._detect_tflite(image)
    
    def _detect_tflite(self, image: np.ndarray) -> List[Detection]:
        """TFLite inference (optimized for RPi)"""
        input_tensor = self.preprocess(image)
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        self.interpreter.invoke()
        
        # Get outputs
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        class_ids = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        confidences = self.interpreter.get_tensor(self.output_details[2]['index'])[0]
        
        # Parse detections
        detections = []
        h_img, w_img = image.shape[:2]
        
        for i in range(len(confidences)):
            if confidences[i] >= self.conf_threshold:
                class_id = int(class_ids[i])
                
                # Only return tuta_absoluta (class 0)
                if class_id != 0:
                    continue
                
                # Convert normalized coordinates to pixel coordinates
                x_center, y_center, width, height = boxes[i]
                x1 = int((x_center - width/2) * w_img)
                y1 = int((y_center - height/2) * h_img)
                x2 = int((x_center + width/2) * w_img)
                y2 = int((y_center + height/2) * h_img)
                
                detections.append(Detection(
                    class_id=class_id,
                    class_name=self.class_names.get(class_id, 'unknown'),
                    confidence=float(confidences[i]),
                    bbox=(x1, y1, x2, y2)
                ))
        
        return detections
    
    def _parse_pytorch_results(self, results) -> List[Detection]:
        """Parse Ultralytics results"""
        detections = []
        
        if len(results) == 0 or results[0].boxes is None:
            return detections
        
        boxes = results[0].boxes
        for box in boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            
            # Only return tuta_absoluta (class 0)
            if class_id != 0:
                continue
            
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            detections.append(Detection(
                class_id=class_id,
                class_name=self.class_names.get(class_id, 'unknown'),
                confidence=confidence,
                bbox=(x1, y1, x2, y2)
            ))
        
        return detections
    
    def detect_from_camera(self, camera_id: int = 0) -> Tuple[List[Detection], np.ndarray]:
        """Capture frame from camera and run detection"""
        cap = cv2.VideoCapture(camera_id)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return [], None
        
        detections = self.detect(frame)
        return detections, frame


# Quick test
if __name__ == "__main__":
    # Test with your trained model
    detector = TutaDetector('D:/yolov8m_final/weights/best.pt')
    
    # Test with a sample image (update path)
    test_image = cv2.imread('test_sample.jpg')
    if test_image is not None:
        detections = detector.detect(test_image)
        print(f"Detected {len(detections)} Tuta absoluta")
        for d in detections:
            print(f"  - Confidence: {d.confidence:.3f}")