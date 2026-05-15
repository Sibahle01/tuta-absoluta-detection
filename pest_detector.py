# pest_detector.py - Updated version
from ultralytics import YOLO
import socket
import json
import time
import os
from PIL import Image

# Load your trained model (99.1% mAP50)
model = YOLO('D:/yolov8m_final/weights/best.pt')

# UDP setup - send to MATLAB
UDP_IP = '192.168.7.2'  # Your MATLAB computer IP
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("🐛 Pest Detector Starting...")
print(f"📡 Sending detections to {UDP_IP}:{UDP_PORT}")

def test_with_image(image_path):
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"⚠️ Image {image_path} not found. Creating dummy test image...")
        # Create a dummy test image
        img = Image.new('RGB', (640, 640), color='green')
        img.save(image_path)
        print(f"✅ Created {image_path}")
    
    results = model(image_path)
    pest_count = len(results[0].boxes)
    print(f"Detected {pest_count} pests")
    
    # Send to MATLAB
    data = json.dumps({'pest_count': pest_count, 'timestamp': time.time()})
    sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
    return pest_count

def test_with_camera():
    import cv2
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ Camera not found. Running in simulation mode...")
        simulate_detections()
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model(frame)
        pest_count = len(results[0].boxes)
        
        # Send to MATLAB
        data = json.dumps({'pest_count': pest_count, 'timestamp': time.time()})
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
        
        # Display
        annotated = results[0].plot()
        cv2.imshow('Pest Detection', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def simulate_detections():
    """Generate simulated pest counts for testing"""
    import random
    print("🔄 Running simulation mode - generating random pest counts")
    for i in range(50):
        # Simulate pest pressure pattern
        if i < 10:
            pest_count = random.randint(0, 1)
        elif i < 20:
            pest_count = random.randint(1, 3)
        elif i < 30:
            pest_count = random.randint(3, 6)
        elif i < 40:
            pest_count = random.randint(5, 8)
        else:
            pest_count = random.randint(2, 4)
        
        data = json.dumps({'pest_count': pest_count, 'timestamp': time.time()})
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
        print(f"📤 Sent: {pest_count} pests")
        time.sleep(1)  # Send every second

# Run test
if __name__ == "__main__":
    # Option 1: Test with sample image
    test_with_image('test_image.jpg')
    
    # Option 2: Simulation mode (uncomment to use)
    # simulate_detections()
    
    # Option 3: Use camera (uncomment to use)
    # test_with_camera()
    
    print("✅ Detection sent to MATLAB")